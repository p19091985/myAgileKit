"""Run Ruff on the existing myAgileKit zones when Ruff is installed."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RuffZone:
    name: str
    select: tuple[str, ...]
    paths: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ()


RUFF_ZONES = (
    RuffZone(
        name="launchers",
        select=("I", "UP", "B", "SIM", "C4"),
        paths=(
            "myagilekit_gui.py",
            "project_paths.py",
            "tool_registry.py",
            "myagilekit/__init__.py",
            "myagilekit/core/__init__.py",
            "myagilekit/core/logging.py",
            "myagilekit/core/paths.py",
            "myagilekit/core/process_runner.py",
            "myagilekit/core/registry.py",
            "myagilekit/manager/__init__.py",
            "myagilekit/manager/gui.py",
            "instalacao/instalador_tk.py",
            "DevTools/main.py",
            "youtube_multilang_downloader/youtube_multilang.py",
            "audioExtract/conversor_ffmpeg_pro.py",
            "editor_tools/vscode_folder_style.py",
            "editor_tools/run_smoke_suite.py",
            "editor_tools/run_incremental_ruff.py",
        ),
    ),
    RuffZone(
        name="package",
        select=("I", "UP", "B", "SIM", "C4"),
        patterns=("myagilekit/**/*.py",),
    ),
    RuffZone(
        name="devtools",
        select=("I", "UP", "B", "SIM", "C4"),
        patterns=("DevTools/tools/*.py",),
    ),
    RuffZone(
        name="tests",
        select=("I", "UP", "B", "SIM", "C4"),
        patterns=("tests/test_*.py",),
    ),
)


def _relative_existing_path(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return path.relative_to(PROJECT_ROOT).as_posix()


def expand_zone_paths(zone: RuffZone, *, project_root: Path = PROJECT_ROOT) -> tuple[str, ...]:
    selected_paths: set[str] = set()
    for raw_path in zone.paths:
        relative_path = _relative_existing_path(project_root / raw_path)
        if relative_path is not None:
            selected_paths.add(relative_path)

    for pattern in zone.patterns:
        for path in project_root.glob(pattern):
            relative_path = _relative_existing_path(path)
            if relative_path is not None:
                selected_paths.add(relative_path)

    return tuple(sorted(selected_paths))


def build_ruff_commands(*, python_executable: str = sys.executable) -> list[list[str]]:
    commands: list[list[str]] = []
    for zone in RUFF_ZONES:
        paths = expand_zone_paths(zone)
        if paths:
            commands.append(
                [
                    python_executable,
                    "-m",
                    "ruff",
                    "check",
                    *paths,
                    "--select",
                    ",".join(zone.select),
                ]
            )
    return commands


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Executa Ruff incremental nas zonas do myAgileKit.")
    parser.add_argument("--list", action="store_true", help="Lista as zonas e arquivos cobertos.")
    parser.add_argument("--dry-run", action="store_true", help="Mostra os comandos sem executar Ruff.")
    args = parser.parse_args(argv)

    if args.list:
        for zone in RUFF_ZONES:
            print(f"{zone.name}: {', '.join(zone.select)}")
            for path in expand_zone_paths(zone):
                print(f"  - {path}")
        return 0

    commands = build_ruff_commands()
    if args.dry_run:
        for command in commands:
            print(" ".join(command))
        return 0

    if importlib.util.find_spec("ruff") is None:
        print("Ruff nao esta instalado neste ambiente. Use --dry-run para listar comandos.")
        return 2

    for command in commands:
        result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
