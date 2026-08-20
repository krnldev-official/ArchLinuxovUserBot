#autor=LinuxAngel
#osred=False
#kernel=kernel
#core=True
#Officoal modules ArchLimuxov Api
from api import registry
def setup(registry):
    registry.register_command("help", mod_help, module_name="Help")
    registry.set_meta("Help", {"autor": "LinuxAngel", "official": True})

async def mod_help(client, message, api):
    info = await api.get_system_info(client, message)
    
    official_cmds = []
    unofficial_cmds = []

    for mod_name, cmds in registry.module_cmds.items():
        meta = registry.get_meta(mod_name)
        is_official = meta.get("official", False)
        
        for cmd in cmds:
            line = f"{cmd} - ({mod_name})"
            if is_official:
                official_cmds.append(line)
            else:
                unofficial_cmds.append(line)

    off_str = "\n".join(official_cmds) if official_cmds else "Нет"
    unoff_str = "\n".join(unofficial_cmds) if unofficial_cmds else "Нет"

    text = f"⚙️ ArchLinuxok Userbot\n"
    text += f"⏱ Uptime: {info['uptime']} | Kernel: {info['kernel']}\n\n"
    text += f"Official modules:\n{off_str}\n\n"
    text += f"No official modules:\n{unoff_str}\n\n"
    text += "Используй .help <команда> для подробностей"

    await api.edit_or_reply(message, text)
