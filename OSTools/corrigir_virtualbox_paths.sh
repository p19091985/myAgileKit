#!/bin/sh

set -eu

OLD_BASE="/media/patrik/5CECE2C8ECE29C10"
NEW_BASE="/run/media/patrik/5CECE2C8ECE29C10"
CONFIG_XML="$HOME/.config/VirtualBox/VirtualBox.xml"
APPLY=0
FORCE=0

usage() {
  cat <<EOF
Uso:
  sh OSTools/corrigir_virtualbox_paths.sh [opcoes]

Corrige caminhos do VirtualBox depois da migracao de montagem:
  antigo: $OLD_BASE
  novo:   $NEW_BASE

Por padrao roda em modo simulacao. Para alterar de verdade:
  sh OSTools/corrigir_virtualbox_paths.sh --apply

Opcoes:
  --apply             Faz as alteracoes e cria backups
  --force             Permite aplicar mesmo se processo do VirtualBox estiver aberto
  --old CAMINHO       Caminho antigo
  --new CAMINHO       Caminho novo
  --config CAMINHO    VirtualBox.xml a corrigir
  -h, --help          Mostra esta ajuda

Backups:
  Cada arquivo alterado recebe uma copia .bak-vbox-paths-AAAAMMDD-HHMMSS
EOF
}

log() {
  printf '%s\n' "$*"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --apply)
      APPLY=1
      ;;
    --force)
      FORCE=1
      ;;
    --old)
      shift
      if [ "$#" -eq 0 ]; then
        log "Erro: --old precisa de um caminho."
        exit 1
      fi
      OLD_BASE="$1"
      ;;
    --new)
      shift
      if [ "$#" -eq 0 ]; then
        log "Erro: --new precisa de um caminho."
        exit 1
      fi
      NEW_BASE="$1"
      ;;
    --config)
      shift
      if [ "$#" -eq 0 ]; then
        log "Erro: --config precisa de um caminho."
        exit 1
      fi
      CONFIG_XML="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log "Erro: opcao desconhecida: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

if ! command -v python3 >/dev/null 2>&1; then
  log "Erro: python3 nao encontrado."
  exit 1
fi

VM_ROOT="$NEW_BASE/VirtualBox VMs"

if [ ! -f "$CONFIG_XML" ]; then
  log "Erro: nao encontrei o arquivo de configuracao:"
  log "  $CONFIG_XML"
  exit 1
fi

if [ ! -d "$NEW_BASE" ]; then
  log "Erro: o novo ponto de montagem nao existe:"
  log "  $NEW_BASE"
  exit 1
fi

if [ "$APPLY" -eq 1 ] && [ "$FORCE" -eq 0 ]; then
  running="$(
    pgrep -a -f '[V]irtualBox|[V]BoxSVC|[V]BoxXPCOMIPCD|[V]BoxHeadless' 2>/dev/null || true
  )"
  if [ -n "$running" ]; then
    log "Erro: feche o VirtualBox antes de aplicar a correcao."
    log "Processos encontrados:"
    log "$running"
    log ""
    log "Depois rode novamente:"
    log "  sh OSTools/corrigir_virtualbox_paths.sh --apply"
    log ""
    log "Se tiver certeza absoluta, use --force."
    exit 1
  fi
fi

tmp_list="$(mktemp)"
cleanup() {
  rm -f "$tmp_list"
}
trap cleanup EXIT INT TERM

printf '%s\0' "$CONFIG_XML" >> "$tmp_list"

if [ -d "$VM_ROOT" ]; then
  find "$VM_ROOT" -type f \( -name '*.vbox' -o -name '*.vbox-prev' \) -print0 >> "$tmp_list"
else
  log "Aviso: nao encontrei a pasta de maquinas:"
  log "  $VM_ROOT"
fi

timestamp="$(date +%Y%m%d-%H%M%S)"

if [ "$APPLY" -eq 1 ]; then
  log "Aplicando correcao de caminho do VirtualBox..."
else
  log "Simulando correcao de caminho do VirtualBox..."
fi

python3 - "$OLD_BASE" "$NEW_BASE" "$APPLY" "$timestamp" "$tmp_list" <<'PY'
from pathlib import Path
import shutil
import sys

old, new, apply_flag, timestamp, list_path = sys.argv[1:6]
apply_changes = apply_flag == "1"
old_b = old.encode()
new_b = new.encode()

raw = Path(list_path).read_bytes()
paths = [Path(item.decode()) for item in raw.split(b"\0") if item]

changed = 0
for path in paths:
    if not path.is_file():
        continue
    data = path.read_bytes()
    count = data.count(old_b)
    if count == 0:
        continue

    changed += 1
    print(f"- {path}")
    print(f"  ocorrencias: {count}")

    if apply_changes:
        backup = path.with_name(path.name + f".bak-vbox-paths-{timestamp}")
        shutil.copy2(path, backup)
        path.write_bytes(data.replace(old_b, new_b))
        print(f"  backup: {backup}")

if changed == 0:
    print("Nenhum arquivo precisava de troca de caminho.")
elif not apply_changes:
    print("")
    print("Modo simulacao: nenhum arquivo foi alterado.")
PY

if [ "$APPLY" -eq 0 ]; then
  cat <<EOF

Para aplicar:
  sh OSTools/corrigir_virtualbox_paths.sh --apply

EOF
  exit 0
fi

log ""
log "Conferindo maquinas registradas no VirtualBox.xml..."

python3 - "$CONFIG_XML" <<'PY'
from pathlib import Path
import html
import re
import sys

config = Path(sys.argv[1])
text = config.read_text(errors="replace")
entries = re.findall(r'<MachineEntry\b[^>]*\bsrc="([^"]+)"', text)

if not entries:
    print("Nenhuma MachineEntry encontrada.")
    raise SystemExit(0)

missing = 0
for raw in entries:
    src = html.unescape(raw)
    status = "OK" if Path(src).is_file() else "FALTANDO"
    if status != "OK":
        missing += 1
    print(f"{status}: {src}")

raise SystemExit(1 if missing else 0)
PY

cat <<EOF

Pronto.

Agora abra o VirtualBox novamente. Se alguma VM ainda aparecer inacessivel,
verifique se o arquivo .vbox dela existe dentro de:
  $VM_ROOT

EOF
