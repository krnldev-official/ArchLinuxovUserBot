#autor=LinuxAngel
#ArchLinuxov api work
#Модуль не приножлэеит изменению
import asyncio
import html
import logging
import os
import re
import shlex
import signal
import time
from hydrogram import Client
from hydrogram.types import Message
logger = logging.getLogger("SnowKernel.Terminal")
ACTIVE_CMDS = {}
DANGEROUS_RM_TARGETS = {
    "/",
    "/bin",
    "/boot",
    "/dev",
    "/etc",
    "/lib",
    "/lib64",
    "/opt",
    "/proc",
    "/root",
    "/sbin",
    "/sys",
    "/usr",
    "/var",
}
DANGEROUS_RM_FILES = {
    "/etc/passwd",
    "/etc/shadow",
}
DANGEROUS_COMMANDS = [
    r"dd\s+.*if=.*of=/dev/",
    r"mkfs\.",
    r"fdisk\s+\/dev/",
    r"\\x72\\x6d\\x20\\x2d\\x72\\x66\\x20\\x2f",
    r"chmod\s+.*000\s+.*\/",
    r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:",
    r"cat\s+.*\/dev\/urandom\s+>\s+\/dev\/[hsv]d[a-z]",
    r"ln\s+.*-s\s+\/\s+\/dev\/null",
    r"echo\s+[\"']?[A-Za-z0-9+/=]{20,}[\"']?\s*\|\s*base64\s+-d\s*\|\s*(sh|bash|zsh)",
    r"base64\s+-d\s*\|\s*(sh|bash|zsh|dash|ksh)",
    r"curl\s+.*\|\s*(sh|bash|zsh|dash|ksh)",
    r"wget\s+.*-O\s*-\s*\|\s*(sh|bash|zsh|dash|ksh)",
    r"nc\s+.*-e\s+(sh|bash|zsh)",
    r"ncat\s+.*-e\s+(sh|bash|zsh)",
    r"python[23]?\s+-c\s+[\"']import\s+os",
    r"python[23]?\s+-c\s+[\"']import\s+socket",
    r"kill\s+-9\s+1\b",
]
def _split_command(cmd: str) -> list[str]:
    try:
        lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return []
def _is_dangerous_rm_target(target: str) -> bool:
    if not target or target.startswith("-"):
        return False
    target = target.rstrip()
    normalized = os.path.normpath(target)
    if normalized in DANGEROUS_RM_TARGETS | DANGEROUS_RM_FILES:
        return True
    if normalized == "/":
        return target in {"/*", "/**"}
    for dangerous_target in DANGEROUS_RM_TARGETS - {"/"}:
        if normalized in {f"{dangerous_target}/*", f"{dangerous_target}/**"}:
            return True
    return False
def _has_dangerous_rm(cmd: str) -> bool:
    tokens = _split_command(cmd)
    if not tokens:
        return False
    separators = {";", "&&", "||", "|", "&"}
    rm_names = {"rm", "/bin/rm", "/usr/bin/rm"}
    for index, token in enumerate(tokens):
        if token not in rm_names:
            continue
        for target in tokens[index + 1 :]:
            if target in separators:
                break
            if target == "--":
                continue
            if _is_dangerous_rm_target(target):
                return True
    return False
def is_dangerous(cmd: str) -> bool:
    if _has_dangerous_rm(cmd):
        return True
    for pattern in DANGEROUS_COMMANDS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False
async def stream_reader(stream, buffer_list):
    while True:
        data = await stream.read(1024)
        if not data:
            break
        buffer_list.append(data.decode("utf-8", errors="replace"))


async def terminal_cmd(client: Client, message: Message, api):
    """Выполнение консольной команды с выводом"""
    cmd = message.text.split(maxsplit=1)
    user_command = cmd[1] if len(cmd) > 1 else ""
    if not user_command and message.reply_to_message:
        user_command = message.reply_to_message.text or ""
    if not user_command:
        await message.edit_text(
            "<b>[ ERROR ]</b> Укажите команду: <code>.exec &lt;команда&gt;</code>"
        )
        return

    if is_dangerous(user_command):
        await message.edit_text(
            f"<b>[ WARN ] Command Protection Intercepted!</b>\n"
            f"Обнаружена опасная система команда:\n<code>{html.escape(user_command)}</code>"
        )
        return

    await message.edit_text(
        f"<b>[ INFO ] Running:</b> <code>{html.escape(user_command)}</code>\n\n"
        f"<code>[ RUNNING... ]</code>"
    )

    shell = os.environ.get("SHELL", "/bin/sh")
    start_time = time.time()

    try:
        process = await asyncio.create_subprocess_exec(
            shell,
            "-c",
            user_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=os.setsid,
        )
    except Exception as e:
        await message.edit_text(
            f"<b>[ ERROR ] Ошибка запуска процесса:</b>\n<code>{html.escape(str(e))}</code>"
        )
        return

    msg_key = f"{message.chat.id}:{message.id}"
    ACTIVE_CMDS[msg_key] = process

    stdout_buf = []
    stderr_buf = []

    stdout_task = asyncio.create_task(stream_reader(process.stdout, stdout_buf))
    stderr_task = asyncio.create_task(stream_reader(process.stderr, stderr_buf))

    last_update = 0

    while process.returncode is None:
        await asyncio.sleep(1.5) 
        current_stdout = "".join(stdout_buf)[-2048:]
        current_stderr = "".join(stderr_buf)[-1024:]

        if time.time() - last_update >= 2.0:
            text = f"<b>[ INFO ] Executing:</b> <code>{html.escape(user_command)}</code>\n\n"
            if current_stdout:
                text += f"<b>STDOUT:</b>\n<code>{html.escape(current_stdout)}</code>\n"
            if current_stderr:
                text += f"<b>STDERR:</b>\n<code>{html.escape(current_stderr)}</code>\n"

            try:
                await message.edit_text(text)
                last_update = time.time()
            except Exception:
                pass

        if stdout_task.done() and stderr_task.done() and process.returncode is not None:
            break

    await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
    await process.wait()

    exec_time = round(time.time() - start_time, 2)
    rc = process.returncode

    final_stdout = "".join(stdout_buf)[-3000:]
    final_stderr = "".join(stderr_buf)[-1000:]

    status_tag = "  OK  " if rc == 0 else " ERROR"
    text = f"<b>[{status_tag}] Process finished with code {rc} ({exec_time}s)</b>\n"
    text += f"<b>Command:</b> <code>{html.escape(user_command)}</code>\n\n"

    if final_stdout:
        text += f"<b>STDOUT:</b>\n<code>{html.escape(final_stdout)}</code>\n"
    if final_stderr:
        text += f"<b>STDERR:</b>\n<code>{html.escape(final_stderr)}</code>\n"

    if not final_stdout and not final_stderr:
        text += "<i>[ Нет вывода ]</i>"
    try:
        await message.edit_text(text)
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса терминала: {e}")
    ACTIVE_CMDS.pop(msg_key, None)
async def terminate_cmd(client: Client, message: Message, api):
    if not message.reply_to_message:
        await message.edit_text(
            "<b>[ ERROR]</b> Ответьте этой командой на сообщение с работающей командой!"
        )
        return

    target_msg = message.reply_to_message
    msg_key = f"{target_msg.chat.id}:{target_msg.id}"
    process = ACTIVE_CMDS.get(msg_key)

    if not process:
        await message.edit_text("<b>[ ERROR]</b> Активный процесс не найден.")
        return

    args = message.text.split()
    sig = signal.SIGKILL if "-f" in args else signal.SIGTERM

    try:
        os.killpg(process.pid, sig)
        await message.edit_text(
            f"<b>[  OK  ] Process PID {process.pid} terminated!</b>"
        )
    except Exception as e:
        await message.edit_text(
            f"<b>[ ERROR ] Не удалось завершить процесс:</b> <code>{html.escape(str(e))}</code>"
        )


def setup(registry):
    registry.commands["exec"] = terminal_cmd
    registry.commands["terminal"] = terminal_cmd
    registry.commands["terminate"] = terminate_cmd
    registry.commands["kill"] = terminate_cmd
    registry.set_meta(
        "terminal",
        {
            "autor": "ArchLinuxok",
            "official": True,
            "description": "Исполнение консольных команд с встроенной защитой",
        },
    )
