#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PY_SCRIPT="${SCRIPT_DIR}/vscode_folder_style.py"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[vscode-folder-style] python3 nao encontrado. Instale o Python 3 ou defina PYTHON_BIN." >&2
  exit 1
fi

set +e
"${PYTHON_BIN}" "${PY_SCRIPT}" "$@"
status=$?
set -e

if [[ ${status} -eq 77 ]]; then
  echo
  echo "[vscode-folder-style] O ajuste + / - precisa alterar arquivos internos do VS Code."
  echo "[vscode-folder-style] Vou manter as configuracoes do usuario e tentar somente o patch com sudo."

  if command -v sudo >/dev/null 2>&1 && [[ -t 0 ]]; then
    read -r -p "[vscode-folder-style] Aplicar patch interno com sudo agora? [s/N] " answer
    case "${answer}" in
      s|S|sim|SIM|Sim)
        exec sudo env HOME="${HOME}" USER="${USER:-}" "${PYTHON_BIN}" "${PY_SCRIPT}" --only-patch-workbench "$@"
        ;;
    esac
  fi

  echo "[vscode-folder-style] Rode manualmente se quiser aplicar depois:"
  echo "  sudo env HOME=\"${HOME}\" USER=\"${USER:-}\" ${PYTHON_BIN} \"${PY_SCRIPT}\" --only-patch-workbench $*"
  exit 77
fi

exit "${status}"
