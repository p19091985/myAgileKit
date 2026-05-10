# Plano para tornar o myAgileKit estado da arte

## Objetivo

Transformar o myAgileKit de uma colecao de scripts em uma plataforma organizada de mini sistemas, com instalacao confiavel, GUI central, testes, lint, logs, documentacao e releases.

## Status em 2026-05-07

Implementado nesta rodada:

1. Criado `pyproject.toml` com metadados, dependencias, comandos e configuracao Ruff.
2. Criado pacote `myagilekit/` com `core/paths.py`, `core/registry.py`, `core/logging.py`, `core/process_runner.py` e `manager/gui.py`.
3. Mantidos wrappers de compatibilidade em `project_paths.py`, `tool_registry.py` e `myagilekit_gui.py`.
4. Criado `config/myagilekit.toml`.
5. Criadas subpastas `logs/install/`, `logs/tools/`, `logs/tests/` e `logs/errors/`.
6. Instalador atualizado com `--gui`, `--cli`, `--check`, `--install-system` e `--skip-tests`.
7. Logs do instalador direcionados para `logs/install/`.
8. Adicionados testes para paths, empacotamento, registry, modos do instalador e CI.
9. Adicionado workflow `.github/workflows/ci.yml` para Linux e checks compativeis com Windows.
10. Criados guias em `docs/`: instalacao, arquitetura, ferramentas, desenvolvimento e troubleshooting.
11. Renomeados os scripts reais de `visual studio code/` para `editor_tools/`, mantendo wrappers de compatibilidade.
12. Criados manifestos JSON em `config/tools/` e registry passou a carregar o catalogo desses arquivos.
13. GUI central ganhou filtro por categoria, diagnostico do ambiente, testes por ferramenta e historico em `logs/tools/`.

Validado localmente:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python editor_tools/run_incremental_ruff.py
.venv/bin/python "visual studio code/run_incremental_ruff.py"
./instalacao/instalar.sh --check
.venv/bin/python -m pip check
```

Ainda falta:

1. Separar fisicamente os testes em `unit/`, `gui/`, `system/` e `windows/`.
2. Migrar os mini sistemas para `myagilekit/tools/`.
3. Criar changelog e artefatos de release.
4. Avaliar PyInstaller para empacotar a GUI.

## Fase 1: Fundacao

1. Criar `pyproject.toml`.
2. Mover configuracoes do Ruff para `pyproject.toml`.
3. Definir metadados do projeto: nome, versao, autores e dependencias.
4. Padronizar comandos de desenvolvimento.
5. Remover caminhos problemáticos, principalmente pastas com espaco no nome.

Comandos esperados:

```bash
.venv/bin/python -m unittest discover -s tests
.venv/bin/python editor_tools/run_incremental_ruff.py
./instalacao/instalar.sh
./instalacao/instalar.sh --check
```

## Fase 2: Arquitetura

1. Criar um pacote principal `myagilekit/`.
2. Mover codigo compartilhado para `myagilekit/core/`.
3. Separar cada mini sistema em modulo proprio.
4. Evitar scripts soltos na raiz.
5. Criar manifestos por ferramenta para reduzir hardcode na GUI.

Estrutura alvo:

```text
myagilekit/
  core/
    registry.py
    paths.py
    logging.py
    process_runner.py
  manager/
    gui.py
  tools/
    devtools/
    youtube_downloader/
    ffmpeg_converter/
    controller_tester/
    editor_tools/
    windows_tools/
```

## Fase 3: Instalacao

1. Manter `./instalacao/instalar.sh` como entrada principal.
2. Adicionar modo CLI ao instalador.
3. Adicionar modo diagnostico/check.
4. Resolver dependencias Python sempre pela `.venv`.
5. Usar `apt-get` somente para ferramentas de sistema que nao cabem na `.venv`, como `python3-tk` e `ffmpeg`.
6. Gerar logs em `logs/install/`.

Modos desejados:

```bash
./instalacao/instalar.sh --gui
./instalacao/instalar.sh --cli
./instalacao/instalar.sh --check
```

## Fase 4: GUI central

1. Melhorar `myagilekit_gui.py` como painel principal.
2. Mostrar status de dependencias por ferramenta.
3. Adicionar execucao de testes por ferramenta.
4. Adicionar log em tempo real.
5. Adicionar tela de diagnostico do ambiente.
6. Adicionar filtros por categoria.
7. Mostrar aviso claro para ferramentas Windows em Linux.
8. Adicionar historico de execucoes.

## Fase 5: Logs e configuracao

1. Manter todos os logs em `logs/`.
2. Criar subpastas:

```text
logs/
  install/
  tools/
  tests/
  errors/
```

3. Criar pasta `config/`.
4. Criar `config/myagilekit.toml`.
5. Criar helpers unicos para paths de log e config.
6. Impedir logs na raiz com teste automatizado.

## Fase 6: Testes

1. Separar testes por tipo.
2. Manter testes rapidos como padrao.
3. Isolar testes com rede, GUI real e sistema operacional.
4. Mockar YouTube, FFmpeg e processos externos quando possivel.
5. Criar checks para arquivos orfaos e dependencias.

Estrutura alvo:

```text
tests/
  unit/
  integration/
  gui/
  system/
  windows/
```

## Fase 7: Qualidade e CI

1. Adicionar GitHub Actions.
2. Rodar testes em Linux.
3. Rodar testes compativeis em Windows.
4. Rodar Ruff.
5. Rodar `pip check`.
6. Validar `requirements.txt`.
7. Validar que logs ficam em `logs/`.
8. Bloquear merge quando testes ou Ruff falharem.

## Fase 8: Releases

1. Definir versionamento semantico.
2. Criar changelog.
3. Criar release `0.1.0`.
4. Gerar pacote `.tar.gz`.
5. Avaliar build com PyInstaller para GUI.
6. Documentar instalacao por release.

Exemplo:

```text
0.1.0 - primeira versao organizada
0.2.0 - pacote myagilekit/
1.0.0 - instalacao e GUI estaveis
```

## Fase 9: Documentacao

1. Manter README enxuto.
2. Criar guias separados em `docs/`.
3. Documentar instalacao.
4. Documentar arquitetura.
5. Documentar cada ferramenta.
6. Criar troubleshooting.

Estrutura sugerida:

```text
docs/
  README.md
  instalacao.md
  ferramentas.md
  desenvolvimento.md
  troubleshooting.md
  arquitetura.md
  plano_estado_da_arte.md
```

## Fase 10: Seguranca e manutencao

1. Nunca versionar `cookies.txt`.
2. Nunca versionar logs sensiveis.
3. Validar caminhos antes de modificar arquivos em massa.
4. Criar backups em pasta propria.
5. Adicionar modo `--dry-run` nas ferramentas destrutivas.
6. Revisar permissões antes de chamar comandos de sistema.
7. Manter `apt-get` restrito a dependencias de sistema indispensaveis.

## Proxima ordem recomendada

1. Separar testes por categoria (`unit`, `gui`, `system`, `windows`) mantendo wrappers para discovery antigo.
2. Migrar mini sistemas para `myagilekit/tools/` em blocos pequenos.
3. Criar `CHANGELOG.md`.
4. Preparar artefatos de release `0.1.0`.
5. Avaliar build com PyInstaller para a GUI.

## Definicao de pronto

O projeto estara no nivel desejado quando uma pessoa conseguir rodar:

```bash
git clone <repo>
cd myAgileKit
./instalacao/instalar.sh
.venv/bin/python myagilekit_gui.py
```

E o projeto conseguir:

1. Diagnosticar dependencias.
2. Instalar apenas o necessario.
3. Rodar testes.
4. Rodar Ruff.
5. Registrar logs no lugar certo.
6. Explicar claramente qualquer problema.
