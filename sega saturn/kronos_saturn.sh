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

GAME_DIR="${GAME_DIR:-$TARGET_HOME/Music/DeathTank2_fixed}"
GAME_CUE="${GAME_CUE:-$GAME_DIR/death2_fixed.cue}"
BIOS_SATURN_DIR="${BIOS_SATURN_DIR:-$SCRIPT_DIR/BIOS-SATURN}"
YMIR_BIOS_DIR="${YMIR_BIOS_DIR:-$TARGET_HOME/.local/share/StrikerX3/Ymir/roms/ipl}"
YMIR_BUP="$TARGET_HOME/.local/share/StrikerX3/Ymir/state/bup-int.bin"
MEDNAFEN_BKR="$TARGET_HOME/.mednafen/sav/262 Duke Nuke'm 3D (U).bkr"

APP_ID="org.libretro.RetroArch"
KRONOS_CORE_URL="${KRONOS_CORE_URL:-https://buildbot.libretro.com/nightly/linux/x86_64/latest/kronos_libretro.so.zip}"
INFO_ZIP_URL="${INFO_ZIP_URL:-https://buildbot.libretro.com/assets/frontend/info.zip}"

RA_BASE="$TARGET_HOME/.var/app/$APP_ID"
RA_CONFIG_HOME="$RA_BASE/config/retroarch"
RA_DATA_HOME="$RA_BASE/data/retroarch"
RA_CORES_DIR="$RA_CONFIG_HOME/cores"
RA_INFO_DIR="$RA_CONFIG_HOME/info"
RA_SYSTEM_DIR="$RA_CONFIG_HOME/system"
RA_SAVE_DIR="$RA_CONFIG_HOME/saves"
RA_STATE_DIR="$RA_CONFIG_HOME/states"
RA_CONFIG_DIR="$RA_CONFIG_HOME/config"
RA_APPEND_CONFIG="$RA_CONFIG_HOME/kronos-saturn.cfg"
RA_CORE_OPTIONS="$RA_CONFIG_HOME/kronos-core-options.cfg"

BIN_DIR="${KRONOS_BIN_DIR:-$TARGET_HOME/.local/bin}"
APPLICATIONS_BASE="${KRONOS_XDG_DATA_HOME:-${XDG_DATA_HOME:-$TARGET_HOME/.local/share}}"
APPLICATIONS_DIR="$APPLICATIONS_BASE/applications"
LAUNCHER="$BIN_DIR/deathtank2-kronos"
MENU_FILE="$APPLICATIONS_DIR/deathtank2-kronos.desktop"
COMPAT_LAUNCHER="$BIN_DIR/duke3d-saturn-kronos"
COMPAT_MENU_FILE="$APPLICATIONS_DIR/duke3d-saturn-kronos.desktop"
NO_INSTALL=0
NO_SHORTCUTS=0

log() {
  printf '%s\n' "$*"
}

usage() {
  cat <<EOF
Uso:
  sh kronos_saturn.sh [opcoes]

Instala e configura RetroArch + Kronos para testar Sega Saturn.

Opcoes:
  --game-dir CAMINHO   Pasta do Death Tank Zwei
                       Padrao: $GAME_DIR
  --cue CAMINHO        Arquivo CUE a abrir
                       Padrao: $GAME_CUE
  --bios-dir CAMINHO   Pasta local das BIOS de Saturn
                       Padrao: $BIOS_SATURN_DIR
  --no-install         Nao instala RetroArch, apenas configura arquivos
  --no-shortcuts       Nao cria launcher/atalhos
  -h, --help           Mostra esta ajuda

Depois de instalar, abra com:
  deathtank2-kronos
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --game-dir|--duke-dir)
      opt="$1"
      shift
      if [ "$#" -eq 0 ]; then
        log "Erro: $opt precisa de um caminho."
        exit 1
      fi
      GAME_DIR="$1"
      GAME_CUE="$GAME_DIR/death2_fixed.cue"
      ;;
    --cue)
      shift
      if [ "$#" -eq 0 ]; then
        log "Erro: --cue precisa de um caminho."
        exit 1
      fi
      GAME_CUE="$1"
      GAME_DIR="$(dirname "$GAME_CUE")"
      ;;
    --bios-dir)
      shift
      if [ "$#" -eq 0 ]; then
        log "Erro: --bios-dir precisa de um caminho."
        exit 1
      fi
      BIOS_SATURN_DIR="$1"
      ;;
    --no-install)
      NO_INSTALL=1
      ;;
    --no-shortcuts)
      NO_SHORTCUTS=1
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

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Erro: comando obrigatorio nao encontrado: $1"
    exit 1
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

get_desktop_dir() {
  if [ -n "${KRONOS_DESKTOP_DIR:-}" ]; then
    printf '%s\n' "$KRONOS_DESKTOP_DIR"
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

run_as_target() {
  if [ "$CURRENT_UID" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ] && command -v sudo >/dev/null 2>&1; then
    sudo -u "$TARGET_USER" env HOME="$TARGET_HOME" "$@"
  else
    env HOME="$TARGET_HOME" "$@"
  fi
}

install_flatpak_retroarch() {
  if [ "$NO_INSTALL" -eq 1 ]; then
    log "Pulando instalacao do RetroArch (--no-install)."
    return
  fi

  need_cmd flatpak

  if ! flatpak remotes --columns=name 2>/dev/null | grep -qx 'flathub'; then
    log "Adicionando Flathub para o usuario $TARGET_USER..."
    run_as_target flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
  fi

  if flatpak list --app --columns=application 2>/dev/null | grep -qx "$APP_ID"; then
    log "RetroArch Flatpak ja esta instalado."
    return
  fi

  log "Instalando RetroArch Flatpak pelo Flathub..."
  run_as_target flatpak install -y --user flathub "$APP_ID"
}

find_bios_by_sha256() {
  wanted="$1"

  for bios_dir in "$BIOS_SATURN_DIR" "$YMIR_BIOS_DIR"; do
    [ -d "$bios_dir" ] || continue
    for candidate in "$bios_dir"/*.bin "$bios_dir"/*.BIN; do
      [ -f "$candidate" ] || continue
      sum="$(sha256sum "$candidate" | awk '{print $1}')"
      if [ "$sum" = "$wanted" ]; then
        printf '%s\n' "$candidate"
        return 0
      fi
    done
  done

  return 1
}

prepare_retroarch_dirs() {
  mkdir -p "$RA_CORES_DIR" "$RA_INFO_DIR" "$RA_SYSTEM_DIR" "$RA_SAVE_DIR" "$RA_STATE_DIR" "$RA_CONFIG_DIR"
  mkdir -p "$RA_DATA_HOME"
  fix_owner "$RA_BASE"
}

download_kronos_core() {
  need_cmd curl
  need_cmd unzip

  tmp_zip="$(mktemp)"
  tmp_info="$(mktemp)"

  log "Baixando core Kronos do Libretro..."
  curl -fL --retry 3 -o "$tmp_zip" "$KRONOS_CORE_URL"
  unzip -p "$tmp_zip" kronos_libretro.so > "$RA_CORES_DIR/kronos_libretro.so"
  chmod +x "$RA_CORES_DIR/kronos_libretro.so"
  rm -f "$tmp_zip"

  log "Baixando informacao do core Kronos..."
  if curl -fL --retry 3 -o "$tmp_info" "$INFO_ZIP_URL"; then
    unzip -p "$tmp_info" kronos_libretro.info > "$RA_INFO_DIR/kronos_libretro.info" 2>/dev/null || true
  fi
  rm -f "$tmp_info"

  fix_owner "$RA_CORES_DIR" "$RA_INFO_DIR"
  log "Core Kronos instalado em:"
  log "  $RA_CORES_DIR/kronos_libretro.so"
}

copy_bios() {
  need_cmd sha256sum
  need_cmd awk

  mkdir -p "$BIOS_SATURN_DIR"
  log "Usando pasta de BIOS do Saturn:"
  log "  $BIOS_SATURN_DIR"

  na_bios="$(find_bios_by_sha256 96e106f740ab448cf89f0dd49dfbac7fe5391cb6bd6e14ad5e3061c13330266f || true)"

  if [ -z "$na_bios" ]; then
    log "Erro: nao achei BIOS US/EU compativel nos diretorios:"
    log "  $BIOS_SATURN_DIR"
    log "  $YMIR_BIOS_DIR"
    log "O Kronos espera saturn_bios.bin no diretorio system do RetroArch."
    exit 1
  fi

  mkdir -p "$RA_SYSTEM_DIR/kronos"
  cp "$na_bios" "$RA_SYSTEM_DIR/kronos/saturn_bios.bin"
  cp "$na_bios" "$RA_SYSTEM_DIR/saturn_bios.bin"
  chmod 644 "$RA_SYSTEM_DIR/kronos/saturn_bios.bin" "$RA_SYSTEM_DIR/saturn_bios.bin"
  fix_owner "$RA_SYSTEM_DIR/kronos/saturn_bios.bin" "$RA_SYSTEM_DIR/saturn_bios.bin"

  log "BIOS copiada para:"
  log "  $RA_SYSTEM_DIR/kronos/saturn_bios.bin"
}

verify_game_cue() {
  if [ ! -f "$GAME_CUE" ]; then
    found_cue="$(find "$GAME_DIR" -maxdepth 1 -type f -name '*.cue' | sort | head -1 || true)"
    if [ -n "$found_cue" ]; then
      GAME_CUE="$found_cue"
    fi
  fi

  if [ ! -f "$GAME_CUE" ]; then
    log "Erro: nao achei o CUE do Death Tank em:"
    log "  $GAME_CUE"
    exit 1
  fi

  log "CUE pronto para o Kronos:"
  log "  $GAME_CUE"
}

prepare_deathtank_save() {
  cue_base="$(basename "$GAME_CUE" .cue)"
  source_save=""

  if [ -f "$MEDNAFEN_BKR" ] && grep -a -q 'LOBOQUAKE__' "$MEDNAFEN_BKR"; then
    source_save="$MEDNAFEN_BKR"
  elif [ -f "$YMIR_BUP" ] && grep -a -q 'LOBOQUAKE__' "$YMIR_BUP"; then
    source_save="$YMIR_BUP"
  else
    log "Aviso: nao achei memoria com LOBOQUAKE__; Death Tank pode nao aparecer no Kronos."
    return 0
  fi

  mkdir -p "$RA_SAVE_DIR/Kronos" "$RA_SAVE_DIR/kronos/saturn" "$RA_SAVE_DIR/beetle_saturn"

  cp "$source_save" "$RA_SAVE_DIR/Kronos/$cue_base.bkr"
  cp "$source_save" "$RA_SAVE_DIR/kronos/saturn/$cue_base.bkr"
  cp "$source_save" "$RA_SAVE_DIR/$cue_base.bkr"
  cp "$source_save" "$RA_SAVE_DIR/beetle_saturn/$cue_base.bkr"

  fix_owner "$RA_SAVE_DIR"
  log "Save LOBOQUAKE__ copiado para o RetroArch/Kronos:"
  log "  $RA_SAVE_DIR/Kronos/$cue_base.bkr"
}

write_retroarch_config() {
  cat > "$RA_CORE_OPTIONS" <<EOF
kronos_addon_cartridge = "512K_backup_ram"
kronos_force_hle_bios = "disabled"
kronos_use_beetle_saves = "enabled"
kronos_multitap_port1 = "disabled"
kronos_multitap_port2 = "disabled"
EOF

  cat > "$RA_APPEND_CONFIG" <<EOF
libretro_directory = "$RA_CORES_DIR"
libretro_info_path = "$RA_INFO_DIR"
system_directory = "$RA_SYSTEM_DIR"
savefile_directory = "$RA_SAVE_DIR"
savestate_directory = "$RA_STATE_DIR"
core_options_path = "$RA_CORE_OPTIONS"
video_driver = "gl"
audio_driver = "pulse"
input_joypad_driver = "sdl2"
input_player1_joypad_index = "0"
input_player1_start = "enter"
input_player1_start_btn = "7"
input_player2_joypad_index = "1"
input_player2_start = "rshift"
input_player2_start_btn = "9"
EOF

  fix_owner "$RA_CORE_OPTIONS" "$RA_APPEND_CONFIG"
  log "Configuracao do RetroArch/Kronos criada:"
  log "  $RA_APPEND_CONFIG"
}

create_launcher() {
  if [ "$NO_SHORTCUTS" -eq 1 ]; then
    log "Pulando atalhos (--no-shortcuts)."
    return
  fi

  mkdir -p "$BIN_DIR" "$APPLICATIONS_DIR"

  cat > "$LAUNCHER" <<EOF
#!/bin/sh
exec flatpak run \\
  --filesystem="$GAME_DIR":ro \\
  --filesystem="$RA_CONFIG_HOME":rw \\
  "$APP_ID" \\
  --appendconfig "$RA_APPEND_CONFIG" \\
  -L "$RA_CORES_DIR/kronos_libretro.so" \\
  "$GAME_CUE"
EOF
  chmod +x "$LAUNCHER"

  cat > "$COMPAT_LAUNCHER" <<EOF
#!/bin/sh
exec "$LAUNCHER" "\$@"
EOF
  chmod +x "$COMPAT_LAUNCHER"

  cat > "$MENU_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Death Tank Zwei (Kronos)
Comment=Abre Death Tank Zwei no Kronos/RetroArch
Exec=$LAUNCHER
Icon=applications-games
Terminal=false
Categories=Game;Emulator;
Keywords=Sega;Saturn;Kronos;RetroArch;Death Tank;
StartupNotify=false
EOF
  chmod +x "$MENU_FILE"

  desktop_dir="$(get_desktop_dir)"
  desktop_file="$desktop_dir/Death Tank Zwei (Kronos).desktop"
  old_desktop_file="$desktop_dir/Duke Nukem 3D Saturn (Kronos).desktop"
  mkdir -p "$desktop_dir"
  cp "$MENU_FILE" "$desktop_file"
  chmod +x "$desktop_file"
  rm -f "$COMPAT_MENU_FILE" "$old_desktop_file"

  fix_owner "$LAUNCHER" "$COMPAT_LAUNCHER" "$MENU_FILE" "$desktop_file"

  if command -v gio >/dev/null 2>&1; then
    gio set "$desktop_file" metadata::trusted true >/dev/null 2>&1 || true
  fi

  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
  fi

  log "Launcher criado:"
  log "  $LAUNCHER"
  log "Atalho do menu criado:"
  log "  $MENU_FILE"
  log "Atalho da area de trabalho criado:"
  log "  $desktop_file"
}

install_flatpak_retroarch
prepare_retroarch_dirs
download_kronos_core
copy_bios
verify_game_cue
prepare_deathtank_save
write_retroarch_config
create_launcher

cat <<EOF

Pronto.

Para testar o Death Tank Zwei no Kronos:
  deathtank2-kronos

Se o RetroArch abrir em tela cheia e voce quiser sair:
  Esc ou F1 abre o menu
  Ctrl+Q geralmente fecha

Observacao:
  Este teste usa Kronos, que e outro emulador/core, diferente do Mednafen.
EOF
