#!/usr/bin/env python3
"""Apply a VS Code folder icon style and plus/minus explorer toggles.

The script updates user settings for VS Code-like editors, installs the folder
icon extension through each available CLI, and optionally patches the workbench
CSS so Explorer folders use + when collapsed and - when expanded.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

FOLDER_ICON_EXTENSION = "PKief.material-icon-theme"
CUSTOM_CSS_EXTENSION = "be5invis.vscode-custom-css"

PATCH_START = "/* vscode-folder-plus-minus:start */"
PATCH_END = "/* vscode-folder-plus-minus:end */"

PLUS_MINUS_CSS = textwrap.dedent(
    f"""
    {PATCH_START}
    .explorer-folders-view .monaco-tl-twistie.collapsible:not(.codicon-tree-item-loading):before {{
      transform: none !important;
    }}

    .explorer-folders-view .monaco-tl-twistie.collapsible.collapsed:not(.codicon-tree-item-loading):before {{
      content: var(--vscode-icon-add-content) !important;
      font-family: var(--vscode-icon-add-font-family) !important;
      transform: none !important;
    }}

    .explorer-folders-view .monaco-tl-twistie.collapsible:not(.collapsed):not(.codicon-tree-item-loading):before {{
      content: var(--vscode-icon-remove-content) !important;
      font-family: var(--vscode-icon-remove-font-family) !important;
      transform: none !important;
    }}
    {PATCH_END}
    """
).strip() + "\n"


@dataclass(frozen=True)
class EditorCandidate:
    label: str
    cli_names: tuple[str, ...]
    config_dirs: tuple[str, ...]
    known_roots: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class EditorInstall:
    candidate: EditorCandidate
    cli_path: Path | None
    user_settings_dirs: list[Path]
    profile_settings_dirs: list[Path]
    css_files: list[Path]


EDITOR_CANDIDATES = (
    EditorCandidate(
        label="Visual Studio Code",
        cli_names=("code",),
        config_dirs=("Code",),
        known_roots=(
            "/usr/share/code",
            "/usr/lib/code",
            "/opt/visual-studio-code",
            "/snap/code/current/usr/share/code",
        ),
    ),
    EditorCandidate(
        label="Visual Studio Code Insiders",
        cli_names=("code-insiders",),
        config_dirs=("Code - Insiders",),
        known_roots=(
            "/usr/share/code-insiders",
            "/usr/lib/code-insiders",
            "/opt/visual-studio-code-insiders",
            "/snap/code-insiders/current/usr/share/code-insiders",
        ),
    ),
    EditorCandidate(
        label="VSCodium",
        cli_names=("codium", "vscodium"),
        config_dirs=("VSCodium",),
        known_roots=(
            "/usr/share/codium",
            "/usr/lib/codium",
            "/usr/share/vscodium",
            "/usr/lib/vscodium",
            "/opt/vscodium-bin",
        ),
    ),
    EditorCandidate(
        label="Code OSS",
        cli_names=("code-oss",),
        config_dirs=("Code - OSS",),
        known_roots=(
            "/usr/share/code-oss",
            "/usr/lib/code-oss",
            "/opt/code-oss",
        ),
    ),
    EditorCandidate(
        label="Cursor",
        cli_names=("cursor",),
        config_dirs=("Cursor",),
        known_roots=(
            "/opt/Cursor",
            "/opt/cursor",
            "/usr/share/cursor",
        ),
    ),
)


def info(message: str) -> None:
    print(f"[vscode-folder-style] {message}")


def warn(message: str) -> None:
    print(f"[vscode-folder-style] aviso: {message}", file=sys.stderr)


def file_uri(path: Path) -> str:
    return path.resolve().as_uri()


def strip_json_comments(source: str) -> str:
    """Remove JSONC comments while preserving string literals."""

    output: list[str] = []
    i = 0
    in_string = False
    escaped = False

    while i < len(source):
        char = source[i]
        next_char = source[i + 1] if i + 1 < len(source) else ""

        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            i += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            i += 1
            continue

        if char == "/" and next_char == "/":
            i += 2
            while i < len(source) and source[i] not in "\r\n":
                i += 1
            continue

        if char == "/" and next_char == "*":
            i += 2
            while i + 1 < len(source) and not (
                source[i] == "*" and source[i + 1] == "/"
            ):
                i += 1
            i += 2
            continue

        output.append(char)
        i += 1

    return "".join(output)


def remove_trailing_commas(source: str) -> str:
    """Remove trailing commas from JSONC after comments have been stripped."""

    previous = None
    current = source
    pattern = re.compile(r",(\s*[}\]])")
    while previous != current:
        previous = current
        current = pattern.sub(r"\1", current)
    return current


def load_settings(settings_file: Path) -> dict:
    if not settings_file.exists() or not settings_file.read_text(encoding="utf-8").strip():
        return {}

    raw = settings_file.read_text(encoding="utf-8")
    cleaned = remove_trailing_commas(strip_json_comments(raw))
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{settings_file} nao parece ser JSON/JSONC valido: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"{settings_file} precisa conter um objeto JSON na raiz")
    return parsed


def save_settings(settings_file: Path, settings: dict, dry_run: bool) -> None:
    formatted = json.dumps(settings, ensure_ascii=False, indent=2) + "\n"
    if dry_run:
        info(f"[dry-run] atualizaria {settings_file}")
        return

    settings_file.parent.mkdir(parents=True, exist_ok=True)
    if settings_file.exists():
        backup = settings_file.with_name(
            f"{settings_file.name}.bak-vscode-folder-style-{timestamp()}"
        )
        shutil.copy2(settings_file, backup)
        info(f"backup criado: {backup}")
    settings_file.write_text(formatted, encoding="utf-8")


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def merge_unique(existing: Iterable[str], additions: Iterable[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in [*existing, *additions]:
        if item not in seen:
            seen.add(item)
            merged.append(item)
    return merged


def update_settings_file(settings_dir: Path, css_path: Path, dry_run: bool) -> bool:
    settings_file = settings_dir / "settings.json"
    settings = load_settings(settings_file)
    before = json.dumps(settings, sort_keys=True, ensure_ascii=False)

    imports = settings.get("vscode_custom_css.imports", [])
    if not isinstance(imports, list):
        imports = []

    settings.update(
        {
            "workbench.iconTheme": "material-icon-theme",
            "material-icon-theme.folders.theme": "specific",
            "material-icon-theme.hidesExplorerArrows": False,
            "explorer.compactFolders": False,
            "workbench.tree.indent": 12,
            "vscode_custom_css.imports": merge_unique(imports, [file_uri(css_path)]),
        }
    )

    after = json.dumps(settings, sort_keys=True, ensure_ascii=False)
    if before == after:
        info(f"settings ja estavam ajustados: {settings_file}")
        return False

    save_settings(settings_file, settings, dry_run)
    if dry_run:
        info(f"settings seriam ajustados: {settings_file}")
    else:
        info(f"settings ajustados: {settings_file}")
    return True


def discover_profile_settings_dirs(user_settings_dir: Path) -> list[Path]:
    profiles_dir = user_settings_dir / "profiles"
    if not profiles_dir.is_dir():
        return []

    profile_dirs = [
        path
        for path in profiles_dir.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ]
    return dedupe_paths(sorted(profile_dirs))


def project_settings_dir(project_dir: Path) -> Path:
    return project_dir.expanduser().resolve() / ".vscode"


def write_custom_css(css_path: Path, dry_run: bool) -> None:
    if css_path.exists() and css_path.read_text(encoding="utf-8") == PLUS_MINUS_CSS:
        info(f"CSS customizado ja esta atualizado: {css_path}")
        return

    if dry_run:
        info(f"[dry-run] escreveria CSS customizado em {css_path}")
        return

    css_path.parent.mkdir(parents=True, exist_ok=True)
    css_path.write_text(PLUS_MINUS_CSS, encoding="utf-8")
    info(f"CSS customizado escrito: {css_path}")


def resolve_cli(cli_names: tuple[str, ...]) -> Path | None:
    for cli_name in cli_names:
        found = shutil.which(cli_name)
        if found:
            return Path(found).resolve()
    return None


def candidate_roots(cli_path: Path | None, known_roots: Iterable[str]) -> list[Path]:
    roots: list[Path] = []

    if cli_path is not None:
        parents = list(cli_path.parents)
        if len(parents) >= 2:
            roots.append(parents[1])
        if len(parents) >= 3:
            roots.append(parents[2])
        roots.append(cli_path.parent)

    roots.extend(Path(root) for root in known_roots)

    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            deduped.append(resolved)
    return deduped


def workbench_css_from_root(root: Path) -> list[Path]:
    relative_paths = (
        Path("resources/app/out/vs/workbench/workbench.desktop.main.css"),
        Path("out/vs/workbench/workbench.desktop.main.css"),
        Path("app/out/vs/workbench/workbench.desktop.main.css"),
    )
    return [root / relative for relative in relative_paths if (root / relative).exists()]


def discover_installs(home: Path) -> list[EditorInstall]:
    installs: list[EditorInstall] = []

    for candidate in EDITOR_CANDIDATES:
        cli_path = resolve_cli(candidate.cli_names)
        user_settings_dirs = [
            home / ".config" / config_dir / "User"
            for config_dir in candidate.config_dirs
            if (home / ".config" / config_dir).exists() or cli_path is not None
        ]
        profile_settings_dirs: list[Path] = []
        for settings_dir in user_settings_dirs:
            profile_settings_dirs.extend(discover_profile_settings_dirs(settings_dir))
        profile_settings_dirs = dedupe_paths(profile_settings_dirs)

        css_files: list[Path] = []
        for root in candidate_roots(cli_path, candidate.known_roots):
            css_files.extend(workbench_css_from_root(root))

        css_files = dedupe_paths(css_files)
        if cli_path or user_settings_dirs or profile_settings_dirs or css_files:
            installs.append(
                EditorInstall(
                    candidate=candidate,
                    cli_path=cli_path,
                    user_settings_dirs=user_settings_dirs,
                    profile_settings_dirs=profile_settings_dirs,
                    css_files=css_files,
                )
            )

    return installs


def dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            deduped.append(resolved)
    return deduped


def install_extension(cli_path: Path, extension_id: str, dry_run: bool) -> bool:
    command = [str(cli_path), "--install-extension", extension_id, "--force"]
    if dry_run:
        info("[dry-run] executaria: " + " ".join(command))
        return True

    info(f"instalando {extension_id} via {cli_path.name}...")
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        warn(f"nao consegui instalar {extension_id} com {cli_path}: {exc}")
        return False

    if completed.returncode == 0:
        info(f"extensao instalada/atualizada: {extension_id}")
        return True

    output = (completed.stderr or completed.stdout).strip()
    warn(f"falha ao instalar {extension_id} com {cli_path.name}: {output}")
    return False


def install_extensions(
    installs: Iterable[EditorInstall],
    folder_icon_extension: str,
    custom_css_extension: str,
    skip_custom_css_extension: bool,
    dry_run: bool,
) -> None:
    for install in installs:
        if install.cli_path is None:
            warn(
                f"{install.candidate.label}: CLI nao encontrada; settings serao ajustados, "
                "mas extensoes nao serao instaladas automaticamente."
            )
            continue

        install_extension(install.cli_path, folder_icon_extension, dry_run)
        if not skip_custom_css_extension:
            install_extension(install.cli_path, custom_css_extension, dry_run)


def replace_patch_block(text: str) -> tuple[str, bool]:
    if PATCH_START in text and PATCH_END in text:
        pattern = re.compile(
            re.escape(PATCH_START) + r".*?" + re.escape(PATCH_END) + r"\n?",
            flags=re.DOTALL,
        )
        replaced = pattern.sub(PLUS_MINUS_CSS, text)
        return replaced, replaced != text

    separator = "\n" if text.endswith("\n") else "\n\n"
    return text + separator + PLUS_MINUS_CSS, True


def patch_workbench_css(css_file: Path, dry_run: bool) -> tuple[bool, bool]:
    """Patch a workbench CSS file.

    Returns (changed, permission_denied).
    """

    try:
        original = css_file.read_text(encoding="utf-8")
    except OSError as exc:
        warn(f"nao consegui ler {css_file}: {exc}")
        return False, False

    updated, changed = replace_patch_block(original)
    if not changed:
        info(f"patch ja estava aplicado: {css_file}")
        return False, False

    if dry_run:
        info(f"[dry-run] aplicaria patch de + / - em {css_file}")
        return True, False

    backup = css_file.with_name(f"{css_file.name}.bak-before-folder-plus-minus")
    try:
        if not backup.exists():
            shutil.copy2(css_file, backup)
            info(f"backup criado: {backup}")
        css_file.write_text(updated, encoding="utf-8")
    except PermissionError:
        warn(f"sem permissao para alterar {css_file}")
        return False, True
    except OSError as exc:
        warn(f"nao consegui alterar {css_file}: {exc}")
        return False, False

    info(f"patch aplicado: {css_file}")
    return True, False


def patch_all_workbenches(installs: Iterable[EditorInstall], dry_run: bool) -> bool:
    permission_denied = False
    patched_any = False

    for install in installs:
        if not install.css_files:
            info(f"{install.candidate.label}: CSS do workbench nao encontrado.")
            continue

        for css_file in install.css_files:
            changed, denied = patch_workbench_css(css_file, dry_run)
            patched_any = patched_any or changed
            permission_denied = permission_denied or denied

    if not patched_any and not permission_denied:
        info("nenhum patch novo de workbench foi necessario.")
    return permission_denied


def print_summary(installs: Iterable[EditorInstall]) -> None:
    info("instalacoes detectadas:")
    for install in installs:
        cli = str(install.cli_path) if install.cli_path else "CLI nao encontrada"
        user_settings = (
            ", ".join(str(path) for path in install.user_settings_dirs)
            or "sem settings de usuario"
        )
        profile_settings = (
            ", ".join(str(path) for path in install.profile_settings_dirs)
            or "sem perfis detectados"
        )
        css_files = ", ".join(str(path) for path in install.css_files) or "sem CSS do workbench"
        info(f"- {install.candidate.label}: {cli}")
        info(f"  settings usuario: {user_settings}")
        info(f"  settings perfis: {profile_settings}")
        info(f"  workbench CSS: {css_files}")


def choose_settings_scope(args: argparse.Namespace) -> str:
    if args.settings_scope:
        return args.settings_scope

    if args.only_patch_workbench or not sys.stdin.isatty():
        return "all"

    info("onde aplicar os settings?")
    print("  1) tudo: usuario global + todos os perfis + projeto atual")
    print("  2) usuario global de todos os VS Code detectados")
    print("  3) todos os perfis de todos os VS Code detectados")
    print("  4) somente este projeto (.vscode/settings.json)")
    answer = input("[vscode-folder-style] escolha [1]: ").strip()
    return {
        "": "all",
        "1": "all",
        "2": "user",
        "3": "profiles",
        "4": "project",
    }.get(answer, "all")


def settings_dirs_for_scope(
    installs: Iterable[EditorInstall],
    scope: str,
    project_dir: Path,
) -> list[Path]:
    settings_dirs: list[Path] = []

    if scope in {"all", "user"}:
        for install in installs:
            settings_dirs.extend(install.user_settings_dirs)

    if scope in {"all", "profiles"}:
        for install in installs:
            settings_dirs.extend(install.profile_settings_dirs)

    if scope in {"all", "project"}:
        settings_dirs.append(project_settings_dir(project_dir))

    return dedupe_paths(settings_dirs)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Instala tema de icones de pasta no VS Code e troca as setas do "
            "Explorer por + e -."
        )
    )
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que faria.")
    parser.add_argument(
        "--no-install-extensions",
        action="store_true",
        help="Nao instala extensoes pelos CLIs detectados.",
    )
    parser.add_argument(
        "--skip-custom-css-extension",
        action="store_true",
        help=f"Nao instala {CUSTOM_CSS_EXTENSION}.",
    )
    parser.add_argument(
        "--no-patch-workbench",
        action="store_true",
        help="Nao altera o CSS interno do VS Code; apenas configura o arquivo CSS customizado.",
    )
    parser.add_argument(
        "--only-patch-workbench",
        action="store_true",
        help="Somente aplica o patch no CSS interno do workbench.",
    )
    parser.add_argument(
        "--settings-scope",
        choices=("all", "user", "profiles", "project"),
        help=(
            "Onde aplicar os settings: all=usuario+perfis+projeto, "
            "user=usuario global, profiles=todos os perfis, project=somente este projeto. "
            "Sem esta opcao, mostra um menu quando estiver em terminal."
        ),
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Projeto que recebera .vscode/settings.json quando o escopo incluir project.",
    )
    parser.add_argument(
        "--folder-icon-extension",
        default=FOLDER_ICON_EXTENSION,
        help=f"Extensao de icones de pasta. Padrao: {FOLDER_ICON_EXTENSION}",
    )
    parser.add_argument(
        "--custom-css-extension",
        default=CUSTOM_CSS_EXTENSION,
        help=f"Extensao de CSS customizado. Padrao: {CUSTOM_CSS_EXTENSION}",
    )
    parser.add_argument(
        "--css-path",
        type=Path,
        default=Path.home() / ".config" / "vscode-folder-style" / "folder-plus-minus.css",
        help="Caminho do CSS usado pela extensao Custom CSS and JS Loader.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    home = Path(os.environ.get("HOME", str(Path.home()))).expanduser()
    css_path = args.css_path.expanduser()
    settings_scope = choose_settings_scope(args)

    installs = discover_installs(home)
    if not installs and settings_scope != "project":
        warn("nenhuma instalacao tipo VS Code foi encontrada.")
        return 1

    if installs:
        print_summary(installs)
    else:
        warn("nenhuma instalacao tipo VS Code foi encontrada; vou ajustar somente o projeto.")

    info(f"escopo de settings: {settings_scope}")

    if not args.only_patch_workbench:
        write_custom_css(css_path, args.dry_run)

        settings_dirs = settings_dirs_for_scope(
            installs=installs,
            scope=settings_scope,
            project_dir=args.project_dir,
        )
        if not settings_dirs:
            warn("nenhum settings encontrado para o escopo escolhido.")
        for settings_dir in settings_dirs:
            try:
                update_settings_file(settings_dir, css_path, args.dry_run)
            except ValueError as exc:
                warn(str(exc))

        if not args.no_install_extensions:
            install_extensions(
                installs=installs,
                folder_icon_extension=args.folder_icon_extension,
                custom_css_extension=args.custom_css_extension,
                skip_custom_css_extension=args.skip_custom_css_extension,
                dry_run=args.dry_run,
            )

    if args.no_patch_workbench:
        info(
            "patch interno pulado. Para ativar o CSS pelo Custom CSS and JS Loader, "
            "rode no VS Code o comando: Reload Custom CSS and JS."
        )
        return 0

    permission_denied = patch_all_workbenches(installs, args.dry_run)
    if permission_denied:
        warn(
            "algum patch interno precisa de permissao de administrador. "
            "O wrapper .sh pode tentar novamente com sudo."
        )
        return 77

    info("pronto. Reinicie o VS Code para ver o estilo aplicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
