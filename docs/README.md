# Documentacao do myAgileKit

Esta pasta guarda os planos e guias de evolucao do projeto.

## Arquivos

- [Plano Estado da Arte](./plano_estado_da_arte.md): passos para organizar o myAgileKit como uma plataforma moderna de mini ferramentas.
- [Instalacao](./instalacao.md): modos do instalador e dependencias.
- [Arquitetura](./arquitetura.md): pacote `myagilekit/` e wrappers de compatibilidade.
- [Ferramentas](./ferramentas.md): catalogo atual dos mini sistemas.
- [Desenvolvimento](./desenvolvimento.md): comandos de teste, Ruff e diagnostico.
- [Troubleshooting](./troubleshooting.md): resolucao dos problemas mais comuns.

## Como usar

1. Leia o plano completo.
2. Escolha uma fase.
3. Quebre a fase em tarefas pequenas.
4. Rode testes e Ruff depois de cada bloco de mudanca.

Comandos base:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python editor_tools/run_incremental_ruff.py
./instalacao/instalar.sh --check
```
