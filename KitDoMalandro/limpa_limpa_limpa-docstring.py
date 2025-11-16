import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import sys
import datetime
import ast
import re
SQL_KEYWORDS = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'WITH', 'FROM', 'WHERE', 'JOIN', 'SET', 'VALUES', 'TABLE', 'VIEW', 'INTO', 'PRAGMA', 'GROUP BY', 'ORDER BY', 'HAVING', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN', 'ON', 'AS'}

class DocstringRemover(ast.NodeTransformer):

    def _is_sql_string(self, s: str) -> bool:
        s_upper = s.upper()
        s_fragment = s_upper[:200]
        found_keywords = 0
        for keyword in SQL_KEYWORDS:
            if re.search('\\b' + keyword + '\\b', s_fragment):
                found_keywords += 1
        s_fragment_clean = s_fragment.strip()
        starts_with_keyword = any((s_fragment_clean.startswith(kw) for kw in SQL_KEYWORDS))
        if starts_with_keyword and found_keywords > 0 or found_keywords >= 2:
            return True
        return False

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
        self.root.title('Removedor de Docstrings Python v1.2 (Ignora SQL)')
        self.root.geometry('700x600')
        self.root.minsize(600, 550)
        self.script_directory = self.get_script_directory()
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        main_frame = ttk.Frame(self.root, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.ast_transformer = DocstringRemover()
        self.create_widgets(main_frame)

    def get_script_directory(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def create_widgets(self, parent):
        source_frame = ttk.LabelFrame(parent, text='1. Selecione o Diretório a ser Modificado', padding='10')
        source_frame.pack(fill=tk.X, expand=True, pady=5)
        self.source_dir_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_dir_var)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        browse_source_btn = ttk.Button(source_frame, text='Procurar...', command=self.browse_source_directory)
        browse_source_btn.pack(side=tk.LEFT)
        ignore_frame = ttk.LabelFrame(parent, text='2. Pastas a Ignorar (separadas por vírgula)', padding='10')
        ignore_frame.pack(fill=tk.X, expand=True, pady=5)
        self.ignore_dirs_var = tk.StringVar(value='.idea, .vscode, .vs, venv, .venv, env, node_modules, dist, build, target, out, .git, bin, obj, __pycache__')
        ignore_entry = ttk.Entry(ignore_frame, textvariable=self.ignore_dirs_var)
        ignore_entry.pack(fill=tk.X, expand=True)
        file_ignore_frame = ttk.LabelFrame(parent, text='3. Arquivos a Ignorar (separados por vírgula)', padding='10')
        file_ignore_frame.pack(fill=tk.X, expand=True, pady=5)
        self.ignore_files_var = tk.StringVar(value='__init__.py, setup.py, manage.py')
        file_ignore_entry = ttk.Entry(file_ignore_frame, textvariable=self.ignore_files_var)
        file_ignore_entry.pack(fill=tk.X, expand=True)
        log_file_frame = ttk.LabelFrame(parent, text='4. Defina o Arquivo de Log', padding='10')
        log_file_frame.pack(fill=tk.X, expand=True, pady=5)
        self.log_file_var = tk.StringVar()
        log_entry = ttk.Entry(log_file_frame, textvariable=self.log_file_var)
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        browse_log_btn = ttk.Button(log_file_frame, text='Salvar Log Como...', command=self.browse_log_file)
        browse_log_btn.pack(side=tk.LEFT)
        self.process_button = ttk.Button(parent, text='Iniciar Remoção de Docstrings (Apenas .py)', command=self.start_processing_thread)
        self.process_button.pack(pady=10, fill=tk.X, ipady=5)
        log_frame = ttk.LabelFrame(parent, text='Log de Progresso', padding='10')
        log_frame.pack(fill='both', expand=True, pady=5)
        toolbar_frame = ttk.Frame(log_frame)
        toolbar_frame.pack(fill='x', pady=(0, 5))
        self.copy_log_button = ttk.Button(toolbar_frame, text='Copiar Log', command=self.copy_log_to_clipboard)
        self.copy_log_button.pack(side='right')
        text_area_frame = ttk.Frame(log_frame)
        text_area_frame.pack(fill='both', expand=True)
        self.log_text = tk.Text(text_area_frame, height=10, state='disabled', wrap=tk.WORD, bg='#f0f0f0')
        log_scrollbar = ttk.Scrollbar(text_area_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_source_directory(self):
        directory = filedialog.askdirectory(title='Selecione a pasta do seu projeto')
        if directory:
            self.source_dir_var.set(directory)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f'remocao_docstrings_log_{timestamp}.log'
            self.log_file_var.set(os.path.join(self.script_directory, log_filename))

    def browse_log_file(self):
        filepath = filedialog.asksaveasfilename(title='Salvar arquivo de log como...', defaultextension='.log', initialdir=self.script_directory, filetypes=[('Log Files', '*.log'), ('Text Files', '*.txt'), ('All Files', '*.*')])
        if filepath:
            self.log_file_var.set(filepath)

    def start_processing_thread(self):
        source_dir = self.source_dir_var.get()
        log_file = self.log_file_var.get()
        ignored_dirs_str = self.ignore_dirs_var.get()
        ignored_files_str = self.ignore_files_var.get()
        if not source_dir or not log_file:
            messagebox.showerror('Erro de Validação', 'O diretório a ser modificado e o arquivo de log devem ser definidos!')
            return
        warning_message = f'''ATENÇÃO!\n\nVocê está prestes a MODIFICAR OS ARQUIVOS ORIGINAIS (.py) no diretório:\n\n'{source_dir}'\n\nEsta ação é IRREVERSÍVEL e removerá TODAS as docstrings (ex: """...""") dos arquivos .py,\nEXCETO os arquivos listados para ignorar (ex: {ignored_files_str.split(',')[0]}...). \nIsto NÃO removerá comentários de linha única (ex: # ...).\n\n**NOVO**: O script NÃO removerá docstrings que contenham palavras-chave SQL (SELECT, INSERT, etc.).\n\nTem certeza que deseja continuar?'''
        if not messagebox.askyesno('Confirmar Modificação Destrutiva', warning_message, icon='warning'):
            return
        self.process_button.config(state='disabled')
        thread = threading.Thread(target=self.process_files, args=(source_dir, log_file, ignored_dirs_str, ignored_files_str))
        thread.daemon = True
        thread.start()

    def remove_python_docstrings_only(self, source_code):
        try:
            tree = ast.parse(source_code)
            new_tree = self.ast_transformer.visit(tree)
            ast.fix_missing_locations(new_tree)
            return ast.unparse(new_tree)
        except (SyntaxError, Exception) as e:
            self.update_log(f'!! Aviso: Falha ao processar com AST (erro de sintaxe no arquivo?), pulando. Erro: {e}')
            return source_code

    def process_files(self, source_dir, log_file, ignored_dirs_str, ignored_files_str):
        self.update_log('Iniciando o processo de remoção de docstrings (.py)...')
        ignored_dirs_set = set()
        if ignored_dirs_str:
            ignored_dirs_set.update({name.strip() for name in ignored_dirs_str.split(',') if name.strip()})
        self.update_log(f'Pastas ignoradas: {', '.join(sorted(list(ignored_dirs_set)))}')
        ignored_files_set = set()
        if ignored_files_str:
            ignored_files_set.update({name.strip() for name in ignored_files_str.split(',') if name.strip()})
        self.update_log(f'Arquivos ignorados: {', '.join(sorted(list(ignored_files_set)))}')
        target_extension = '.py'
        modified_count = 0
        processed_count = 0
        sql_skipped_count = 0
        try:
            with open(log_file, 'w', encoding='utf-8') as log_f:
                log_f.write(f'Log de Remoção de Docstrings (v1.2 - Ignora SQL) - {datetime.datetime.now()}\n')
                log_f.write(f'Diretório Alvo: {source_dir}\n')
                log_f.write('=' * 80 + '\n\n')
                for root, dirs, files in os.walk(source_dir):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignored_dirs_set]
                    for filename in files:
                        if filename in ignored_files_set:
                            file_path = os.path.join(root, filename)
                            relative_path = os.path.relpath(file_path, source_dir)
                            log_message = f'[IGNORADO (exceção)] {relative_path}'
                            self.update_log(log_message)
                            log_f.write(log_message + '\n')
                            continue
                        if filename.lower().endswith(target_extension):
                            file_path = os.path.join(root, filename)
                            relative_path = os.path.relpath(file_path, source_dir)
                            processed_count += 1
                            self.update_log(f'Analisando: {relative_path}')
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                                    original_content = infile.read()
                                if not original_content.strip():
                                    log_message = f'[IGNORADO (vazio)] {relative_path}'
                                    log_f.write(log_message + '\n')
                                    continue
                                is_sql_docstring = False
                                try:
                                    tree_check = ast.parse(original_content)
                                    if tree_check.body and isinstance(tree_check.body[0], ast.Expr) and isinstance(tree_check.body[0].value, ast.Str):
                                        if self.ast_transformer._is_sql_string(tree_check.body[0].value.s):
                                            is_sql_docstring = True
                                except:
                                    pass
                                cleaned_content = self.remove_python_docstrings_only(original_content)
                                if original_content != cleaned_content:
                                    with open(file_path, 'w', encoding='utf-8') as outfile:
                                        outfile.write(cleaned_content)
                                    modified_count += 1
                                    log_message = f'[MODIFICADO] {relative_path}'
                                    self.update_log(log_message)
                                    log_f.write(log_message + '\n')
                                elif is_sql_docstring:
                                    log_message = f'[PRESERVADO (SQL detectado)] {relative_path}'
                                    self.update_log(log_message)
                                    log_f.write(log_message + '\n')
                                    sql_skipped_count += 1
                                else:
                                    log_message = f'[IGNORADO (sem alterações)] {relative_path}'
                                    log_f.write(log_message + '\n')
                            except Exception as e:
                                error_log = f'!! ERRO ao processar {relative_path}: {e}'
                                self.update_log(error_log)
                                log_f.write(error_log + '\n')
                final_summary = f'\nPROCESSO CONCLUÍDO!\n{processed_count} arquivos .py analisados.\n{modified_count} arquivos .py foram modificados.\n{sql_skipped_count} arquivos .py foram preservados por conterem SQL em docstrings.\n(Arquivos na lista de exceção não foram contados)\n\nUm log detalhado foi salvo em: {log_file}'
                self.update_log(final_summary)
                log_f.write('\n' + '=' * 80 + '\n')
                log_f.write(final_summary.strip())
                self.root.after(0, lambda: messagebox.showinfo('Sucesso', final_summary.strip()))
        except Exception as e:
            error_message = f'!! ERRO GERAL: {e}'
            self.update_log(error_message)
            self.root.after(0, lambda: messagebox.showerror('Erro Fatal', f'Ocorreu um erro inesperado: {e}'))
        finally:
            self.root.after(0, lambda: self.process_button.config(state='normal'))

    def copy_log_to_clipboard(self):
        try:
            log_content = self.log_text.get('1.0', tk.END).strip()
            if not log_content:
                return
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            original_text = self.copy_log_button.cget('text')
            self.copy_log_button.config(text='Copiado!', state='disabled')
            self.root.after(2000, lambda: self.copy_log_button.config(text=original_text, state='normal'))
        except Exception as e:
            messagebox.showwarning('Erro ao Copiar', f'Não foi possível copiar o log: {e}')

    def update_log(self, message):
        self.root.after(0, self._update_log_thread_safe, message)

    def _update_log_thread_safe(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)
if __name__ == '__main__':
    if sys.version_info < (3, 9):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('Erro de Versão', "Este script requer Python 3.9 ou superior para funcionar corretamente (devido ao módulo 'ast.unparse').")
        sys.exit(1)
    root = tk.Tk()
    app = DocstringRemoverApp(root)
    root.mainloop()