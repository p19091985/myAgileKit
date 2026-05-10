# Troubleshooting

## Diagnostico rapido

```bash
./instalacao/instalar.sh --check
```

## Tkinter ausente

No Linux/Debian/Ubuntu, instale:

```bash
sudo apt-get install python3-tk
```

## FFmpeg ausente

No Linux/Debian/Ubuntu, instale:

```bash
sudo apt-get install ffmpeg
```

## Dependencias Python ausentes

```bash
.venv/bin/python -m pip install -r requirements.txt
```

## Logs

Logs devem ficar sempre em `logs/`, com subpastas para `install`, `tools`, `tests` e `errors`.

