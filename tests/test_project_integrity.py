from __future__ import annotations

import ast
import unittest
from pathlib import Path

from tests.helpers import PROJECT_ROOT

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility.
    tomllib = None

EXCLUDED_DIRS = {".git", ".venv", ".idea", ".agents", ".codex", "__pycache__"}


def iter_project_python_files() -> list[Path]:
    files: list[Path] = []
    for path in PROJECT_ROOT.rglob("*.py"):
        relative_parts = path.relative_to(PROJECT_ROOT).parts
        if any(part in EXCLUDED_DIRS for part in relative_parts):
            continue
        files.append(path)
    return sorted(files)


class ProjectIntegrityTests(unittest.TestCase):
    def test_python_sources_parse_successfully(self) -> None:
        failures: list[str] = []
        for path in iter_project_python_files():
            try:
                ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError as exc:
                failures.append(f"{path.relative_to(PROJECT_ROOT)}: {exc}")

        self.assertEqual(failures, [])

    def test_no_stale_external_project_references_remain(self) -> None:
        stale_refs: list[str] = []
        stale_import = "".join(("yolo", "_master"))
        for path in iter_project_python_files():
            text = path.read_text(encoding="utf-8")
            if stale_import in text:
                stale_refs.append(str(path.relative_to(PROJECT_ROOT)))

        self.assertEqual(stale_refs, [])

    def test_tests_are_centralized_under_tests_folder(self) -> None:
        misplaced = [
            str(path.relative_to(PROJECT_ROOT))
            for path in PROJECT_ROOT.rglob("test_*.py")
            if "tests" not in path.relative_to(PROJECT_ROOT).parts
            and not any(part in EXCLUDED_DIRS for part in path.relative_to(PROJECT_ROOT).parts)
        ]

        self.assertEqual(misplaced, [])

    def test_generated_log_files_are_centralized(self) -> None:
        misplaced: list[str] = []
        for path in PROJECT_ROOT.rglob("*"):
            if not path.is_file():
                continue

            relative_parts = path.relative_to(PROJECT_ROOT).parts
            if any(part in EXCLUDED_DIRS for part in relative_parts):
                continue

            is_log_file = path.suffix == ".log" or path.name.startswith("debug_log")
            if is_log_file and relative_parts[0] != "logs":
                misplaced.append(str(path.relative_to(PROJECT_ROOT)))

        self.assertEqual(misplaced, [])

    def test_pyproject_declares_project_metadata_and_ruff(self) -> None:
        if tomllib is None:
            self.skipTest("tomllib esta disponivel a partir do Python 3.11")

        data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(data["project"]["name"], "myagilekit")
        self.assertIn("version", data["project"])
        self.assertIn("tool", data)
        self.assertIn("ruff", data["tool"])

    def test_config_and_log_layout_exists(self) -> None:
        expected_paths = [
            PROJECT_ROOT / "config" / "myagilekit.toml",
            PROJECT_ROOT / "logs" / "install" / ".gitkeep",
            PROJECT_ROOT / "logs" / "tools" / ".gitkeep",
            PROJECT_ROOT / "logs" / "tests" / ".gitkeep",
            PROJECT_ROOT / "logs" / "errors" / ".gitkeep",
        ]

        missing = [str(path.relative_to(PROJECT_ROOT)) for path in expected_paths if not path.exists()]

        self.assertEqual(missing, [])

    def test_sensitive_cookie_files_are_ignored(self) -> None:
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("cookies.txt", gitignore)


if __name__ == "__main__":
    unittest.main()
