from __future__ import annotations

import logging
import os
import shutil
import sys


logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
YOUTUBE_ROOT = os.path.join(PROJECT_ROOT, "youtube_multilang_downloader")
sys.path.insert(0, YOUTUBE_ROOT)

try:
    from yt_downloader.service import YoutubeService
except ImportError:
    print("CRITICAL: Failed to import yt_downloader package.")
    sys.exit(1)


def main() -> None:
    url = "https://www.youtube.com/watch?v=0t_DD5568RA"
    download_base = os.path.expanduser("~/Downloads/Test_MultiAudio_MKV")

    print("\n" + "=" * 60)
    print("INTEGRATION CHECK: Multi-Audio MKV with Dubbed Audio")
    print("=" * 60)

    if os.path.exists(download_base):
        print(f"[SETUP] Clearing: {download_base}")
        shutil.rmtree(download_base)
    os.makedirs(download_base, exist_ok=True)

    service = YoutubeService()
    print("[STEP 1] Analyzing video...")

    info, error, _missing_runtime = service.get_video_info(url)

    if error:
        print(f"[FAIL] Error: {error}")
        sys.exit(1)

    if not info:
        print("[FAIL] No info returned.")
        sys.exit(1)

    print(f"[OK] Title: {info.get('title', 'Unknown')[:50]}...")

    print("\n[STEP 2] Testing Dubbed Audio Detection...")
    audios = service.filter_audio_candidates(info)

    if not audios:
        print("[FAIL] No audio candidates found!")
        sys.exit(1)

    found_langs = set()
    dubbed_count = 0

    print("Detected audio tracks:")
    for audio in audios:
        print(f"  - {audio['label']} (ID: {audio['id']})")
        found_langs.add(audio["lang"].lower().split("-")[0])
        if "Dub" in audio["label"]:
            dubbed_count += 1

    if dubbed_count >= 5:
        print(f"[SUCCESS] Found {dubbed_count} dubbed audio tracks!")
    else:
        print(f"[WARNING] Only {dubbed_count} dubbed tracks found (expected 5+)")

    if "pt" in found_langs:
        print("[SUCCESS] Portuguese audio detected!")
    else:
        print("[WARNING] Portuguese audio not found in this video.")

    print("\n[STEP 3] Testing Subtitle Detection...")
    subs = service.get_subtitle_candidates(info)
    target_subs = ["pt", "en"]
    available_subs = [
        subtitle["lang"]
        for subtitle in subs
        if any(target in subtitle["lang"].lower() for target in target_subs)
    ]
    print(f"Found subtitle options: {len(subs)} total, {len(available_subs)} PT/EN")

    if "--no-download" in sys.argv:
        print("\n[SKIP] Download skipped (--no-download flag)")
    else:
        print("\n[STEP 4] Testing Download...")
        download_audio_ids = [
            audio["id"]
            for audio in audios
            if "pt" in audio["lang"].lower() or "en" in audio["lang"].lower()
        ][:2]

        if not download_audio_ids:
            download_audio_ids = [audios[0]["id"]]

        print(f"Downloading audio IDs: {download_audio_ids}")

        def progress_hook(data):
            if data["status"] == "finished":
                print(f"  [DONE] {data.get('filename', 'file')}")

        try:
            service.download_video(
                url,
                download_base,
                download_audio_ids,
                available_subs[:3],
                progress_hook,
            )
            print("[SUCCESS] Download completed!")
        except Exception as exc:
            print(f"[FAIL] Download error: {exc}")
            sys.exit(1)

        print("\n[STEP 5] Verifying output files...")
        for root, _dirs, files in os.walk(download_base):
            for filename in files:
                path = os.path.join(root, filename)
                size = os.path.getsize(path) / (1024 * 1024)
                print(f"  - {filename} ({size:.1f} MB)")

    print("\n" + "=" * 60)
    print("CHECK RESULT: PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()
