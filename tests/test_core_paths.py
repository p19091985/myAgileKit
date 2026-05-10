from __future__ import annotations

import unittest

import project_paths
from myagilekit.core import paths


class CorePathsTests(unittest.TestCase):
    def test_project_layout_has_config_and_log_subfolders(self) -> None:
        paths.ensure_project_layout()

        self.assertTrue(paths.DEFAULT_CONFIG_FILE.exists())
        for category in paths.LOG_SUBDIRS:
            with self.subTest(category=category):
                self.assertTrue(paths.ensure_logs_dir(category).is_dir())

    def test_log_path_rejects_absolute_or_parent_paths(self) -> None:
        with self.assertRaises(ValueError):
            paths.log_path("../outside.log", "tools")

        with self.assertRaises(ValueError):
            paths.log_path("/tmp/outside.log", "tools")

    def test_compatibility_wrapper_uses_package_paths(self) -> None:
        self.assertEqual(project_paths.PROJECT_ROOT, paths.PROJECT_ROOT)
        self.assertEqual(project_paths.LOGS_DIR, paths.LOGS_DIR)


if __name__ == "__main__":
    unittest.main()

