import re
import argparse
import os
import sys
import datetime
import shutil

def remover_citacoes(texto):
    padrao_original = '\\[\\s*cite\\s*\\\\?:\\s*.*?\\]'
    padrao_start = '\\[\\s*cite\\\\?_start\\s*\\]'
    padrao_end = '\\[\\s*cite\\\\?_end\\s*\\]'
    padrao_combinado = f'({padrao_original})|({padrao_start})|({padrao_end})'
    texto_limpo, num_remocoes = re.subn(padrao_combinado, '', texto, flags=re.IGNORECASE)
    return (texto_limpo, num_remocoes)

def log(msg, log_file=None):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted = f"{ts} | INFO | {msg}"
    print(formatted)
    if log_file:
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(formatted + '\n')
        except: pass

def criar_backup(caminho, log_file=None):
    try:
        bak = caminho + ".bak"
        shutil.copy2(caminho, bak)
        log(f"Backup criado: {os.path.basename(bak)}", log_file)
    except Exception as e:
        log(f"Falha ao criar backup de {caminho}: {e}", log_file)

def limpar_arquivo_inplace(caminho_arquivo, log_file=None):
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='replace') as f:
            conteudo_original = f.read()
    except Exception as e:
        log(f'ERRO ao ler {caminho_arquivo}: {e}', log_file)
        return 0
        
    conteudo_limpo, contagem = remover_citacoes(conteudo_original)
    
    if contagem > 0 and conteudo_original != conteudo_limpo:
        try:
            criar_backup(caminho_arquivo, log_file)
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo_limpo)
            log(f'Modificado: {caminho_arquivo} ({contagem} remoções)', log_file)
            return contagem
        except Exception as e:
            log(f'ERRO ao salvar {caminho_arquivo}: {e}', log_file)
            return 0
    return 0

def processar_pasta_recursivamente(pasta_path, log_file=None):
    extensoes_validas = ('.txt', '.md', '.py', '.html', '.xml', '.tex', '.c', '.h', '.sql', '.js', '.java', '.cs', '.cpp', '.hpp', '.ts', '.php', '.go', '.swift', '.rb')
    log(f'Iniciando varredura recursiva de: {pasta_path}', log_file)
    
    total_arquivos_modificados = 0
    total_remocoes_geral = 0
    
    for root, _, files in os.walk(pasta_path):
        for file in files:
            if file.lower().endswith(extensoes_validas):
                caminho_completo = os.path.join(root, file)
                remocoes_no_arquivo = limpar_arquivo_inplace(caminho_completo, log_file)
                if remocoes_no_arquivo > 0:
                    total_arquivos_modificados += 1
                    total_remocoes_geral += remocoes_no_arquivo
                    
    log('Varredura concluída.', log_file)
    log(f'Total de arquivos modificados: {total_arquivos_modificados}', log_file)
    log(f'Total de citações removidas: {total_remocoes_geral}', log_file)

def main():
    parser = argparse.ArgumentParser(description='Remove marcações de citação.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-p', '--pasta', help='Caminho para limpar recursivamente.')
    parser.add_argument('arquivo_entrada', nargs='?', help='Arquivo único.')
    parser.add_argument('-o', '--output', help='Arquivo de saída (sem backup).')
    parser.add_argument('-i', '--in-place', action='store_true', help='Modifica o original (Gera backup).')
    parser.add_argument('-l', '--log', help='Arquivo de log.')
    
    args = parser.parse_args()
    
    if args.pasta:
        processar_pasta_recursivamente(args.pasta, args.log)
    elif args.arquivo_entrada:
        if args.in_place:
            limpar_arquivo_inplace(args.arquivo_entrada, args.log)
        elif args.output:
            try:
                with open(args.arquivo_entrada, 'r', encoding='utf-8') as f: content = f.read()
                clean, cnt = remover_citacoes(content)
                with open(args.output, 'w', encoding='utf-8') as f: f.write(clean)
                log(f"Salvo em {args.output} ({cnt} remoções)", args.log)
            except Exception as e:
                log(f"Erro: {e}", args.log)
        else:
            base, ext = os.path.splitext(args.arquivo_entrada)
            out = f'{base}_limpo{ext}'
            try:
                with open(args.arquivo_entrada, 'r', encoding='utf-8') as f: content = f.read()
                clean, cnt = remover_citacoes(content)
                with open(out, 'w', encoding='utf-8') as f: f.write(clean)
                log(f"Salvo em {out} ({cnt} remoções)", args.log)
            except Exception as e:
                log(f"Erro: {e}", args.log)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()