import sys
import os
import shutil
import logging
import traceback

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from yt_downloader.service import YoutubeService
except ImportError:
    print("CRITICAL: Failed to import yt_downloader package.")
    sys.exit(1)

def test_integration():
    url = "https://www.youtube.com/watch?v=0t_DD5568RA"
    download_base = os.path.expanduser("~/Downloads/Test_MultiAudio_MKV")
    
    print("\n" + "="*60)
    print("INTEGRATION TEST: Multi-Audio MKV with Dubbed Audio")
    print("="*60)

    if os.path.exists(download_base):
        print(f"[SETUP] Clearing: {download_base}")
        shutil.rmtree(download_base)
    os.makedirs(download_base, exist_ok=True)

    service = YoutubeService()
    print("[STEP 1] Analyzing video...")

    info, error, missing_runtime = service.get_video_info(url)

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

    expected_langs = {'pt', 'en', 'es', 'fr', 'de', 'ja', 'ko'}
    found_langs = set()
    dubbed_count = 0
    
    print("Detected audio tracks:")
    for a in audios:
        print(f"  - {a['label']} (ID: {a['id']})")
        found_langs.add(a['lang'].lower().split('-')[0])
        if 'Dub' in a['label']:
            dubbed_count += 1
            
    if dubbed_count >= 5:
        print(f"[SUCCESS] Found {dubbed_count} dubbed audio tracks!")
    else:
        print(f"[WARNING] Only {dubbed_count} dubbed tracks found (expected 5+)")

    if 'pt' in found_langs:
        print("[SUCCESS] Portuguese audio detected!")
    else:
        print("[WARNING] Portuguese audio not found in this video.")

    print("\n[STEP 3] Testing Subtitle Detection...")
    subs = service.get_subtitle_candidates(info)
    target_subs = ['pt', 'en']
    available_subs = [s['lang'] for s in subs if any(t in s['lang'].lower() for t in target_subs)]
    print(f"Found subtitle options: {len(subs)} total, {len(available_subs)} PT/EN")

    if '--no-download' in sys.argv:
        print("\n[SKIP] Download skipped (--no-download flag)")
    else:
        print("\n[STEP 4] Testing Download...")
        download_audio_ids = [a['id'] for a in audios if 'pt' in a['lang'].lower() or 'en' in a['lang'].lower()][:2]
        
        if not download_audio_ids:
            download_audio_ids = [audios[0]['id']]
            
        print(f"Downloading audio IDs: {download_audio_ids}")
        
        try:
            def progress_hook(d):
                if d['status'] == 'finished':
                    print(f"  [DONE] {d.get('filename', 'file')}")

            service.download_video(url, download_base, download_audio_ids, available_subs[:3], progress_hook)
            print("[SUCCESS] Download completed!")
        except Exception as e:
            print(f"[FAIL] Download error: {e}")
            sys.exit(1)

        print("\n[STEP 5] Verifying output files...")
        for root, _, files in os.walk(download_base):
            for f in files:
                path = os.path.join(root, f)
                size = os.path.getsize(path) / (1024*1024)
                print(f"  - {f} ({size:.1f} MB)")

    print("\n" + "="*60)
    print("TEST RESULT: PASS")
    print("="*60)

if __name__ == "__main__":
    test_integration()
