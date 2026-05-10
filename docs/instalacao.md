# Instalacao

Entrada principal:

```bash
./instalacao/instalar.sh
```

Modos disponiveis:

```bash
./instalacao/instalar.sh --gui
./instalacao/instalar.sh --cli
./instalacao/instalar.sh --check
```

O modo `--check` apenas diagnostica o ambiente. O modo `--cli` instala/atualiza pela linha de comando. O modo `--gui` abre a interface Tkinter e continua sendo o padrao quando nenhum modo e informado.

Por padrao, o instalador usa a `.venv`, instala `requirements.txt` e roda `unittest`. Use `--skip-tests` para pular os testes e `--install-system` para permitir `apt-get` apenas para dependencias de sistema indispensaveis, como `python3-tk` e `ffmpeg`.

Logs de instalacao ficam em `logs/install/`.

