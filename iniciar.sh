#!/bin/sh

set -eu

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
STAMP_FILE="$VENV_DIR/.requirements-installed"
SETUP_ONLY=0
CHECK_ONLY=0
SKIP_SETUP=0

log() {
  printf '%s\n' "$*"
}

usage() {
  cat <<EOF
Uso:
  ./iniciar.sh [opcoes]

Verifica a .venv, instala requirements.txt quando necessario e abre o
myAgileKit Manager.

Opcoes:
  --setup-only   Prepara a .venv e sai sem abrir a GUI
  --check-only   Apenas verifica o estado atual e sai
  --skip-setup   Abre a GUI sem instalar/verificar dependencias
  -h, --help     Mostra esta ajuda
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --setup-only)
      SETUP_ONLY=1
      ;;
    --check-only)
      CHECK_ONLY=1
      ;;
    --skip-setup)
      SKIP_SETUP=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
  shift
done

cd "$PROJECT_DIR"

find_system_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi
  return 1
}

venv_python_ok() {
  [ -x "$VENV_PYTHON" ] && "$VENV_PYTHON" -c 'import sys; print(sys.version)' >/dev/null 2>&1
}

required_modules_ok() {
  "$VENV_PYTHON" - <<'PY'
from __future__ import annotations

import importlib.util
import sys

from myagilekit.core.registry import TOOL_CATALOG

required = sorted({module for tool in TOOL_CATALOG for module in tool.requires_modules})
missing = [module for module in required if importlib.util.find_spec(module) is None]

if missing:
    print("Modulos Python ausentes na .venv:")
    for module in missing:
        print(f"  - {module}")
    raise SystemExit(1)

print("Modulos Python da .venv: OK")
PY
}

commands_report() {
  "$VENV_PYTHON" - <<'PY'
from __future__ import annotations

import shutil

from myagilekit.core.registry import TOOL_CATALOG

required = sorted({command for tool in TOOL_CATALOG for command in tool.requires_commands})
missing = [command for command in required if shutil.which(command) is None]

if missing:
    print("Aviso: comandos de sistema ausentes no PATH:")
    for command in missing:
        print(f"  - {command}")
    print("Esses itens podem precisar de instalacao pelo gerenciador do sistema.")
else:
    print("Comandos de sistema declarados no catalogo: OK")
PY
}

pip_check_ok() {
  "$VENV_PYTHON" -m pip check >/dev/null 2>&1
}

install_requirements() {
  if [ ! -f "$REQUIREMENTS_FILE" ]; then
    log "Erro: requirements.txt nao encontrado em:"
    log "  $REQUIREMENTS_FILE"
    exit 1
  fi

  log "Atualizando pip na .venv..."
  "$VENV_PYTHON" -m ensurepip --upgrade >/dev/null 2>&1 || true
  "$VENV_PYTHON" -m pip install --upgrade pip

  log "Instalando dependencias do requirements.txt na .venv..."
  "$VENV_PYTHON" -m pip install -r "$REQUIREMENTS_FILE"
  date +%Y%m%d-%H%M%S > "$STAMP_FILE"
}

ensure_venv() {
  system_python="$(find_system_python)" || {
    log "Erro: python3/python nao encontrado no PATH."
    exit 1
  }

  if ! venv_python_ok; then
    if [ -e "$VENV_DIR" ]; then
      log ".venv existe, mas o Python dela nao esta funcionando. Recriando..."
      log "Python antigo pode ter mudado durante a migracao do Linux."
    else
      log "Criando .venv..."
    fi
    "$system_python" -m venv --clear "$VENV_DIR"
  fi
}

setup_environment() {
  ensure_venv

  needs_install=0
  if [ ! -f "$STAMP_FILE" ]; then
    needs_install=1
  elif [ "$REQUIREMENTS_FILE" -nt "$STAMP_FILE" ]; then
    needs_install=1
  elif ! required_modules_ok >/dev/null 2>&1; then
    needs_install=1
  elif ! pip_check_ok; then
    needs_install=1
  fi

  if [ "$needs_install" -eq 1 ]; then
    install_requirements
  else
    log ".venv ja esta atualizada."
  fi

  required_modules_ok
  commands_report
}

if [ "$SKIP_SETUP" -eq 0 ]; then
  if [ "$CHECK_ONLY" -eq 1 ]; then
    if venv_python_ok && required_modules_ok && pip_check_ok; then
      commands_report
      log "Ambiente pronto."
      exit 0
    fi
    log "Ambiente precisa de ajuste. Rode: ./iniciar.sh --setup-only"
    exit 1
  fi

  setup_environment
fi

if [ "$SETUP_ONLY" -eq 1 ]; then
  log "Setup concluido. GUI nao foi aberta por causa de --setup-only."
  exit 0
fi

exec "$VENV_PYTHON" "$PROJECT_DIR/myagilekit_gui.py" "$@"
