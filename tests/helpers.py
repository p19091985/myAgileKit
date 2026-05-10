from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_module_from_path(module_name: str, relative_path: str, extra_paths: tuple[str, ...] = ()):
    for extra_path in extra_paths:
        path = str(PROJECT_ROOT / extra_path)
        if path not in sys.path:
            sys.path.insert(0, path)

    module_path = PROJECT_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
