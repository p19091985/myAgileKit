from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from tests.helpers import load_module_from_path

installer_module = load_module_from_path(
    "installer_cli_for_tests",
    "instalacao/instalador_tk.py",
)


class InstallerCliTests(unittest.TestCase):
    def test_arg_parser_accepts_cli_check_and_gui_modes(self) -> None:
        parser = installer_module.build_arg_parser()

        self.assertTrue(parser.parse_args(["--cli"]).cli)
        self.assertTrue(parser.parse_args(["--check"]).check)
        self.assertTrue(parser.parse_args(["--gui"]).gui)

    def test_check_mode_returns_nonzero_for_required_pending_items(self) -> None:
        items = [
            installer_module.CheckItem("ok", "OK"),
            installer_module.CheckItem("missing", "Pendente"),
            installer_module.CheckItem("optional", "Opcional", required=False),
        ]
        output = io.StringIO()

        with (
            patch.object(installer_module, "status_items", return_value=items),
            patch.object(installer_module, "python_for_checks", return_value="/fake/python"),
        ):
            status = installer_module.run_check(output=output.write)

        self.assertEqual(status, 1)
        self.assertIn("missing", output.getvalue())

    def test_install_logs_are_written_under_install_subfolder(self) -> None:
        log_file = installer_module.new_install_log_path()

        self.assertEqual(log_file.parent.name, "install")
        self.assertEqual(log_file.parent.parent.name, "logs")


if __name__ == "__main__":
    unittest.main()

