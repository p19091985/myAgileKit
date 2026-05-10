"""Shared filesystem paths for myAgileKit."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG_FILE = CONFIG_DIR / "myagilekit.toml"
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_SUBDIRS = ("install", "tools", "tests", "errors")


def _safe_child(base_dir: Path, filename: str) -> Path:
    candidate = Path(filename)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"caminho inseguro: {filename}")
    return base_dir / candidate


def ensure_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def config_path(filename: str = "myagilekit.toml") -> Path:
    return _safe_child(ensure_config_dir(), filename)


def ensure_logs_dir(category: str | None = None) -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    for subdir in LOG_SUBDIRS:
        (LOGS_DIR / subdir).mkdir(parents=True, exist_ok=True)

    if category is None:
        return LOGS_DIR
    if category not in LOG_SUBDIRS:
        raise ValueError(f"categoria de log desconhecida: {category}")
    return LOGS_DIR / category


def log_path(filename: str, category: str | None = None) -> Path:
    return _safe_child(ensure_logs_dir(category), filename)


def ensure_project_layout() -> None:
    ensure_config_dir()
    ensure_logs_dir()

