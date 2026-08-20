import logging
import time
from colorama import init, Fore, Style
init(autoreset=True)
class ArchLogger(logging.Formatter):
    format_info = f"{Style.BRIGHT}{Fore.GREEN}[  OK  ]{Style.RESET_ALL} %(message)s"
    format_warn = f"{Style.BRIGHT}{Fore.YELLOW}[ WARN ]{Style.RESET_ALL} %(message)s"
    format_err  = f"{Style.BRIGHT}{Fore.RED}[ FAILED ]{Style.RESET_ALL} %(message)s"
    def format(self, record):
        if record.levelno == logging.INFO:
            log_fmt = self.format_info
        elif record.levelno == logging.WARNING:
            log_fmt = self.format_warn
        elif record.levelno == logging.ERROR:
            log_fmt = self.format_err
        else:
            log_fmt = self.format_info
            
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
logger = logging.getLogger("SnowKernel")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(ArchLogger())
logger.addHandler(ch)
class KernelConfig:
    def __init__(self, mode: str):
        self.mode = mode
        self.flood_delay = 0.0
        self.allowed_modules = ["ping", "help"]
        if mode == "linux-zen":
            self.flood_delay = 0.1 
            logger.info("Kernel mode set to: linux-zen (Max Performance)")
        elif mode == "linux-hardened":
            self.flood_delay = 0.8
            logger.info("Kernel mode set to: linux-hardened (Security & Strict Anti-Flood)")
            logger.warning("Hardened mode ACTIVE: Non-essential modules will be stripped!")
        else:
            self.mode = "linux"
            self.flood_delay = 0.3
            logger.info("Kernel mode set to: linux (Standard)")

