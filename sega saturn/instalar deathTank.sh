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

BIOS_SATURN_DIR="${BIOS_SATURN_DIR:-$SCRIPT_DIR/BIOS-SATURN}"
DT_DIR="${DT_DIR:-$SCRIPT_DIR/DT}"
LEGACY_FIXED_DIR="${LEGACY_FIXED_DIR:-$TARGET_HOME/Music/DeathTank2_fixed}"
GAME_DIR="${GAME_DIR:-$DT_DIR/DeathTank2_fixed}"
GAME_CUE="${GAME_CUE:-$GAME_DIR/death2_fixed.cue}"
YMIR_BIOS_DIR="${YMIR_BIOS_DIR:-$TARGET_HOME/.local/share/StrikerX3/Ymir/roms/ipl}"
YMIR_INSTALL_IPL_DIR="${YMIR_INSTALL_IPL_DIR:-$TARGET_HOME/Apps/Ymir/roms/ipl}"
MEDNAFEN_HOME="${MEDNAFEN_HOME:-$TARGET_HOME/.mednafen}"
MEDNAFEN_FIRMWARE_DIR="$MEDNAFEN_HOME/firmware"
RETROARCH_SYSTEM_DIR="$TARGET_HOME/.var/app/org.libretro.RetroArch/config/retroarch/system"
BIN_DIR="${DEATHTANK_BIN_DIR:-$TARGET_HOME/.local/bin}"
APPLICATIONS_BASE="${DEATHTANK_XDG_DATA_HOME:-${XDG_DATA_HOME:-$TARGET_HOME/.local/share}}"
APPLICATIONS_DIR="$APPLICATIONS_BASE/applications"
RUN_YMIR=1
RUN_MEDNAFEN=1
RUN_KRONOS=1
NO_SHORTCUTS=0
PREPARE_ONLY=0
YMIR_CHANNEL_ARG="--nightly"
GAME_SELECTED_BY_USER=0

US_EU_BIOS_SHA256="96e106f740ab448cf89f0dd49dfbac7fe5391cb6bd6e14ad5e3061c13330266f"
JP_BIOS_SHA256="dcfef4b99605f872b6c3b6d05c045385cdea3d1b702906a0ed930df7bcb7deac"

log() {
  printf '%s\n' "$*"
}

usage() {
  cat <<EOF
Uso:
  sh "instalar deathTank.sh" [opcoes]

Instala/atualiza Ymir, Mednafen e Kronos, configura BIOS e cria atalhos
para abrir Death Tank Zwei direto.

Opcoes:
  --game-dir CAMINHO   Pasta do Death Tank Zwei
                       Padrao: $GAME_DIR
  --cue CAMINHO        Arquivo CUE do jogo
                       Padrao: $GAME_CUE
  --dt-dir CAMINHO     Pasta local para arquivos do Death Tank
                       Padrao: $DT_DIR
  --bios-dir CAMINHO   Pasta local das BIOS
                       Padrao: $BIOS_SATURN_DIR
  --ymir-stable        Instala/atualiza Ymir pelo canal estavel
  --no-ymir            Nao instala/atualiza Ymir
  --no-mednafen        Nao instala/configura Mednafen
  --no-kronos          Nao instala/configura Kronos/RetroArch
  --no-shortcuts       Nao cria o atalho recomendado do Death Tank
  --prepare-only       Apenas prepara/copia BIOS; nao chama os instaladores
  -h, --help           Mostra esta ajuda

Importante:
  Este script nao baixa automaticamente imagens/ISOs/RARs de jogos da internet.
  Coloque seus arquivos locais DeathTank.rar e DeathTank2.rar em:
    $DT_DIR

  Se encontrar esses arquivos, o script extrai e monta:
    $DT_DIR/DeathTank2_fixed/death2_fixed.cue

  Este script nao baixa BIOS proprietarias automaticamente. Coloque suas
  BIOS de Sega Saturn em:
    $BIOS_SATURN_DIR

  Se voce ja configurou BIOS no Ymir, eu tambem tento reaproveitar as de:
    $YMIR_BIOS_DIR
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
      GAME_SELECTED_BY_USER=1
      ;;
    --cue)
      shift
      if [ "$#" -eq 0 ]; then
        log "Erro: --cue precisa de um caminho."
        exit 1
      fi
      GAME_CUE="$1"
      GAME_DIR="$(dirname "$GAME_CUE")"
      GAME_SELECTED_BY_USER=1
      ;;
    --dt-dir)
      shift
      if [ "$#" -eq 0 ]; then
        log "Erro: --dt-dir precisa de um caminho."
        exit 1
      fi
      DT_DIR="$1"
      if [ "$GAME_SELECTED_BY_USER" -eq 0 ]; then
        GAME_DIR="$DT_DIR/DeathTank2_fixed"
        GAME_CUE="$GAME_DIR/death2_fixed.cue"
      fi
      ;;
    --bios-dir)
      shift
      if [ "$#" -eq 0 ]; then
        log "Erro: --bios-dir precisa de um caminho."
        exit 1
      fi
      BIOS_SATURN_DIR="$1"
      ;;
    --ymir-stable)
      YMIR_CHANNEL_ARG="--stable"
      ;;
    --no-ymir)
      RUN_YMIR=0
      ;;
    --no-mednafen)
      RUN_MEDNAFEN=0
      ;;
    --no-kronos)
      RUN_KRONOS=0
      ;;
    --no-shortcuts)
      NO_SHORTCUTS=1
      ;;
    --prepare-only)
      PREPARE_ONLY=1
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
  if [ -n "${DEATHTANK_DESKTOP_DIR:-}" ]; then
    printf '%s\n' "$DEATHTANK_DESKTOP_DIR"
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

extract_archive() {
  archive="$1"
  out_dir="$2"
  [ -f "$archive" ] || return 1

  marker="$out_dir/.extracted-$(basename "$archive").ok"
  if [ -f "$marker" ]; then
    log "Arquivo ja extraido:"
    log "  $archive"
    return 0
  fi

  mkdir -p "$out_dir"
  log "Extraindo arquivo local:"
  log "  $archive"
  log "Para:"
  log "  $out_dir"

  if command -v unrar >/dev/null 2>&1; then
    unrar x -o+ "$archive" "$out_dir/"
  elif command -v 7z >/dev/null 2>&1; then
    7z x -y "-o$out_dir" "$archive"
  elif command -v bsdtar >/dev/null 2>&1; then
    bsdtar -xf "$archive" -C "$out_dir"
  elif command -v unar >/dev/null 2>&1; then
    unar -force-overwrite -o "$out_dir" "$archive"
  else
    log "Erro: nao achei ferramenta para extrair .rar."
    log "Instale uma delas: unrar, 7z, bsdtar ou unar."
    exit 1
  fi

  : > "$marker"
  fix_owner "$out_dir"
  return 0
}

prepare_dt_folder() {
  mkdir -p "$DT_DIR"
  fix_owner "$DT_DIR"

  log "Pasta local do Death Tank:"
  log "  $DT_DIR"

  if [ ! -f "$DT_DIR/DeathTank.rar" ] || [ ! -f "$DT_DIR/DeathTank2.rar" ]; then
    log "Aviso: nao vou baixar ISOs/RARs de jogos automaticamente."
    log "Para extrair os CDs pelo script, coloque seus arquivos locais aqui:"
    log "  $DT_DIR/DeathTank.rar"
    log "  $DT_DIR/DeathTank2.rar"
  fi
}

prepare_game_archives() {
  extracted_any=0

  if extract_archive "$DT_DIR/DeathTank.rar" "$DT_DIR/DeathTank"; then
    extracted_any=1
  fi

  if extract_archive "$DT_DIR/DeathTank2.rar" "$DT_DIR/DeathTank2_raw"; then
    extracted_any=1
  fi

  if [ "$extracted_any" -eq 1 ]; then
    log "Arquivos locais do Death Tank extraidos em:"
    log "  $DT_DIR"
  fi
}

prepare_deathtank2_fixed() {
  need_cmd python3

  python3 - "$DT_DIR" "$LEGACY_FIXED_DIR" <<'PY'
from pathlib import Path
import shutil
import sys

dt_dir = Path(sys.argv[1])
legacy_fixed = Path(sys.argv[2])
fixed = dt_dir / "DeathTank2_fixed"
raw = dt_dir / "DeathTank2_raw"
cue_path = fixed / "death2_fixed.cue"
iso_out = fixed / "Death2.iso"

def copy_tree_contents(src: Path, dst: Path) -> bool:
    if not src.is_dir():
        return False
    dst.mkdir(parents=True, exist_ok=True)
    copied = False
    for item in src.iterdir():
        dest = dst / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
        copied = True
    return copied

def all_fixed_files_exist() -> bool:
    if not cue_path.is_file() or not iso_out.is_file():
        return False
    return all((fixed / f"track{i:02d}.wav").is_file() for i in range(2, 24))

def find_first(root: Path, patterns):
    if not root.is_dir():
        return None
    matches = []
    for pattern in patterns:
        matches.extend(root.rglob(pattern))
    files = [p for p in matches if p.is_file()]
    if not files:
        return None
    return sorted(files, key=lambda p: (len(str(p)), str(p).lower()))[0]

def find_named_wav(root: Path, names):
    if not root.is_dir():
        return None
    wanted = {name.lower() for name in names}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name.lower() in wanted:
            return path
    return None

def build_from_raw() -> bool:
    iso = find_first(raw, ["*.iso", "*.ISO", "*.bin", "*.BIN"])
    if iso is None:
        return False

    filler = find_named_wav(raw, ["dukefiller.wav", "track02.wav"])
    duke21 = find_named_wav(raw, ["duke21.wav", "track21.wav"])
    duke22 = find_named_wav(raw, ["duke22.wav", "track22.wav"])
    duke23 = find_named_wav(raw, ["duke23.wav", "track23.wav"])

    fixed.mkdir(parents=True, exist_ok=True)
    shutil.copy2(iso, iso_out)

    missing = []
    for track in range(2, 24):
        exact = find_named_wav(raw, [f"track{track:02d}.wav"])
        src = exact
        if src is None and 2 <= track <= 20:
            src = filler
        elif src is None and track == 21:
            src = duke21
        elif src is None and track == 22:
            src = duke22
        elif src is None and track == 23:
            src = duke23

        if src is None:
            missing.append(f"track{track:02d}.wav")
            continue
        shutil.copy2(src, fixed / f"track{track:02d}.wav")

    if missing:
        print("Aviso: faltam faixas de audio para Death Tank 2:", ", ".join(missing))
        return False

    lines = [
        'FILE "Death2.iso" BINARY',
        "  TRACK 01 MODE1/2048",
        "    INDEX 01 00:00:00",
        "    POSTGAP 00:02:00",
    ]
    for track in range(2, 24):
        lines.append(f'FILE "track{track:02d}.wav" WAVE')
        lines.append(f"  TRACK {track:02d} AUDIO")
        if track == 2:
            lines.append("    PREGAP 00:02:00")
        lines.append("    INDEX 01 00:00:00")
    cue_path.write_text("\n".join(lines) + "\n")
    return True

if all_fixed_files_exist():
    print(f"Death Tank 2 ja esta preparado em: {fixed}")
    raise SystemExit(0)

if build_from_raw():
    print(f"Death Tank 2 corrigido/preparado em: {fixed}")
    raise SystemExit(0)

if copy_tree_contents(legacy_fixed, fixed) and all_fixed_files_exist():
    print(f"Death Tank 2 reaproveitado de: {legacy_fixed}")
    print(f"Copiado para: {fixed}")
    raise SystemExit(0)

print("Aviso: nao consegui preparar Death Tank 2 automaticamente.")
print(f"Coloque DeathTank2.rar em: {dt_dir}")
print(f"Ou mantenha uma pasta ja corrigida em: {legacy_fixed}")
raise SystemExit(1)
PY

  fix_owner "$DT_DIR/DeathTank2_fixed"
}

copy_missing_bios_from_dir() {
  source_dir="$1"
  [ -d "$source_dir" ] || return 0

  for bios in "$source_dir"/*.bin "$source_dir"/*.BIN; do
    [ -f "$bios" ] || continue
    dest="$BIOS_SATURN_DIR/$(basename "$bios")"
    if [ ! -f "$dest" ]; then
      cp "$bios" "$dest"
      log "BIOS reaproveitada:"
      log "  $dest"
    fi
  done
}

find_bios_by_sha256() {
  wanted="$1"

  for bios_dir in "$BIOS_SATURN_DIR" "$YMIR_BIOS_DIR" "$YMIR_INSTALL_IPL_DIR"; do
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
    log "Use --cue /caminho/arquivo.cue se ele estiver em outro lugar."
    exit 1
  fi

  log "Jogo configurado:"
  log "  $GAME_CUE"
}

prepare_bios_folder() {
  mkdir -p "$BIOS_SATURN_DIR"
  fix_owner "$BIOS_SATURN_DIR"

  log "Pasta local de BIOS:"
  log "  $BIOS_SATURN_DIR"
  log "Nao vou baixar BIOS proprietarias automaticamente; vou usar arquivos locais."

  copy_missing_bios_from_dir "$YMIR_BIOS_DIR"
  copy_missing_bios_from_dir "$YMIR_INSTALL_IPL_DIR"
  fix_owner "$BIOS_SATURN_DIR"
}

copy_bios_to_emulators() {
  need_cmd sha256sum
  need_cmd awk

  na_bios="$(find_bios_by_sha256 "$US_EU_BIOS_SHA256" || true)"
  jp_bios="$(find_bios_by_sha256 "$JP_BIOS_SHA256" || true)"

  if [ -z "$na_bios" ]; then
    log "Erro: nao achei BIOS US/EU compativel."
    log "Coloque a BIOS US/EU de Sega Saturn em:"
    log "  $BIOS_SATURN_DIR"
    log "Nome esperado pelo Mednafen depois da copia: mpr-17933.bin"
    exit 1
  fi

  if [ -z "$jp_bios" ]; then
    log "Erro: nao achei BIOS japonesa compativel."
    log "Coloque a BIOS JP de Sega Saturn em:"
    log "  $BIOS_SATURN_DIR"
    log "Nome esperado pelo Mednafen depois da copia: sega_101.bin"
    exit 1
  fi

  mkdir -p "$BIOS_SATURN_DIR" "$YMIR_BIOS_DIR" "$YMIR_INSTALL_IPL_DIR" "$MEDNAFEN_FIRMWARE_DIR" "$RETROARCH_SYSTEM_DIR/kronos"

  for bios in "$BIOS_SATURN_DIR"/*.bin "$BIOS_SATURN_DIR"/*.BIN; do
    [ -f "$bios" ] || continue
    cp "$bios" "$YMIR_BIOS_DIR/"
    cp "$bios" "$YMIR_INSTALL_IPL_DIR/"
  done

  cp "$na_bios" "$MEDNAFEN_FIRMWARE_DIR/mpr-17933.bin"
  cp "$jp_bios" "$MEDNAFEN_FIRMWARE_DIR/sega_101.bin"
  cp "$na_bios" "$RETROARCH_SYSTEM_DIR/kronos/saturn_bios.bin"
  cp "$na_bios" "$RETROARCH_SYSTEM_DIR/saturn_bios.bin"

  chmod 644 \
    "$MEDNAFEN_FIRMWARE_DIR/mpr-17933.bin" \
    "$MEDNAFEN_FIRMWARE_DIR/sega_101.bin" \
    "$RETROARCH_SYSTEM_DIR/kronos/saturn_bios.bin" \
    "$RETROARCH_SYSTEM_DIR/saturn_bios.bin"

  fix_owner "$BIOS_SATURN_DIR" "$YMIR_BIOS_DIR" "$YMIR_INSTALL_IPL_DIR" "$MEDNAFEN_HOME" "$RETROARCH_SYSTEM_DIR"

  log "BIOS copiadas para Ymir, Mednafen e Kronos."
}

run_installers() {
  if [ "$PREPARE_ONLY" -eq 1 ]; then
    log "Modo --prepare-only: nao vou chamar os instaladores dos emuladores."
    return
  fi

  if [ "$RUN_YMIR" -eq 1 ]; then
    log ""
    log "Instalando/atualizando Ymir..."
    sh "$SCRIPT_DIR/ymir.sh" "$YMIR_CHANNEL_ARG" --bios-dir "$BIOS_SATURN_DIR"
  fi

  if [ "$RUN_MEDNAFEN" -eq 1 ]; then
    log ""
    log "Instalando/configurando Mednafen com Death Tank..."
    GAME_DIR="$GAME_DIR" GAME_CUE="$GAME_CUE" sh "$SCRIPT_DIR/mednafen_saturn.sh" --bios-dir "$BIOS_SATURN_DIR"
  fi

  if [ "$RUN_KRONOS" -eq 1 ]; then
    log ""
    log "Instalando/configurando Kronos com Death Tank..."
    GAME_DIR="$GAME_DIR" GAME_CUE="$GAME_CUE" sh "$SCRIPT_DIR/kronos_saturn.sh" --bios-dir "$BIOS_SATURN_DIR"
  fi
}

create_recommended_shortcut() {
  if [ "$NO_SHORTCUTS" -eq 1 ]; then
    log "Pulando atalho recomendado (--no-shortcuts)."
    return
  fi

  launcher="$BIN_DIR/deathtank2-mednafen"
  if [ ! -x "$launcher" ]; then
    log "Aviso: launcher recomendado ainda nao existe:"
    log "  $launcher"
    log "O atalho principal sera criado quando o Mednafen terminar de configurar."
    return
  fi

  desktop_dir="$(get_desktop_dir)"
  menu_file="$APPLICATIONS_DIR/deathtank2.desktop"
  desktop_file="$desktop_dir/Death Tank Zwei.desktop"

  mkdir -p "$APPLICATIONS_DIR" "$desktop_dir"
  cat > "$menu_file" <<EOF
[Desktop Entry]
Type=Application
Name=Death Tank Zwei
Comment=Abre Death Tank Zwei no Mednafen
Exec=$launcher
Icon=applications-games
Terminal=false
Categories=Game;Emulator;
Keywords=Sega;Saturn;Death Tank;Mednafen;
StartupNotify=false
EOF
  chmod +x "$menu_file"
  cp "$menu_file" "$desktop_file"
  chmod +x "$desktop_file"

  if command -v gio >/dev/null 2>&1; then
    gio set "$desktop_file" metadata::trusted true >/dev/null 2>&1 || true
  fi

  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
  fi

  fix_owner "$menu_file" "$desktop_file"

  log "Atalho recomendado criado:"
  log "  $desktop_file"
  log "  $menu_file"
}

prepare_dt_folder
prepare_game_archives
if [ "$GAME_SELECTED_BY_USER" -eq 0 ] || [ ! -f "$GAME_CUE" ]; then
  prepare_deathtank2_fixed
fi
verify_game_cue
prepare_bios_folder
copy_bios_to_emulators
run_installers
create_recommended_shortcut

cat <<EOF

Pronto.

Para abrir o Death Tank Zwei no emulador que funcionou melhor:
  deathtank2-mednafen

Para testar nos outros:
  deathtank2-kronos
  ymir-sdl3

BIOS local usada pelo instalador:
  $BIOS_SATURN_DIR

Arquivos locais do Death Tank:
  $DT_DIR

EOF
