import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import json


class FFmpegConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Titan FFmpeg Converter | Ultra Fast")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)

        # Verifica se o FFmpeg está instalado
        if not self.check_ffmpeg():
            messagebox.showerror("Erro Crítico", "FFmpeg não encontrado!\nInstale com: sudo apt install ffmpeg")
            self.root.destroy()
            return

        # Estilo Dark Mode
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.colors = {
            "bg": "#2b2b2b", "fg": "#ffffff", "accent": "#ff5722",  # Laranja FFmpeg
            "secondary": "#3c3f41", "success": "#4caf50", "warning": "#ff9800"
        }
        self.configure_styles()
        self.root.configure(bg=self.colors["bg"])

        # Variáveis
        self.files_queue = []
        self.target_size_mb = tk.DoubleVar(value=98.0)  # Margem de segurança para 100MB
        self.is_converting = False

        self.create_widgets()

    def check_ffmpeg(self):
        """Verifica se o FFmpeg responde no terminal"""
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    def configure_styles(self):
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"],
                             font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground=self.colors["accent"])
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), background=self.colors["secondary"],
                             foreground=self.colors["fg"], borderwidth=0)
        self.style.map("TButton", background=[('active', self.colors["accent"])])
        self.style.configure("Action.TButton", background=self.colors["accent"])
        self.style.map("Action.TButton", background=[('active', "#e64a19")])
        self.style.configure("Treeview", background="#333", foreground="white", fieldbackground="#333", borderwidth=0,
                             font=("Consolas", 9))
        self.style.configure("Treeview.Heading", background="#444", foreground="white", borderwidth=0)
        self.style.map("Treeview", background=[('selected', self.colors["accent"])])
        self.style.configure("Horizontal.TProgressbar", background=self.colors["accent"], troughcolor="#444")

    def create_widgets(self):
        # Header
        header = ttk.Frame(self.root, padding="20")
        header.pack(fill="x")
        ttk.Label(header, text="Conversor FFmpeg Pro", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text="Engine Nativa (C++)", foreground="#888").pack(side="left", padx=10, pady=(5, 0))

        # Toolbar
        toolbar = ttk.Frame(self.root, padding="20 0 20 10")
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="📂 Adicionar Vídeo", command=self.add_files, width=20).pack(side="left", padx=(0, 10))
        ttk.Button(toolbar, text="🗑️ Limpar", command=self.clear_list).pack(side="left")

        sets = ttk.Frame(toolbar)
        sets.pack(side="right")
        ttk.Label(sets, text="Tam. Máx (MB):").pack(side="left", padx=5)
        self.spin_size = ttk.Spinbox(sets, from_=10, to=500, textvariable=self.target_size_mb, width=5)
        self.spin_size.pack(side="left", padx=5)

        # Lista
        list_frame = ttk.Frame(self.root, padding="20 10 20 10")
        list_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(list_frame, columns=("file", "status"), show="headings", selectmode="extended")
        self.tree.heading("file", text="Arquivo")
        self.tree.heading("status", text="Status")
        self.tree.column("file", width=600)
        self.tree.column("status", width=150, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        # Log e Ação
        btm = ttk.Frame(self.root, padding="20 10 20 20")
        btm.pack(fill="x", side="bottom")
        self.lbl_status = ttk.Label(btm, text="Pronto.")
        self.lbl_status.pack(anchor="w")
        self.progress = ttk.Progressbar(btm, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=5)
        self.btn_run = ttk.Button(btm, text="🚀 INICIAR CONVERSÃO RÁPIDA", style="Action.TButton",
                                  command=self.start_thread)
        self.btn_run.pack(fill="x", pady=5)
        self.console = scrolledtext.ScrolledText(btm, height=8, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9),
                                                 state='disabled')
        self.console.pack(fill="x", pady=(10, 0))

    def log(self, msg):
        self.console.config(state='normal')
        self.console.insert(tk.END, f"> {msg}\n")
        self.console.see(tk.END)
        self.console.config(state='disabled')

    def add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Vídeo", "*.mp4 *.mkv *.avi *.mov"), ("Todos", "*.*")])
        for f in files:
            if f not in [i[0] for i in self.files_queue]:
                self.files_queue.append([f, "Pendente"])
                self.tree.insert("", "end", values=(os.path.basename(f), "Pendente"))
                self.log(f"Adicionado: {os.path.basename(f)}")

    def clear_list(self):
        if not self.is_converting:
            self.tree.delete(*self.tree.get_children())
            self.files_queue = []
            self.log("Lista limpa.")

    def get_duration(self, file_path):
        """Usa ffprobe para pegar duração exata em segundos"""
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        try:
            result = subprocess.check_output(cmd).decode('utf-8').strip()
            return float(result)
        except:
            return 0.0

    def start_thread(self):
        if not self.files_queue: return
        self.is_converting = True
        self.btn_run.config(state="disabled")
        threading.Thread(target=self.run_process).start()

    def run_process(self):
        total = len(self.files_queue)
        limit_mb = self.target_size_mb.get()

        for i, item in enumerate(self.files_queue):
            filepath = item[0]
            filename = os.path.basename(filepath)

            # Atualiza UI
            self.root.after(0, lambda: self.progress.configure(value=(i / total) * 100))
            self.root.after(0, lambda: self.lbl_status.configure(text=f"Convertendo: {filename}"))
            child_id = self.tree.get_children()[i]
            self.root.after(0, lambda: self.tree.set(child_id, "status", "🔄 Convertendo..."))

            try:
                # 1. Pega duração
                duration = self.get_duration(filepath)
                if duration == 0:
                    raise Exception("Não foi possível ler a duração.")

                # 2. Calcula Bitrate
                # Fórmula: (MB * 8192) / segundos = kbit/s
                # Ex: (100 * 8192) / 3600 = ~227k
                target_bits = limit_mb * 8192  # 1 MB = 8192 kilobits (1024*8)
                bitrate_calc = int(target_bits / duration)

                # Limites de sanidade (min 32k, max 192k)
                bitrate = max(32, min(bitrate_calc, 192))

                self.root.after(0, lambda m=f"Duração: {duration / 60:.1f}m | Bitrate: {bitrate}k": self.log(m))

                # 3. Prepara Comando FFmpeg
                output_name = os.path.splitext(filepath)[0] + ".mp3"

                # Comando robusto
                cmd = [
                    "ffmpeg", "-y",  # Sobrescrever
                    "-i", filepath,  # Entrada
                    "-vn",  # Sem vídeo
                    "-b:a", f"{bitrate}k",  # Bitrate calculado
                    "-acodec", "libmp3lame",  # Codec MP3
                    output_name  # Saída
                ]

                # Executa
                process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                if process.returncode == 0:
                    self.root.after(0, lambda: self.tree.set(child_id, "status", "✅ Sucesso"))
                    self.root.after(0, lambda n=os.path.basename(output_name): self.log(f"Salvo: {n}"))
                else:
                    raise Exception("FFmpeg retornou erro.")

            except Exception as e:
                self.root.after(0, lambda: self.tree.set(child_id, "status", "❌ Erro"))
                self.root.after(0, lambda err=str(e): self.log(f"ERRO: {err}"))

        self.root.after(0, self.finish)

    def finish(self):
        self.progress.configure(value=100)
        self.lbl_status.configure(text="Concluído.")
        self.btn_run.config(state="normal")
        self.is_converting = False
        messagebox.showinfo("Fim", "Processo finalizado!")


if __name__ == "__main__":
    root = tk.Tk()
    app = FFmpegConverterApp(root)
    root.mainloop()