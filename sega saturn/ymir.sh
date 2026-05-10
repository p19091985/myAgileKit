#!/bin/sh

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
CURRENT_UID="$(id -u)"
TARGET_USER="${USER:-$(id -un)}"
TARGET_HOME="$HOME"

if [ "$CURRENT_UID" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
  TARGET_USER="$SUDO_USER"
  if command -v getent >/dev/null 2>&1; then
    TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
  else
    TARGET_HOME="/home/$TARGET_USER"
  fi
fi

if [ -z "$TARGET_HOME" ]; then
  TARGET_HOME="/home/$TARGET_USER"
fi

TARGET_GROUP="$(id -gn "$TARGET_USER" 2>/dev/null || printf '%s' "$TARGET_USER")"

REPO="StrikerX3/Ymir"
STABLE_API_URL="https://api.github.com/repos/$REPO/releases/latest"
NIGHTLY_API_URL="https://api.github.com/repos/$REPO/releases/tags/latest-nightly"
INSTALL_DIR="${YMIR_INSTALL_DIR:-$TARGET_HOME/Apps/Ymir}"
BIN_DIR="${YMIR_BIN_DIR:-$TARGET_HOME/.local/bin}"
APPLICATIONS_BASE="${YMIR_XDG_DATA_HOME:-${XDG_DATA_HOME:-$TARGET_HOME/.local/share}}"
APPLICATIONS_DIR="$APPLICATIONS_BASE/applications"
BIOS_SATURN_DIR="${BIOS_SATURN_DIR:-$SCRIPT_DIR/BIOS-SATURN}"
YMIR_USER_DATA_DIR="${YMIR_USER_DATA_DIR:-$TARGET_HOME/.local/share/StrikerX3/Ymir}"
YMIR_USER_IPL_DIR="$YMIR_USER_DATA_DIR/roms/ipl"
VERSION_FILE="$INSTALL_DIR/.ymir-version"
BUILD_FILE="$INSTALL_DIR/.ymir-build"
CHANNEL_FILE="$INSTALL_DIR/.ymir-channel"
CHANNEL="${YMIR_CHANNEL:-nightly}"
DEBUG=0
FORCE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --nightly)
      CHANNEL="nightly"
      ;;
    --stable)
      CHANNEL="stable"
      ;;
    d|-d|--debug)
      DEBUG=1
      set -x
      ;;
    f|-f|--force)
      FORCE=1
      ;;
    --bios-dir)
      shift
      if [ "$#" -eq 0 ]; then
        printf 'Erro: --bios-dir precisa de um caminho.\n'
        exit 1
      fi
      BIOS_SATURN_DIR="$1"
      ;;
    -h|--help)
      cat <<EOF
Uso:
  sh ymir.sh [d] [--force] [--nightly|--stable]

Instala ou atualiza o emulador Ymir em:
  $INSTALL_DIR

Opcoes:
  --nightly        Usa a build nightly/dev mais recente (padrao)
  --stable         Usa somente a release estavel mais recente
  --bios-dir DIR   Pasta local das BIOS de Saturn
  d, -d, --debug   Mostra os comandos durante a execucao
  f, -f, --force   Reinstala mesmo se ja estiver na versao mais recente
  -h, --help       Mostra esta ajuda

Variaveis opcionais:
  YMIR_CHANNEL=nightly|stable
  YMIR_INSTALL_DIR=/caminho/de/instalacao
  YMIR_BIN_DIR=/caminho/para/atalho
  YMIR_DESKTOP_DIR=/caminho/da/area/de/trabalho
  BIOS_SATURN_DIR=/caminho/para/BIOS-SATURN
EOF
      exit 0
      ;;
    *)
      printf 'Erro: opcao desconhecida: %s\n' "$1"
      printf 'Use: sh ymir.sh --help\n'
      exit 1
      ;;
  esac
  shift
done

log() {
  printf '%s\n' "$*"
}

debug() {
  if [ "$DEBUG" -eq 1 ]; then
    printf '[debug] %s\n' "$*"
  fi
}

fix_owner() {
  if [ "$CURRENT_UID" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
    for item in "$@"; do
      [ -e "$item" ] || continue
      chown -R "$TARGET_USER:$TARGET_GROUP" "$item" 2>/dev/null || true
    done
  fi
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Erro: comando obrigatorio nao encontrado: $1"
    exit 1
  fi
}

cleanup() {
  if [ -n "${TMP_DIR:-}" ] && [ -d "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
}

trap cleanup EXIT INT TERM

need_cmd curl
need_cmd grep
need_cmd head
need_cmd sed
need_cmd tar
need_cmd uname
need_cmd mktemp
need_cmd chmod
need_cmd mkdir
need_cmd cp
need_cmd ln
need_cmd rm

case "$CHANNEL" in
  nightly)
    API_URL="$NIGHTLY_API_URL"
    CHANNEL_LABEL="nightly/dev"
    RELEASE_PAGE="https://github.com/$REPO/releases/tag/latest-nightly"
    ;;
  stable)
    API_URL="$STABLE_API_URL"
    CHANNEL_LABEL="estavel"
    RELEASE_PAGE="https://github.com/$REPO/releases/latest"
    ;;
  *)
    log "Erro: canal invalido: $CHANNEL"
    log "Use YMIR_CHANNEL=nightly, YMIR_CHANNEL=stable, --nightly ou --stable."
    exit 1
    ;;
esac

get_desktop_dir() {
  if [ -n "${YMIR_DESKTOP_DIR:-}" ]; then
    printf '%s\n' "$YMIR_DESKTOP_DIR"
    return
  fi

  if command -v xdg-user-dir >/dev/null 2>&1; then
    if [ "$CURRENT_UID" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
      su - "$TARGET_USER" -c 'xdg-user-dir DESKTOP' 2>/dev/null || printf '%s/Desktop\n' "$TARGET_HOME"
    else
      xdg-user-dir DESKTOP
    fi
    return
  fi

  printf '%s/Desktop\n' "$TARGET_HOME"
}

escape_desktop_value() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/`/\\`/g; s/\$/\\$/g; s/%/%%/g'
}

create_desktop_shortcuts() {
  DESKTOP_DIR="$(get_desktop_dir)"
  MENU_FILE="$APPLICATIONS_DIR/ymir.desktop"
  DESKTOP_FILE="$DESKTOP_DIR/Ymir.desktop"
  EXEC_PATH="$(escape_desktop_value "$INSTALL_DIR/ymir-sdl3")"
  WORK_PATH="$(escape_desktop_value "$INSTALL_DIR")"

  log "Criando atalho no menu iniciar: $MENU_FILE"
  mkdir -p "$APPLICATIONS_DIR"
  cat > "$MENU_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Ymir
Comment=Emulador de Sega Saturn
Exec="$EXEC_PATH"
Path=$WORK_PATH
Icon=applications-games
Terminal=false
Categories=Game;Emulator;
Keywords=Ymir;Sega;Saturn;Emulator;
StartupNotify=false
EOF
  chmod +x "$MENU_FILE"

  log "Criando atalho na area de trabalho: $DESKTOP_FILE"
  mkdir -p "$DESKTOP_DIR"
  cp "$MENU_FILE" "$DESKTOP_FILE"
  chmod +x "$DESKTOP_FILE"

  if command -v gio >/dev/null 2>&1; then
    gio set "$DESKTOP_FILE" metadata::trusted true >/dev/null 2>&1 || true
  fi

  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
  fi

  fix_owner "$MENU_FILE" "$DESKTOP_FILE"
}

create_bin_shortcut() {
  log "Criando atalho em: $BIN_DIR/ymir-sdl3"
  mkdir -p "$BIN_DIR"
  ln -sf "$INSTALL_DIR/ymir-sdl3" "$BIN_DIR/ymir-sdl3"
  fix_owner "$BIN_DIR/ymir-sdl3"
}

copy_bios_files() {
  mkdir -p "$BIOS_SATURN_DIR" "$INSTALL_DIR/roms/ipl" "$YMIR_USER_IPL_DIR"
  log "Usando pasta de BIOS do Saturn:"
  log "  $BIOS_SATURN_DIR"

  copied=0
  for bios in "$BIOS_SATURN_DIR"/*.bin "$BIOS_SATURN_DIR"/*.BIN; do
    [ -f "$bios" ] || continue
    cp "$bios" "$INSTALL_DIR/roms/ipl/"
    cp "$bios" "$YMIR_USER_IPL_DIR/"
    copied=1
  done

  if [ "$copied" -eq 1 ]; then
    chmod 644 "$INSTALL_DIR/roms/ipl"/*.bin "$INSTALL_DIR/roms/ipl"/*.BIN "$YMIR_USER_IPL_DIR"/*.bin "$YMIR_USER_IPL_DIR"/*.BIN 2>/dev/null || true
    fix_owner "$BIOS_SATURN_DIR" "$INSTALL_DIR/roms/ipl" "$YMIR_USER_IPL_DIR"
    log "BIOS copiadas para o Ymir:"
    log "  $INSTALL_DIR/roms/ipl"
    log "  $YMIR_USER_IPL_DIR"
  else
    fix_owner "$BIOS_SATURN_DIR" "$INSTALL_DIR/roms/ipl" "$YMIR_USER_IPL_DIR"
    log "Aviso: nenhuma BIOS .bin encontrada em:"
    log "  $BIOS_SATURN_DIR"
    log "Coloque suas BIOS de Saturn nessa pasta para o script copiar automaticamente."
  fi
}

normalize_version() {
  RAW_VERSION="$(
    printf '%s\n' "$1" \
      | grep -Eo 'v?[0-9]+(\.[0-9]+)+([-+][A-Za-z0-9]+([._+-][A-Za-z0-9]+)*)?' \
      | head -n 1 \
      || true
  )"

  if [ -z "$RAW_VERSION" ]; then
    return 0
  fi

  RAW_VERSION="$(printf '%s\n' "$RAW_VERSION" | sed 's/_/+/g')"

  case "$RAW_VERSION" in
    v*) printf '%s\n' "$RAW_VERSION" ;;
    *) printf 'v%s\n' "$RAW_VERSION" ;;
  esac
}

base_version() {
  normalize_version "$1" | grep -Eo '^v?[0-9]+(\.[0-9]+)+' | head -n 1 || true
}

version_from_asset_url() {
  ASSET_NAME="${1##*/}"
  ASSET_NAME="$(printf '%s\n' "$ASSET_NAME" | sed 's/\.tar\.xz$//; s/\.zip$//')"
  normalize_version "$ASSET_NAME"
}

detect_installed_version() {
  FILE_VERSION=""
  CHANGELOG_VERSION=""

  if [ -f "$VERSION_FILE" ]; then
    FILE_VERSION="$(normalize_version "$(sed -n '1p' "$VERSION_FILE")")"
  fi

  if [ -f "$INSTALL_DIR/CHANGELOG.md" ]; then
    CHANGELOG_LINE="$(grep -m 1 -E '^## Version ' "$INSTALL_DIR/CHANGELOG.md" || true)"
    CHANGELOG_VERSION="$(normalize_version "$CHANGELOG_LINE")"
  fi

  if [ -n "$FILE_VERSION" ]; then
    if [ -n "$CHANGELOG_VERSION" ] \
      && [ "$(base_version "$FILE_VERSION")" != "$(base_version "$CHANGELOG_VERSION")" ]; then
      printf '%s\n' "$CHANGELOG_VERSION"
      return 0
    fi

    printf '%s\n' "$FILE_VERSION"
    return 0
  fi

  if [ -n "$CHANGELOG_VERSION" ]; then
    printf '%s\n' "$CHANGELOG_VERSION"
    return 0
  fi

  if [ -x "$INSTALL_DIR/ymir-sdl3" ]; then
    TITLE_VERSION="$(
      timeout 3 "$INSTALL_DIR/ymir-sdl3" --help 2>&1 \
        | grep -Eom 1 'Ymir v?[0-9]+(\.[0-9]+)+([-+][A-Za-z0-9]+([._+-][A-Za-z0-9]+)*)?' \
        || true
    )"
    TITLE_VERSION="$(normalize_version "$TITLE_VERSION")"
    if [ -n "$TITLE_VERSION" ]; then
      printf '%s\n' "$TITLE_VERSION"
      return 0
    fi
  fi

  if [ -x "$INSTALL_DIR/ymir-sdl3" ] && command -v strings >/dev/null 2>&1; then
    BINARY_LINE="$(strings "$INSTALL_DIR/ymir-sdl3" | grep -Eom 1 'Ymir v?[0-9]+(\.[0-9]+)+([+.-][A-Za-z0-9]+)?' || true)"
    BINARY_VERSION="$(normalize_version "$BINARY_LINE")"
    if [ -n "$BINARY_VERSION" ]; then
      printf '%s\n' "$BINARY_VERSION"
      return 0
    fi
  fi

  return 0
}

detect_installed_build() {
  if [ -f "$BUILD_FILE" ]; then
    sed -n '1p' "$BUILD_FILE"
  fi
}

detect_installed_channel() {
  if [ -f "$CHANNEL_FILE" ]; then
    sed -n '1p' "$CHANNEL_FILE"
  fi
}

OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" != "Linux" ]; then
  log "Erro: este script instala a build Linux do Ymir."
  log "Sistema detectado: $OS"
  log "Para Windows ou macOS, baixe o ZIP em: https://github.com/$REPO/releases/latest"
  exit 1
fi

case "$ARCH" in
  x86_64|amd64)
    if grep -qi 'avx2' /proc/cpuinfo 2>/dev/null; then
      ASSET_PATTERN='ymir-linux-x86_64-AVX2-.*\.tar\.xz$'
      CPU_FLAVOR="x86_64 AVX2"
    else
      ASSET_PATTERN='ymir-linux-x86_64-SSE2-.*\.tar\.xz$'
      CPU_FLAVOR="x86_64 SSE2"
    fi
    ;;
  aarch64|arm64)
    ASSET_PATTERN='ymir-linux-AArch64-NEON-.*\.tar\.xz$'
    CPU_FLAVOR="AArch64 NEON"
    ;;
  *)
    log "Erro: arquitetura nao suportada por este script: $ARCH"
    log "Veja os pacotes disponiveis em: https://github.com/$REPO/releases/latest"
    exit 1
    ;;
esac

log "Baixando informacoes da release mais recente do Ymir ($CHANNEL_LABEL)..."
RELEASE_JSON="$(curl -fsSL "$API_URL")"
ASSET_URL="$(
  printf '%s\n' "$RELEASE_JSON" \
    | sed -n 's/.*"browser_download_url": *"\([^"]*\)".*/\1/p' \
    | grep "$ASSET_PATTERN" \
    | head -n 1
)"
VERSION="$(version_from_asset_url "$ASSET_URL")"

if [ -z "$VERSION" ]; then
  VERSION="$(printf '%s\n' "$RELEASE_JSON" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -n 1)"
  VERSION="$(normalize_version "$VERSION")"
fi

if [ -z "$VERSION" ] || [ -z "$ASSET_URL" ]; then
  log "Erro: nao consegui encontrar um pacote Linux compativel na release mais recente."
  log "Padrao procurado: $ASSET_PATTERN"
  log "Confira manualmente: $RELEASE_PAGE"
  exit 1
fi

debug "Versao: $VERSION"
debug "Canal: $CHANNEL"
debug "Build selecionada: $CPU_FLAVOR"
debug "URL: $ASSET_URL"

INSTALLED_VERSION="$(detect_installed_version)"
INSTALLED_BUILD="$(detect_installed_build)"
INSTALLED_CHANNEL="$(detect_installed_channel)"

if [ -x "$INSTALL_DIR/ymir-sdl3" ]; then
  if [ -n "$INSTALLED_VERSION" ]; then
    log "Versao instalada detectada: $INSTALLED_VERSION"
  else
    log "Versao instalada: desconhecida"
  fi

  if [ -n "$INSTALLED_BUILD" ]; then
    log "Build instalada: $INSTALLED_BUILD"
  fi

  if [ -n "$INSTALLED_CHANNEL" ]; then
    log "Canal instalado: $INSTALLED_CHANNEL"
  fi
else
  log "Ymir ainda nao esta instalado neste caminho."
fi
log "Canal verificado: $CHANNEL"
log "Versao mais recente disponivel nesse canal: $VERSION"
log "Build recomendada para este computador: $CPU_FLAVOR"

if [ "$FORCE" -eq 0 ] \
  && [ -x "$INSTALL_DIR/ymir-sdl3" ] \
  && [ "$INSTALLED_VERSION" = "$VERSION" ] \
  && { [ -z "$INSTALLED_BUILD" ] || [ "$INSTALLED_BUILD" = "$CPU_FLAVOR" ]; } \
  && { [ -z "$INSTALLED_CHANNEL" ] || [ "$INSTALLED_CHANNEL" = "$CHANNEL" ]; }; then
  log "Ymir ja esta atualizado. Nenhum download necessario."
  printf '%s\n' "$VERSION" > "$VERSION_FILE"
  if [ -z "$INSTALLED_BUILD" ]; then
    printf '%s\n' "$CPU_FLAVOR" > "$BUILD_FILE"
  fi
  if [ -z "$INSTALLED_CHANNEL" ]; then
    printf '%s\n' "$CHANNEL" > "$CHANNEL_FILE"
  fi
  mkdir -p "$INSTALL_DIR/roms/ipl" "$INSTALL_DIR/roms/cdb"
  copy_bios_files
  create_bin_shortcut
  create_desktop_shortcuts
  fix_owner "$INSTALL_DIR"

  cat <<EOF

Ymir ja estava na versao mais recente ($VERSION).

Canal:
  $CHANNEL

Executavel:
  $INSTALL_DIR/ymir-sdl3

Atalho:
  $BIN_DIR/ymir-sdl3

Menu iniciar:
  $APPLICATIONS_DIR/ymir.desktop

Area de trabalho:
  $(get_desktop_dir)/Ymir.desktop

EOF
  exit 0
fi

if [ "$FORCE" -eq 1 ]; then
  log "Reinstalacao forcada ativada."
elif [ -n "$INSTALLED_CHANNEL" ] && [ "$INSTALLED_CHANNEL" != "$CHANNEL" ]; then
  log "Canal solicitado diferente do instalado. Atualizacao sera aplicada."
elif [ -n "$INSTALLED_BUILD" ] && [ "$INSTALLED_BUILD" != "$CPU_FLAVOR" ]; then
  log "A build instalada nao e a recomendada para este computador. Atualizacao sera aplicada."
elif [ -x "$INSTALL_DIR/ymir-sdl3" ]; then
  log "Nova instalacao/atualizacao sera aplicada."
fi

TMP_DIR="$(mktemp -d)"
ARCHIVE="$TMP_DIR/ymir.tar.xz"
EXTRACT_DIR="$TMP_DIR/extract"

mkdir -p "$EXTRACT_DIR"

log "Baixando Ymir $VERSION ($CPU_FLAVOR, canal $CHANNEL)..."
curl -fL "$ASSET_URL" -o "$ARCHIVE"

log "Extraindo arquivos..."
tar -xf "$ARCHIVE" -C "$EXTRACT_DIR"

log "Instalando em: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
if [ -e "$INSTALL_DIR/ymir-sdl3" ]; then
  rm -f "$INSTALL_DIR/ymir-sdl3"
fi
cp -R "$EXTRACT_DIR/." "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/ymir-sdl3"
printf '%s\n' "$VERSION" > "$VERSION_FILE"
printf '%s\n' "$CPU_FLAVOR" > "$BUILD_FILE"
printf '%s\n' "$CHANNEL" > "$CHANNEL_FILE"

mkdir -p "$INSTALL_DIR/roms/ipl" "$INSTALL_DIR/roms/cdb"
copy_bios_files

create_bin_shortcut
create_desktop_shortcuts
fix_owner "$INSTALL_DIR"

cat <<EOF

Ymir instalado/atualizado com sucesso.

Versao instalada:
  $VERSION

Canal:
  $CHANNEL

Executavel:
  $INSTALL_DIR/ymir-sdl3

Atalho:
  $BIN_DIR/ymir-sdl3

Menu iniciar:
  $APPLICATIONS_DIR/ymir.desktop

Area de trabalho:
  $(get_desktop_dir)/Ymir.desktop

Para funcionar, coloque sua BIOS/IPL do Sega Saturn em:
  $BIOS_SATURN_DIR

Para abrir:
  $INSTALL_DIR/ymir-sdl3

Ou, se $BIN_DIR estiver no PATH:
  ymir-sdl3

EOF
