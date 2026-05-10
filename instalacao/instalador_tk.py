"""GUI and CLI installer for myAgileKit."""

from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import os
import platform
import queue
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

BOOTSTRAP_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(BOOTSTRAP_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(BOOTSTRAP_PROJECT_ROOT))

from myagilekit.core.paths import CONFIG_DIR, LOGS_DIR, PROJECT_ROOT, ensure_project_layout, log_path  # noqa: E402
from myagilekit.core.process_runner import run_streamed  # noqa: E402

REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
VENV_DIR = PROJECT_ROOT / ".venv"
PYTHON_BIN = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

OutputWriter = Callable[[str], None]


@dataclass(frozen=True)
class CheckItem:
    name: str
    status: str
    required: bool = True
    detail: str = ""


def python_module_available(module: str, python: str) -> bool:
    command = [python, "-c", f"import {module}"]
    try:
        result = subprocess.run(command, cwd=PROJECT_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return result.returncode == 0


def missing_system_packages(python: str) -> list[str]:
    """Return OS packages that cannot be solved inside .venv."""

    packages: list[str] = []
    if not python_module_available("tkinter", python):
        packages.append("python3-tk")

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        packages.append("ffmpeg")

    return packages


def python_for_checks() -> str:
    if PYTHON_BIN.exists():
        return str(PYTHON_BIN)
    return shutil.which("python3") or sys.executable or "python3"


def status_items(python: str | None = None) -> list[CheckItem]:
    python = python or python_for_checks()
    ensure_project_layout()
    return [
        CheckItem("Sistema", f"{platform.system()} {platform.release()}", required=False),
        CheckItem("Ambiente virtual .venv", "OK" if PYTHON_BIN.exists() else "Pendente"),
        CheckItem("requirements.txt", "OK" if REQUIREMENTS_FILE.exists() else "Pendente"),
        CheckItem("config/myagilekit.toml", "OK" if (CONFIG_DIR / "myagilekit.toml").exists() else "Pendente"),
        CheckItem("tkinter/ttk", "OK" if python_module_available("tkinter", python) else "Pendente"),
        CheckItem("yt-dlp", "OK" if python_module_available("yt_dlp", python) else "Pendente"),
        CheckItem("pygame", "OK" if python_module_available("pygame", python) else "Pendente"),
        CheckItem("ruff", "OK" if python_module_available("ruff", python) else "Pendente"),
        CheckItem("ffmpeg", "OK" if shutil.which("ffmpeg") else "Pendente"),
        CheckItem("ffprobe", "OK" if shutil.which("ffprobe") else "Pendente"),
        CheckItem("bash", "OK" if shutil.which("bash") else "Pendente"),
        CheckItem("node ou deno", "OK" if shutil.which("node") or shutil.which("deno") else "Opcional", required=False),
        CheckItem("logs/install", "OK" if (LOGS_DIR / "install").exists() else "Pendente"),
        CheckItem("logs/tools", "OK" if (LOGS_DIR / "tools").exists() else "Pendente"),
        CheckItem("logs/tests", "OK" if (LOGS_DIR / "tests").exists() else "Pendente"),
        CheckItem("logs/errors", "OK" if (LOGS_DIR / "errors").exists() else "Pendente"),
    ]


def run_check(output: OutputWriter | None = None) -> int:
    writer = output or (lambda text: print(text, end=""))
    items = status_items()
    width = max(len(item.name) for item in items)
    writer("Diagnostico myAgileKit\n")
    writer(f"Python usado: {python_for_checks()}\n\n")
    for item in items:
        detail = f" - {item.detail}" if item.detail else ""
        writer(f"{item.name:<{width}}  {item.status}{detail}\n")
    return 0 if all(not item.required or item.status == "OK" for item in items) else 1


def new_install_log_path() -> Path:
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_path(f"install_{ts}.log", "install")


def _emit(output: OutputWriter | None, log_file: Path | None, text: str) -> None:
    if output is not None:
        output(text)
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(text)


def _run_step(title: str, command: list[str], output: OutputWriter | None, log_file: Path | None) -> None:
    _emit(output, log_file, f"\n== {title} ==\n")
    try:
        return_code = run_streamed(command, cwd=PROJECT_ROOT, output=output, log_file=log_file)
    except OSError as exc:
        raise RuntimeError(f"{title} falhou: {exc}") from exc
    if return_code != 0:
        raise RuntimeError(f"{title} falhou com codigo {return_code}")


def run_install(
    *,
    install_system: bool = False,
    run_tests: bool = True,
    output: OutputWriter | None = None,
    log_file: Path | None = None,
) -> Path:
    ensure_project_layout()
    log_file = log_file or new_install_log_path()
    _emit(output, log_file, f"Log de instalacao: {log_file.relative_to(PROJECT_ROOT)}\n")
    _emit(output, log_file, "Diretorios logs/ e config/ verificados.\n")

    if not PYTHON_BIN.exists():
        _run_step("Criando ambiente virtual", ["python3", "-m", "venv", str(VENV_DIR)], output, log_file)

    if install_system:
        if platform.system() == "Linux":
            packages = missing_system_packages(str(PYTHON_BIN))
            if packages:
                _run_step(
                    "Instalando dependencias de sistema indispensaveis",
                    ["sudo", "apt-get", "install", "-y", *packages],
                    output,
                    log_file,
                )
            else:
                _emit(output, log_file, "apt-get pulado: dependencias de sistema ja atendidas.\n")
        else:
            _emit(output, log_file, "apt-get pulado: disponivel apenas em Linux/Debian/Ubuntu.\n")

    _run_step("Atualizando pip", [str(PYTHON_BIN), "-m", "pip", "install", "--upgrade", "pip"], output, log_file)
    _run_step(
        "Instalando requirements",
        [str(PYTHON_BIN), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        output,
        log_file,
    )

    if run_tests:
        _run_step("Rodando testes", [str(PYTHON_BIN), "-m", "unittest", "discover", "-s", "tests"], output, log_file)

    _emit(output, log_file, "Instalacao finalizada.\n")
    return log_file


def _load_tkinter():
    import tkinter as tk
    from tkinter import messagebox, ttk

    return tk, messagebox, ttk


def create_installer_app_class():
    tk, messagebox, ttk = _load_tkinter()

    class InstallerApp(tk.Tk):
        def __init__(self) -> None:
            super().__init__()
            self.title("myAgileKit Installer")
            self.geometry("980x680")
            self.minsize(860, 560)

            self.install_log = new_install_log_path()
            self.output_queue: queue.Queue[str] = queue.Queue()
            self.install_thread: threading.Thread | None = None

            self._configure_style()
            self._create_widgets()
            self._refresh_status()
            self.after(100, self._drain_output_queue)

        def _configure_style(self) -> None:
            style = ttk.Style(self)
            with contextlib.suppress(tk.TclError):
                style.theme_use("clam")
            style.configure(".", font=("Segoe UI", 10))
            style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
            style.configure("Muted.TLabel", foreground="#5f6368")
            style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))

        def _create_widgets(self) -> None:
            header = ttk.Frame(self, padding=(18, 16, 18, 8))
            header.pack(fill=tk.X)
            ttk.Label(header, text="Instalador myAgileKit", style="Title.TLabel").pack(anchor=tk.W)
            ttk.Label(
                header,
                text="Cria/atualiza o ambiente, instala dependencias Python e roda verificacoes.",
                style="Muted.TLabel",
            ).pack(anchor=tk.W, pady=(4, 0))

            body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
            body.pack(fill=tk.BOTH, expand=True, padx=18, pady=10)

            status_frame = ttk.LabelFrame(body, text="Status", padding=10)
            body.add(status_frame, weight=1)
            self.status_tree = ttk.Treeview(status_frame, columns=("status",), show="tree headings")
            self.status_tree.heading("#0", text="Item")
            self.status_tree.heading("status", text="Estado")
            self.status_tree.column("#0", width=260)
            self.status_tree.column("status", width=160, anchor=tk.CENTER)
            self.status_tree.pack(fill=tk.BOTH, expand=True)

            right = ttk.Frame(body)
            body.add(right, weight=2)

            options = ttk.LabelFrame(right, text="Opcoes", padding=10)
            options.pack(fill=tk.X)
            self.install_system_var = tk.BooleanVar(value=False)
            self.run_tests_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                options,
                text="Usar apt-get somente para dependencias fora da .venv (python3-tk, ffmpeg)",
                variable=self.install_system_var,
            ).pack(anchor=tk.W)
            ttk.Checkbutton(
                options,
                text="Rodar testes depois da instalacao",
                variable=self.run_tests_var,
            ).pack(anchor=tk.W, pady=(4, 0))

            button_row = ttk.Frame(right)
            button_row.pack(fill=tk.X, pady=10)
            self.install_button = ttk.Button(
                button_row,
                text="Instalar / atualizar tudo",
                style="Action.TButton",
                command=self._start_install,
            )
            self.install_button.pack(side=tk.LEFT)
            ttk.Button(button_row, text="Atualizar status", command=self._refresh_status).pack(side=tk.LEFT, padx=8)

            log_frame = ttk.LabelFrame(right, text=f"Log: {self.install_log.relative_to(PROJECT_ROOT)}", padding=8)
            log_frame.pack(fill=tk.BOTH, expand=True)
            self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED)
            self.log_text.pack(fill=tk.BOTH, expand=True)

        def _status_items(self) -> list[tuple[str, str]]:
            return [(item.name, item.status) for item in status_items()]

        def _refresh_status(self) -> None:
            self.status_tree.delete(*self.status_tree.get_children())
            for item, status in self._status_items():
                self.status_tree.insert("", tk.END, text=item, values=(status,))

        def _start_install(self) -> None:
            if self.install_thread and self.install_thread.is_alive():
                messagebox.showinfo("Instalacao em andamento", "Aguarde a instalacao atual terminar.")
                return

            self.install_button.config(state=tk.DISABLED)
            self.install_thread = threading.Thread(target=self._install, daemon=True)
            self.install_thread.start()

        def _install(self) -> None:
            try:
                run_install(
                    install_system=self.install_system_var.get(),
                    run_tests=self.run_tests_var.get(),
                    output=self._write,
                    log_file=self.install_log,
                )
            except RuntimeError as exc:
                self._write(f"Instalacao interrompida: {exc}\n")
            finally:
                self.output_queue.put("__REFRESH_STATUS__")
                self.output_queue.put("__ENABLE_BUTTON__")

        def _write(self, text: str) -> None:
            self.output_queue.put(text)

        def _append_log(self, text: str) -> None:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        def _drain_output_queue(self) -> None:
            while True:
                try:
                    item = self.output_queue.get_nowait()
                except queue.Empty:
                    break

                if item == "__REFRESH_STATUS__":
                    self._refresh_status()
                elif item == "__ENABLE_BUTTON__":
                    self.install_button.config(state=tk.NORMAL)
                else:
                    self._append_log(item)

            self.after(100, self._drain_output_queue)

    return InstallerApp


def run_gui() -> int:
    InstallerApp = create_installer_app_class()
    app = InstallerApp()
    app.mainloop()
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Instalador do myAgileKit.")
    parser.add_argument("--gui", action="store_true", help="Abre a interface grafica do instalador.")
    parser.add_argument("--cli", action="store_true", help="Executa instalacao pelo terminal.")
    parser.add_argument("--check", action="store_true", help="Mostra diagnostico do ambiente e sai.")
    parser.add_argument(
        "--install-system",
        action="store_true",
        help="Permite apt-get para python3-tk e ffmpeg quando estiverem ausentes.",
    )
    parser.add_argument("--skip-tests", action="store_true", help="Nao roda unittest depois da instalacao.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    selected_modes = sum(bool(value) for value in (args.gui, args.cli, args.check))
    if selected_modes > 1:
        parser.error("use apenas um modo: --gui, --cli ou --check")

    if args.check:
        return run_check()

    if args.cli:
        def cli_output(text: str) -> None:
            print(text, end="")

        try:
            log_file = run_install(install_system=args.install_system, run_tests=not args.skip_tests, output=cli_output)
        except RuntimeError as exc:
            print(f"Instalacao interrompida: {exc}", file=sys.stderr)
            return 1
        print(f"Instalacao finalizada. Log: {log_file.relative_to(PROJECT_ROOT)}")
        return 0

    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
