from __future__ import annotations

import sys
import unittest

from tests.helpers import PROJECT_ROOT

youtube_root = str(PROJECT_ROOT / "youtube_multilang_downloader")
if youtube_root not in sys.path:
    sys.path.insert(0, youtube_root)

from yt_downloader.service import YoutubeService


class YoutubeServiceLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = YoutubeService()

    def test_filter_audio_candidates_prefers_distinct_languages(self) -> None:
        info = {
            "formats": [
                {
                    "format_id": "251",
                    "language": "en",
                    "acodec": "opus",
                    "vcodec": "none",
                    "ext": "webm",
                },
                {
                    "format_id": "18",
                    "language": "pt-BR",
                    "acodec": "mp4a",
                    "vcodec": "avc1",
                    "ext": "mp4",
                },
                {
                    "format_id": "22",
                    "language": "en",
                    "acodec": "mp4a",
                    "vcodec": "avc1",
                    "ext": "mp4",
                },
            ]
        }

        audios = self.service.filter_audio_candidates(info)
        by_language = {item["lang"]: item for item in audios}

        self.assertEqual(by_language["en"]["id"], "251")
        self.assertIn("Orig.", by_language["en"]["label"])
        self.assertEqual(by_language["pt-BR"]["id"], "18")
        self.assertIn("Dub", by_language["pt-BR"]["label"])
        self.assertTrue(by_language["pt-BR"]["is_default"])

    def test_filter_audio_candidates_has_safe_fallback(self) -> None:
        audios = self.service.filter_audio_candidates({"formats": []})

        self.assertEqual(audios[0]["id"], "bestaudio")
        self.assertTrue(audios[0]["is_default"])

    def test_subtitle_candidates_merge_manual_and_automatic(self) -> None:
        info = {
            "subtitles": {"en": [{}], "pt-BR": [{}]},
            "automatic_captions": {"es": [{}], "en": [{}]},
        }

        subtitles = self.service.get_subtitle_candidates(info)
        by_language = {item["lang"]: item for item in subtitles}

        self.assertFalse("(Auto)" in by_language["en"]["label"])
        self.assertIn("(Auto)", by_language["es"]["label"])
        self.assertTrue(by_language["pt-BR"]["is_default"])


if __name__ == "__main__":
    unittest.main()
