"""Logging helpers for myAgileKit scripts."""

from __future__ import annotations

import logging
from pathlib import Path

from .paths import log_path


def configure_file_logger(
    name: str,
    filename: str,
    *,
    category: str = "tools",
    level: int = logging.DEBUG,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    target = log_path(filename, category)
    if not _has_handler_for(logger, target):
        handler = logging.FileHandler(target, encoding="utf-8")
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)

    return logger


def _has_handler_for(logger: logging.Logger, target: Path) -> bool:
    target = target.resolve()
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename).resolve() == target:
            return True
    return False

