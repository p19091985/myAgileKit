from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from tests.helpers import PROJECT_ROOT, load_module_from_path
from tool_registry import (
    TOOL_CATALOG,
    TOOL_MANIFEST_DIR,
    build_environment_check_command,
    build_launch_command,
    build_test_command,
    build_tool_test_command,
    check_tool,
    filter_tools_by_group,
    load_tool_catalog,
    tool_groups,
)


class ToolRegistryTests(unittest.TestCase):
    def test_tool_identifiers_are_unique(self) -> None:
        identifiers = [tool.identifier for tool in TOOL_CATALOG]

        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_root_registry_is_compatibility_wrapper_for_package_registry(self) -> None:
        import myagilekit.core.registry as package_registry

        self.assertIs(TOOL_CATALOG, package_registry.TOOL_CATALOG)

    def test_tool_catalog_is_loaded_from_manifests(self) -> None:
        manifests = sorted(TOOL_MANIFEST_DIR.glob("*.json"))
        catalog = load_tool_catalog()

        self.assertTrue(manifests)
        self.assertEqual(len(catalog), len(manifests))
        self.assertEqual(catalog[0].identifier, "installer")

    def test_registered_entrypoints_exist(self) -> None:
        missing = [
            f"{tool.identifier}: {tool.entrypoint}"
            for tool in TOOL_CATALOG
            if not tool.entrypoint_path.exists()
        ]

        self.assertEqual(missing, [])

    def test_launch_commands_are_non_empty(self) -> None:
        for tool in TOOL_CATALOG:
            with self.subTest(tool=tool.identifier):
                command = build_launch_command(tool)
                self.assertTrue(command)
                self.assertTrue(command[0])

    def test_check_tool_returns_boolean_and_problem_list(self) -> None:
        for tool in TOOL_CATALOG:
            with self.subTest(tool=tool.identifier):
                ready, problems = check_tool(tool)
                self.assertIsInstance(ready, bool)
                self.assertIsInstance(problems, list)

    def test_test_command_uses_unittest_discovery(self) -> None:
        command = build_test_command()

        self.assertIn("unittest", command)
        self.assertIn("discover", command)
        self.assertIn("tests", command)

    def test_tool_test_command_uses_tool_specific_target(self) -> None:
        tool = next(item for item in TOOL_CATALOG if item.identifier == "installer")
        command = build_tool_test_command(tool)

        self.assertIn("unittest", command)
        self.assertIn("tests.test_tool_registry", command)

    def test_environment_check_command_uses_installer_check_mode(self) -> None:
        command = build_environment_check_command()

        self.assertIn("instalador_tk.py", command[-2])
        self.assertEqual(command[-1], "--check")

    def test_tool_group_helpers_filter_catalog(self) -> None:
        groups = tool_groups()
        filtered = filter_tools_by_group("Midia")

        self.assertIn("Midia", groups)
        self.assertTrue(filtered)
        self.assertTrue(all(tool.group == "Midia" for tool in filtered))

    def test_requirements_include_runtime_and_quality_dependencies(self) -> None:
        requirements = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")

        for package in ("yt-dlp", "pygame", "ruff"):
            with self.subTest(package=package):
                self.assertIn(package, requirements)

    def test_installer_shell_script_is_executable(self) -> None:
        installer = Path(PROJECT_ROOT / "instalacao" / "instalar.sh")

        self.assertTrue(installer.exists())
        self.assertTrue(installer.stat().st_mode & 0o111)

    def test_root_start_script_is_executable(self) -> None:
        start_script = Path(PROJECT_ROOT / "iniciar.sh")

        self.assertTrue(start_script.exists())
        self.assertTrue(start_script.stat().st_mode & 0o111)

    def test_installer_uses_apt_only_for_missing_system_dependencies(self) -> None:
        installer_module = load_module_from_path(
            "installer_for_tests",
            "instalacao/instalador_tk.py",
        )

        with (
            patch.object(installer_module, "python_module_available", return_value=True),
            patch.object(installer_module.shutil, "which", return_value="/usr/bin/tool"),
        ):
            self.assertEqual(installer_module.missing_system_packages("/fake/python"), [])

        def fake_which(command: str) -> str | None:
            return None if command in {"ffmpeg", "ffprobe"} else "/usr/bin/tool"

        with (
            patch.object(installer_module, "python_module_available", return_value=False),
            patch.object(installer_module.shutil, "which", side_effect=fake_which),
        ):
            self.assertEqual(
                installer_module.missing_system_packages("/fake/python"),
                ["python3-tk", "ffmpeg"],
            )

    def test_installer_supports_cli_gui_and_check_modes(self) -> None:
        installer_module = load_module_from_path(
            "installer_parser_for_tests",
            "instalacao/instalador_tk.py",
        )

        parser = installer_module.build_arg_parser()

        self.assertTrue(parser.parse_args(["--gui"]).gui)
        self.assertTrue(parser.parse_args(["--cli"]).cli)
        self.assertTrue(parser.parse_args(["--check"]).check)


if __name__ == "__main__":
    unittest.main()
