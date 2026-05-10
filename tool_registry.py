"""Compatibility wrapper for the myAgileKit tool registry."""

from __future__ import annotations

from myagilekit.core.registry import (
    PROJECT_ROOT,
    TOOL_CATALOG,
    TOOL_MANIFEST_DIR,
    ToolDefinition,
    build_environment_check_command,
    build_launch_command,
    build_test_command,
    build_tool_test_command,
    check_tool,
    filter_tools_by_group,
    load_tool_catalog,
    load_tool_manifest,
    logs_directory,
    python_executable,
    tool_groups,
)

__all__ = [
    "PROJECT_ROOT",
    "TOOL_CATALOG",
    "TOOL_MANIFEST_DIR",
    "ToolDefinition",
    "build_environment_check_command",
    "build_launch_command",
    "build_test_command",
    "build_tool_test_command",
    "check_tool",
    "filter_tools_by_group",
    "load_tool_catalog",
    "load_tool_manifest",
    "logs_directory",
    "python_executable",
    "tool_groups",
]
