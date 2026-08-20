#Autor=Necromanser
#LinuxovAngel Api dev
#Necromanser api dev 2
import os
import sys
import asyncio
def setup(registry):
    registry.register_command("restart", mod_restart, module_name="Core")
    registry.register_command("reboot", mod_restart, module_name="Core")
async def mod_restart(client, message, api):
    """Перезапустить юзербота"""
    await api.edit_or_reply(message, "Юзербот перезапускается...")
    await asyncio.sleep(1)
    try:
        await client.stop()
    except Exception:
        pass
    os.execv(sys.executable, [sys.executable] + sys.argv)

