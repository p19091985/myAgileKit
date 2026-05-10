# Arquitetura

O projeto agora tem um pacote principal `myagilekit/` para codigo compartilhado e entradas novas:

```text
myagilekit/
  core/
    paths.py
    registry.py
    logging.py
    process_runner.py
  manager/
    gui.py
```

Arquivos antigos na raiz continuam existindo como wrappers de compatibilidade:

- `myagilekit_gui.py` chama `myagilekit.manager.gui`.
- `tool_registry.py` reexporta `myagilekit.core.registry`.
- `project_paths.py` reexporta `myagilekit.core.paths`.

Isso permite migrar os mini sistemas gradualmente sem quebrar os comandos atuais.

Os scripts de editor ficam em `editor_tools/`. A pasta `visual studio code/` foi mantida apenas com wrappers pequenos para comandos antigos.

O catalogo de ferramentas fica em manifestos JSON dentro de `config/tools/`; o registry carrega e valida esses arquivos.
