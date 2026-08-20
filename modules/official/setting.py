#autor=LinuxAngel
#osred=False
#kernel=kernel
#Dev 2 biuld
#Modules official
#No work modules!
#core=True
import json
import os
CONFIG_FILE = "config.json"

def setup(registry):
    registry.register_command("setting", mod_setting, module_name="Settings")
    registry.register_command("setval", mod_setval, module_name="Settings")
    registry.set_meta("Settings", {"autor": "LinuxAngel", "official": True})

def read_cfg():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"system": {}, "modules_config": {}}

def write_cfg(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def mod_setting(client, message, api):
    args = api.get_args(message)
    cfg = read_cfg()
    sys_cfg = cfg.get("system", {})

    if args == "mod":
        text = "Настройки модулей:\n"
        mod_cfgs = cfg.get("modules_config", {})
        if not mod_cfgs:
            text += "Нет сохраненого конфига модулей"
        else:
            for m_name, m_vals in mod_cfgs.items():
                text += f"\nМодуль {m_name}:\n"
                for k, v in m_vals.items():
                    text += f"  {k}: {v}\n"
        await api.edit_or_reply(message, text)
        return
    text = "Выберите настройки:\n\n"
    text += "Системные настройки (.setting):\n"
    text += f"1. Kernel mode: {sys_cfg.get('kernel_mode', 'linux')}\n"
    text += f"2. Floodwait: {sys_cfg.get('floodwait', 3)}s\n"
    text += f"3. Bot Token: {'Установлен' if sys_cfg.get('bot_token') else 'Отсутствует'}\n"
    text += f"4. Auto Update: {sys_cfg.get('auto_update', True)}\n"
    text += f"5. Version: {sys_cfg.get('version', '1.0.0')}\n\n"
    text += "Просмотр конфигов модулей: .setting mod\n"
    text += "Изменение параметра: .setval <ключ> <значение>"
    await api.edit_or_reply(message, text)
async def mod_setval(client, message, api):
    args = api.get_args_list(message)
    if len(args) < 2:
        await api.edit_or_reply(message, "Использование: .setval floodwait 5")
        return
    key, val = args[0], args[1]
    cfg = read_cfg()
    if key in cfg.get("system", {}):
        if val.isdigit():
            val = int(val)
        elif val.lower() in ["true", "false"]:
            val = val.lower() == "true"
            
        cfg["system"][key] = val
        write_cfg(cfg)
        await api.edit_or_reply(message, f"Параметр {key} изменен на {val}")
    else:
        await api.edit_or_reply(message, f"Ключ {key} не найден в системном конфиге")

