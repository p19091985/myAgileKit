import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import logging
import traceback
from .service import YoutubeService

class YoutubeDownloaderApp:
    def __init__(self, root):
        logging.info("Inicializando a interface gráfica...")
        self.root = root
        self.service = YoutubeService()
        
        self.root.title("YouTube Downloader Pro")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        self.url_var = tk.StringVar()
        self.path_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        self.status_var = tk.StringVar(value="Cole o link e clique em ANALISAR para carregar opções.")
        self.progress_var = tk.DoubleVar(value=0)
        
        self.video_info = None
        self.audio_checkboxes = {} 
        self.sub_checkboxes = {}

        self.create_widgets()
        logging.info("Interface inicializada com sucesso.")

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TButton", padding=5, font=("Arial", 10))
        style.configure("Big.TButton", font=("Arial", 11, "bold"), padding=10)
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        lbl_title = ttk.Label(main_frame, text="Downloader YouTube Pro", font=("Segoe UI", 16, "bold"))
        lbl_title.pack(pady=(0, 20))

        url_frame = ttk.LabelFrame(main_frame, text="Vídeo", padding=(10, 5))
        url_frame.pack(fill=tk.X, pady=(0, 15))

        lbl_url = ttk.Label(url_frame, text="Link do YouTube:")
        lbl_url.pack(anchor=tk.W)
        
        url_input_frame = ttk.Frame(url_frame)
        url_input_frame.pack(fill=tk.X, pady=(5, 5))

        entry_url = ttk.Entry(url_input_frame, textvariable=self.url_var)
        entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_paste = ttk.Button(url_input_frame, text="Colar", width=8, command=self.paste_url)
        btn_paste.pack(side=tk.LEFT, padx=(0, 5))

        btn_clear = ttk.Button(url_input_frame, text="Limpar", width=8, command=self.clear_url)
        btn_clear.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_analyze = ttk.Button(url_input_frame, text="🔍 ANALISAR", width=12, style="Big.TButton", command=self.analyze_video)
        self.btn_analyze.pack(side=tk.LEFT, padx=(10, 0))

        path_frame = ttk.LabelFrame(main_frame, text="Salvar em", padding=(10, 5))
        path_frame.pack(fill=tk.X, pady=(0, 15))
        
        path_input_frame = ttk.Frame(path_frame)
        path_input_frame.pack(fill=tk.X, pady=(5, 5))

        entry_path = ttk.Entry(path_input_frame, textvariable=self.path_var)
        entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_browse = ttk.Button(path_input_frame, text="Escolher...", width=10, command=self.browse_folder)
        btn_browse.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_open_folder = ttk.Button(path_input_frame, text="Abrir Pasta", width=10, command=self.open_folder, state=tk.DISABLED)
        self.btn_open_folder.pack(side=tk.LEFT)

        self.selection_frame = ttk.LabelFrame(main_frame, text="Seleção de Conteúdo (Carregue o vídeo primeiro)", padding=(10, 5))
        self.selection_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.selection_grid = ttk.Frame(self.selection_frame)
        self.selection_grid.pack(fill=tk.BOTH, expand=True)
        
        self.selection_grid.columnconfigure(0, weight=1)
        self.selection_grid.columnconfigure(2, weight=1)
        self.selection_grid.rowconfigure(1, weight=1)

        lbl_audio = ttk.Label(self.selection_grid, text="Áudios Disponíveis", font=("Arial", 10, "bold"))
        lbl_audio.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.audio_canvas = tk.Canvas(self.selection_grid, borderwidth=0, background="#f0f0f0")
        self.audio_frame = ttk.Frame(self.audio_canvas)
        self.vsb_audio = ttk.Scrollbar(self.selection_grid, orient="vertical", command=self.audio_canvas.yview)
        self.audio_canvas.configure(yscrollcommand=self.vsb_audio.set)

        self.vsb_audio.grid(row=1, column=1, sticky="ns", padx=(0,10))
        self.audio_canvas.grid(row=1, column=0, sticky="nsew", padx=5)
        self.audio_canvas.create_window((0,0), window=self.audio_frame, anchor="nw", tags="self.audio_frame")
        self.audio_frame.bind("<Configure>", lambda event: self.audio_canvas.configure(scrollregion=self.audio_canvas.bbox("all")))

        lbl_sub = ttk.Label(self.selection_grid, text="Legendas Disponíveis", font=("Arial", 10, "bold"))
        lbl_sub.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.sub_canvas = tk.Canvas(self.selection_grid, borderwidth=0, background="#f0f0f0")
        self.sub_frame = ttk.Frame(self.sub_canvas)
        self.vsb_sub = ttk.Scrollbar(self.selection_grid, orient="vertical", command=self.sub_canvas.yview)
        self.sub_canvas.configure(yscrollcommand=self.vsb_sub.set)

        self.vsb_sub.grid(row=1, column=3, sticky="ns")
        self.sub_canvas.grid(row=1, column=2, sticky="nsew", padx=5)
        self.sub_canvas.create_window((0,0), window=self.sub_frame, anchor="nw", tags="self.sub_frame")
        self.sub_frame.bind("<Configure>", lambda event: self.sub_canvas.configure(scrollregion=self.sub_canvas.bbox("all")))

        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.lbl_status = ttk.Label(main_frame, textvariable=self.status_var, font=("Segoe UI", 9), foreground="blue")
        self.lbl_status.pack(pady=(0, 20))

        self.btn_download = ttk.Button(main_frame, text="INICIAR DOWNLOAD", style="Big.TButton", command=self.start_download_thread)
        self.btn_download.pack(fill=tk.X, ipady=5)

    def paste_url(self):
        try:
            self.url_var.set(self.root.clipboard_get())
        except:
            pass

    def clear_url(self):
        self.url_var.set("")
        self.status_var.set("Aguardando link...")
        self.progress_var.set(0)
        self.btn_open_folder.config(state=tk.DISABLED)
        self.btn_download.config(state=tk.DISABLED)
        self.video_info = None
        self._clear_checkboxes()

    def _clear_checkboxes(self):
        for widget in self.audio_frame.winfo_children(): widget.destroy()
        for widget in self.sub_frame.winfo_children(): widget.destroy()
        self.audio_checkboxes.clear()
        self.sub_checkboxes.clear()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder: self.path_var.set(folder)

    def open_folder(self):
        path = self.path_var.get()
        if not os.path.exists(path):
            messagebox.showwarning("Aviso", "Caminho não encontrado.")
            return
        
        import platform, subprocess
        try:
            system = platform.system()
            if system == "Windows": os.startfile(path)
            elif system == "Darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir pasta:\n{e}")

    def analyze_video(self):
        url = self.url_var.get()
        if not url:
            messagebox.showwarning("Aviso", "Cole um link primeiro!")
            return
            
        self.status_var.set("Analisando metadados... Aguarde.")
        self.btn_download.config(state=tk.DISABLED)
        self.btn_analyze.config(state=tk.DISABLED)
        self._clear_checkboxes()
        
        threading.Thread(target=self._run_analysis_thread, args=(url,)).start()

    def _run_analysis_thread(self, url):
        info, error, missing_runtime = self.service.get_video_info(url)
        
        if missing_runtime:
            self.root.after(0, lambda: messagebox.showwarning("Aviso de Sistema", 
                "Runtime JavaScript não encontrado!\n\n"
                "Sem o Node.js, áudios dublados não aparecerão.\n"
                "Instale: 'sudo apt install nodejs'"))

        if error:
            logging.error(f"Erro análise: {error}")
            self.root.after(0, lambda: self.status_var.set(f"Erro: {error}"))
            self.root.after(0, lambda: messagebox.showerror("Erro", "Falha ao analisar vídeo."))
            self.root.after(0, lambda: self.btn_analyze.config(state=tk.NORMAL))
        else:
            self.video_info = info
            self.root.after(0, lambda: self.populate_selection_ui(info))

    def populate_selection_ui(self, info):
        self._clear_checkboxes()
        self.status_var.set(f"Vídeo: {info.get('title', 'Desconhecido')[:40]}...")
        self.btn_download.config(state=tk.NORMAL)
        self.btn_analyze.config(state=tk.NORMAL)
        
        audios = self.service.filter_audio_candidates(info)
        for a in audios:
            var = tk.BooleanVar(value=a['is_default'])
            chk = ttk.Checkbutton(self.audio_frame, text=a['label'], variable=var)
            chk.pack(anchor="w", padx=5, pady=2)
            self.audio_checkboxes[a['id']] = var

        subs = self.service.get_subtitle_candidates(info)
        for s in subs:
            var = tk.BooleanVar(value=s['is_default'])
            chk = ttk.Checkbutton(self.sub_frame, text=s['label'], variable=var)
            chk.pack(anchor="w", padx=5, pady=2)
            self.sub_checkboxes[s['lang']] = var

    def start_download_thread(self):
        if not self.video_info: return
        
        url = self.url_var.get()
        path = self.path_var.get()
        
        sel_audios = [fid for fid, var in self.audio_checkboxes.items() if var.get()]
        sel_subs = [lang for lang, var in self.sub_checkboxes.items() if var.get()]
        
        if not sel_audios:
            messagebox.showwarning("Aviso", "Selecione um áudio!")
            return

        self.btn_download.config(state=tk.DISABLED)
        self.status_var.set("Baixando...")
        self.progress_var.set(0)

        threading.Thread(target=self._run_download_thread, args=(url, path, sel_audios, sel_subs)).start()

    def _run_download_thread(self, url, path, audios, subs):
        try:
            self.service.download_video(url, path, audios, subs, self.progress_hook)
            self.root.after(0, lambda: messagebox.showinfo("Sucesso", "Download concluído!"))
            self.root.after(0, lambda: self.status_var.set("Concluído."))
            self.root.after(0, lambda: self.btn_open_folder.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_download.config(state=tk.NORMAL))
        except Exception as e:
            logging.critical(f"Erro download: {traceback.format_exc()}")
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha no download:\n{e}"))
            self.root.after(0, lambda: self.btn_download.config(state=tk.NORMAL))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%', '')
                import re
                p = re.sub(r'\x1b\[[0-9;]*m', '', p)
                self.progress_var.set(float(p))
                self.status_var.set(f"Baixando: {d.get('_percent_str')} | Vel: {d.get('_speed_str')}")
            except: pass
        elif d['status'] == 'finished':
            self.status_var.set("Processando arquivo final...")
            self.progress_var.set(100)
