import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import datetime
import threading
import sys
import logging

# Import shared GUI utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import gui_utils

class FileMergerApp:

    def __init__(self, root):
        self.root = root
        gui_utils.setup_window(self.root, 'DevTools - Fusor de Arquivos')
        self.script_directory = gui_utils.get_script_directory()
        self.logger = None
        self.create_widgets(self.root)

    def create_widgets(self, parent):
        gui_utils.create_header(parent, "Concatenador de Arquivos", "Combine múltiplos arquivos de código em um único documento")

        main_pad = ttk.Frame(parent, padding=10)
        main_pad.pack(fill=tk.BOTH, expand=True)
        
        # 1. Source
        source_frame = ttk.LabelFrame(main_pad, text='Diretório de Origem', padding='10')
        source_frame.pack(fill=tk.X, pady=5)
        
        self.source_dir_var = tk.StringVar()
        ttk.Entry(source_frame, textvariable=self.source_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(source_frame, text='Procurar...', command=self.browse_source_directory).pack(side=tk.LEFT)

        # 2. Extensions
        ext_frame = ttk.LabelFrame(main_pad, text='Tipos de Arquivo', padding='10')
        ext_frame.pack(fill=tk.X, pady=5)
        
        self.extension_vars = {}
        common_extensions = ['.py', '.txt', '.sql', '.md', '.json', '.ini', '.log', '.jinja', '.java', '.html', '.css', '.js', '.xml', '.yml']
        
        files_grid = ttk.Frame(ext_frame)
        files_grid.pack(fill='x')
        
        for i, ext in enumerate(common_extensions):
            var = tk.BooleanVar(value=ext == '.py')
            cb = ttk.Checkbutton(files_grid, text=ext, variable=var)
            cb.grid(row=i // 5, column=i % 5, sticky='w', padx=5, pady=2)
            self.extension_vars[ext] = var

        # 3. Ignore
        ignore_frame = ttk.LabelFrame(main_pad, text='Diretórios Ignorados', padding='10')
        ignore_frame.pack(fill=tk.X, pady=5)
        self.ignore_dirs_var = tk.StringVar(value='node_modules, dist, build, target, out, .venv, venv, .git, __pycache__')
        ttk.Entry(ignore_frame, textvariable=self.ignore_dirs_var).pack(fill=tk.X)

        # 4. Output
        output_frame = ttk.LabelFrame(main_pad, text='Arquivo de Saída', padding='10')
        output_frame.pack(fill=tk.X, pady=5)
        self.output_file_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text='Salvar Como...', command=self.browse_save_file).pack(side=tk.LEFT)

        # Run
        self.process_button = ttk.Button(main_pad, text='Iniciar Concatenação', command=self.start_processing_thread, style='Primary.TButton')
        self.process_button.pack(pady=10, fill=tk.X, ipady=5)

        # Log
        log_frame = ttk.LabelFrame(main_pad, text='Log de Execução', padding='10')
        log_frame.pack(fill='both', expand=True, pady=5)
        
        toolbar = ttk.Frame(log_frame)
        toolbar.pack(fill='x')
        self.copy_log_button = ttk.Button(toolbar, text='Copiar Log', command=self.copy_log_to_clipboard)
        self.copy_log_button.pack(side='right')

        self.log_text = tk.Text(log_frame, height=8, state='disabled', wrap=tk.WORD, bg='#f9f9f9', font=gui_utils.FONT_CODE)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def browse_source_directory(self):
        directory = filedialog.askdirectory(title='Selecione a pasta do seu projeto')
        if directory:
            self.source_dir_var.set(directory)
            project_name = os.path.basename(directory)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'{project_name}_concatenado_{timestamp}.txt'
            self.output_file_var.set(os.path.join(self.script_directory, output_filename))

    def browse_save_file(self):
        filepath = filedialog.asksaveasfilename(title='Salvar como...', defaultextension='.txt', initialdir=self.script_directory, filetypes=[('Text Files', '*.txt')])
        if filepath:
            self.output_file_var.set(filepath)

    def copy_log_to_clipboard(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.log_text.get('1.0', tk.END))
            messagebox.showinfo("Copiado", "Log copiado!")
        except: pass

    def start_processing_thread(self):
        source_dir = self.source_dir_var.get()
        output_file = self.output_file_var.get()
        exts = [ext for ext, var in self.extension_vars.items() if var.get()]
        ignored = self.ignore_dirs_var.get()

        if not source_dir or not output_file: return messagebox.showerror('Erro', 'Preencha todos os campos.')
        if not exts: return messagebox.showerror('Erro', 'Selecione extensões.')
        
        # Setup Logger (Output file + .log)
        log_file = output_file + ".log"
        self.logger = gui_utils.setup_logger("Merger", log_file, self.log_text)

        self.process_button.config(state='disabled')
        threading.Thread(target=self.process_files, args=(source_dir, exts, output_file, ignored), daemon=True).start()

    def process_files(self, source_dir, extensions, output_file, ignored_dirs_str):
        self.logger.info(f'Iniciando concatenação em: {source_dir}')
        ignored_set = {'__pycache__'}
        if ignored_dirs_str: ignored_set.update(x.strip() for x in ignored_dirs_str.split(',') if x.strip())
        
        try:
            count = 0
            with open(output_file, 'w', encoding='utf-8', errors='ignore') as outfile:
                for root, dirs, files in os.walk(source_dir):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignored_set]
                    for filename in files:
                        if any(filename.lower().endswith(e) for e in extensions):
                            path = os.path.join(root, filename)
                            rel = os.path.relpath(path, source_dir)
                            self.logger.info(f'Adicionando: {rel}')
                            outfile.write(f"\n{'='*80}\n### FILE: {rel}\n{'='*80}\n")
                            try:
                                with open(path, 'r', encoding='utf-8', errors='ignore') as infile:
                                    outfile.write(infile.read())
                            except Exception as e:
                                self.logger.error(f'Erro ao ler {rel}: {e}')
                                outfile.write(f"Error reading file: {e}")
                            count += 1
            
            self.logger.info('Concluído!')
            self.root.after(0, lambda: messagebox.showinfo('Sucesso', f'{count} arquivos concatenados.'))
        except Exception as e:
            self.logger.error(f"Erro Fatal: {e}")
            self.root.after(0, lambda: messagebox.showerror('Erro', str(e)))
        finally:
            self.root.after(0, lambda: self.process_button.config(state='normal'))

if __name__ == '__main__':
    root = tk.Tk()
    app = FileMergerApp(root)
    root.mainloop()