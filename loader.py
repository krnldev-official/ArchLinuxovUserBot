import os
import sys
import importlib.util
import logging
from api import registry
logger = logging.getLogger("SnowKernel")
class ModuleLoader:
    def __init__(self, modules_dir: str = "modules", kernel=None):
        self.modules_dir = modules_dir
        self.kernel = kernel
        os.makedirs(os.path.join(self.modules_dir, "official"), exist_ok=True)
        os.makedirs(os.path.join(self.modules_dir, "unofficial"), exist_ok=True)
    def load_all(self):
        loaded_count = 0
        for root, _, files in os.walk(self.modules_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    file_path = os.path.join(root, file)
                    mod_name = os.path.splitext(file)[0]
                    if self.load_module_by_path(mod_name, file_path):
                        loaded_count += 1
        logger.info(f"Target reached: Loaded {loaded_count} module(s).")
    def load_module(self, mod_name: str) -> bool:
        for root, _, files in os.walk(self.modules_dir):
            if f"{mod_name}.py" in files:
                file_path = os.path.join(root, f"{mod_name}.py")
                return self.load_module_by_path(mod_name, file_path)
        logger.error(f"Module file not found for: {mod_name}")
        return False
    def load_module_by_path(self, mod_name: str, file_path: str) -> bool:
        if self.kernel and self.kernel.mode == "linux-hardened":
            if mod_name not in self.kernel.allowed_modules:
                logger.warning(f"Kernel hardened blocked module: '{mod_name}'")
                return False
        if not os.path.exists(file_path):
            logger.error(f"Module file not found: {file_path}")
            return False
        rel_path = os.path.relpath(file_path, self.modules_dir)
        path_parts = os.path.normpath(rel_path).split(os.sep)
        is_official = "official" in path_parts
        try:
            known_cmds = set(registry.module_cmds.keys())
            known_meta = set(registry.module_meta.keys())

            spec = importlib.util.spec_from_file_location(mod_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            if hasattr(module, "setup"):
                module.setup(registry)
                registry.modules[mod_name] = module
                new_cmds = set(registry.module_cmds.keys()) - known_cmds
                new_meta = set(registry.module_meta.keys()) - known_meta
                affected_modules = new_cmds | new_meta
                if not affected_modules:
                    affected_modules = {mod_name}
                for m_name in affected_modules:
                    meta = registry.get_meta(m_name)
                    meta["official"] = is_official
                    registry.set_meta(m_name, **meta)
                status_str = "Official" if is_official else "Unofficial"
                logger.info(f"Loaded module: [{mod_name}] ({status_str})")
                return True
            else:
                logger.error(f"Module [{mod_name}] missing setup() function!")
                return False
        except Exception as e:
            logger.error(f"Failed to load module [{mod_name}]: {e}")
            return False
