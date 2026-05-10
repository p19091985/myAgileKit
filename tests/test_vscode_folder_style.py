from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import PROJECT_ROOT, load_module_from_path

vscode_style = load_module_from_path(
    "vscode_folder_style_for_tests",
    "editor_tools/vscode_folder_style.py",
)


class VSCodeFolderStyleTests(unittest.TestCase):
    def test_legacy_visual_studio_code_wrapper_remains_available(self) -> None:
        wrapper = PROJECT_ROOT / "visual studio code" / "vscode_folder_style.py"

        self.assertTrue(wrapper.exists())

    def test_jsonc_cleanup_preserves_urls_and_removes_trailing_commas(self) -> None:
        raw = '''
{
  // normal comment
  "url": "https://example.com/a//b",
  "items": [1, 2,],
  /* block comment */
}
'''
        cleaned = vscode_style.remove_trailing_commas(vscode_style.strip_json_comments(raw))
        parsed = json.loads(cleaned)

        self.assertEqual(parsed["url"], "https://example.com/a//b")
        self.assertEqual(parsed["items"], [1, 2])

    def test_replace_patch_block_is_idempotent(self) -> None:
        first, first_changed = vscode_style.replace_patch_block("body {}\n")
        second, second_changed = vscode_style.replace_patch_block(first)

        self.assertTrue(first_changed)
        self.assertFalse(second_changed)
        self.assertEqual(first, second)

    def test_update_settings_file_writes_expected_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings_dir = Path(tmp) / "User"
            css_path = Path(tmp) / "folder-plus-minus.css"

            with contextlib.redirect_stdout(io.StringIO()):
                changed = vscode_style.update_settings_file(settings_dir, css_path, dry_run=False)

            settings = json.loads((settings_dir / "settings.json").read_text(encoding="utf-8"))
            self.assertTrue(changed)
            self.assertEqual(settings["workbench.iconTheme"], "material-icon-theme")
            self.assertIn(css_path.resolve().as_uri(), settings["vscode_custom_css.imports"])


if __name__ == "__main__":
    unittest.main()
