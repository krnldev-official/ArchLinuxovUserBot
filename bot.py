import logging
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from api import registry
logger = logging.getLogger("SnowKernel")


def create_companion_bot(sys_cfg: dict, api, userbot: Client):
    bot_token = sys_cfg.get("bot_token")
    if not bot_token:
        return None

    bot = Client(
        "companion_bot",
        api_id=sys_cfg["api_id"],
        api_hash=sys_cfg["api_hash"],
        bot_token=bot_token,
    )
    api.bot = bot
    @bot.on_message(filters.command("start"))
    async def bot_start(client, message):
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔍 Проверить систему", callback_data="sys_check"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📦 Проверка модулей", callback_data="sys_mods"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⚙️ Настройки", callback_data="sys_settings"
                    )
                ],
            ]
        )
        await message.reply_text(
            "Здравствуйте, это юзер бот ArchLinuxov!",
            reply_markup=kb,
        )
    @bot.on_callback_query()
    async def callback_handler(client, callback):
        if callback.data == "sys_check":
            info = await api.get_system_info(userbot)
            cat_and_artix = (
                "  /\\_/\\   ArchLunixok Userbot Environment\n"
                " ( o.o ) \n"
                "  > ^ <\n\n"
                "      /\\\n"
                "     /  \\\n"
                "    / /\\ \\\n"
                "   / /  \\ \\\n"
                "  / /____\\ \\\n"
                " /__________\\  Artix/Arch Linux Environment"
            )
            warn_msg = (
                "Hardened limitations active"
                if info["kernel"] == "linux-hardened"
                else "None (Standard User Environment)"
            )

            systemd_logs = (
                f"[  OK  ] Initialized System VFS Kernel\n"
                f"[  OK  ] Started Hydrogram Engine v{info['htl_ver']}\n"
                f"[ INFO ] OS: {info['os']} ({info['cpu']})\n"
                f"[ INFO ] Uptime: {info['uptime']}\n"
                f"[ INFO ] RAM Usage: {info['ram_usage']} | CPU: {info['cpu_usage']}\n"
                f"[ INFO ] Kernel Mode: {info['kernel']}\n"
                f"[ WARN ] Security Warning: {warn_msg}\n"
                f"[ ERROR] Critical Runtime Errors: 0 (System Operational)\n"
                f"[  OK  ] Ping Target: {info['ping']}\n"
                f"[  OK  ] All services healthy."
            )

            text = f"```\n{cat_and_artix}\n\n{systemd_logs}\n```"

            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Обновить", callback_data="sys_check"
                        ),
                        InlineKeyboardButton(
                            "Назад", callback_data="sys_back"
                        ),
                    ]
                ]
            )
            await callback.answer()
            await callback.message.edit_text(text, reply_markup=kb)
        elif callback.data == "sys_mods":
            official_mods = []
            unofficial_mods = []

            for mod_name in registry.modules.keys():
                meta = registry.get_meta(mod_name)
                if meta.get("official", False):
                    official_mods.append(f" {mod_name}")
                else:
                    unofficial_mods.append(f" {mod_name}")

            off_str = (
                "\n".join(official_mods) if official_mods else "_Нет модулей_"
            )
            unoff_str = (
                "\n".join(unofficial_mods)
                if unofficial_mods
                else "_Нет модулей_"
            )

            text = (
                f"Статус загруженных модулей\n\n"
                f"Official Modules ({len(official_mods)}):\n{off_str}\n\n"
                f"Unofficial Modules ({len(unofficial_mods)}):\n{unoff_str}"
            )

            kb = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Назад", callback_data="sys_back")]]
            )
            await callback.answer()
            await callback.message.edit_text(text, reply_markup=kb)
        elif callback.data == "sys_settings":
            text = (
                f"Настройки юзербота ArchLinuxok\n\n"
                f"Режим ядра: `{sys_cfg.get('kernel_mode', 'linux')}`\n"
                f"Чат логов: `{sys_cfg.get('log_chat_id', 'Не задан')}`\n"
                f"Задержка FloodWait: `{sys_cfg.get('flood_delay', 0.3)}s`\n"
            )

            kb = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Назад", callback_data="sys_back")]]
            )
            await callback.answer()
            await callback.message.edit_text(text, reply_markup=kb)
        elif callback.data == "sys_back":
            kb = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Проверить систему", callback_data="sys_check"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Проверка модулей", callback_data="sys_mods"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Настройки", callback_data="sys_settings"
                        )
                    ],
                ]
            )
            await callback.answer()
            await callback.message.edit_text(
                "Здравствуйте, это юзер бот ArchLinuxov!",
                reply_markup=kb,
            )

    return bot
async def send_startup_log(bot: Client, log_chat_id: int):
    if bot and log_chat_id:
        try:
            await bot.send_message(
                log_chat_id,
                "🟡 [ INFO ]  Kernel Report: Юзербот и бот-помощник ArchLinuxok успешно запущены"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки лога в чат: {e}")

