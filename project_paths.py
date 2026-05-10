"""Compatibility wrapper for shared filesystem paths."""

from __future__ import annotations

from myagilekit.core.paths import (
    CONFIG_DIR,
    DEFAULT_CONFIG_FILE,
    LOG_SUBDIRS,
    LOGS_DIR,
    PROJECT_ROOT,
    config_path,
    ensure_config_dir,
    ensure_logs_dir,
    ensure_project_layout,
    log_path,
)

__all__ = [
    "CONFIG_DIR",
    "DEFAULT_CONFIG_FILE",
    "LOGS_DIR",
    "LOG_SUBDIRS",
    "PROJECT_ROOT",
    "config_path",
    "ensure_config_dir",
    "ensure_logs_dir",
    "ensure_project_layout",
    "log_path",
]
