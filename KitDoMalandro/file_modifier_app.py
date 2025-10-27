import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import sys
import re
import tokenize
import io
import datetime

class CommentRemoverApp:
    """
    Uma aplicação para remover todos os comentários de arquivos .py, .sql, .c, .cpp, etc.
    diretamente no local. A operação modifica os arquivos originais e gera
    um log detalhado.
    """

    def __init__(self, root):
        self.root = root

        self.root.title("Removedor de Comentários v3.4 (.py, .sql, C/C++, JS, CSS, HTML/Jinja2)")
        self.root.geometry("700x730")
        self.root.minsize(600, 650)

        self.script_directory = self.get_script_directory()

        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_widgets(main_frame)

    def get_script_directory(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))

    def create_widgets(self, parent):
        source_frame = ttk.LabelFrame(parent, text="1. Selecione o Diretório a ser Modificado", padding="10")
        source_frame.pack(fill=tk.X, expand=True, pady=5)

        self.source_dir_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_dir_var)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        browse_source_btn = ttk.Button(source_frame, text="Procurar...", command=self.browse_source_directory)
        browse_source_btn.pack(side=tk.LEFT)

        ext_frame = ttk.LabelFrame(parent, text="2. Tipos de Arquivo para Processar", padding="10")
        ext_frame.pack(fill=tk.X, expand=True, pady=5)

        self.extension_vars = {}

        target_extensions = ['.py', '.sql', '.c', '.h', '.cpp', '.hpp', '.js', '.css', '.html']
        num_columns = 5

        for i, ext in enumerate(target_extensions):
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(ext_frame, text=ext, variable=var)

            row = i // num_columns
            col = i % num_columns
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)

            self.extension_vars[ext] = var

        ignore_frame = ttk.LabelFrame(parent, text="3. Pastas a Ignorar (separadas por vírgula)", padding="10")
        ignore_frame.pack(fill=tk.X, expand=True, pady=5)

        self.ignore_dirs_var = tk.StringVar(
            value=".idea, .vscode, .vs, venv, .venv, env, node_modules, dist, build, target, out, .git, bin, obj")
        ignore_entry = ttk.Entry(ignore_frame, textvariable=self.ignore_dirs_var)
        ignore_entry.pack(fill=tk.X, expand=True)

        options_frame = ttk.LabelFrame(parent, text="4. Opções Adicionais", padding="10")
        options_frame.pack(fill=tk.X, expand=True, pady=5)

        self.reduce_line_breaks_var = tk.BooleanVar(value=False)
        cb_lines = ttk.Checkbutton(
            options_frame,
            text="Reduzir múltiplas linhas em branco (2+) para apenas uma",
            variable=self.reduce_line_breaks_var
        )
        cb_lines.pack(side=tk.LEFT, padx=5, pady=2)

        log_file_frame = ttk.LabelFrame(parent, text="5. Defina o Arquivo de Log", padding="10")
        log_file_frame.pack(fill=tk.X, expand=True, pady=5)

        self.log_file_var = tk.StringVar()
        log_entry = ttk.Entry(log_file_frame, textvariable=self.log_file_var)
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        browse_log_btn = ttk.Button(log_file_frame, text="Salvar Log Como...", command=self.browse_log_file)
        browse_log_btn.pack(side=tk.LEFT)

        self.process_button = ttk.Button(parent, text="Iniciar Remoção de Comentários",
                                         command=self.start_processing_thread)
        self.process_button.pack(pady=10, fill=tk.X, ipady=5)

        log_frame = ttk.LabelFrame(parent, text="Log de Progresso", padding="10")
        log_frame.pack(fill="both", expand=True, pady=5)
        toolbar_frame = ttk.Frame(log_frame)
        toolbar_frame.pack(fill='x', pady=(0, 5))
        self.copy_log_button = ttk.Button(toolbar_frame, text="Copiar Log", command=self.copy_log_to_clipboard)
        self.copy_log_button.pack(side="right")
        text_area_frame = ttk.Frame(log_frame)
        text_area_frame.pack(fill='both', expand=True)
        self.log_text = tk.Text(text_area_frame, height=10, state='disabled', wrap=tk.WORD, bg="#f0f0f0")
        log_scrollbar = ttk.Scrollbar(text_area_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def browse_source_directory(self):
        directory = filedialog.askdirectory(title="Selecione a pasta do seu projeto")
        if directory:
            self.source_dir_var.set(directory)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"remocao_comentarios_log_{timestamp}.log"
            self.log_file_var.set(os.path.join(self.script_directory, log_filename))

    def browse_log_file(self):
        filepath = filedialog.asksaveasfilename(
            title="Salvar arquivo de log como...",
            defaultextension=".log",
            initialdir=self.script_directory,
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filepath:
            self.log_file_var.set(filepath)

    def start_processing_thread(self):
        source_dir = self.source_dir_var.get()
        log_file = self.log_file_var.get()
        selected_extensions = [ext for ext, var in self.extension_vars.items() if var.get()]
        ignored_dirs_str = self.ignore_dirs_var.get()
        reduce_lines = self.reduce_line_breaks_var.get()

        if not source_dir or not log_file:
            messagebox.showerror("Erro de Validação",
                                 "O diretório a ser modificado e o arquivo de log devem ser definidos!")
            return
        if not selected_extensions:
            messagebox.showerror("Erro de Validação", "Selecione pelo menos um tipo de arquivo para processar!")
            return

        warning_message = (
            "ATENÇÃO!\n\n"
            "Você está prestes a MODIFICAR OS ARQUIVOS ORIGINAIS no diretório:\n\n"
            f"'{source_dir}'\n\n"
            "Esta ação é IRREVERSÍVEL e removerá TODOS os comentários dos arquivos selecionados.\n"
            "Se a opção de reduzir linhas estiver marcada, isso também será aplicado.\n\n"
            "Tem certeza que deseja continuar?"
        )
        if not messagebox.askyesno("Confirmar Modificação Destrutiva", warning_message, icon='warning'):
            return

        self.process_button.config(state='disabled')
        thread = threading.Thread(target=self.process_files,
                                  args=(source_dir, selected_extensions, log_file, ignored_dirs_str, reduce_lines))
        thread.daemon = True
        thread.start()

    def remove_python_comments(self, source_code):
        """Usa o tokenizador do Python para remover comentários de forma segura."""
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source_code).readline)
            non_comment_tokens = [tok for tok in tokens if tok.type != tokenize.COMMENT]
            return tokenize.untokenize(non_comment_tokens)
        except (tokenize.TokenError, IndentationError):
            return source_code

    def remove_sql_comments(self, sql_code):
        """Remove comentários de linha (--) e de bloco (/*...*/) de um código SQL."""
        code = re.sub(r'/\*.*?\*/', '', sql_code, flags=re.DOTALL)
        code = re.sub(r'--.*$', '', code, flags=re.MULTILINE)
        return "\n".join(line for line in code.splitlines() if line.strip())

    def remove_c_style_comments(self, c_code):
        """Remove comentários de linha C++ (//) e de bloco C (/*...*/) de um código."""
        code = re.sub(r'/\*.*?\*/', '', c_code, flags=re.DOTALL)
        code = re.sub(r'//.*$', '', c_code, flags=re.MULTILINE)
        return "\n".join(line for line in code.splitlines() if line.strip())

    def remove_html_comments(self, html_code):
        """Remove comentários de HTML e {#...#} de Jinja2."""
                                    
        code = re.sub(r'', '', html_code, flags=re.DOTALL)

        code = re.sub(r'\{#.*?#\}', '', code, flags=re.DOTALL)
        return "\n".join(line for line in code.splitlines() if line.strip())

    def process_files(self, source_dir, extensions, log_file, ignored_dirs_str, reduce_lines):
        self.update_log("Iniciando o processo de remoção de comentários...")
        if reduce_lines:
            self.update_log("Opção 'Reduzir múltiplas linhas em branco' ESTÁ ATIVA.")

        ignored_dirs_set = {'__pycache__'}
        if ignored_dirs_str:
            ignored_dirs_set.update({name.strip() for name in ignored_dirs_str.split(',') if name.strip()})
        self.update_log(f"Pastas ignoradas: {', '.join(sorted(list(ignored_dirs_set)))}")

        modified_count = 0
        processed_count = 0

        try:
            with open(log_file, 'w', encoding='utf-8') as log_f:
                log_f.write(f"Log de Remoção de Comentários - {datetime.datetime.now()}\n")
                log_f.write(f"Diretório Alvo: {source_dir}\n")
                log_f.write(f"Reduzir linhas em branco: {'Sim' if reduce_lines else 'Não'}\n")
                log_f.write("=" * 80 + "\n\n")

                for root, dirs, files in os.walk(source_dir):
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignored_dirs_set]

                    for filename in files:
                        if any(filename.lower().endswith(ext) for ext in extensions):
                            file_path = os.path.join(root, filename)
                            relative_path = os.path.relpath(file_path, source_dir)
                            processed_count += 1
                            self.update_log(f"Analisando: {relative_path}")

                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                                    original_content = infile.read()

                                cleaned_content = original_content

                                f_lower = filename.lower()

                                if f_lower.endswith('.py'):
                                    cleaned_content = self.remove_python_comments(original_content)
                                elif f_lower.endswith('.sql'):
                                    cleaned_content = self.remove_sql_comments(original_content)
                                elif f_lower.endswith(('.c', '.h', '.cpp', '.hpp', '.js', '.css')):
                                    cleaned_content = self.remove_c_style_comments(original_content)
                                elif f_lower.endswith('.html'):
                                                                              
                                    cleaned_content = self.remove_html_comments(original_content)

                                if reduce_lines:

                                    cleaned_content = re.sub(r'(\s*?\n){3,}', '\n\n', cleaned_content)

                                if original_content != cleaned_content:
                                    with open(file_path, 'w', encoding='utf-8') as outfile:
                                        outfile.write(cleaned_content)
                                    modified_count += 1
                                    log_message = f"[MODIFICADO] {relative_path}"
                                    self.update_log(log_message)
                                    log_f.write(log_message + "\n")
                                else:
                                    log_message = f"[IGNORADO (sem alterações)] {relative_path}"
                                    log_f.write(log_message + "\n")

                            except Exception as e:
                                error_log = f"!! ERRO ao processar {relative_path}: {e}"
                                self.update_log(error_log)
                                log_f.write(error_log + "\n")

                final_summary = (f"\nPROCESSO CONCLUÍDO!\n"
                                 f"{processed_count} arquivos analisados.\n"
                                 f"{modified_count} arquivos foram modificados.\n\n"
                                 f"Um log detalhado foi salvo em: {log_file}")
                self.update_log(final_summary)
                log_f.write("\n" + "=" * 80 + "\n")
                log_f.write(final_summary.strip())
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", final_summary.strip()))

        except Exception as e:
            error_message = f"!! ERRO GERAL: {e}"
            self.update_log(error_message)
            self.root.after(0, lambda: messagebox.showerror("Erro Fatal", f"Ocorreu um erro inesperado: {e}"))
        finally:
            self.root.after(0, lambda: self.process_button.config(state='normal'))

    def copy_log_to_clipboard(self):
        try:
            log_content = self.log_text.get("1.0", tk.END).strip()
            if not log_content: return
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            original_text = self.copy_log_button.cget("text")
            self.copy_log_button.config(text="Copiado!", state="disabled")
            self.root.after(2000, lambda: self.copy_log_button.config(text=original_text, state="normal"))
        except Exception as e:
            messagebox.showwarning("Erro ao Copiar", f"Não foi possível copiar o log: {e}")

    def update_log(self, message):
        self.root.after(0, self._update_log_thread_safe, message)

    def _update_log_thread_safe(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = CommentRemoverApp(root)
    root.mainloop()