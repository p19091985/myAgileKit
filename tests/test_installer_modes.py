from __future__ import annotations

import io
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.helpers import load_module_from_path

installer_module = load_module_from_path(
    "installer_modes_for_tests",
    "instalacao/instalador_tk.py",
)


class InstallerModesTests(unittest.TestCase):
    def test_check_mode_runs_without_loading_tkinter(self) -> None:
        output = io.StringIO()

        with (
            patch.object(installer_module, "status_items", return_value=[installer_module.CheckItem("x", "OK")]),
            patch.object(installer_module, "_load_tkinter", side_effect=AssertionError("tkinter nao deveria carregar")),
            patch("sys.stdout", output),
        ):
            result = installer_module.main(["--check"])

        self.assertEqual(result, 0)
        self.assertIn("Diagnostico myAgileKit", output.getvalue())

    def test_cli_mode_forwards_options_to_install_runner(self) -> None:
        fake_log = Path(installer_module.PROJECT_ROOT / "logs" / "install" / "fake.log")

        with (
            patch.object(installer_module, "run_install", return_value=fake_log) as run_install,
            patch("sys.stdout", io.StringIO()),
        ):
            result = installer_module.main(["--cli", "--skip-tests"])

        self.assertEqual(result, 0)
        run_install.assert_called_once()
        self.assertFalse(run_install.call_args.kwargs["run_tests"])
        self.assertFalse(run_install.call_args.kwargs["install_system"])

    def test_mode_options_are_mutually_exclusive(self) -> None:
        with patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
            installer_module.main(["--gui", "--check"])


if __name__ == "__main__":
    unittest.main()
