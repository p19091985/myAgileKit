import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import gui_utils

class LimparCitacoesApp(tk.Tk):

    def __init__(self):
        super().__init__()
        gui_utils.setup_window(self, 'DevTools - Interface Limpador')
        
        self.script_alvo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'limpar_citacoes.py')
        self.log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"Limpador_Log_{datetime.datetime.now().strftime('%Y%m%d')}.log")

        self.create_widgets()

    def create_widgets(self):
        gui_utils.create_header(self, "Interface Limpador", "Remove citações [cite] (Cria backups .bak automaticamente)")

        main_pad = ttk.Frame(self, padding=20)
        main_pad.pack(fill=tk.BOTH, expand=True)

        nb = ttk.Notebook(main_pad)
        nb.pack(fill=tk.BOTH, expand=True)

        frame_arquivo = ttk.Frame(nb, padding=20)
        nb.add(frame_arquivo, text=' Modo Arquivo ')
        self.montar_aba_arquivo(frame_arquivo)

        frame_pasta = ttk.Frame(nb, padding=20)
        nb.add(frame_pasta, text=' Modo Diretório ')
        self.montar_aba_pasta(frame_pasta)
        
        log_frame = ttk.LabelFrame(main_pad, text="Log de Execução", padding=10)
        log_frame.pack(fill='both', expand=True, pady=10)
        self.log_text = tk.Text(log_frame, height=8, font=gui_utils.FONT_CODE)
        self.log_text.pack(fill='both', expand=True)

        gui_utils.create_footer(self, "DevTools - Interface Limpador")

    def montar_aba_arquivo(self, parent):
        ttk.Label(parent, text='Selecione o arquivo para limpar:', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.input_file_var = tk.StringVar()
        frame_input = ttk.Frame(parent)
        frame_input.pack(fill=tk.X, pady=5)
        ttk.Entry(frame_input, textvariable=self.input_file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(frame_input, text='Procurar...', command=self.browse_file).pack(side=tk.LEFT)

        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=20)
        
        self.mode_var = tk.StringVar(value='output')
        ttk.Radiobutton(parent, text='Salvar em novo arquivo (padrão)', variable=self.mode_var, value='output', command=self.toggle_output_entry).pack(anchor='w', pady=2)
        
        self.output_file_var = tk.StringVar()
        self.entry_output = ttk.Entry(parent, textvariable=self.output_file_var)
        self.entry_output.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        ttk.Radiobutton(parent, text='Modificar arquivo original (Gera Backup)', variable=self.mode_var, value='inplace', command=self.toggle_output_entry).pack(anchor='w', pady=2)

        ttk.Button(parent, text='Iniciar Limpeza', command=self.run_file_mode, style='Primary.TButton').pack(pady=20, fill=tk.X)

    def montar_aba_pasta(self, parent):
        ttk.Label(parent, text='Selecione a pasta para limpar recursivamente:', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        self.input_folder_var = tk.StringVar()
        frame_input = ttk.Frame(parent)
        frame_input.pack(fill=tk.X, pady=5)
        ttk.Entry(frame_input, textvariable=self.input_folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(frame_input, text='Procurar...', command=self.browse_folder).pack(side=tk.LEFT)

        ttk.Label(parent, text='Atenção: Modifica arquivos originais! Backups serão criados.', foreground='red').pack(pady=20)
        
        ttk.Button(parent, text='Iniciar Limpeza', command=self.run_folder_mode, style='Primary.TButton').pack(pady=10, fill=tk.X)

    def toggle_output_entry(self):
        if self.mode_var.get() == 'output':
            self.entry_output.config(state='normal')
        else:
            self.entry_output.config(state='disabled')

    def browse_file(self):
        f = filedialog.askopenfilename()
        if f: self.input_file_var.set(f)

    def browse_folder(self):
        f = filedialog.askdirectory()
        if f: self.input_folder_var.set(f)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def run_file_mode(self):
        inp = self.input_file_var.get()
        if not inp: return messagebox.showwarning("Aviso", "Selecione um arquivo.")
        
        cmd = [sys.executable, self.script_alvo, inp, '--log', self.log_file]
        
        if self.mode_var.get() == 'inplace':
            if not messagebox.askyesno("Confirmar", "Modificar original? Backup será criado."): return
            cmd.append('--in-place')
        else:
            out = self.output_file_var.get()
            if out:
                cmd.extend(['--output', out])
        
        self.exec_command(cmd)

    def run_folder_mode(self):
        folder = self.input_folder_var.get()
        if not folder: return messagebox.showwarning("Aviso", "Selecione uma pasta.")
        if not messagebox.askyesno("Confirmar", "Modificar TODOS os arquivos? Backups serão criados."): return
        
        cmd = [sys.executable, self.script_alvo, '--pasta', folder, '--log', self.log_file]
        self.exec_command(cmd)

    def exec_command(self, cmd):
        self.log(f"Executando: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.log(result.stdout)
            if result.stderr: self.log(f"ERROS:\n{result.stderr}")
            messagebox.showinfo("Sucesso", "Processamento concluído. Verifique o log.")
        except Exception as e:
            self.log(f"Erro Crítico: {e}")
            messagebox.showerror("Erro Crítico", str(e))

if __name__ == '__main__':
    app = LimparCitacoesApp()
    app.mainloop()