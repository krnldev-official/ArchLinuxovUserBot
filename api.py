import asyncio
import getpass
import logging
import os
import platform
import shlex
import socket
import sys
import time
from typing import Dict, Any, List, Optional, Union
import hydrogram
logger = logging.getLogger("ArchKernel")
START_TIME = time.time()
class ModuleRegistry:
    def __init__(self):
        self.commands: Dict[str, Any] = {}          
        self.modules: Dict[str, Any] = {}
        self.module_cmds: Dict[str, List[str]] = {} 
        self.module_meta: Dict[str, Dict[str, Any]] = {}

    def register_command(self, cmd_name: str, func, module_name: str = "Core") -> None:
        cmd_name = cmd_name.lower().strip()
        self.commands[cmd_name] = func
        if module_name not in self.module_cmds:
            self.module_cmds[module_name] = []
        if cmd_name not in self.module_cmds[module_name]:
            self.module_cmds[module_name].append(cmd_name)
    def set_meta(
        self,
        module_name: str,
        data: Optional[Dict[str, Any]] = None,
        autor: str = "Unknown",
        osred: bool = False,
        kernel: str = "kernel",
        core: bool = False,
        **extra
    ) -> None:
        if module_name not in self.module_meta:
            self.module_meta[module_name] = {
                "autor": autor,
                "osred": bool(osred),
                "kernel": kernel,
                "core": bool(core),
                "official": False
            }

        if isinstance(data, dict):
            self.module_meta[module_name].update(data)
        if extra:
            self.module_meta[module_name].update(extra)
    def get_meta(self, module_name: str) -> Dict[str, Any]:
        return self.module_meta.get(
            module_name,
            {"autor": "Unknown", "osred": False, "kernel": "kernel", "core": False}
        )

    def unregister_module(self, module_name: str) -> None:
        if module_name in self.module_cmds:
            for cmd in self.module_cmds[module_name]:
                self.commands.pop(cmd, None)
            del self.module_cmds[module_name]
        self.modules.pop(module_name, None)
        self.module_meta.pop(module_name, None)


class ArchAPI:

    def __init__(self, kernel):
        self.kernel = kernel

    async def get_system_info(self, client, message=None) -> dict:
        uptime_seconds = int(time.time() - START_TIME)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)        
        uptime_parts = []
        if days:
            uptime_parts.append(f"{days}d")
        if hours:
            uptime_parts.append(f"{hours}h")
        if minutes:
            uptime_parts.append(f"{minutes}m")
        uptime_parts.append(f"{seconds}s")
        uptime_str = " ".join(uptime_parts)
        start_ping = time.perf_counter()
        ping_ms = "N/A"
        if message:
            end_ping = time.perf_counter()
            ping_ms = f"{round((end_ping - start_ping) * 1000, 2)}ms"
        me_user = await client.get_me() if client else None
        me_str = f"@{me_user.username}" if me_user and me_user.username else (me_user.first_name if me_user else "User")
        ram_usage = "N/A"
        cpu_usage = "N/A"
        try:
            import psutil
            ram_usage = f"{psutil.virtual_memory().percent}%"
            cpu_usage = f"{psutil.cpu_percent()}%"
        except ImportError:
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo") as f:
                    lines = f.readlines()
                    total = int(lines[0].split()[1])
                    free = int(lines[1].split()[1])
                    ram_usage = f"{round((1 - free/total)*100, 1)}%"
        branch = "main"
        git_status = "Clean"
        upd = "Latest"
        git_res = await self.exec_shell("git rev-parse --abbrev-ref HEAD")
        if git_res["code"] == 0 and git_res["stdout"]:
            branch = git_res["stdout"]
        git_stat_res = await self.exec_shell("git status --porcelain")
        if git_stat_res["code"] == 0 and git_stat_res["stdout"]:
            git_status = "Modified"
        return {
            "me": me_str,
            "version": "1.0.0",
            "build": "Arch-Release",
            "prefix": ".",
            "platform": platform.system(),
            "upd": upd,
            "uptime": uptime_str,
            "cpu_usage": cpu_usage,
            "ram_usage": ram_usage,
            "branch": branch,
            "hostname": socket.gethostname(),
            "user": getpass.getuser(),
            "os": f"{platform.system()} {platform.release()}",
            "kernel": getattr(self.kernel, "mode", "linux"),
            "cpu": platform.machine(),
            "ping": ping_ms,
            "python_ver": platform.python_version(),
            "htl_ver": hydrogram.__version__,
            "git_status": git_status
        }

    async def format_text(self, text: str, client, message=None) -> str:
        info = await self.get_system_info(client, message)
        try:
            class SafeDict(dict):
                def __missing__(self, key):
                    return f"{{{key}}}"
            return text.format_map(SafeDict(info))
        except Exception as e:
            logger.error(f"Format text error: {e}")
            return text
    async def edit_or_reply(self, message, text: str, disable_web_page_preview: bool = True):
        if getattr(self.kernel, "flood_delay", 0) > 0:
            await asyncio.sleep(self.kernel.flood_delay)

        formatted_text = text

        try:
            if hasattr(message, "from_user") and message.from_user and message.from_user.is_self:
                return await message.edit_text(
                    formatted_text,
                    disable_web_page_preview=disable_web_page_preview
                )
            else:
                return await message.reply_text(
                    formatted_text,
                    disable_web_page_preview=disable_web_page_preview
                )
        except Exception as e:
            logger.error(f"[API Exec Error] edit_or_reply: {e}")
            return None

    def get_args(self, message) -> str:
        if not message.text:
            return ""
        args = message.text.split(maxsplit=1)
        return args[1].strip() if len(args) > 1 else ""

    def get_args_list(self, message) -> List[str]:
        raw_args = self.get_args(message)
        if not raw_args:
            return []
        return shlex.split(raw_args)

    async def exec_shell(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                return {
                    "code": process.returncode,
                    "stdout": stdout.decode("utf-8", errors="replace").strip(),
                    "stderr": stderr.decode("utf-8", errors="replace").strip()
                }
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "code": -1,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds."
                }
        except Exception as e:
            logger.error(f"[API Shell Error]: {e}")
            return {"code": -1, "stdout": "", "stderr": str(e)}

    async def delete(self, message, delay: int = 0):
        if delay > 0:
            await asyncio.sleep(delay)
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"[API Exec Error] delete: {e}")
archapi = ArchAPI
registry = ModuleRegistry()
