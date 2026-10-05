#!/usr/bin/env python3
"""Install GeneralsX ZH and toggle AEI AI on a user's own game assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


VERSION = "1.0.2"
ENGINE_URL = f"https://github.com/fbraz3/GeneralsX/releases/download/{VERSION}/macOS-GeneralsXZH.zip"
ENGINE_SHA256 = "92930b71c232eb289cf743eb8cdc4081020a870dfdaa2adad553bec2798ac568"
ENGINE_BINARY_SHA256 = "62bd04c72288bb0664834cdad02355c520bed14140d3ee3790ae4c6866b0d078"
AI_SHA256 = "d15f78a0712e9046523aa731006d4882dab83b604e4c68b7dfdb2bc70730dfdb"
ROOT = Path.home() / "GeneralsX"
ZH = ROOT / "GeneralsZH"
BASE = ROOT / "Generals"
APP = Path.home() / "Applications" / "GeneralsXZH.app"
STATE = Path.home() / "Library/Application Support/ZeroHourMacKit"
MANIFEST = STATE / "ai-manifest.json"


def die(message: str) -> None:
    raise SystemExit(f"Ошибка: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_platform() -> None:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        die("этот набор рассчитан на macOS с Apple Silicon (arm64)")


def check_zh() -> None:
    if not (ZH / "INIZH.big").is_file() or not (ZH / "generals.exe").is_file():
        die(f"нет файлов Zero Hour в {ZH}; выполните import-data")


def game_running() -> bool:
    for name in ("GeneralsXZH", "generals.exe"):
        if subprocess.run(["pgrep", "-x", name], capture_output=True, check=False).returncode == 0:
            return True
    return False


def ensure_closed() -> None:
    if game_running():
        die("закройте Zero Hour перед переключением AI")


def install_engine() -> None:
    if APP.exists():
        die(f"приложение уже существует: {APP}. Удалите его вручную, если хотите переустановить")
    with tempfile.TemporaryDirectory(prefix="zhkit-engine-") as temporary:
        root = Path(temporary)
        archive = root / "GeneralsXZH.zip"
        print(f"Скачиваю GeneralsXZH {VERSION} из официального релиза…")
        with urllib.request.urlopen(ENGINE_URL, timeout=60) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        if sha256(archive) != ENGINE_SHA256:
            die("контрольная сумма приложения не совпала; установка остановлена")
        subprocess.run(["ditto", "-x", "-k", str(archive), str(root)], check=True)
        extracted = root / "GeneralsXZH.app"
        if not (extracted / "Contents/MacOS/run.sh").is_file():
            die("в архиве нет ожидаемого приложения")
        APP.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(extracted), str(APP))
    print(f"Установлено: {APP}")


def import_data(generals: Path, zh: Path) -> None:
    generals, zh = generals.expanduser().resolve(), zh.expanduser().resolve()
    if not (generals / "INI.big").is_file():
        die(f"в папке Generals не найден INI.big: {generals}")
    if not (zh / "INIZH.big").is_file() or not (zh / "generals.exe").is_file():
        die(f"в папке Zero Hour не найдены INIZH.big и generals.exe: {zh}")
    if BASE.exists() or ZH.exists():
        die(f"{BASE} или {ZH} уже существует; существующие игровые файлы не перезаписываются")
    ROOT.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(generals, BASE)
        shutil.copytree(zh, ZH)
    except Exception:
        shutil.rmtree(BASE, ignore_errors=True)
        shutil.rmtree(ZH, ignore_errors=True)
        raise
    print(f"Игровые файлы скопированы в {ROOT}")


def read_manifest() -> dict:
    if not MANIFEST.is_file():
        die("AI-мод не включён через этот набор")
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def ai_enable(archive: Path) -> None:
    check_zh()
    ensure_closed()
    if MANIFEST.exists():
        die("AI-мод уже включён; сначала выполните ai-off")
    archive = archive.expanduser().resolve()
    if not archive.is_file() or sha256(archive) != AI_SHA256:
        die("нужен оригинальный AdvancedAIMod_v2.8.9.rar с ожидаемой SHA-256; ссылка в README")
    with tempfile.TemporaryDirectory(prefix="zhkit-ai-") as temporary:
        extracted = Path(temporary)
        subprocess.run(["bsdtar", "-xf", str(archive), "-C", str(extracted)], check=True)
        mod = extracted / "AdvancedAIMod v2.8/For ZH 1.04"
        script = mod / "SkirmishScripts.scb"
        ini = mod / "INI"
        if not script.is_file() or not (ini / "AIData.ini").is_file():
            die("архив не содержит ожидаемого набора для Zero Hour 1.04")
        files = {Path("Data/Scripts/SkirmishScripts.scb"): script}
        files.update({Path("Data/INI") / p.relative_to(ini): p for p in ini.rglob("*") if p.is_file()})
        backup = STATE / "ai-originals"
        if backup.exists():
            die(f"найдена старая резервная копия: {backup}; проверьте её вручную")
        backup.mkdir(parents=True, exist_ok=False)
        entries = []
        try:
            for relative, source in files.items():
                destination = ZH / relative
                if destination.exists() and not destination.is_file():
                    die(f"ожидался файл: {destination}")
                existed = destination.is_file()
                if existed:
                    saved = backup / relative
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(destination, saved)
                entries.append({"path": relative.as_posix(), "existed": existed, "mod_sha256": sha256(source)})
            # All originals are safe before a single game file changes.
            for relative, source in files.items():
                destination = ZH / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            MANIFEST.write_text(json.dumps({"version": "AEI 2.8 / ZH 1.04", "files": entries}, indent=2), encoding="utf-8")
        except Exception:
            for entry in entries:
                destination = ZH / entry["path"]
                saved = backup / entry["path"]
                if saved.is_file():
                    shutil.copy2(saved, destination)
                elif not entry["existed"]:
                    destination.unlink(missing_ok=True)
            shutil.rmtree(backup, ignore_errors=True)
            raise
    print("AEI 2.8 включён. Запустите Skirmish против бота Hard.")


def ai_disable() -> None:
    check_zh()
    ensure_closed()
    manifest = read_manifest()
    backup = STATE / "ai-originals"
    for entry in manifest["files"]:
        destination = ZH / entry["path"]
        if not destination.is_file() or sha256(destination) != entry["mod_sha256"]:
            die(f"файл изменён после установки AI: {destination}; автоматическое восстановление остановлено")
        if entry["existed"] and not (backup / entry["path"]).is_file():
            die(f"потеряна резервная копия: {backup / entry['path']}")
    for entry in manifest["files"]:
        destination = ZH / entry["path"]
        if entry["existed"]:
            shutil.copy2(backup / entry["path"], destination)
        else:
            destination.unlink()
    MANIFEST.unlink()
    shutil.rmtree(backup)
    print("Исходные файлы восстановлены. Можно играть по сети.")


def status() -> None:
    installed = next((app for app in (APP, Path('/Applications/GeneralsXZH.app')) if app.is_dir()), None)
    print(f"macOS/CPU: {platform.system()} / {platform.machine()}")
    print(f"GeneralsXZH: {installed if installed else 'не найден'}")
    print(f"Generals: {'есть' if (BASE / 'INI.big').is_file() else 'нет'}")
    print(f"Zero Hour: {'есть' if (ZH / 'INIZH.big').is_file() else 'нет'}")
    print(f"AEI 2.8: {'включён' if MANIFEST.is_file() else 'выключен'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("install-engine")
    importer = sub.add_parser("import-data")
    importer.add_argument("--generals", required=True, type=Path)
    importer.add_argument("--zh", required=True, type=Path)
    ai = sub.add_parser("ai-on")
    ai.add_argument("archive", type=Path)
    sub.add_parser("ai-off")
    sub.add_parser("online-check")
    args = parser.parse_args()
    check_platform()
    if args.command == "status":
        status()
    elif args.command == "install-engine":
        install_engine()
    elif args.command == "import-data":
        import_data(args.generals, args.zh)
    elif args.command == "ai-on":
        ai_enable(args.archive)
    elif args.command == "ai-off":
        ai_disable()
    elif args.command == "online-check":
        check_zh()
        if MANIFEST.exists():
            die("AI включён. Выполните ai-off перед сетевой игрой")
        installed = next((app for app in (APP, Path('/Applications/GeneralsXZH.app')) if app.is_dir()), None)
        if installed is None:
            die("GeneralsXZH не найден; выполните install-engine")
        binary = installed / "Contents/Resources/bin/GeneralsXZH"
        if not binary.is_file() or sha256(binary) != ENGINE_BINARY_SHA256:
            die("исполняемый файл GeneralsXZH отличается от версии 1.0.2")
        print("ZH и GeneralsXZH 1.0.2 найдены, AEI выключен. Откройте Online → Custom Lobby.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        die(str(error))
