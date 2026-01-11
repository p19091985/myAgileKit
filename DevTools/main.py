import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import subprocess
from typing import List, Tuple

# Import shared GUI utils
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
import gui_utils

class DevToolsLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Setup Window (Size, Center, Theme)
        gui_utils.setup_window(self, "DevTools - Unified Launcher")

        # Layout principal
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Tool area expands

        # Standard Header
        gui_utils.create_header(self, "DevTools", "Selecione uma ferramenta para continuar")

        # --- Tool List Area ---
        self.tools_list: List[Tuple[str, str, str]] = [
            ("Corretor Streamlit", "corretor_streamlit.py", "Refatora scripts Streamlit corrigindo avisos de depreciação (use_container_width)."),
            ("File Modifier", "file_modifier.py", "Ferramenta para modificação em massa de arquivos com suporte a 30+ linguagens."),
            ("Interface Limpador", "interface_limpador.py", "Interface gráfica para ferramentas de limpeza e remoção de citações."),
            ("Juntar Arquivos", "juntar_arquivos.py", "Utilitário para combinar múltiplos arquivos em um só para análise."),
            ("Removedor de Docstrings", "removedor_docstrings.py", "Remove docstrings de arquivos Python preservando strings SQL."),
            ("Limpar Citações (CLI)", "limpar_citacoes.py", "Ferramenta de linha de comando para limpar citações em textos (Executa no terminal)."),
        ]

        # Canvas for Scrolling
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(self.canvas_frame, bg=gui_utils.COLOR_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.create_tool_cards()

        # Standard Footer
        gui_utils.create_footer(self, "v1.0 - DevTools Unified Launcher")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_tool_cards(self):
        style = ttk.Style()
        style.configure('Card.TFrame', relief='groove', borderwidth=1, background='white')
        
        for name, filename, desc in self.tools_list:
            card = ttk.Frame(self.scrollable_frame, style='Card.TFrame', padding=15)
            card.pack(fill="x", expand=True, padx=10, pady=5)
            
            # Info
            info_frame = ttk.Frame(card, style='Card.TFrame') # Inherit white bg
            info_frame.pack(side="left", fill="both", expand=True)

            ttk.Label(info_frame, text=name, font=('Segoe UI', 12, 'bold'), background='white').pack(anchor="w")
            ttk.Label(info_frame, text=desc, foreground='#555', wraplength=550, background='white').pack(fill="x", anchor="w")

            # Button
            btn = ttk.Button(card, text="Abrir", style='Primary.TButton', command=lambda f=filename: self.launch_tool(f))
            btn.pack(side="right", padx=10)

    def launch_tool(self, filename: str):
        # We assume tools are in 'tools/' subdirectory relative to this script
        script_path = os.path.join(os.path.dirname(__file__), "tools", filename)
        
        if not os.path.exists(script_path):
            messagebox.showerror("Erro", f"Arquivo não encontrado: {script_path}")
            return

        print(f"Iniciando: {filename}...")
        
        try:
            if sys.platform == "win32":
                subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("Erro ao Executar", f"Falha ao iniciar {filename}:\n{e}")

if __name__ == "__main__":
    app = DevToolsLauncher()
    app.mainloop()
