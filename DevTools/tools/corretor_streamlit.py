import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import sys
import threading
from typing import Set
import datetime

# Import shared GUI utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import gui_utils

'\nScript com GUI (TTK) para refatorar scripts Streamlit, \ncorrigindo avisos de depreciação (DeprecationWarning) do \'use_container_width\'.\n\nLógica de Substituição:\n- \'use_container_width=True\' é SUBSTITUÍDO por \'width="stretch"\'.\n- \'use_container_width=False\' é SUBSTITUÍDO por \'width="content"\'.\n'
pattern_true = re.compile(r'\buse_container_width\s*=\s*True', re.IGNORECASE)
replacement_true = "width='stretch'"
pattern_false = re.compile(r'\buse_container_width\s*=\s*False', re.IGNORECASE)
replacement_false = "width='content'"
EXCLUDE_DIRS: Set[str] = {'.venv', 'venv', 'env', '.git', '.idea', '__pycache__', 'node_modules'}

class RefactorGUI(tk.Tk):

    def __init__(self):
        super().__init__()
        gui_utils.setup_window(self, 'DevTools - Corretor Streamlit')
        
        self.selected_paths: Set[str] = set()
        self.thread = None
        self.logger = None
        
        self.create_widgets()

    def create_widgets(self):
        gui_utils.create_header(self, "Corretor Streamlit", "Corrige deprecações como 'use_container_width'")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Main content expands

        main_frame = ttk.Frame(self, padding='10')
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=0) # Button column
        main_frame.rowconfigure(1, weight=1) # Listbox expands
        main_frame.rowconfigure(3, weight=1) # Log expands

        # Input Section
        ttk.Label(main_frame, text='Seleção de Fonte:', font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 5))
        
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, rowspan=2, sticky='nsew', padx=(0, 10))
        
        self.path_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=8)
        self.path_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.path_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.path_listbox.config(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=1, sticky='n')
        
        ttk.Button(button_frame, text='Adicionar Arquivos...', command=self.select_files).pack(fill='x', pady=2)
        ttk.Button(button_frame, text='Adicionar Pasta...', command=self.select_directory).pack(fill='x', pady=2)
        ttk.Separator(button_frame, orient='horizontal').pack(fill='x', pady=5)
        ttk.Button(button_frame, text='Remover Selecionados', command=self.remove_selected).pack(fill='x', pady=2)
        ttk.Button(button_frame, text='Limpar Lista', command=self.clear_list).pack(fill='x', pady=2)
        
        self.btn_copy_log = ttk.Button(button_frame, text='Copiar Log', command=self.copy_log)
        self.btn_copy_log.pack(fill='x', pady=2)

        # Run Button
        self.run_button = ttk.Button(main_frame, text='Iniciar Correção', command=self.start_refactor, style='Primary.TButton')
        self.run_button.grid(row=2, column=1, sticky='sew', padx=0, pady=5)

        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text='Log de Execução', padding='5')
        log_frame.grid(row=3, column=0, columnspan=2, sticky='nsew', pady=5)
        
        self.log_area = tk.Text(log_frame, height=10, state='disabled', font=gui_utils.FONT_CODE)
        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_area.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_area.config(yscrollcommand=log_scroll.set)
        
        # Status Bar
        self.status_label = ttk.Label(self, text='Status: Aguardando Início', relief='sunken', padding=5, background='#e0e0e0', anchor='w')
        self.status_label.grid(row=2, column=0, sticky='ew')

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[('Python Files', '*.py'), ('All Files', '*.*')])
        for f in files:
            if f not in self.selected_paths:
                self.selected_paths.add(f)
                self.update_listbox()

    def select_directory(self):
        d = filedialog.askdirectory()
        if d:
            if d not in self.selected_paths:
                self.selected_paths.add(d)
                self.update_listbox()

    def remove_selected(self):
        selection = self.path_listbox.curselection()
        if not selection: return
        paths_to_remove = [self.path_listbox.get(i) for i in selection]
        for p in paths_to_remove:
            self.selected_paths.discard(p)
        self.update_listbox()

    def clear_list(self):
        self.selected_paths.clear()
        self.update_listbox()
        self.log_area.config(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.config(state='disabled')
        self.status_label.config(text='Status: Aguardando Início')

    def update_listbox(self):
        self.path_listbox.delete(0, tk.END)
        for p in sorted(self.selected_paths):
            self.path_listbox.insert(tk.END, p)

    def copy_log(self):
        self.clipboard_clear()
        self.clipboard_append(self.log_area.get('1.0', tk.END))
        messagebox.showinfo("Sucesso", "Log copiado para a área de transferência.")

    def toggle_controls(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        self.run_button.config(state=state)
        self.btn_copy_log.config(state=state)
        if enabled:
            self.run_button.config(text='Iniciar Correção')
        else:
            self.run_button.config(text='Executando...')

    def start_refactor(self):
        if not self.selected_paths:
            messagebox.showwarning('Nada Selecionado', 'Por favor, selecione arquivos ou pastas para processar.')
            return
        
        # Setup Logger
        ts = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"Corretor_Log_{ts}.log")
        self.logger = gui_utils.setup_logger("Corretor", log_file, self.log_area)

        self.toggle_controls(False)
        self.status_label.config(text='Status: Iniciando...')
        self.thread = threading.Thread(target=self.run_refactor_logic, daemon=True)
        self.thread.start()

    def run_refactor_logic(self):
        self.logger.info("Iniciando varredura para correção do 'use_container_width'...")
        self.logger.info(f"Pastas ignoradas: {', '.join(EXCLUDE_DIRS)}")
        
        arquivos_modificados = 0
        arquivos_verificados = 0
        
        paths_to_process = self.selected_paths.copy()
        
        for path in paths_to_process:
            if os.path.isfile(path):
                if path.endswith('.py'):
                    self.logger.info(f"Verificando arquivo: {path}")
                    arquivos_verificados += 1
                    if self.processar_arquivo_thread(path):
                        arquivos_modificados += 1
                else:
                    self.logger.info(f"[IGNORADO] Não é um arquivo .py: {path}")
                    
            elif os.path.isdir(path):
                self.logger.info(f"--- Varrendo diretório recursivamente: {path} ---")
                for dirpath, dirnames, filenames in os.walk(path, topdown=True):
                    dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
                    for filename in filenames:
                        if filename.endswith('.py'):
                            file_path = os.path.join(dirpath, filename)
                            self.logger.info(f"Verificando arquivo: {file_path}")
                            arquivos_verificados += 1
                            if self.processar_arquivo_thread(file_path):
                                arquivos_modificados += 1
                self.logger.info(f"--- Fim da varredura: {path} ---")
        
        self.logger.info("--- Concluído ---")
        self.logger.info(f"Arquivos .py verificados: {arquivos_verificados}")
        self.logger.info(f"Arquivos .py modificados: {arquivos_modificados}")
        self.status_label.config(text=f'Concluído. Modificados: {arquivos_modificados}')
        
        self.after(0, lambda: self.toggle_controls(True))
        self.after(0, lambda: messagebox.showinfo("Fim", f"Processamento finalizado!\nModificados: {arquivos_modificados}"))

    def processar_arquivo_thread(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified_content = content
            
            # Count matches for detailed logging
            matches_true = len(pattern_true.findall(content))
            matches_false = len(pattern_false.findall(content))
            
            if matches_true > 0 or matches_false > 0:
                # Create Backup
                gui_utils.create_backup(file_path, self.logger)
                
                modified_content = pattern_true.sub(replacement_true, modified_content)
                modified_content = pattern_false.sub(replacement_false, modified_content)
                
                if modified_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    
                    self.logger.info(f"[MODIFICADO] {file_path}")
                    if matches_true: self.logger.info(f"  - Substituído 'use_container_width=True' -> 'stretch' ({matches_true} vezes)")
                    if matches_false: self.logger.info(f"  - Substituído 'use_container_width=False' -> 'content' ({matches_false} vezes)")
                    return True
            
        except Exception as e:
            self.logger.error(f"[ERRO] Falha ao processar {file_path}: {e}")
            
        return False

if __name__ == '__main__':
    app = RefactorGUI()
    app.mainloop()