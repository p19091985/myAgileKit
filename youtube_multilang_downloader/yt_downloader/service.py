import os
import sys
import logging
import shutil
import traceback
import json
import subprocess

venv_bin = os.path.dirname(sys.executable)
if venv_bin not in os.environ["PATH"]:
     os.environ["PATH"] += os.pathsep + venv_bin
     
import yt_dlp
from .logger import YtDlpLogger

class YoutubeService:
    def __init__(self):
        self.js_runtime_missing = False

    def check_runtime_warning(self, msg):
        if "JavaScript" in msg and "runtime" in msg:
            logging.warning(f"YT-DLP Runtime Warning suppressed: {msg}")

    def get_video_info(self, url):
        self.js_runtime_missing = False
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        wrapper_path = os.path.abspath(os.path.join(script_dir, '..', 'wrapper.sh'))
        
        cmd = [
            wrapper_path,
            '--dump-json',
            '--no-playlist',
            url
        ]
        
        if os.path.exists('cookies.txt'):
             cmd.extend(['--cookies', 'cookies.txt'])
             
        logging.debug(f"Executing CLI: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.stderr:
                 logging.debug(f"CLI Stderr: {result.stderr}")
                 self.check_runtime_warning(result.stderr)

            if result.returncode != 0:
                 err_msg = result.stderr
                 if "Unsupported URL" in err_msg:
                     return None, "URL inválida ou não suportada pelo YT-DLP.", self.js_runtime_missing
                 if "Video unavailable" in err_msg:
                     return None, "Vídeo indisponível (privado ou removido).", self.js_runtime_missing
                     
                 return None, f"CLI Error: {err_msg}", self.js_runtime_missing
                 
            info = json.loads(result.stdout)
            return info, None, self.js_runtime_missing
            
        except Exception as e:
            logging.error(f"Erro no Service.get_video_info (CLI):\n{traceback.format_exc()}")
            return None, str(e), self.js_runtime_missing

    def filter_audio_candidates(self, info):
        formats = info.get('formats', [])
        lang_formats = {}
        
        for f in formats:
            lang = f.get('language')
            acodec = f.get('acodec')
            vcodec = f.get('vcodec')
            
            if not acodec or acodec == 'none':
                continue
            
            if vcodec == 'none':
                key = lang or 'und'
                if key not in lang_formats:
                    lang_formats[key] = f
                continue
            
            if lang and lang not in lang_formats:
                lang_formats[lang] = f
        
        results = []
        for lang, f in sorted(lang_formats.items()):
            f_id = f.get('format_id')
            ext = f.get('ext') or ''
            vcodec = f.get('vcodec')
            is_muxed = vcodec and vcodec != 'none'
            source_type = "Dub" if is_muxed else "Orig."
            
            display_lang = lang.upper() if lang else 'UND'
            label_text = f"[{display_lang}] {source_type} ({ext})"
            is_default = 'pt' in lang.lower() if lang else False
            
            results.append({
                'id': f_id,
                'lang': lang or 'und',
                'label': label_text,
                'is_default': is_default
            })
        
        if not results:
            results.append({
                'id': 'bestaudio',
                'lang': 'und',
                'label': '[UND] Áudio Padrão',
                'is_default': True
            })
            
        return results

    def get_subtitle_candidates(self, info):
        subs = info.get('subtitles', {})
        auto_subs = info.get('automatic_captions', {})
        
        all_langs = set(list(subs.keys()) + list(auto_subs.keys()))
        sorted_langs = sorted(list(all_langs))
        
        results = []
        for lang in sorted_langs:
            is_auto = lang not in subs
            suffix = "(Auto)" if is_auto else ""
            label_text = f"[{lang}] {suffix}"
            is_default = 'pt' in lang or 'en' == lang
            
            results.append({
                'lang': lang,
                'label': label_text,
                'is_default': is_default
            })
        return results

    def download_video(self, url, path, audio_ids, sub_langs, progress_hook=None):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        wrapper_path = os.path.abspath(os.path.join(script_dir, '..', 'wrapper.sh'))
        
        outtmpl = os.path.join(path, '%(title)s', '%(title)s.%(ext)s')
        
        if not audio_ids or 'bestaudio' in audio_ids:
            format_string = "bestvideo*+bestaudio/best"
        else:
            unique_ids = list(set(audio_ids))
            audio_part = "+".join(unique_ids)
            format_string = f"bestvideo*+{audio_part}/bestvideo*+bestaudio/best"
        
        cmd = [
            wrapper_path,
            '-f', format_string,
            '-o', outtmpl,
            '--audio-multistreams',
            '--video-multistreams',
            '--merge-output-format', 'mkv',
            '--embed-subs',
            '--write-auto-subs',
            '--sub-format', 'srt/ass/best',
            '--convert-subs', 'srt',
            '--sub-langs', ",".join(sub_langs) if sub_langs else "pt,en,pt-BR,en-US",
            '--newline',
            '--ignore-errors',
            '--no-playlist',
            '--embed-metadata',
            '--embed-chapters',
            url
        ]
        
        if os.path.exists('cookies.txt'):
             cmd.extend(['--cookies', 'cookies.txt'])
             
        logging.debug(f"Starting Download CLI: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1
            )
            
            for line in process.stdout:
                line = line.strip()
                if not line: continue
                
                if progress_hook and '[download]' in line and '%' in line:
                    try:
                        parts = line.split()
                        percent_str = next((p for p in parts if '%' in p), '0%')
                        
                        d = {
                            'status': 'downloading',
                            '_percent_str': percent_str,
                            'filename': 'downloading...'
                        }
                        progress_hook(d)
                    except:
                        pass
                
                elif progress_hook and '[download]' in line and 'Destination:' in line:
                     d = {'status': 'extracting'}
                     progress_hook(d)

            return_code = process.wait()
            
            if return_code != 0:
                 raise Exception(f"CLI Download failed with code {return_code}")
                 
            if progress_hook:
                 progress_hook({'status': 'finished', 'filename': 'Video'})
                 
        except Exception as e:
            logging.error(f"Download CLI Error:\n{traceback.format_exc()}")
            raise e
