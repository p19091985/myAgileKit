import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import os
SCRIPT_ALVO = 'limpar_citacoes.py'

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('Limpador de Citações v3.0 (com Modo Pasta)')
        self.geometry('700x600')
        self.minsize(600, 500)
        self.arquivo_entrada_path = tk.StringVar()
        self.arquivo_saida_path = tk.StringVar()
        self.in_place_var = tk.BooleanVar(value=True)
        self.modo_operacao_var = tk.StringVar(value='arquivo')
        self.create_widgets()
        self.setup_initial_state()

    def create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        modo_frame = ttk.LabelFrame(self, text='Modo de Operação', padding='10')
        modo_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 5))
        modo_frame.columnconfigure(1, weight=1)
        ttk.Radiobutton(modo_frame, text='Arquivo Único', variable=self.modo_operacao_var, value='arquivo', command=self.toggle_modo_operacao).grid(row=0, column=0, sticky='w')
        ttk.Radiobutton(modo_frame, text='Pasta (Recursivo)', variable=self.modo_operacao_var, value='pasta', command=self.toggle_modo_operacao).grid(row=0, column=1, sticky='w', padx=20)
        self.input_frame = ttk.LabelFrame(self, text='1. Selecione a Origem', padding='10')
        self.input_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(10, 5))
        self.input_frame.columnconfigure(0, weight=1)
        self.entrada_entry = ttk.Entry(self.input_frame, textvariable=self.arquivo_entrada_path, state='readonly', font=('Segoe UI', 9))
        self.entrada_entry.grid(row=0, column=0, sticky='ew')
        self.select_button = ttk.Button(self.input_frame, text='📁 Selecionar...', command=self.selecionar_origem)
        self.select_button.grid(row=0, column=1, padx=(10, 0))
        self.opcoes_frame = ttk.LabelFrame(self, text='2. Escolha a Opção de Saída (apenas Modo Arquivo)', padding='10')
        self.opcoes_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=5)
        self.opcoes_frame.columnconfigure(1, weight=1)
        self.in_place_check = ttk.Checkbutton(self.opcoes_frame, text='Modificar arquivo original (padrão)', variable=self.in_place_var, command=self.toggle_output_options)
        self.in_place_check.grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 5))
        self.saida_entry = ttk.Entry(self.opcoes_frame, textvariable=self.arquivo_saida_path, state='disabled', font=('Segoe UI', 9))
        self.saida_entry.grid(row=1, column=0, columnspan=2, sticky='ew')
        self.saida_button = ttk.Button(self.opcoes_frame, text='Salvar Como...', state='disabled', command=self.selecionar_arquivo_saida)
        self.saida_button.grid(row=1, column=2, padx=(10, 0))
        bottom_frame = ttk.Frame(self)
        bottom_frame.grid(row=3, column=0, sticky='nsew')
        bottom_frame.rowconfigure(0, weight=1)
        bottom_frame.columnconfigure(0, weight=1)
        log_frame = ttk.LabelFrame(bottom_frame, text='Monitor de Status (Log)', padding='10')
        log_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=5)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', height=10, font=('Consolas', 9))
        self.log_area.grid(row=0, column=0, sticky='nsew')
        action_frame = ttk.Frame(self, padding=(0, 5, 0, 5))
        action_frame.grid(row=4, column=0, sticky='ew', padx=10, pady=5)
        action_frame.columnconfigure(0, weight=1)
        self.run_button = ttk.Button(action_frame, text='▶ Executar Limpeza', command=self.run_script, style='Accent.TButton')
        self.run_button.grid(row=0, column=0, sticky='e')
        s = ttk.Style()
        s.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))

    def setup_initial_state(self):
        self.log('Bem-vindo ao Limpador de Citações!')
        self.log("Selecione o 'Modo de Operação' para começar.")
        self.toggle_modo_operacao()

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f'{message}\n')
        self.log_area.config(state='disabled')
        self.log_area.see(tk.END)

    def selecionar_origem(self):
        modo = self.modo_operacao_var.get()
        path = ''
        if modo == 'arquivo':
            path = filedialog.askopenfilename(title='Selecione o arquivo para limpar')
            if path:
                self.log(f'Arquivo selecionado: {os.path.basename(path)}')
        elif modo == 'pasta':
            path = filedialog.askdirectory(title='Selecione a pasta para limpar recursivamente')
            if path:
                self.log(f'Pasta selecionada: {path}')
        if path:
            self.arquivo_entrada_path.set(path)
            self.arquivo_saida_path.set('')

    def selecionar_arquivo_saida(self):
        path = filedialog.asksaveasfilename(title='Salvar arquivo limpo como...')
        if path:
            self.arquivo_saida_path.set(path)
            self.log(f'Arquivo de saída definido para: {os.path.basename(path)}')

    def toggle_output_options(self):
        is_inplace = self.in_place_var.get()
        new_state = 'disabled' if is_inplace else 'normal'
        self.saida_button.config(state=new_state)
        self.saida_entry.config(state='readonly' if not is_inplace else 'disabled')
        if is_inplace:
            self.arquivo_saida_path.set('')
            self.log('Modo de operação (Arquivo): Modificar arquivo original.')
        else:
            self.log('Modo de operação (Arquivo): Salvar em um novo arquivo.')

    def toggle_modo_operacao(self):
        modo = self.modo_operacao_var.get()
        self.arquivo_entrada_path.set('')
        if modo == 'arquivo':
            self.input_frame.config(text='1. Selecione o Arquivo')
            self.select_button.config(text='📁 Selecionar Arquivo...')
            self.in_place_check.config(state='normal')
            self.toggle_output_options()
            self.log('Modo de operação: Arquivo Único.')
        elif modo == 'pasta':
            self.input_frame.config(text='1. Selecione a Pasta')
            self.select_button.config(text='📁 Selecionar Pasta...')
            self.in_place_check.config(state='disabled')
            self.saida_entry.config(state='disabled')
            self.saida_button.config(state='disabled')
            self.log('Modo de operação: Pasta (Recursivo).')
            self.log("ATENÇÃO: A limpeza será feita 'in-place' (modificando os arquivos originais).")

    def run_script(self):
        entrada = self.arquivo_entrada_path.get()
        if not entrada:
            messagebox.showerror('Erro', 'Nenhuma origem (arquivo ou pasta) foi selecionada.')
            return
        modo = self.modo_operacao_var.get()
        comando = ['python', SCRIPT_ALVO]
        if modo == 'arquivo':
            if self.in_place_var.get():
                if not messagebox.askyesno('Confirmação de Segurança (Arquivo)', f'Você está prestes a MODIFICAR O ARQUIVO ORIGINAL.\n\nArquivo: {os.path.basename(entrada)}\n\nEsta ação não pode ser desfeita. Deseja continuar?', icon='warning'):
                    self.log('Operação cancelada pelo usuário.')
                    return
                comando.append('-i')
            else:
                saida = self.arquivo_saida_path.get()
                if not saida:
                    messagebox.showerror('Erro', "Nenhum arquivo de saída foi selecionado para o modo 'Salvar Como'.")
                    return
                comando.extend(['-o', saida])
            comando.append(entrada)
        elif modo == 'pasta':
            if not messagebox.askyesno('Confirmação de Segurança (PASTA)', f'Você está prestes a MODIFICAR RECURSIVAMENTE os arquivos na pasta:\n\n{entrada}\n\nEsta ação não pode ser desfeita e afetará TODOS os arquivos compatíveis (ex: .txt, .md) dentro dela.\n\nDeseja continuar?', icon='warning'):
                self.log('Operação cancelada pelo usuário.')
                return
            comando.extend(['--pasta', entrada])
        self.run_button.config(state='disabled')
        try:
            self.log('-' * 50)
            self.log(f"Executando no modo '{modo}'...")
            self.log(f'Comando: {' '.join(comando)}')
            resultado = subprocess.run(comando, capture_output=True, text=True, check=False, encoding='utf-8')
            if resultado.stdout:
                self.log(f'Resultado:\n{resultado.stdout.strip()}')
            if resultado.stderr:
                self.log(f'ERROS:\n{resultado.stderr.strip()}')
            if resultado.returncode == 0:
                messagebox.showinfo('Sucesso', 'A limpeza foi concluída!')
            else:
                messagebox.showerror('Erro no Script', 'Ocorreu um erro ao processar.')
        except FileNotFoundError:
            messagebox.showerror('Erro Crítico', f"O script '{SCRIPT_ALVO}' não foi encontrado.")
            self.log(f"ERRO: Verifique se '{SCRIPT_ALVO}' está na mesma pasta que este programa.")
        except Exception as e:
            messagebox.showerror('Erro Inesperado', f'Ocorreu um erro: {e}')
        finally:
            self.log('Operação finalizada.')
            self.log('-' * 50)
            self.run_button.config(state='normal')
if __name__ == '__main__':
    app = App()
    app.mainloop()