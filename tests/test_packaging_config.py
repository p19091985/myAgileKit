from __future__ import annotations

import unittest

import myagilekit
from tests.helpers import PROJECT_ROOT

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility.
    tomllib = None


class PackagingConfigTests(unittest.TestCase):
    def test_pyproject_defines_metadata_dependencies_and_commands(self) -> None:
        if tomllib is None:
            self.skipTest("tomllib esta disponivel a partir do Python 3.11")

        pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(pyproject["project"]["name"], "myagilekit")
        self.assertEqual(pyproject["project"]["version"], myagilekit.__version__)
        self.assertIn("myagilekit-manager", pyproject["project"]["scripts"])
        self.assertIn("ruff", pyproject["tool"])

        dependencies = "\n".join(pyproject["project"]["dependencies"])
        for package in ("yt-dlp", "pygame", "ruff"):
            with self.subTest(package=package):
                self.assertIn(package, dependencies)

    def test_project_config_declares_log_categories(self) -> None:
        if tomllib is None:
            self.skipTest("tomllib esta disponivel a partir do Python 3.11")

        config = tomllib.loads((PROJECT_ROOT / "config" / "myagilekit.toml").read_text(encoding="utf-8"))

        self.assertEqual(config["logs"]["root"], "logs")
        self.assertEqual(
            set(config["logs"]["categories"]),
            {"install", "tools", "tests", "errors"},
        )

    def test_tool_manifests_exist_for_registered_tools(self) -> None:
        manifests = sorted((PROJECT_ROOT / "config" / "tools").glob("*.json"))

        self.assertGreaterEqual(len(manifests), 1)
        self.assertTrue(any("installer" in path.name for path in manifests))

    def test_ci_workflow_exists(self) -> None:
        workflow = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

        self.assertTrue(workflow.exists())
        self.assertIn("unittest discover", workflow.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
