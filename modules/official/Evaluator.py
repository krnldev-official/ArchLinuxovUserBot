#autor=LinuxAngel
#osred=True
#kernel=kernel
#core=True

#Official modules ArchLinuxov Api
import asyncio
import contextlib
import os
import sys
import tempfile
import time
from io import StringIO
from api import registry
def setup(registry):
    registry.register_command("e", mod_e, module_name="Evaluator")
    registry.register_command("eval", mod_e, module_name="Evaluator")
    registry.register_command("ecpp", mod_ecpp, module_name="Evaluator")
    registry.register_command("ec", mod_ec, module_name="Evaluator")
    registry.register_command("ers", mod_ers, module_name="Evaluator")
    registry.register_command("eg", mod_eg, module_name="Evaluator")
    registry.register_command("enode", mod_enode, module_name="Evaluator")
    registry.set_meta("Evaluator", {
        "autor": "LinuxAngel",
        "osred": True,
        "kernel": "kernel",
        "core": True
    })
async def mod_e(client, message, api):
    """Выполнить код python и тд"""
    args = api.get_args(message)
    reply = message.reply_to_message

    if not args and reply and reply.text:
        args = reply.text

    if not args:
        await api.edit_or_reply(message, "Передай код для выполнения")
        return

    skip_output = False
    if args.startswith("-so ") or args.startswith("--skip-output "):
        skip_output = True
        args = args.split(" ", 1)[1]

    output_print = StringIO()
    start_time = time.time()

    eval_globals = {
        "client": client,
        "c": client,
        "message": message,
        "m": message,
        "reply": reply,
        "r": reply,
        "api": api,
        "registry": registry,
        "asyncio": asyncio,
        "os": os,
        "sys": sys,
    }

    result = None
    error = False

    try:
        with contextlib.redirect_stdout(output_print):
            try:
                from meval import meval
                result = await meval(args, globals(), **eval_globals)
            except ImportError:
                exec_code = f"async def __ex():\n" + "\n".join(f"    {line}" for line in args.split("\n"))
                exec_globals = {**globals(), **eval_globals}
                exec(exec_code, exec_globals)
                result = await exec_globals["__ex"]()

        print_output = output_print.getvalue()
    except Exception as e:
        error = True
        print_output = output_print.getvalue()
        result = str(e)

    exec_time = round(time.time() - start_time, 3)

    if skip_output:
        return

    out_text = f"Python Exec ({exec_time}s)\n"
    if args:
        out_text += f"Код:\n{args}\n\n"

    if print_output:
        out_text += f"Консоль:\n{print_output}\n"

    if result is not None:
        out_text += f"Результат:\n{result}"

    if error and not print_output and not result:
        out_text += "Ошибка выполнения"

    await api.edit_or_reply(message, out_text)


async def _run_compiler(message, api, code, ext, cmd_build, cmd_run):
    if not code:
        reply = message.reply_to_message
        if reply and reply.text:
            code = reply.text

    if not code:
        await api.edit_or_reply(message, "Передай код для выполнения")
        return

    await api.edit_or_reply(message, "Компиляция...")

    error = False
    result = ""

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, f"code.{ext}")
        with open(file_path, "w") as f:
            f.write(code)

        try:
            if cmd_build:
                res_b = await api.exec_shell(f"cd {tmpdir} && {cmd_build}")
                if res_b["code"] != 0:
                    result = res_b["stderr"] or res_b["stdout"]
                    error = True

            if not error and cmd_run:
                res_r = await api.exec_shell(f"cd {tmpdir} && {cmd_run}")
                result = res_r["stdout"] or res_r["stderr"]
                if res_r["code"] != 0:
                    error = True

        except Exception as e:
            result = str(e)
            error = True

    status = "Ошибка" if error else "Вывод"
    await api.edit_or_reply(message, f"Результат ({status}):\n{result}")


async def mod_ecpp(client, message, api):
    """Скомпилировать и выполнить C++ код."""
    code = api.get_args(message)
    await _run_compiler(
        message, api, code, "cpp",
        "g++ -o code code.cpp",
        "./code"
    )


async def mod_ec(client, message, api):
    """Скомпилировать и выполнить C код."""
    code = api.get_args(message)
    await _run_compiler(
        message, api, code, "c",
        "gcc -o code code.c",
        "./code"
    )


async def mod_ers(client, message, api):
    """Скомпилировать и выполнить Rust код."""
    code = api.get_args(message)
    await _run_compiler(
        message, api, code, "rs",
        "rustc code.rs -o code",
        "./code"
    )


async def mod_eg(client, message, api):
    """Выполнить Go код."""
    code = api.get_args(message)
    await _run_compiler(
        message, api, code, "go",
        "",
        "go run code.go"
    )


async def mod_enode(client, message, api):
    """Выполнить JavaScript через Node.js."""
    code = api.get_args(message)
    await _run_compiler(
        message, api, code, "js",
        "",
        "node code.js"
    )
