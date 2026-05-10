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
MEDNAFEN_HOME="${MEDNAFEN_HOME:-$TARGET_HOME/.mednafen}"
FIRMWARE_DIR="$MEDNAFEN_HOME/firmware"
SAV_DIR="$MEDNAFEN_HOME/sav"
BIN_DIR="${MEDNAFEN_BIN_DIR:-$TARGET_HOME/.local/bin}"
APPLICATIONS_BASE="${MEDNAFEN_XDG_DATA_HOME:-${XDG_DATA_HOME:-$TARGET_HOME/.local/share}}"
APPLICATIONS_DIR="$APPLICATIONS_BASE/applications"
LAUNCHER="$BIN_DIR/deathtank2-mednafen"
MENU_FILE="$APPLICATIONS_DIR/deathtank2-mednafen.desktop"
COMPAT_LAUNCHER="$BIN_DIR/duke3d-saturn-mednafen"
COMPAT_MENU_FILE="$APPLICATIONS_DIR/duke3d-saturn-mednafen.desktop"
NO_APT=0
NO_SHORTCUTS=0

log() {
  printf '%s\n' "$*"
}

usage() {
  cat <<EOF
Uso:
  sh mednafen_saturn.sh [opcoes]

Instala e configura o Mednafen para Sega Saturn.

Opcoes:
  --game-dir CAMINHO   Pasta do Death Tank Zwei
                       Padrao: $GAME_DIR
  --cue CAMINHO        Arquivo CUE a abrir
                       Padrao: $GAME_CUE
  --bios-dir CAMINHO   Pasta local das BIOS de Saturn
                       Padrao: $BIOS_SATURN_DIR
  --no-apt             Nao instala pacotes, apenas configura arquivos
  --no-shortcuts       Nao cria atalhos/launcher
  -h, --help           Mostra esta ajuda

Depois de instalar, abra com:
  deathtank2-mednafen
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
    --no-apt)
      NO_APT=1
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
  if [ -n "${MEDNAFEN_DESKTOP_DIR:-}" ]; then
    printf '%s\n' "$MEDNAFEN_DESKTOP_DIR"
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

install_packages() {
  if [ "$NO_APT" -eq 1 ]; then
    log "Pulando instalacao por apt (--no-apt)."
    return
  fi

  if command -v mednafen >/dev/null 2>&1 && command -v mdf2iso >/dev/null 2>&1; then
    log "Mednafen e mdf2iso ja estao instalados."
    return
  fi

  need_cmd apt-get

  if [ "$CURRENT_UID" -eq 0 ]; then
    log "Instalando Mednafen pelo apt."
    apt-get update
    apt-get install -y mednafen mednaffe mdf2iso || apt-get install -y mednafen mdf2iso
  else
    need_cmd sudo
    log "Instalando Mednafen pelo apt. Sua senha sudo pode ser solicitada."
    sudo apt-get update
    sudo apt-get install -y mednafen mednaffe mdf2iso || sudo apt-get install -y mednafen mdf2iso
  fi
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

copy_bios_files() {
  need_cmd sha256sum
  need_cmd awk

  mkdir -p "$BIOS_SATURN_DIR" "$FIRMWARE_DIR"
  log "Usando pasta de BIOS do Saturn:"
  log "  $BIOS_SATURN_DIR"

  na_bios="$(find_bios_by_sha256 96e106f740ab448cf89f0dd49dfbac7fe5391cb6bd6e14ad5e3061c13330266f || true)"
  jp_bios="$(find_bios_by_sha256 dcfef4b99605f872b6c3b6d05c045385cdea3d1b702906a0ed930df7bcb7deac || true)"

  if [ -z "$na_bios" ]; then
    log "Erro: nao achei BIOS US/EU compativel nos diretorios:"
    log "  $BIOS_SATURN_DIR"
    log "  $YMIR_BIOS_DIR"
    log "O Mednafen espera mpr-17933.bin."
    exit 1
  fi

  if [ -z "$jp_bios" ]; then
    log "Erro: nao achei BIOS japonesa compativel nos diretorios:"
    log "  $BIOS_SATURN_DIR"
    log "  $YMIR_BIOS_DIR"
    log "O Mednafen espera sega_101.bin."
    exit 1
  fi

  cp "$na_bios" "$FIRMWARE_DIR/mpr-17933.bin"
  cp "$jp_bios" "$FIRMWARE_DIR/sega_101.bin"
  chmod 644 "$FIRMWARE_DIR/mpr-17933.bin" "$FIRMWARE_DIR/sega_101.bin"
  fix_owner "$MEDNAFEN_HOME"

  log "BIOS US/EU copiada para: $FIRMWARE_DIR/mpr-17933.bin"
  log "BIOS JP copiada para:    $FIRMWARE_DIR/sega_101.bin"
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
    return 1
  fi

  log "CUE pronto para o Mednafen:"
  log "  $GAME_CUE"
  return 0
}

prepare_deathtank_bkr() {
  need_cmd python3

  cue_base="$(basename "$GAME_CUE" .cue)"
  bkr_file="$SAV_DIR/$cue_base.bkr"
  mkdir -p "$SAV_DIR"

  if [ -f "$bkr_file" ]; then
    backup="$bkr_file.bak-$(date +%Y%m%d-%H%M%S)"
    cp "$bkr_file" "$backup"
    log "Backup da memoria antiga do Mednafen:"
    log "  $backup"
  fi

  if [ -f "$YMIR_BUP" ] && grep -a -q 'LOBOQUAKE__' "$YMIR_BUP"; then
    cp "$YMIR_BUP" "$bkr_file"
    fix_owner "$SAV_DIR" "$bkr_file"
    log "Memoria interna copiada do Ymir para destravar Death Tank:"
    log "  $bkr_file"
    return 0
  fi

  single_save=""
  if [ -f "$GAME_DIR/LOBOQUAKE__.ymbup" ]; then
    single_save="$GAME_DIR/LOBOQUAKE__.ymbup"
  elif [ -f "$GAME_DIR/LOBOQUAKE__.BUP" ]; then
    single_save="$GAME_DIR/LOBOQUAKE__.BUP"
  else
    single_save="$MEDNAFEN_HOME/LOBOQUAKE__"
    log "Baixando save publico LOBOQUAKE__ para destravar Death Tank..."
    need_cmd curl
    if ! curl -fsSL -o "$single_save" "https://www.whipassgaming.com/Patches/LOBOQUAKE__"; then
      log "Aviso: nao consegui baixar/criar o save de desbloqueio."
      log "O jogo deve abrir, mas o save de desbloqueio pode nao estar disponivel."
      return 0
    fi
  fi

  python3 - "$bkr_file" "$single_save" <<'PY'
from pathlib import Path
import struct
import sys
import time

out_path = Path(sys.argv[1])
save_path = Path(sys.argv[2])
blob = save_path.read_bytes()

if blob[:4] == b"YmBP":
    size = struct.unpack_from("<I", blob, 0x1E)[0]
    raw = blob[0x22:0x22 + size]
elif blob[:4] == b"Vmem":
    size = struct.unpack_from(">I", blob, 0x2C)[0]
    raw = blob[0x40:0x40 + size]
else:
    raw = blob

filename = b"LOBOQUAKE__"
comment = b"save games"
language = 1
date_minutes = int((time.time() - 315532800) // 60)
block_size = 64
total_size = 32768
mem = bytearray(total_size)
header = b"BackUpRam Format"

for i in range(block_size):
    mem[i] = header[i % len(header)]

used = [False] * (total_size // block_size)
used[0] = used[1] = True

def alloc_block():
    for i in range(2, len(used)):
        if not used[i]:
            used[i] = True
            return i
    raise SystemExit("Sem espaco na memoria interna do Saturn.")

blocks = []
remaining = len(raw) + 30
while remaining > 0:
    blocks.append(alloc_block())
    remaining += 2
    remaining = remaining - (block_size - 4) if remaining >= (block_size - 4) else 0

remaining = len(raw) + len(blocks) * 2 + 30
block_index = 0
file_offset = 0
block_list_write_index = 1
written_entries = 0
header_written = False

while remaining > 0:
    bi = blocks[block_index]
    block_index += 1
    off = bi * block_size
    remain_block = block_size - 4
    if block_index == 1:
        mem[off:off + 4] = b"\x80\x00\x00\x00"
    if not header_written:
        mem[off + 0x04:off + 0x0F] = filename.ljust(11, b"\0")
        mem[off + 0x0F] = language
        mem[off + 0x10:off + 0x1A] = comment.ljust(10, b"\0")
        mem[off + 0x1A:off + 0x1E] = struct.pack(">I", date_minutes)
        mem[off + 0x1E:off + 0x22] = struct.pack(">I", len(raw))
        off += 30
        remain_block -= 30
        remaining -= 30
        header_written = True
    off += 4
    if written_entries < len(blocks):
        entries_to_write = min(len(blocks) - written_entries, remain_block // 2)
        for j in range(entries_to_write):
            val = blocks[block_list_write_index] if block_list_write_index < len(blocks) else 0
            if block_list_write_index < len(blocks):
                block_list_write_index += 1
            mem[off + j * 2:off + j * 2 + 2] = struct.pack(">H", val)
        written_entries += entries_to_write
        remain_block -= entries_to_write * 2
        remaining -= entries_to_write * 2
        off += entries_to_write * 2
    data_to_write = min(remain_block, remaining)
    if data_to_write:
        mem[off:off + data_to_write] = raw[file_offset:file_offset + data_to_write]
        file_offset += data_to_write
        remaining -= data_to_write

out_path.write_bytes(mem)
PY

  fix_owner "$SAV_DIR" "$bkr_file"
  log "Memoria interna do Mednafen criada para destravar Death Tank:"
  log "  $bkr_file"
}

configure_mednafen_controls() {
  need_cmd python3

  cfg_file="$MEDNAFEN_HOME/mednafen.cfg"

  if [ ! -f "$cfg_file" ] && command -v mednafen >/dev/null 2>&1; then
    mkdir -p "$MEDNAFEN_HOME"
    if [ "$CURRENT_UID" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ] && command -v sudo >/dev/null 2>&1; then
      sudo -u "$TARGET_USER" env HOME="$TARGET_HOME" MEDNAFEN_HOME="$MEDNAFEN_HOME" mednafen -help >/dev/null 2>&1 || true
    else
      env HOME="$TARGET_HOME" MEDNAFEN_HOME="$MEDNAFEN_HOME" mednafen -help >/dev/null 2>&1 || true
    fi
  fi

  if [ ! -f "$cfg_file" ]; then
    log "Aviso: nao achei o arquivo de configuracao do Mednafen para mapear controles:"
    log "  $cfg_file"
    return 0
  fi

  backup="$cfg_file.bak-before-controllers-$(date +%Y%m%d-%H%M%S)"
  cp "$cfg_file" "$backup"

  python3 - "$cfg_file" <<'PY'
from pathlib import Path
import sys

cfg_path = Path(sys.argv[1])
text = cfg_path.read_text()

xbox = "0x0003045e028e01100008000b00000000"
usb = "0x00030810000101100006000c00000000"

replacements = {
    "ss.input.port1 gamepad": "ss.input.port1 gamepad",
    "ss.input.port2 gamepad": "ss.input.port2 gamepad",
    "ss.input.port1.gamepad.a": f"ss.input.port1.gamepad.a keyboard 0x0 89 || joystick {xbox} button_0",
    "ss.input.port1.gamepad.b": f"ss.input.port1.gamepad.b keyboard 0x0 90 || joystick {xbox} button_1",
    "ss.input.port1.gamepad.c": f"ss.input.port1.gamepad.c keyboard 0x0 91 || joystick {xbox} button_2",
    "ss.input.port1.gamepad.down": f"ss.input.port1.gamepad.down keyboard 0x0 22 || joystick {xbox} abs_7+ || joystick {xbox} abs_1+",
    "ss.input.port1.gamepad.left": f"ss.input.port1.gamepad.left keyboard 0x0 4 || joystick {xbox} abs_6- || joystick {xbox} abs_0-",
    "ss.input.port1.gamepad.ls": f"ss.input.port1.gamepad.ls keyboard 0x0 95 || joystick {xbox} button_4",
    "ss.input.port1.gamepad.right": f"ss.input.port1.gamepad.right keyboard 0x0 7 || joystick {xbox} abs_6+ || joystick {xbox} abs_0+",
    "ss.input.port1.gamepad.rs": f"ss.input.port1.gamepad.rs keyboard 0x0 97 || joystick {xbox} button_5",
    "ss.input.port1.gamepad.start": f"ss.input.port1.gamepad.start keyboard 0x0 40 || joystick {xbox} button_7",
    "ss.input.port1.gamepad.up": f"ss.input.port1.gamepad.up keyboard 0x0 26 || joystick {xbox} abs_7- || joystick {xbox} abs_1-",
    "ss.input.port1.gamepad.x": f"ss.input.port1.gamepad.x keyboard 0x0 92 || joystick {xbox} button_3",
    "ss.input.port1.gamepad.y": f"ss.input.port1.gamepad.y keyboard 0x0 93 || joystick {xbox} abs_2+",
    "ss.input.port1.gamepad.z": f"ss.input.port1.gamepad.z keyboard 0x0 94 || joystick {xbox} abs_5+",
    "ss.input.port2.gamepad.a": f"ss.input.port2.gamepad.a joystick {usb} button_0",
    "ss.input.port2.gamepad.b": f"ss.input.port2.gamepad.b joystick {usb} button_1",
    "ss.input.port2.gamepad.c": f"ss.input.port2.gamepad.c joystick {usb} button_2",
    "ss.input.port2.gamepad.down": f"ss.input.port2.gamepad.down joystick {usb} abs_5+ || joystick {usb} abs_1+",
    "ss.input.port2.gamepad.left": f"ss.input.port2.gamepad.left joystick {usb} abs_4- || joystick {usb} abs_0-",
    "ss.input.port2.gamepad.ls": f"ss.input.port2.gamepad.ls joystick {usb} button_4",
    "ss.input.port2.gamepad.right": f"ss.input.port2.gamepad.right joystick {usb} abs_4+ || joystick {usb} abs_0+",
    "ss.input.port2.gamepad.rs": f"ss.input.port2.gamepad.rs joystick {usb} button_5",
    "ss.input.port2.gamepad.start": f"ss.input.port2.gamepad.start joystick {usb} button_9",
    "ss.input.port2.gamepad.up": f"ss.input.port2.gamepad.up joystick {usb} abs_5- || joystick {usb} abs_1-",
    "ss.input.port2.gamepad.x": f"ss.input.port2.gamepad.x joystick {usb} button_3",
    "ss.input.port2.gamepad.y": f"ss.input.port2.gamepad.y joystick {usb} button_6",
    "ss.input.port2.gamepad.z": f"ss.input.port2.gamepad.z joystick {usb} button_7",
}

lines = []
for line in text.splitlines():
    key = line.split(" ", 1)[0]
    lines.append(replacements.get(key, line))

cfg_path.write_text("\n".join(lines) + "\n")
PY

  fix_owner "$cfg_file" "$backup"
  log "Controles do Mednafen configurados:"
  log "  Porta 1: Microsoft X-Box 360 pad"
  log "  Porta 2: USB Gamepad"
}

create_launcher() {
  if [ "$NO_SHORTCUTS" -eq 1 ]; then
    log "Pulando atalhos (--no-shortcuts)."
    return
  fi

  mkdir -p "$BIN_DIR" "$APPLICATIONS_DIR"

  cat > "$LAUNCHER" <<EOF
#!/bin/sh
exec mednafen \\
  -force_module ss \\
  -filesys.path_firmware "$FIRMWARE_DIR" \\
  -filesys.path_sav "$SAV_DIR" \\
  -filesys.fname_sav "%f.%x" \\
  -cd.image_memcache 1 \\
  -sound.driver sdl \\
  -ss.bios_na_eu mpr-17933.bin \\
  -ss.bios_jp sega_101.bin \\
  -ss.input.port1 gamepad \\
  -ss.input.port2 gamepad \\
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
Name=Death Tank Zwei (Mednafen)
Comment=Abre Death Tank Zwei no Mednafen
Exec=$LAUNCHER
Icon=applications-games
Terminal=false
Categories=Game;Emulator;
Keywords=Sega;Saturn;Mednafen;Death Tank;
StartupNotify=false
EOF
  chmod +x "$MENU_FILE"

  desktop_dir="$(get_desktop_dir)"
  desktop_file="$desktop_dir/Death Tank Zwei (Mednafen).desktop"
  old_desktop_file="$desktop_dir/Duke Nukem 3D Saturn (Mednafen).desktop"
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

install_packages
copy_bios_files
configure_mednafen_controls

if verify_game_cue; then
  prepare_deathtank_bkr
  create_launcher
fi

cat <<EOF

Pronto.

Para abrir o Death Tank Zwei no Mednafen:
  deathtank2-mednafen

Controles padrao no teclado:
  Enter       = Start
  W/S/A/D     = direcional
  Keypad 1    = A
  Keypad 2    = B
  Keypad 3    = C

Para configurar controles no Mednafen durante o jogo:
  Alt+Shift+1 = configurar controle da porta 1
  Alt+Shift+2 = configurar controle da porta 2
  F12         = sair
EOF
