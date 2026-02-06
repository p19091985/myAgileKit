import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import sys
import re
import tokenize
import io
import datetime
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import gui_utils

SUPPORTED_LANGUAGES = {
    'C': (['.c'], 'c_style'), 'C++': (['.cpp', '.cc', '.cxx', '.h', '.hpp'], 'c_style'), 'C#': (['.cs'], 'c_style'),
    'Java': (['.java'], 'c_style'), 'JavaScript': (['.js', '.jsx', '.mjs'], 'c_style'), 'TypeScript': (['.ts', '.tsx'], 'c_style'),
    'Go': (['.go'], 'c_style'), 'Rust': (['.rs'], 'c_style'), 'Swift': (['.swift'], 'c_style'), 'Kotlin': (['.kt', '.kts'], 'c_style'),
    'Scala': (['.scala'], 'c_style'), 'Dart': (['.dart'], 'c_style'), 'PHP': (['.php'], 'c_style'), 'Groovy': (['.groovy'], 'c_style'),
    'Objective-C': (['.m', '.mm'], 'c_style'), 'CSS': (['.css'], 'c_style'), 'Python': (['.py'], 'python'), 'Ruby': (['.rb'], 'hash_style'),
    'Perl': (['.pl', '.pm'], 'hash_style'), 'R': (['.r'], 'hash_style'), 'Shell/Bash': (['.sh', '.bash', '.zsh'], 'hash_style'),
    'YAML': (['.yaml', '.yml'], 'hash_style'), 'TOML': (['.toml'], 'hash_style'), 'Dockerfile': (['Dockerfile'], 'hash_style'),
    'Elixir': (['.ex', '.exs'], 'hash_style'), 'Julia': (['.jl'], 'hash_style'), 'PowerShell': (['.ps1'], 'hash_style'),
    'Properties/INI': (['.ini', '.properties'], 'hash_style'), 'HTML': (['.html', '.htm'], 'xml_style'),
    'XML': (['.xml', '.xsd', '.config'], 'xml_style'), 'SVG': (['.svg'], 'xml_style'), 'Vue': (['.vue'], 'xml_style'),
    'SQL': (['.sql'], 'sql_style'), 'Lua': (['.lua'], 'doubledash_style'), 'Haskell': (['.hs'], 'doubledash_style'),
    'Visual Basic/VBA': (['.vb', '.vbs'], 'quote_style'), 'Assembly': (['.asm', '.s'], 'semicolon_style'),
    'Batch': (['.bat', '.cmd'], 'batch_style'), 'Matlab': (['.m'], 'percent_style'), 'LaTeX': (['.tex'], 'percent_style'),
}

class ScrollableCheckboxFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self, height=150, bg=gui_utils.COLOR_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

class CommentRemoverApp:

    def __init__(self, root):
        self.root = root
        gui_utils.setup_window(self.root, 'DevTools - File Modifier')
        self.script_directory = gui_utils.get_script_directory()
        self.logger = None
        
        self.create_widgets(self.root)

    def create_widgets(self, parent):
        gui_utils.create_header(parent, "File Modifier", "Remoção de comentários para 30+ linguagens com segurança")

        main_pad = ttk.Frame(parent, padding=10)
        main_pad.pack(fill=tk.BOTH, expand=True)

        source_frame = ttk.LabelFrame(main_pad, text='Diretório de Origem', padding='10')
        source_frame.pack(fill=tk.X, expand=False, pady=(0, 5))
        
        self.source_dir_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_dir_var)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_source_btn = ttk.Button(source_frame, text='Procurar...', command=self.browse_source_directory)
        browse_source_btn.pack(side=tk.LEFT)

        ext_frame_container = ttk.LabelFrame(main_pad, text='Filtro de Linguagens', padding='10')
        ext_frame_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tools_frame = ttk.Frame(ext_frame_container)
        tools_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(tools_frame, text="Selecionar Todos", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(tools_frame, text="Deselecionar Todos", command=self.deselect_all).pack(side=tk.LEFT)

        self.scroll_frame = ScrollableCheckboxFrame(ext_frame_container)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.extension_vars = {}
        num_columns = 4
        sorted_languages = sorted(SUPPORTED_LANGUAGES.keys())
        for i, lang in enumerate(sorted_languages):
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(self.scroll_frame.scrollable_frame, text=lang, variable=var)
            row = i // num_columns
            col = i % num_columns
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
            self.extension_vars[lang] = var

        ignore_frame = ttk.LabelFrame(main_pad, text='Diretórios Ignorados (separados por vírgula)', padding='10')
        ignore_frame.pack(fill=tk.X, expand=False, pady=5)
        self.ignore_dirs_var = tk.StringVar(value='.idea, .vscode, .vs, venv, .venv, env, node_modules, dist, build, target, out, .git, bin, obj, __pycache__')
        ttk.Entry(ignore_frame, textvariable=self.ignore_dirs_var).pack(fill=tk.X, expand=True)

        options_frame = ttk.LabelFrame(main_pad, text='Opções', padding='10')
        options_frame.pack(fill=tk.X, expand=False, pady=5)
        self.reduce_line_breaks_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text='Reduzir múltiplas linhas em branco (2+) para apenas uma', variable=self.reduce_line_breaks_var).pack(side=tk.LEFT, padx=5)

        log_file_frame = ttk.LabelFrame(main_pad, text='Arquivo de Log', padding='10')
        log_file_frame.pack(fill=tk.X, expand=False, pady=5)
        
        self.log_file_var = tk.StringVar()
        ttk.Entry(log_file_frame, textvariable=self.log_file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(log_file_frame, text='Salvar Log Como...', command=self.browse_log_file).pack(side=tk.LEFT)

        self.process_button = ttk.Button(main_pad, text='Iniciar Remoção', command=self.start_processing_thread, style='Primary.TButton')
        self.process_button.pack(pady=10, fill=tk.X, ipady=5)
        
        log_frame = ttk.LabelFrame(main_pad, text='Log de Execução', padding='10')
        log_frame.pack(fill='both', expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, state='disabled', wrap=tk.WORD, bg='#f9f9f9', font=gui_utils.FONT_CODE)
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def select_all(self):
        for var in self.extension_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.extension_vars.values():
            var.set(False)

    def browse_source_directory(self):
        directory = filedialog.askdirectory(title='Selecione a pasta do seu projeto')
        if directory:
            self.source_dir_var.set(directory)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f'Modifier_Log_{timestamp}.log'
            self.log_file_var.set(os.path.join(self.script_directory, log_filename))

    def browse_log_file(self):
        filepath = filedialog.asksaveasfilename(title='Salvar log...', defaultextension='.log', initialdir=self.script_directory, filetypes=[('Log Files', '*.log')])
        if filepath:
            self.log_file_var.set(filepath)

    def start_processing_thread(self):
        source_dir = self.source_dir_var.get()
        log_file = self.log_file_var.get()
        
        selected_languages = [lang for lang, var in self.extension_vars.items() if var.get()]
        ignored_dirs_str = self.ignore_dirs_var.get()
        reduce_lines = self.reduce_line_breaks_var.get()

        if not source_dir or not log_file:
            messagebox.showerror('Erro', 'Diretório e Log são obrigatórios!')
            return
        if not selected_languages:
            messagebox.showerror('Erro', 'Selecione pelo menos uma linguagem!')
            return

        warning_message = f"ATENÇÃO!\n\nVocê vai modificar arquivos em: '{source_dir}'\n\nIsso removerá comentários. BACKUPS (.bak) SERÃO CRIADOS.\n\nContinuar?"
        if not messagebox.askyesno('Confirmação', warning_message, icon='warning'):
            return

        self.logger = gui_utils.setup_logger("FileModifier", log_file, self.log_text)

        self.process_button.config(state='disabled')
        thread = threading.Thread(target=self.process_files, args=(source_dir, selected_languages, ignored_dirs_str, reduce_lines))
        thread.daemon = True
        thread.start()

    def remove_python_comments(self, source_code):
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source_code).readline)
            non_comment_tokens = [tok for tok in tokens if tok.type != tokenize.COMMENT]
            return tokenize.untokenize(non_comment_tokens)
        except: return source_code

    def generic_regex_cleaner(self, text, line_pattern, block_pattern=None):
        if block_pattern: text = re.sub(block_pattern, '', text, flags=re.DOTALL)
        if line_pattern: text = re.sub(line_pattern, '', text, flags=re.MULTILINE)
        return text

    def clean_content(self, content, strategy):
        if strategy == 'python': return self.remove_python_comments(content)
        elif strategy == 'c_style': return self.generic_regex_cleaner(content, r'//.*$', r'/\*.*?\*/')
        elif strategy == 'hash_style': return self.generic_regex_cleaner(content, r'#.*$', None)
        elif strategy == 'xml_style': return self.generic_regex_cleaner(content, None, r'<!--.*?-->')
        elif strategy == 'sql_style': return self.generic_regex_cleaner(content, r'--.*$', r'/\*.*?\*/')
        elif strategy == 'doubledash_style': return self.generic_regex_cleaner(content, r'--.*$', None)
        elif strategy == 'quote_style': return self.generic_regex_cleaner(content, r"'.*$", None)
        elif strategy == 'semicolon_style': return self.generic_regex_cleaner(content, r';.*$', None)
        elif strategy == 'batch_style':
             content = re.sub(r'^\s*REM.*$', '', content, flags=re.MULTILINE | re.IGNORECASE)
             content = re.sub(r'^\s*::.*$', '', content, flags=re.MULTILINE)
             return content
        elif strategy == 'percent_style': return self.generic_regex_cleaner(content, r'%.*$', None)
        return content

    def process_files(self, source_dir, selected_langs, ignored_dirs_str, reduce_lines):
        self.logger.info('Iniciando processamento...')
        ignored_dirs_set = {'__pycache__'}
        if ignored_dirs_str: ignored_dirs_set.update({name.strip() for name in ignored_dirs_str.split(',') if name.strip()})
        
        target_extensions = {}
        for lang in selected_langs:
            exts, strategy = SUPPORTED_LANGUAGES[lang]
            for ext in exts:
                target_extensions[ext] = strategy

        processed = 0
        modified = 0

        try:
            self.logger.info(f"Diretório: {source_dir}")
            self.logger.info(f"Linguagens: {', '.join(selected_langs)}")

            for root, dirs, files in os.walk(source_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignored_dirs_set]
                for filename in files:
                    _, ext = os.path.splitext(filename)
                    ext = ext.lower()
                    if filename == 'Dockerfile' and 'Dockerfile' in target_extensions:
                        strategy = target_extensions['Dockerfile']
                    elif ext in target_extensions:
                        strategy = target_extensions[ext]
                    else: continue

                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, source_dir)
                    processed += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            original = f.read()
                        
                        cleaned = self.clean_content(original, strategy)
                        if reduce_lines:
                            cleaned = re.sub(r'(\s*?\n){3,}', '\n\n', cleaned)
                        
                        if original != cleaned:
                            gui_utils.create_backup(file_path, self.logger)
                            
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(cleaned)
                            modified += 1
                            self.logger.info(f"[MODIFICADO] {relative_path}")
                        else:
                            self.logger.info(f"[SEM MUDANÇAS] {relative_path}")

                    except Exception as e:
                        self.logger.error(f"[ERRO] {relative_path}: {e}")

            self.logger.info(f'Concluído! Processados: {processed}, Modificados: {modified}')
            self.root.after(0, lambda: messagebox.showinfo('Fim', f'Processamento concluído.\nModificados: {modified}'))

        except Exception as e:
            self.logger.error(f"Erro Fatal: {e}")
            self.root.after(0, lambda: messagebox.showerror('Erro Fatal', str(e)))
        finally:
            self.root.after(0, lambda: self.process_button.config(state='normal'))

if __name__ == '__main__':
    root = tk.Tk()
    app = CommentRemoverApp(root)
    root.mainloop()