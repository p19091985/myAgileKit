import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import os
import re
import sys
import threading
import queue
from typing import Set

"""
Script "Padrão Ouro" com GUI (TTK) para refatorar scripts Streamlit, 
corrigindo avisos de depreciação (DeprecationWarning) do 'use_container_width'.

Lógica de Duas Passagens:
1.  Gráficos Altair (st.altair_chart): O parâmetro 'use_container_width'
    é COMPLETAMENTE REMOVIDO.
2.  Outros Elementos (st.dataframe, st.button, etc.):
    - 'use_container_width=True' é SUBSTITUÍDO por 'width="stretch"'.
    - 'use_container_width=False' é SUBSTITUÍDO por 'width="content"'.
"""

# --- Lógica de Refatoração (Padrão Ouro) ---

# Regex para st.altair_chart(..., use_container_width=True)
pattern_altair = re.compile(
    r"(st\.altair_chart\([^\)]*?)"  # (1) Início da chamada
    r"(,?\s*use_container_width\s*=\s*True\s*,?)"  # (2) O parâmetro (e vírgulas)
    r"([^\)]*\))",  # (3) O resto da chamada
    re.IGNORECASE
)
replacement_altair = r"\1\3"  # Remove o grupo (2)

# Padrões gerais para outros elementos
pattern_true = re.compile(r"use_container_width\s*=\s*True", re.IGNORECASE)
replacement_true = "width='stretch'"

pattern_false = re.compile(r"use_container_width\s*=\s*False", re.IGNORECASE)
replacement_false = "width='content'"


# --- Classe da Aplicação GUI ---

class RefactorGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Corretor de Depreciação Streamlit (Padrão Ouro)")
        self.geometry("800x600")
        self.minsize(600, 400)

        # Tenta usar um tema TTK mais moderno
        try:
            style = ttk.Style(self)
            style.theme_use('clam')  # 'clam', 'alt', 'default', 'classic'
        except tk.TclError:
            print("Tema 'clam' não encontrado, usando padrão.")

        self.selected_paths: Set[str] = set()
        self.log_queue = queue.Queue()
        self.thread = None

        self.create_widgets()
        self.process_log_queue()

    def create_widgets(self):
        """Cria a estrutura principal da interface."""

        # --- Configuração do Layout Principal ---
        # Faz com que o frame principal expanda com a janela
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configura as colunas e linhas do main_frame
        main_frame.columnconfigure(0, weight=1)  # Coluna da lista
        main_frame.columnconfigure(1, weight=0)  # Coluna dos botões
        main_frame.rowconfigure(1, weight=1)  # Linha da lista
        main_frame.rowconfigure(3, weight=2)  # Linha do log

        # --- 1. Seleção de Arquivos/Pastas ---
        ttk.Label(main_frame, text="Arquivos e Pastas para Processar:",
                  font=("-weight bold")).grid(row=0, column=0, columnspan=2, sticky="w")

        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(0, 5))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.path_listbox = tk.Listbox(list_frame, selectmode="extended", width=70, height=10)
        self.path_listbox.grid(row=0, column=0, sticky="nsew")

        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.path_listbox.yview)
        list_scrollbar.grid(row=0, column=1, sticky="ns")
        self.path_listbox.config(yscrollcommand=list_scrollbar.set)

        # --- 2. Botões de Ação (Seleção) ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=1, sticky="nw")

        self.btn_select_files = ttk.Button(button_frame, text="Selecionar Arquivos (.py)", command=self.select_files)
        self.btn_select_files.pack(fill="x", pady=2)

        self.btn_select_dir = ttk.Button(button_frame, text="Selecionar Pasta (Recursivo)",
                                         command=self.select_directory)
        self.btn_select_dir.pack(fill="x", pady=2)

        self.btn_clear_list = ttk.Button(button_frame, text="Limpar Lista", command=self.clear_list)
        self.btn_clear_list.pack(fill="x", pady=2)

        # --- 3. Botão de Execução ---
        self.run_button = ttk.Button(main_frame, text="🚀 EXECUTAR REFATORAÇÃO 🚀", command=self.start_refactor,
                                     style="Accent.TButton")
        self.run_button.grid(row=2, column=1, sticky="sew", padx=0, pady=5)
        style = ttk.Style(self)
        style.configure("Accent.TButton", font=("-weight bold"), padding=10)

        # --- 4. Log de Saída ---
        ttk.Label(main_frame, text="Log de Saída:",
                  font=("-weight bold")).grid(row=2, column=0, sticky="sw", pady=(5, 0))

        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(5, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled", height=15)
        self.log_area.grid(row=0, column=0, sticky="nsew")

        # --- 5. Status Bar ---
        self.status_label = ttk.Label(main_frame, text="Status: Ocioso", relief="sunken", padding=5)
        self.status_label.grid(row=4, column=0, columnspan=2, sticky="sew", pady=(5, 0))

    # --- Funções de Callback ---

    def select_files(self):
        """Abre diálogo para selecionar arquivos .py."""
        files = filedialog.askopenfilenames(
            title="Selecione os arquivos Python",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if files:
            for f in files:
                self.selected_paths.add(os.path.abspath(f))
            self.update_listbox()

    def select_directory(self):
        """Abre diálogo para selecionar um diretório."""
        directory = filedialog.askdirectory(title="Selecione uma pasta para varrer recursivamente")
        if directory:
            self.selected_paths.add(os.path.abspath(directory))
            self.update_listbox()

    def clear_list(self):
        """Limpa a lista de seleção e o log."""
        self.selected_paths.clear()
        self.update_listbox()
        self.log_area.config(state="normal")
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state="disabled")
        self.status_label.config(text="Status: Ocioso")

    def update_listbox(self):
        """Atualiza a Listbox com os caminhos selecionados."""
        self.path_listbox.delete(0, tk.END)
        sorted_paths = sorted(list(self.selected_paths))
        for path in sorted_paths:
            # Adiciona um marcador se for diretório
            marker = "[PASTA] " if os.path.isdir(path) else ""
            self.path_listbox.insert(tk.END, f"{marker}{path}")

    def log(self, message: str):
        """Insere uma mensagem na área de log (deve ser chamado pelo GUI thread)."""
        if not message:
            return
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message.strip() + "\n")
        self.log_area.config(state="disabled")
        self.log_area.see(tk.END)

    def process_log_queue(self):
        """Processa mensagens da fila de log (thread-safe)."""
        try:
            while not self.log_queue.empty():
                message = self.log_queue.get_nowait()

                if message == "---THREAD_DONE---":
                    self.toggle_controls(True)
                elif message.startswith("STATUS:"):
                    self.status_label.config(text=message)
                else:
                    self.log(message)

        finally:
            self.after(100, self.process_log_queue)  # Re-agenda a verificação

    def toggle_controls(self, enabled: bool):
        """Ativa ou desativa os botões durante a execução."""
        state = "normal" if enabled else "disabled"
        self.btn_select_files.config(state=state)
        self.btn_select_dir.config(state=state)
        self.btn_clear_list.config(state=state)
        self.run_button.config(state=state)

        if enabled:
            self.run_button.config(text="🚀 EXECUTAR REFATORAÇÃO 🚀")
        else:
            self.run_button.config(text="⏳ Executando...")

    def start_refactor(self):
        """Inicia a thread de refatoração."""
        if not self.selected_paths:
            tk.messagebox.showwarning("Nada Selecionado", "Por favor, selecione arquivos ou pastas para processar.")
            return

        # Limpa o log e desativa controles
        self.log_area.config(state="normal")
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state="disabled")
        self.toggle_controls(False)
        self.status_label.config(text="Status: Iniciando...")

        # Inicia a thread de trabalho
        self.thread = threading.Thread(target=self.run_refactor_logic, daemon=True)
        self.thread.start()

    # --- Lógica de Trabalho (Executada na Thread) ---

    def run_refactor_logic(self):
        """Lógica principal de varredura e refatoração (executa em background)."""
        self.log_queue.put("Iniciando varredura para correção do 'use_container_width'...")
        self.log_queue.put("=" * 60)

        arquivos_modificados = 0
        arquivos_verificados = 0
        paths_to_process = self.selected_paths.copy()  # Copia para thread-safety

        for path in paths_to_process:
            if os.path.isfile(path):
                if path.endswith(".py"):
                    self.log_queue.put(f"Verificando arquivo: {path}")
                    arquivos_verificados += 1
                    if self.processar_arquivo_thread(path):
                        arquivos_modificados += 1
                else:
                    self.log_queue.put(f"[IGNORADO] Não é um arquivo .py: {path}")

            elif os.path.isdir(path):
                self.log_queue.put(f"--- Varrendo diretório recursivamente: {path} ---")
                for dirpath, _, filenames in os.walk(path):
                    for filename in filenames:
                        if filename.endswith(".py"):
                            file_path = os.path.join(dirpath, filename)
                            self.log_queue.put(f"Verificando arquivo: {file_path}")
                            arquivos_verificados += 1
                            if self.processar_arquivo_thread(file_path):
                                arquivos_modificados += 1
                self.log_queue.put(f"--- Fim da varredura: {path} ---")

        self.log_queue.put("=" * 60)
        self.log_queue.put("--- Concluído ---")
        self.log_queue.put(f"Arquivos .py verificados: {arquivos_verificados}")
        self.log_queue.put(f"Arquivos .py modificados: {arquivos_modificados}")
        self.log_queue.put(
            f"STATUS: Concluído (Verificados: {arquivos_verificados}, Modificados: {arquivos_modificados})")
        self.log_queue.put("---THREAD_DONE---")  # Sinaliza para reativar botões

    def processar_arquivo_thread(self, file_path: str) -> bool:
        """
        Versão da lógica de processamento que usa a 'log_queue'
        para ser thread-safe.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            modified_content = content

            # --- Passagem 1: Corrigir st.altair_chart ---
            modified_content = pattern_altair.sub(replacement_altair, modified_content)

            # --- Passagem 2: Corrigir outros elementos ---
            modified_content = pattern_true.sub(replacement_true, modified_content)
            modified_content = pattern_false.sub(replacement_false, modified_content)

            if modified_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                self.log_queue.put(f"  [MODIFICADO] {file_path}")
                return True

        except Exception as e:
            self.log_queue.put(f"  [ERRO] Não foi possível processar {file_path}: {e}")

        return False


# --- Ponto de Entrada ---
if __name__ == "__main__":
    app = RefactorGUI()
    app.mainloop()