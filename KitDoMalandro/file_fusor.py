import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import datetime
import threading
import sys

class FileMergerApp:
    """
    Uma aplicação com interface gráfica para concatenar múltiplos arquivos de um
    diretório e seus subdiretórios em um único arquivo de texto, preservando
    metadados sobre a estrutura original dos arquivos.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Fusor de Arquivos para Análise de IA v2.4")
        self.root.geometry("700x680")
        self.root.minsize(600, 600)

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
        source_frame = ttk.LabelFrame(parent, text="1. Selecione o Diretório do Projeto", padding="10")
        source_frame.pack(fill=tk.X, expand=True, pady=5)

        self.source_dir_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_dir_var)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        browse_source_btn = ttk.Button(source_frame, text="Procurar...", command=self.browse_source_directory)
        browse_source_btn.pack(side=tk.LEFT)

        ext_frame = ttk.LabelFrame(parent, text="2. Selecione os Tipos de Arquivo", padding="10")
        ext_frame.pack(fill=tk.X, expand=True, pady=5)

        self.extension_vars = {}
        common_extensions = [
            '.py', '.txt',  '.sql','.md', '.json', '.ini', '.log', '.jinja',
            '.java', '.html', '.css', '.js', '.xml', '.yml'
        ]

        num_columns = 4
        for i, ext in enumerate(common_extensions):
            var = tk.BooleanVar(value=(ext == '.py'))
            cb = ttk.Checkbutton(ext_frame, text=ext, variable=var)
            row = i // num_columns
            col = i % num_columns
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.extension_vars[ext] = var

        ignore_frame = ttk.LabelFrame(parent, text="3. Pastas a Ignorar (separadas por vírgula)", padding="10")
        ignore_frame.pack(fill=tk.X, expand=True, pady=5)

        self.ignore_dirs_var = tk.StringVar(value="node_modules, dist, build, target, out, .venv, venv, .git")
        ignore_entry = ttk.Entry(ignore_frame, textvariable=self.ignore_dirs_var)
        ignore_entry.pack(fill=tk.X, expand=True)

        output_frame = ttk.LabelFrame(parent, text="4. Defina o Arquivo de Saída", padding="10")
        output_frame.pack(fill=tk.X, expand=True, pady=5)

        self.output_file_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_file_var)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        browse_output_btn = ttk.Button(output_frame, text="Salvar Como...", command=self.browse_save_file)
        browse_output_btn.pack(side=tk.LEFT)

        self.process_button = ttk.Button(parent, text="Iniciar Fusão de Arquivos", command=self.start_processing_thread)
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

    def copy_log_to_clipboard(self):
        """Copia o conteúdo do campo de log para a área de transferência."""
        try:
            log_content = self.log_text.get("1.0", tk.END).strip()
            if not log_content:
                return

            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)

            original_text = self.copy_log_button.cget("text")
            self.copy_log_button.config(text="Copiado!", state="disabled")
            self.root.after(2000, lambda: self.copy_log_button.config(text=original_text, state="normal"))
        except Exception as e:
            messagebox.showwarning("Erro ao Copiar", f"Não foi possível copiar o log: {e}")

    def browse_source_directory(self):
        directory = filedialog.askdirectory(title="Selecione a pasta do seu projeto")
        if directory:
            self.source_dir_var.set(directory)
            project_name = os.path.basename(directory)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{project_name}_concatenado_{timestamp}.txt"
            self.output_file_var.set(os.path.join(self.script_directory, output_filename))

    def browse_save_file(self):
        filepath = filedialog.asksaveasfilename(
            title="Salvar arquivo concatenado como...",
            defaultextension=".txt",
            initialdir=self.script_directory,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filepath:
            self.output_file_var.set(filepath)

    def update_log(self, message):
        """
        ATUALIZA A CAIXA DE TEXTO.
        Esta função SÓ PODE ser chamada pela thread principal (através de 'root.after').
        """
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def schedule_log_update(self, message):
        """
        Agenda a atualização do log na thread principal da GUI para
        garantir a segurança entre threads (thread-safety).
        Esta é a função que a thread de processamento deve chamar.
        """
        self.root.after(0, self.update_log, message)

    def start_processing_thread(self):
        source_dir = self.source_dir_var.get()
        output_file = self.output_file_var.get()
        selected_extensions = [ext for ext, var in self.extension_vars.items() if var.get()]
        ignored_dirs_str = self.ignore_dirs_var.get()

        if not source_dir or not output_file:
            messagebox.showerror("Erro", "O diretório do projeto e o arquivo de saída devem ser definidos!")
            return

        if not selected_extensions:
            messagebox.showerror("Erro", "Selecione pelo menos um tipo de arquivo para incluir!")
            return

        self.process_button.config(state='disabled')

        self.log_text.config(state='normal')
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state='disabled')

        thread = threading.Thread(target=self.process_files,
                                  args=(source_dir, selected_extensions, output_file, ignored_dirs_str))
        thread.daemon = True
        thread.start()

    def process_files(self, source_dir, extensions, output_file, ignored_dirs_str):
        """Processa os arquivos em uma thread separada."""

        self.schedule_log_update("Iniciando o processo...")
        self.schedule_log_update(f"Extensões a serem buscadas: {', '.join(extensions)}")

        ignored_dirs_set = {'__pycache__'}                    
        if ignored_dirs_str:
            user_ignored_dirs = {name.strip() for name in ignored_dirs_str.split(',') if name.strip()}
            ignored_dirs_set.update(user_ignored_dirs)

        self.schedule_log_update(f"Pastas que serão ignoradas: {', '.join(sorted(list(ignored_dirs_set)))}")

        try:
            file_count = 0
            with open(output_file, 'w', encoding='utf-8', errors='ignore') as outfile:
                self.schedule_log_update(f"Arquivo de saída criado em: {output_file}")

                for root, dirs, files in os.walk(source_dir):
                                                           
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignored_dirs_set]

                    for filename in files:
                        if any(filename.lower().endswith(ext) for ext in extensions):
                            file_path = os.path.join(root, filename)
                            relative_path = os.path.relpath(file_path, source_dir)

                            self.schedule_log_update(f"Processando: {relative_path}")

                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                                    content = infile.read()
                                    outfile.write("=" * 80 + "\n")
                                    outfile.write(f"### INÍCIO DO ARQUIVO: {relative_path.replace(os.sep, '/')}\n")
                                    outfile.write("=" * 80 + "\n\n")
                                    outfile.write(content)
                                    outfile.write("\n\n")
                                    outfile.write("=" * 80 + "\n")
                                    outfile.write(f"### FIM DO ARQUIVO: {relative_path.replace(os.sep, '/')}\n")
                                    outfile.write("=" * 80 + "\n\n\n")
                                    file_count += 1

                            except Exception as e:
                                                 
                                self.schedule_log_update(f"!! ERRO ao ler o arquivo {relative_path}: {e}")

            self.schedule_log_update(f"\nPROCESSO CONCLUÍDO!")
            self.schedule_log_update(f"Total de {file_count} arquivos foram concatenados.")

            self.root.after(0, lambda: messagebox.showinfo("Sucesso",
                                                           f"Processo concluído!\n{file_count} arquivos foram salvos em:\n{output_file}"))

        except Exception as e:
            self.schedule_log_update(f"!! ERRO GERAL: {e}")

            self.root.after(0, lambda: messagebox.showerror("Erro", f"Ocorreu um erro inesperado: {e}"))

        finally:
                                                                 
            self.root.after(0, lambda: self.process_button.config(state='normal'))

if __name__ == "__main__":
    root = tk.Tk()
    app = FileMergerApp(root)
    root.mainloop()