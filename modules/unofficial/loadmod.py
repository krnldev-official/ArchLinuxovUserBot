#autor=LinuxAngel
#osred=True
#kernel=kernel
#core=True

import os
from api import registry
from loader import ModuleLoader

def setup(registry):
    registry.register_command("loadmod", mod_loadmod, module_name="Core")
    registry.register_command("lm", mod_loadmod, module_name="Core")
    
    registry.set_meta("Core", {
        "autor": "LinuxAngel",
        "osred": True,
        "kernel": "kernel",
        "core": True,
        "official": True
    })

async def mod_loadmod(client, message, api):
    """Загрузить и активировать модуль из отправленного .py файла."""
    reply = message.reply_to_message

    if not reply or not reply.document:
        await api.edit_or_reply(message, "Ответь на файл модуля")
        return

    doc = reply.document
    if not doc.file_name or not doc.file_name.endswith(".py"):
        await api.edit_or_reply(message, "Файл должен иметь расширение .py")
        return

    file_name = doc.file_name
    mod_name = file_name[:-3]
    
    # Сохраняем кастомные модули в папку неофициальных
    target_dir = os.path.join("modules", "unofficial")
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, file_name)

    await api.edit_or_reply(message, f"Загрузка модуля {file_name}...")

    try:
        if mod_name in registry.module_cmds:
            registry.unregister_module(mod_name)

        await client.download_media(message=reply, file_name=file_path)

        loader = ModuleLoader(modules_dir="modules", kernel=api.kernel)
        success = loader.load_module(mod_name)

        if success:
            # Принудительно ставим флагом, что модуль не официальный
            meta = registry.get_meta(mod_name)
            meta["official"] = False
            registry.set_meta(mod_name, **meta)

            await api.edit_or_reply(
                message, 
                f"Модуль {mod_name} успешно сохранен в неофициальные!\n"
                f"Проверь команды через .help"
            )
        else:
            if os.path.exists(file_path):
                os.remove(file_path)
            await api.edit_or_reply(message, f"Ошибка инициализации модуля {mod_name}!")

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        await api.edit_or_reply(message, f"Ошибка при скачивании: {e}")

