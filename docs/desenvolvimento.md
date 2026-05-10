# Desenvolvimento

Comandos base:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python editor_tools/run_incremental_ruff.py
.venv/bin/python instalacao/instalador_tk.py --check
```

Metadados e configuracao do Ruff ficam em `pyproject.toml`. Dependencias Python continuam espelhadas em `requirements.txt` para o instalador e CI.

Antes de mexer em ferramentas destrutivas, prefira adicionar `--dry-run` e testes que validem caminhos seguros.
