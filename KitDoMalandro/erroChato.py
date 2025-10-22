import os
import re
import sys


def refatorar_codigo_streamlit(root_dir):
    """
    Percorre recursivamente um diretório e substitui os argumentos
    'use_container_width=True' por 'width="stretch"' e
    'use_container_width=False' por 'width="content"'.
    """

                                                     
                                                                         
    pattern_true = re.compile(r"use_container_width\s*=\s*True")
    replacement_true = "width='stretch'"

    pattern_false = re.compile(r"use_container_width\s*=\s*False")
    replacement_false = "width='content'"

    arquivos_modificados = 0
    arquivos_verificados = 0

    print(f"Iniciando varredura no diretório: {os.path.abspath(root_dir)}\n")

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
                                             
            if filename.endswith(".py"):
                arquivos_verificados += 1
                file_path = os.path.join(dirpath, filename)

                try:
                                              
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    modified_content = content

                                             
                    modified_content = pattern_true.sub(replacement_true, modified_content)
                    modified_content = pattern_false.sub(replacement_false, modified_content)

                                                                      
                    if modified_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                        print(f"[MODIFICADO] {file_path}")
                        arquivos_modificados += 1

                except Exception as e:
                    print(f"[ERRO] Não foi possível processar o arquivo {file_path}: {e}")

    print(f"\n--- Concluído ---")
    print(f"Arquivos .py verificados: {arquivos_verificados}")
    print(f"Arquivos .py modificados: {arquivos_modificados}")


if __name__ == "__main__":
                                                                  
                                                                                       
    start_directory = '.'

                                                                           
    if len(sys.argv) > 1:
        start_directory = sys.argv[1]

    if not os.path.isdir(start_directory):
        print(f"Erro: Diretório '{start_directory}' não encontrado.")
    else:
        refatorar_codigo_streamlit(start_directory)