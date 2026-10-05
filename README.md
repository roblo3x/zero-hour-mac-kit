# Zero Hour на двух Mac с Apple Silicon

Набор для установки **Command & Conquer: Generals — Zero Hour**, игры вдвоём через интернет и переключения на **Advanced AI Mod 0.98 improved by AEI v2.8** для одиночного Skirmish. Версия движка для обоих игроков закреплена: **GeneralsXZH 1.0.2**.

Репозиторий содержит только инструкции и скрипт. Игровые файлы EA и файлы AI-мода сюда не входят. Каждому игроку нужна собственная легальная копия игры. Мод скачивается с сайта автора.

## 1. Получить игровые файлы

Купи игру в [Steam](https://store.steampowered.com/app/2732960/Command__Conquer_Generals_Zero_Hour/) или используй уже приобретённую копию. Для GeneralsX нужны файлы **Generals** и **Zero Hour**. На Mac Steam может не предлагать установку Windows-версии; официальный проект GeneralsX описывает два способа получить файлы: установить Windows Steam в [CrossOver](https://www.codeweavers.com/crossover) или использовать [SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD). Можно также скопировать файлы **с собственного** Windows-компьютера. [Подробная официальная инструкция](https://github.com/fbraz3/GeneralsX/wiki/Getting-the-Game-Files).

Найди две папки, содержащие соответственно `INI.big` (Generals) и `INIZH.big` вместе с `generals.exe` (Zero Hour). Удобно положить их сначала в `~/Downloads/Generals` и `~/Downloads/GeneralsZH`. Пути с пробелами в командах ниже обязательно заключай в кавычки.

## 2. Установить GeneralsXZH и импортировать файлы

Нужны macOS на Apple Silicon, Python 3 и примерно 3 ГБ свободного места для копии игровых данных. В Terminal:

```sh
git clone https://github.com/roblo3x/zero-hour-mac-kit.git
cd zero-hour-mac-kit
python3 zhkit.py install-engine
python3 zhkit.py import-data --generals "$HOME/Downloads/Generals" --zh "$HOME/Downloads/GeneralsZH"
python3 zhkit.py status
```

Если `git` недоступен, скачай этот репозиторий кнопкой **Code → Download ZIP** на GitHub, распакуй и запускай те же команды из распакованной папки. Если команда `python3` отсутствует, установи [Python для macOS](https://www.python.org/downloads/macos/).

Скрипт скачивает **официальный** `macOS-GeneralsXZH.zip` версии 1.0.2, проверяет SHA-256 и помещает приложение в `~/Applications/GeneralsXZH.app`. Файлы игры копируются в `~/GeneralsX/Generals` и `~/GeneralsX/GeneralsZH`. Он откажется перезаписать уже существующие папки. Если приложение уже установлено, пропусти `install-engine`. Открой `~/Applications/GeneralsXZH.app` через Finder. Если macOS блокирует запуск неподписанного приложения, после первой попытки открой **System Settings → Privacy & Security → Open Anyway** — это описано в [инструкции GeneralsX](https://github.com/fbraz3/GeneralsX/wiki/How-to-Install-GeneralsX).

## 3. Игра вдвоём через интернет

Оба игрока устанавливают **одну и ту же версию 1.0.2** и начинают с обычной Zero Hour, без AI-мода и других модов. На каждом Mac:

```sh
python3 zhkit.py online-check
```

В игре открой **Multiplayer → Online** и выполни вход через браузер. Один игрок открывает **Custom Lobby → Host**, создаёт комнату с паролем. Второй открывает **Custom Lobby → Refresh**, выбирает комнату и нажимает **Join**. Для первого теста возьмите встроенную карту и играйте **1 на 1 без ботов**. Пустой список общих комнат не мешает создать свою. В релизе GeneralsX 1.0.2 интернет-мультиплеер встроен в Zero Hour; отдельные GameRanger, Hamachi и Wine для этого пути не требуются. [Описание релиза](https://github.com/fbraz3/GeneralsX/releases/tag/1.0.2).

Встроенный режим **LAN/Network** в GeneralsX сейчас отмечен как проблемный в [трекере проекта](https://github.com/fbraz3/GeneralsX/issues/337), поэтому для двух Mac используйте **Online → Custom Lobby**, даже когда сидите в одной локальной сети. Интернет и доступ к сервису нужны обоим.

## 4. Умные боты для одиночной игры

Скачай архив **AdvancedAIMod_v2.8.9.rar** со [страницы автора на ModDB](https://www.moddb.com/mods/advanced-ai-mod-for-zero-hour-improved-by-aei/downloads/advanced-ai-mod-098-improved-by-aei-v28). Должна быть именно версия для **ZH 1.04**; скрипт сверяет SHA-256 архива `d15f78a0712e9046523aa731006d4882dab83b604e4c68b7dfdb2bc70730dfdb` и распаковывает его штатным `bsdtar`.

Закрой игру. Затем:

```sh
python3 zhkit.py ai-on "$HOME/Downloads/AdvancedAIMod_v2.8.9.rar"
python3 zhkit.py status
```

Запусти GeneralsXZH, открой **Skirmish**, выбери бота **Hard**. AEI меняет скрипты и настройки ботов: экономику, расширение базы, состав атак и использование способностей. Это скриптовый AI, не LLM. [Описание автора](https://www.moddb.com/mods/advanced-ai-mod-for-zero-hour-improved-by-aei).

Перед сетевой игрой закрой игру и восстанови исходные файлы:

```sh
python3 zhkit.py ai-off
python3 zhkit.py online-check
```

Скрипт сохраняет заменённые файлы в `~/Library/Application Support/ZeroHourMacKit/ai-originals` и при отключении сверяет их контрольные суммы. Если после установки AI файлы менялись вручную, автоматическое восстановление остановится, чтобы не затереть твои правки.

**Предел проверки:** установка AEI 2.8 подтверждена на оригинальной ZH 1.04 под Wine. GeneralsX заявляет поддержку модов и считывает обычные файлы поверх `.big`, но поведение именно AEI 2.8 в его Skirmish ещё надо проверить в живом матче. Поэтому сначала сыграй 10–15 минут против Hard: бот должен строить базу, собирать ресурсы и атаковать. Если он не развивается, выполни `ai-off` и сообщи версию приложения и лог. Не включай AEI в сетевом матче, пока оба игрока не подтвердят совместимость этого набора файлов.

## Проверка и проблемы

```sh
python3 zhkit.py status
```

Если приложение не находит файлы игры, убедись, что `~/GeneralsX/GeneralsZH/INIZH.big` и `~/GeneralsX/Generals/INI.big` существуют. Если возникают ошибки при скачивании, возьми архив вручную из [официального релиза](https://github.com/fbraz3/GeneralsX/releases/tag/1.0.2), сверь SHA-256 `92930b71c232eb289cf743eb8cdc4081020a870dfdaa2adad553bec2798ac568` и распакуй `GeneralsXZH.app` в `~/Applications`.

Код набора — [MIT](LICENSE). Права на игру, GeneralsX и AEI принадлежат их авторам.
