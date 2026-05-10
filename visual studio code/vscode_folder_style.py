#!/usr/bin/env python3
"""Compatibility wrapper for editor_tools.vscode_folder_style."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from editor_tools.vscode_folder_style import *  # noqa: F403
from editor_tools.vscode_folder_style import main


if __name__ == "__main__":
    raise SystemExit(main())
