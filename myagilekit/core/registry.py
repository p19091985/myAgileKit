"""Shared registry for the myAgileKit tool launchers and checks."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from .paths import PROJECT_ROOT, ensure_logs_dir

TOOL_MANIFEST_DIR = PROJECT_ROOT / "config" / "tools"


@dataclass(frozen=True)
class ToolDefinition:
    """Description of a runnable mini system in the repository."""

    identifier: str
    name: str
    group: str
    description: str
    entrypoint: str
    launch_mode: str = "python"
    default_args: tuple[str, ...] = ()
    platforms: tuple[str, ...] = ("linux", "darwin", "win32")
    requires_modules: tuple[str, ...] = ()
    requires_commands: tuple[str, ...] = ()
    test_target: str | None = None
    working_dir: str = "."

    @property
    def entrypoint_path(self) -> Path:
        return PROJECT_ROOT / self.entrypoint

    @property
    def working_dir_path(self) -> Path:
        return PROJECT_ROOT / self.working_dir

    def supports_current_platform(self) -> bool:
        return any(sys.platform.startswith(platform) for platform in self.platforms)


def python_executable() -> str:
    local_python = PROJECT_ROOT / ".venv" / "bin" / "python"
    if local_python.exists():
        return str(local_python)
    return sys.executable or shutil.which("python3") or "python3"


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def build_launch_command(tool: ToolDefinition) -> list[str]:
    entrypoint = str(tool.entrypoint_path)
    if tool.launch_mode == "python":
        return [python_executable(), entrypoint, *tool.default_args]
    if tool.launch_mode == "shell":
        return ["bash", entrypoint, *tool.default_args]
    if tool.launch_mode == "powershell":
        return [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            entrypoint,
            *tool.default_args,
        ]
    if tool.launch_mode == "batch":
        return [entrypoint, *tool.default_args]
    raise ValueError(f"Modo de execucao desconhecido: {tool.launch_mode}")


def check_tool(tool: ToolDefinition) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if not tool.entrypoint_path.exists():
        problems.append(f"arquivo nao encontrado: {tool.entrypoint}")

    if not tool.supports_current_platform():
        platforms = ", ".join(tool.platforms)
        problems.append(f"indisponivel nesta plataforma; suporte: {platforms}")

    for module_name in tool.requires_modules:
        if not _module_available(module_name):
            problems.append(f"modulo Python ausente: {module_name}")

    for command_name in tool.requires_commands:
        if shutil.which(command_name) is None:
            problems.append(f"comando ausente no PATH: {command_name}")

    return not problems, problems


def build_test_command() -> list[str]:
    return [python_executable(), "-m", "unittest", "discover", "-s", "tests"]


def build_tool_test_command(tool: ToolDefinition) -> list[str]:
    if not tool.test_target or tool.test_target == "tests":
        return build_test_command()

    target = tool.test_target
    if target.endswith(".py"):
        target = target.removesuffix(".py").replace("/", ".").replace("\\", ".")
    return [python_executable(), "-m", "unittest", target]


def build_environment_check_command() -> list[str]:
    return [python_executable(), str(PROJECT_ROOT / "instalacao" / "instalador_tk.py"), "--check"]


def logs_directory() -> Path:
    return ensure_logs_dir("tools")


def _string_tuple(raw: object, field_name: str, manifest_path: Path) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError(f"{manifest_path}: campo {field_name} precisa ser uma lista de strings")
    return tuple(raw)


def load_tool_manifest(manifest_path: Path) -> ToolDefinition:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{manifest_path}: manifesto precisa conter um objeto JSON")

    required = ("identifier", "name", "group", "description", "entrypoint")
    missing = [field for field in required if not raw.get(field)]
    if missing:
        fields = ", ".join(missing)
        raise ValueError(f"{manifest_path}: campos obrigatorios ausentes: {fields}")

    for field in required:
        if not isinstance(raw[field], str):
            raise ValueError(f"{manifest_path}: campo {field} precisa ser texto")

    test_target = raw.get("test_target")
    if test_target is not None and not isinstance(test_target, str):
        raise ValueError(f"{manifest_path}: campo test_target precisa ser texto")

    launch_mode = raw.get("launch_mode", "python")
    working_dir = raw.get("working_dir", ".")
    if not isinstance(launch_mode, str) or not isinstance(working_dir, str):
        raise ValueError(f"{manifest_path}: launch_mode e working_dir precisam ser texto")

    return ToolDefinition(
        identifier=raw["identifier"],
        name=raw["name"],
        group=raw["group"],
        description=raw["description"],
        entrypoint=raw["entrypoint"],
        launch_mode=launch_mode,
        default_args=_string_tuple(raw.get("default_args"), "default_args", manifest_path),
        platforms=_string_tuple(raw.get("platforms", ["linux", "darwin", "win32"]), "platforms", manifest_path),
        requires_modules=_string_tuple(raw.get("requires_modules"), "requires_modules", manifest_path),
        requires_commands=_string_tuple(raw.get("requires_commands"), "requires_commands", manifest_path),
        test_target=test_target,
        working_dir=working_dir,
    )


def load_tool_catalog(manifest_dir: Path = TOOL_MANIFEST_DIR) -> tuple[ToolDefinition, ...]:
    manifests = sorted(manifest_dir.glob("*.json"))
    if not manifests:
        raise FileNotFoundError(f"nenhum manifesto de ferramenta encontrado em {manifest_dir}")
    return tuple(load_tool_manifest(path) for path in manifests)


TOOL_CATALOG: tuple[ToolDefinition, ...] = load_tool_catalog()


def tool_groups(catalog: tuple[ToolDefinition, ...] = TOOL_CATALOG) -> tuple[str, ...]:
    return tuple(sorted({tool.group for tool in catalog}))


def filter_tools_by_group(group: str | None, catalog: tuple[ToolDefinition, ...] = TOOL_CATALOG) -> tuple[ToolDefinition, ...]:
    if not group or group == "Todas":
        return catalog
    return tuple(tool for tool in catalog if tool.group == group)
