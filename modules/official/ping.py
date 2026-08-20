#core=True
#autor=Necromanser
#Official modules archLinuxov api
#Dev 2 biuld
import time
def setup(registry):
    registry.register_command("ping", mod_ping)
async def mod_ping(client, message, api):
    start = time.perf_counter()
    await client.get_me()
    end = time.perf_counter()  
    ms = round((end - start) * 1000, 2)
    await api.edit_or_reply(message, f"Latency:{ms}ms\nKernel: {api.kernel.mode}")

