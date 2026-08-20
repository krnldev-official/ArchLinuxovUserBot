#Linux Angel Devoloper
#Official mpdules ArchLinuxov Api
import platform
import time
import hydrogram
from hydrogram import Client
from hydrogram.types import Message

BOT_START_TIME = time.time()


def get_readable_time(seconds: int) -> str:
    """Uptime"""
    count = 0
    time_list = []
    time_suffix_list = ["с", "м", "ч", "д"]

    while count < 4:
        count += 1
        remainder, result = (
            divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        )
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]
    if len(time_list) == 0:
        return "0с"
    return " ".join(time_list[::-1])


async def info_cmd(client: Client, message: Message, api):
    """Info информация о боте"""
    info = await api.get_system_info(client)

    text = (
        "<b> ArchLinuxok UserBot Info</b>\n\n"
        f"<b>Движок:</b> <code>Hydrogram v{hydrogram.__version__}</code>\n"
        f"<b>Режим ядра:</b> <code>{info.get('kernel', 'linux')}</code>\n"
        f"<b>Python:</b> <code>v{platform.python_version()}</code>\n"
        f"<b> Хост / Узел:</b> <code>{platform.node()}</code>\n"
        f"<b>ОС:</b> <code>{info.get('os', platform.system())}</code>"
    )
    await message.edit_text(text)


async def sysinfo_cmd(client: Client, message: Message, api):
    """Команда .sysinfo — детализированные метрики железа и ОС."""
    await message.edit_text("<i>Сбор инфоммации...</i>")
    info = await api.get_system_info(client)

    text = (
        "<b> System Info & Hardware Metrics</b>\n\n"
        f"<b> Операционная система:</b> <code>{info.get('os', 'Linux')}</code>\n"
        f"<b> Архитектура CPU:</b> <code>{info.get('cpu', platform.machine())}</code>\n"
        f"<b> Загрузка CPU:</b> <code>{info.get('cpu_usage', 'N/A')}</code>\n"
        f"<b>  Использование ОЗУ:</b> <code>{info.get('ram_usage', 'N/A')}</code>\n"
        f"<b> Задержка сети (Ping):</b> <code>{info.get('ping', 'N/A')}</code>\n"
        f"<b> Uptime хоста:</b> <code>{info.get('uptime', 'N/A')}</code>"
    )
    await message.edit_text(text)


async def uptime_cmd(client: Client, message: Message, api):
    """Команда .uptime — аптайм процесса юзербота и сервера """
    uptime_sec = int(time.time() - BOT_START_TIME)
    bot_uptime_str = get_readable_time(uptime_sec)

    info = await api.get_system_info(client)
    host_uptime_str = info.get("uptime", "N/A")

    text = (
        "<b>⏱ Uptime Report</b>\n\n"
        f"<b> Работа бота:</b> <code>{bot_uptime_str}</code>\n"
        f"<b> Работа системы (Host):</b> <code>{host_uptime_str}</code>"
    )
    await message.edit_text(text)


def setup(registry):
    registry.commands["info"] = info_cmd
    registry.commands["sysinfo"] = sysinfo_cmd
    registry.commands["uptime"] = uptime_cmd


