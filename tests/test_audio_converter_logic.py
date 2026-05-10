from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from tests.helpers import load_module_from_path

converter_module = load_module_from_path(
    "audio_converter_for_tests",
    "audioExtract/conversor_ffmpeg_pro.py",
)


class AudioConverterLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = converter_module.FFmpegConverterApp.__new__(converter_module.FFmpegConverterApp)

    def test_check_ffmpeg_reports_available_command(self) -> None:
        with patch.object(converter_module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)):
            self.assertTrue(self.app.check_ffmpeg())

    def test_check_ffmpeg_reports_missing_command(self) -> None:
        with patch.object(converter_module.subprocess, "run", side_effect=FileNotFoundError):
            self.assertFalse(self.app.check_ffmpeg())

    def test_get_duration_parses_ffprobe_output(self) -> None:
        with patch.object(converter_module.subprocess, "check_output", return_value=b"125.5\n"):
            self.assertEqual(self.app.get_duration("video.mp4"), 125.5)

    def test_get_duration_falls_back_to_zero_on_errors(self) -> None:
        with patch.object(converter_module.subprocess, "check_output", side_effect=OSError("boom")):
            self.assertEqual(self.app.get_duration("missing.mp4"), 0.0)


if __name__ == "__main__":
    unittest.main()
