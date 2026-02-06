import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import threading
import os
import logging
import traceback

logging.basicConfig(
    filename='debug_log_user.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

class YtDlpLogger:
    def debug(self, msg):
        if not msg.startswith('[debug] '):
            logging.debug(f"[YT-DLP] {msg}")
    def info(self, msg):
        logging.info(f"[YT-DLP] {msg}")
    def warning(self, msg):
        logging.warning(f"[YT-DLP] {msg}")
    def error(self, msg):
        logging.error(f"[YT-DLP] {msg}")

class YoutubeDownloaderApp:
    def __init__(self, root):
        logging.info("Inicializando a interface gráfica...")
        self.root = root
        self.root.title("YouTube 4K Downloader (Debug Mode)")
        
        self.url_var = tk.StringVar(value="https://www.youtube.com/watch?v=0t_DD5568RA")
        self.path_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.status_var = tk.StringVar(value="Aguardando...")
        self.progress_var = tk.DoubleVar(value=0)
        self.lang_var = tk.StringVar(value="Português (Brasil)")

    def start_download_thread(self):
        url = self.url_var.get()
        path = self.path_var.get()
        threading.Thread(target=self.run_download, args=(url, path)).start()

    def progress_hook(self, d):
        if d['status'] == 'finished':
            logging.info("Download finished.")

    def run_download(self, url, path):
        logging.info("Thread de download iniciada.")
        lang_choice = self.lang_var.get()
        
        if "Português" in lang_choice:
            audio_filter = 'bestaudio[language^=pt]'
        else:
            audio_filter = 'bestaudio'

        format_string = f'bestvideo+{audio_filter}/bestvideo+bestaudio/best'

        ydl_opts = {
            'format': format_string,
            'outtmpl': f'{path}/%(title)s.%(ext)s',
            'audio_multistreams': True,
            'merge_output_format': 'mp4',
            'progress_hooks': [self.progress_hook],
            'logger': YtDlpLogger(),
            'cookiefile': 'cookies.txt', 
        }

        try:
            print(f"Attempting download with format: {format_string}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print("Download Success")
        except Exception as e:
            print(f"Download Error: {e}")
            logging.critical(f"FATAL: {traceback.format_exc()}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    app = YoutubeDownloaderApp(root)
    
    app.run_download(app.url_var.get(), app.path_var.get())
