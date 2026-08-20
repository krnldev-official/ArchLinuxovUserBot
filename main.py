import argparse
import asyncio
import glob
import json
import os
from hydrogram import Client, filters
from hydrogram.errors import (
    PasswordHashInvalid,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    SessionPasswordNeeded,
)
from api import archapi, registry
from bot import create_companion_bot, send_startup_log
from loader import ModuleLoader
from logger import KernelConfig
CONFIG_FILE = "config.json"
DEFAULT_SESSION = "snow_session"
def print_systemd_boot():
    print("[  OK  ] Started Virtual File System (VFS)")
    print("[  OK  ] Initialized Hydrogram MTProto Client")
    print("[ INFO ] ArchLinuxok UserBot Kernel Initializing...")
    print("[  OK  ] System Core Loaded\n")
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)
def find_existing_sessions():
    files = glob.glob("*.session")
    return [os.path.splitext(f)[0] for f in files]
async def register_session(api_id, api_hash, session_name=DEFAULT_SESSION):
    client = Client(session_name, api_id=api_id, api_hash=api_hash)
    await client.connect()
    while True:
        print("\n[ INFO ] Авторизация Telegram")
        phone = input("Введите номер телефона (+7...): ").strip()
        try:
            sent_code = await client.send_code(phone)
            break
        except Exception as e:
            print(f"\n[ ERROR ] Ошибка отправки кода: {e}")
            print("Введите корректный номер!")
    while True:
        print("\n[ INFO ] Подтверждение входа")
        code = input("Введите полученный код из Telegram: ").strip()
        try:
            await client.sign_in(phone, sent_code.phone_code_hash, code)
            break
        except SessionPasswordNeeded:
            while True:
                print("\n[ INFO ] Обнаружена 2FA защита")
                password = input("Введите пароль двухэтапки: ").strip()
                try:
                    await client.check_password(password)
                    break
                except PasswordHashInvalid:
                    print("\n[ ERROR ] Неправильный пароль! Попробуйте снова.")
            break
        except (PhoneCodeInvalid, PhoneCodeExpired):
            print("\n[ ERROR ] Неверный или истекший код!")
        except Exception as e:
            print(f"\n[ ERROR ] Ошибка: {e}")
    await client.disconnect()
    print(f"\n[  OK  ] Сессия '{session_name}' успешно создана и сохранена!")
async def main():
    parser = argparse.ArgumentParser(description="ArchLinuxok Kernel Engine")
    parser.add_argument(
        "--kernel", choices=["linux", "linux-zen", "linux-hardened"]
    )
    args = parser.parse_args()
    print_systemd_boot()
    cfg = load_config()
    sys_cfg = cfg.get("system", {})
    existing_sessions = find_existing_sessions()
    active_session_name = (
        existing_sessions[0] if existing_sessions else DEFAULT_SESSION
    )
    print("=== ArchLinuxok Control Menu ===")

    if not existing_sessions or not sys_cfg.get("api_id"):
        print("[ INFO ] Обнаружен первый запуск или отсутствие сессии.")
        print("1) Ввести конфиг (API_ID, API_HASH, BOT_TOKEN)")
        print("2) Зарегистрировать новую сессию (номер телефона)")

        while True:
            choice = input("\n[ INFO ] Выберите пункт (1 или 2): ").strip()
            if choice == "1":
                api_id = input("API_ID: ").strip()
                api_hash = input("API_HASH: ").strip()
                bot_token = input("BOT_TOKEN: ").strip()
                log_chat = input(
                    "Log Chat ID (или нажмите Enter): "
                ).strip()

                sys_cfg["api_id"] = (
                    int(api_id) if api_id.isdigit() else api_id
                )
                sys_cfg["api_hash"] = api_hash
                sys_cfg["bot_token"] = bot_token
                sys_cfg["log_chat_id"] = (
                    int(log_chat) if log_chat.lstrip("-").isdigit() else None
                )
                sys_cfg["kernel_mode"] = "linux"
                cfg["system"] = sys_cfg
                save_config(cfg)
                print("[  OK  ] Конфиг успешно сохранен!")

            elif choice == "2":
                if not sys_cfg.get("api_id"):
                    print(
                        "\n[ ERROR ] Сначала укажите API_ID и API_HASH (пункт 1)!"
                    )
                    continue
                await register_session(
                    sys_cfg["api_id"],
                    sys_cfg["api_hash"],
                    session_name=active_session_name,
                )
                break
            else:
                print("[ ERROR ] Введите нормальный номер пункта (1 или 2)!")
    else:
        print(f"[  OK  ] Найдена активная сессия: '{active_session_name}.session'")
        print("1) Изменить API_ID / API_HASH / BOT_TOKEN")
        print("2) Запустить юзербот")
        print("3) Добавить еще один аккаунт (новую сессию)")
        while True:
            choice = input("\n[ INFO ] Выберите пункт (1, 2 или 3): ").strip()
            if choice == "1":
                api_id = input("Новый API_ID: ").strip()
                api_hash = input("Новый API_HASH: ").strip()
                bot_token = input("Новый BOT_TOKEN: ").strip()
                sys_cfg["api_id"] = (
                    int(api_id) if api_id.isdigit() else api_id
                )
                sys_cfg["api_hash"] = api_hash
                if bot_token:
                    sys_cfg["bot_token"] = bot_token
                cfg["system"] = sys_cfg
                save_config(cfg)
                print("[  OK  ] Данные успешно обновлены!")
            elif choice == "2":
                break
            elif choice == "3":
                new_session_name = input(
                    "Введите имя для новой сессии: "
                ).strip()
                if not new_session_name:
                    new_session_name = f"session_{len(existing_sessions) + 1}"
                await register_session(
                    sys_cfg["api_id"],
                    sys_cfg["api_hash"],
                    session_name=new_session_name,
                )
                active_session_name = new_session_name
                break
            else:
                print("[ ERROR ] Введите нормальный номер пункта (1, 2 или 3)!")

    kernel_mode = args.kernel or sys_cfg.get("kernel_mode", "linux")
    kernel = KernelConfig(kernel_mode)
    api = archapi(kernel)

    print("\n[ INFO ] Загрузка системных модулей...")
    loader = ModuleLoader(modules_dir="modules", kernel=kernel)
    loader.load_all()

    userbot = Client(
        active_session_name,
        api_id=sys_cfg["api_id"],
        api_hash=sys_cfg["api_hash"],
    )
    bot = create_companion_bot(sys_cfg, api, userbot)

    @userbot.on_message(filters.me & filters.text)
    async def userbot_router(client, message):
        text = message.text
        if not text.startswith("."):
            return
        cmd = text.split()[0][1:]
        if cmd in registry.commands:
            func = registry.commands[cmd]
            await func(client, message, api)

    print("[  OK  ] Запуск сессий Hydrogram...")
    await userbot.start()

    if bot:
        await bot.start()
        print("[  OK  ] Бот-помощник подключен")
        await send_startup_log(bot, sys_cfg.get("log_chat_id"))

    print("[  OK  ] ArchLinuxok UserBot успешно запущен и работает в штатном режиме\n")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[ WARN ] Работа системы остановлена пользователем.")
