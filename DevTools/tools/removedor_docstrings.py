import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import sys
import datetime
import ast
import re

# Import shared GUI utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import gui_utils

SQL_KEYWORDS = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'WITH', 'FROM', 'WHERE', 'JOIN', 'SET', 'VALUES', 'TABLE', 'VIEW', 'INTO', 'PRAGMA', 'GROUP BY', 'ORDER BY', 'HAVING', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN', 'ON', 'AS'}

class DocstringRemover(ast.NodeTransformer):
    def _is_sql_string(self, s: str) -> bool:
        s_upper = s.upper()
        s_fragment = s_upper[:200]
        found_keywords = 0
        for keyword in SQL_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', s_fragment):
                found_keywords += 1
        return (found_keywords >= 2)

    def _remove_docstring(self, node):
        if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str)):
            return node
        docstring_content = node.body[0].value.s
        if self._is_sql_string(docstring_content):
            return node
        node.body = node.body[1:]
        return node

    def visit_Module(self, node):
        node = self._remove_docstring(node)
        self.generic_visit(node)
        return node
    def visit_FunctionDef(self, node):
        node = self._remove_docstring(node)
        self.generic_visit(node)
        return node
    def visit_AsyncFunctionDef(self, node):
        node = self._remove_docstring(node)
        self.generic_visit(node)
        return node
    def visit_ClassDef(self, node):
        node = self._remove_docstring(node)
        self.generic_visit(node)
        return node

class DocstringRemoverApp:

    def __init__(self, root):
        self.root = root
        gui_utils.setup_window(self.root, 'DevTools - Removedor Docstrings')
        self.script_directory = gui_utils.get_script_directory()
        self.ast_transformer = DocstringRemover()
        self.logger = None
        self.create_widgets(self.root)

    def create_widgets(self, parent):
        gui_utils.create_header(parent, "Removedor de Docstrings", "Remove docstrings de Python (Cria Backups .bak)")

        main_pad = ttk.Frame(parent, padding=10)
        main_pad.pack(fill=tk.BOTH, expand=True)

        # 1. Source
        source_frame = ttk.LabelFrame(main_pad, text='Diretório Alvo', padding='10')
        source_frame.pack(fill=tk.X, pady=(0, 5))
        self.source_dir_var = tk.StringVar()
        ttk.Entry(source_frame, textvariable=self.source_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(source_frame, text='Procurar...', command=self.browse_source_directory).pack(side=tk.LEFT)

        # 2. Ignored Dirs
        ignore_frame = ttk.LabelFrame(main_pad, text='Diretórios Ignorados', padding='10')
        ignore_frame.pack(fill=tk.X, pady=5)
        self.ignore_dirs_var = tk.StringVar(value='.idea, .vscode, .vs, venv, .venv, env, node_modules, dist, build, target, out, .git, bin, obj, __pycache__')
        ttk.Entry(ignore_frame, textvariable=self.ignore_dirs_var).pack(fill=tk.X)

        # 3. Output Log
        log_frame = ttk.LabelFrame(main_pad, text='Arquivo de Log', padding='10')
        log_frame.pack(fill=tk.X, pady=5)
        self.log_file_var = tk.StringVar()
        ttk.Entry(log_frame, textvariable=self.log_file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(log_frame, text='Salvar Como...', command=self.browse_log_file).pack(side=tk.LEFT)

        # Run
        self.process_button = ttk.Button(main_pad, text='Iniciar Remoção', command=self.start_processing_thread, style='Primary.TButton')
        self.process_button.pack(pady=10, fill=tk.X, ipady=5)

        # Log
        log_disp = ttk.LabelFrame(main_pad, text='Log de Execução', padding='10')
        log_disp.pack(fill='both', expand=True, pady=5)
        
        self.log_text = tk.Text(log_disp, height=8, state='disabled', wrap=tk.WORD, bg='#f9f9f9', font=gui_utils.FONT_CODE)
        sc = ttk.Scrollbar(log_disp, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=sc.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sc.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_source_directory(self):
        d = filedialog.askdirectory()
        if d:
            self.source_dir_var.set(d)
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            self.log_file_var.set(os.path.join(self.script_directory, f'log_docstrings_{ts}.log'))

    def browse_log_file(self):
        f = filedialog.asksaveasfilename(defaultextension='.log', filetypes=[('Log', '*.log')])
        if f: self.log_file_var.set(f)

    def start_processing_thread(self):
        src = self.source_dir_var.get()
        log = self.log_file_var.get()
        if not src or not log: return messagebox.showerror('Erro', 'Defina diretório e log.')
        
        if not messagebox.askyesno('Atenção', f"Isso modificará arquivos em: {src}\nBackups (.bak) serão criados.\nContinuar?", icon='warning'): return
        
        self.process_button.config(state='disabled')
        # Setup Logger
        self.logger = gui_utils.setup_logger("DocstringRemover", log, self.log_text)
        threading.Thread(target=self.process_files, args=(src, self.ignore_dirs_var.get()), daemon=True).start()

    def remove_python_docstrings_only(self, code):
        try:
            tree = ast.parse(code)
            new_tree = self.ast_transformer.visit(tree)
            ast.fix_missing_locations(new_tree)
            return ast.unparse(new_tree)
        except Exception as e:
            return None

    def process_files(self, source_dir, ignored_dirs_str):
        self.logger.info(f"Iniciando em: {source_dir}")
        ign = {x.strip() for x in ignored_dirs_str.split(',') if x.strip()}
        
        try:
            processed = 0
            modified = 0
            
            for root, dirs, files in os.walk(source_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ign]
                for f in files:
                    if f.endswith('.py'):
                        path = os.path.join(root, f)
                        rel = os.path.relpath(path, source_dir)
                        self.logger.info(f"Processando: {rel}")
                        processed += 1
                        
                        try:
                            with open(path, 'r', encoding='utf-8') as ifile:
                                orig = ifile.read()
                            
                            clean = self.remove_python_docstrings_only(orig)
                            if clean and clean != orig:
                                # Backup
                                gui_utils.create_backup(path, self.logger)
                                
                                with open(path, 'w', encoding='utf-8') as ofile:
                                    ofile.write(clean)
                                modified += 1
                                self.logger.info(f"[MODIFICADO] {rel}")
                            else:
                                self.logger.info(f"[SEM MUDANÇAS] {rel}")
                        except Exception as e:
                            self.logger.error(f"[ERRO] {rel}: {e}")
            
            self.logger.info(f'Concluído! Processados: {processed}, Modificados: {modified}')
            self.root.after(0, lambda: messagebox.showinfo('Fim', f'Processados: {processed}, Modificados: {modified}'))
        
        except Exception as e:
            self.logger.error(f"Erro Fatal: {e}")
        finally:
            self.root.after(0, lambda: self.process_button.config(state='normal'))

if __name__ == '__main__':
    root = tk.Tk()
    app = DocstringRemoverApp(root)
    root.mainloop()