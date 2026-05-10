# Ferramentas

O catalogo compartilhado das ferramentas e carregado por `myagilekit/core/registry.py` a partir dos manifestos JSON em `config/tools/`.

Ferramentas registradas:

- Instalador myAgileKit: `instalacao/instalar.sh`
- Suite de testes: `editor_tools/pipeline_runner.py`
- DevTools Launcher: `DevTools/main.py`
- YouTube Multilang Downloader: `youtube_multilang_downloader/youtube_multilang.py`
- Conversor FFmpeg Pro: `audioExtract/conversor_ffmpeg_pro.py`
- PS Controller Tester: `OSTools/vericar controle.py`
- Corretor de caminhos VirtualBox: `OSTools/corrigir_virtualbox_paths.sh`
- VS Code Folder Style: `editor_tools/vscode_folder_style.sh`
- Sega Saturn / Death Tank: `sega saturn/instalar deathTank.sh`
- Windows Update Menu: `OSTools/windows-update-menu.bat` e `OSTools/windows-update-menu.ps1`

Para adicionar uma ferramenta, crie um novo manifesto JSON em `config/tools/` e use um prefixo numerico no nome do arquivo para definir a ordem na GUI.
