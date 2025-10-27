import re
import argparse
import os
import sys

def remover_citacoes(texto):
    """
    Remove marcações de citação e retorna o texto limpo e a contagem de remoções.
    (Atualizado para incluir [cite_end] e tags escapadas com \ em Markdown)
    """

    padrao_original = r'\[\s*cite\s*\\?:\s*.*?\]'

    padrao_start = r'\[\s*cite\\?_start\s*\]'
    padrao_end = r'\[\s*cite\\?_end\s*\]'

    padrao_combinado = f"({padrao_original})|({padrao_start})|({padrao_end})"

    texto_limpo, num_remocoes = re.subn(padrao_combinado, '', texto, flags=re.IGNORECASE)

    return texto_limpo, num_remocoes

def limpar_arquivo_inplace(caminho_arquivo):
    """
    Função auxiliar para o modo pasta. Lê, limpa e salva um arquivo in-place.
    Retorna o número de remoções feitas.
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='replace') as f:
            conteudo_original = f.read()
    except Exception as e:
                                                     
        print(f"ERRO ao ler {caminho_arquivo}: {e}", file=sys.stderr)
        return 0

    conteudo_limpo, contagem = remover_citacoes(conteudo_original)

    if contagem > 0 and conteudo_original != conteudo_limpo:
        try:
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo_limpo)
                                                     
            print(f"Modificado: {caminho_arquivo} ({contagem} remoções)")
            return contagem
        except Exception as e:
            print(f"ERRO ao salvar {caminho_arquivo}: {e}", file=sys.stderr)
            return 0

    return 0

def processar_pasta_recursivamente(pasta_path):
    """
    Varre uma pasta recursivamente e limpa os arquivos de texto válidos.
    """

    extensoes_validas = (
                   
        '.txt', '.md', '.py', '.html', '.xml', '.tex',

        '.c', '.h', '.sql',

        '.js',
        '.java',
        '.cs',
        '.cpp', '.hpp',       
        '.ts',              
        '.php',
        '.go',
        '.swift',
        '.rb'        
    )

    print(f"Iniciando varredura recursiva de: {pasta_path}")
    print(f"Processando arquivos: {extensoes_validas}")
    print("-" * 50)

    total_arquivos_modificados = 0
    total_remocoes_geral = 0

    for root, _, files in os.walk(pasta_path):
        for file in files:
            if file.lower().endswith(extensoes_validas):
                caminho_completo = os.path.join(root, file)
                remocoes_no_arquivo = limpar_arquivo_inplace(caminho_completo)

                if remocoes_no_arquivo > 0:
                    total_arquivos_modificados += 1
                    total_remocoes_geral += remocoes_no_arquivo

    print("-" * 50)
    print("Varredura concluída.")
    print(f"Total de arquivos modificados: {total_arquivos_modificados}")
    print(f"Total de citações removidas: {total_remocoes_geral}")

def processar_arquivo_unico(args):
    """
    Toda a lógica original do seu script para processar um único arquivo.
    """
    if args.in_place and args.output:
        print("Erro: Não é possível usar as opções '--in-place' e '--output' ao mesmo tempo.")
        sys.exit(1)

    try:
        with open(args.arquivo_entrada, 'r', encoding='utf-8', errors='replace') as f:
            conteudo_original = f.read()
        print(f"Arquivo '{os.path.basename(args.arquivo_entrada)}' lido com sucesso.")
    except FileNotFoundError:
        print(f"ERRO: O arquivo '{args.arquivo_entrada}' não foi encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"ERRO: Ocorreu um erro ao ler o arquivo: {e}")
        sys.exit(1)

    conteudo_limpo, contagem = remover_citacoes(conteudo_original)

    if contagem > 0:
        print(f"Sucesso: Foram encontradas e removidas {contagem} marcações de citação.")
    else:
        print("Aviso: Nenhuma marcação de citação foi encontrada no arquivo.")

    if conteudo_original == conteudo_limpo:
        print("Nenhuma modificação foi necessária.")
        sys.exit(0)

    caminho_saida = ""
    if args.in_place:
        caminho_saida = args.arquivo_entrada
    elif args.output:
        caminho_saida = args.output
    else:
        base, ext = os.path.splitext(args.arquivo_entrada)
        caminho_saida = f"{base}_limpo{ext}"

    try:
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(conteudo_limpo)
        print(f"Arquivo limpo salvo com sucesso em: '{os.path.basename(caminho_saida)}'")
    except Exception as e:
        print(f"ERRO: Ocorreu um erro ao salvar o arquivo: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Remove marcações de citação de arquivos de texto ou pastas.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "-p", "--pasta",
        help="Opcional: O caminho para a PASTA a ser limpa recursivamente."
    )

    parser.add_argument(
        "arquivo_entrada",
        nargs='?',                           
        help="O caminho para o ARQUIVO que será limpo (usado se --pasta não for especificado)."
    )
    parser.add_argument("-o", "--output", help="Opcional: O caminho para salvar o arquivo limpo.")
    parser.add_argument("-i", "--in-place", action="store_true", help="Opcional: Modifica o arquivo original.")

    args = parser.parse_args()

    if args.pasta:
                    
        if args.arquivo_entrada or args.output or args.in_place:
            print("Erro: Ao usar '--pasta', não forneça 'arquivo_entrada', '--output' ou '--in-place'.")
            print("O modo pasta SEMPRE modifica os arquivos originais (in-place).")
            sys.exit(1)

        processar_pasta_recursivamente(args.pasta)

    elif args.arquivo_entrada:
                                                        
        processar_arquivo_unico(args)

    else:
                                 
        print("Erro: Você deve fornecer um 'arquivo_entrada' ou a opção '--pasta'.")
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()