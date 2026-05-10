# myAgileKit

Colecao de mini sistemas para produtividade, midia, editores e automacoes locais.

## GUI principal

Use o gerenciador raiz para visualizar status, dependencias e executar os mini sistemas:

```bash
./iniciar.sh
```

O catalogo usado pela GUI e carregado por `myagilekit/core/registry.py` a partir dos manifestos em `config/tools/`. O arquivo `tool_registry.py` continua como wrapper para manter os comandos antigos funcionando.

## Instalacao

O instalador fica em `instalacao/` e pode rodar com GUI Tkinter, CLI ou diagnostico:

```bash
./instalacao/instalar.sh
```

Modos disponiveis:

```bash
./instalacao/instalar.sh --gui
./instalacao/instalar.sh --cli
./instalacao/instalar.sh --check
```

Sem argumentos, ele abre a GUI. Ele cria/atualiza o `.venv`, instala `requirements.txt` e roda os testes ao final. O `apt-get` fica desabilitado por padrao e so deve ser usado com `--install-system` para dependencias que nao cabem dentro da `.venv`, como `python3-tk` e `ffmpeg`.

Instalacao manual equivalente:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

## Ferramentas

| Mini sistema | Caminho | Funcao |
| --- | --- | --- |
| Instalador myAgileKit | `instalacao/instalar.sh` | GUI ttk para preparar ambiente, requirements e checks. |
| myAgileKit Manager | `myagilekit_gui.py` | GUI central para gerenciar todos os mini sistemas. |
| DevTools | `DevTools/main.py` | Launcher das ferramentas de limpeza, refatoracao e manipulacao de arquivos. |
| YouTube Multilang Downloader | `youtube_multilang_downloader/youtube_multilang.py` | Baixa videos com multiplas faixas de audio e legendas. |
| Conversor FFmpeg Pro | `audioExtract/conversor_ffmpeg_pro.py` | Converte videos para MP3 com alvo de tamanho em MB. |
| PS Controller Tester | `OSTools/vericar controle.py` | Diagnostico visual de controles via Pygame. |
| Corretor de caminhos VirtualBox | `OSTools/corrigir_virtualbox_paths.sh` | Corrige referencias antigas de montagem em configuracoes e arquivos `.vbox`. |
| Windows Update Menu | `OSTools/windows-update-menu.bat` / `.ps1` | Menus de manutencao do Windows Update. |
| VS Code Folder Style | `editor_tools/vscode_folder_style.sh` | Ajusta tema de icones e estilo + / - do Explorer em editores tipo VS Code. |
| Sega Saturn / Death Tank | `sega saturn/instalar deathTank.sh` | Instala/configura Ymir, Mednafen e Kronos, prepara Death Tank Zwei e cria atalhos locais. |

## Testes

Os testes foram centralizados em `tests/`.

```bash
# Testes unitarios e checks leves
.venv/bin/python -m unittest discover -s tests

# Pipeline local usada pela GUI e pelos scripts de editor
.venv/bin/python editor_tools/pipeline_runner.py

# Ruff incremental
.venv/bin/python editor_tools/run_incremental_ruff.py
```

O teste de integracao do YouTube continua separado para evitar rede/download durante a suite padrao:

```bash
.venv/bin/python tests/integration/youtube_subs_generation_check.py --no-download
```

## Setup

Dependencias de sistema comuns:

```bash
# Linux/Debian/Ubuntu
sudo apt-get install python3-tk ffmpeg
```

Observacoes:

- Primeiro resolva dependencias Python pela `.venv` usando `requirements.txt`.
- Use `apt-get` apenas quando faltar uma ferramenta de sistema que nao pode ser instalada corretamente dentro da `.venv`.
- `tkinter` normalmente vem do pacote do sistema (`python3-tk` no Linux), nao do `pip`.
- Dependencias Python ficam em `requirements.txt`: `yt-dlp`, `pygame` e `ruff`.
- O downloader do YouTube usa `yt-dlp` e se beneficia de Deno ou Node instalados para resolver desafios recentes do YouTube.
- O conversor de audio precisa de `ffmpeg` e `ffprobe` no `PATH`.
- O testador de controle precisa de `pygame`.
- Os menus de Windows Update sao executaveis apenas no Windows.
- Todos os logs gerados pelo projeto devem ficar em `logs/`.

## Logs

Arquivos de log antigos e novos ficam centralizados em `logs/`. O instalador grava em `logs/install/`; as pastas padrao sao `logs/install/`, `logs/tools/`, `logs/tests/` e `logs/errors/`.

## Configuracao

O arquivo base de configuracao fica em `config/myagilekit.toml`. Helpers compartilhados de paths e logs ficam em `myagilekit/core/paths.py`.

## Evolucao recomendada

- Concluir a migracao interna dos mini sistemas para `myagilekit/tools/`.
- Migrar os mini sistemas para `myagilekit/tools/` em blocos pequenos.
- Separar testes unitarios de integracao com marcadores claros para rede, GUI e sistema operacional.
- Padronizar UI visual entre launchers e reduzir dependencias especificas por ferramenta.
- Criar uma tela de diagnostico no manager com versoes, comandos ausentes e links diretos para correcao.

## Estrutura

```text
myagilekit/                       Pacote principal
config/myagilekit.toml            Configuracao base
instalacao/                      Instalador GUI/CLI e wrapper .sh
DevTools/                         Ferramentas de desenvolvimento
audioExtract/                     Conversor FFmpeg
youtube_multilang_downloader/     Downloader YouTube
OSTools/                          Utilitarios de sistema
editor_tools/                     Scripts auxiliares para editores
visual studio code/               Wrappers de compatibilidade para comandos antigos
sega saturn/                      Utilitarios de Sega Saturn e instalador do Death Tank
tests/                            Testes centralizados
logs/                             Logs centralizados por categoria
requirements.txt                  Dependencias Python
pyproject.toml                    Metadados, Ruff e comandos do projeto
iniciar.sh                        Atalho raiz para abrir o myAgileKit Manager
myagilekit_gui.py                 GUI principal
tool_registry.py                  Wrapper do catalogo compartilhado
project_paths.py                  Wrapper dos caminhos compartilhados
```

## Licenca

MIT
