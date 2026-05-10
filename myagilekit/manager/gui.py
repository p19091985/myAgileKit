"""Tkinter manager for all myAgileKit mini systems."""

from __future__ import annotations

import contextlib
import datetime as _dt
import json
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from myagilekit.core.registry import (
    PROJECT_ROOT,
    TOOL_CATALOG,
    ToolDefinition,
    build_environment_check_command,
    build_launch_command,
    build_test_command,
    build_tool_test_command,
    check_tool,
    filter_tools_by_group,
    logs_directory,
    tool_groups,
)


class Tooltip:
    """Small Tk tooltip helper for ttk/tk widgets."""

    def __init__(self, widget: tk.Widget, text: str = "", delay_ms: int = 450) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id: str | None = None
        self._window: tk.Toplevel | None = None
        self._last_x = 0
        self._last_y = 0

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Motion>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def set_text(self, text: str) -> None:
        self.text = text
        if self._window is not None:
            self._hide()

    def _schedule(self, event: tk.Event) -> None:
        self._last_x = event.x_root
        self._last_y = event.y_root
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _show(self) -> None:
        self._after_id = None
        if not self.text.strip() or self._window is not None:
            return

        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.wm_geometry(f"+{self._last_x + 14}+{self._last_y + 12}")

        label = tk.Label(
            self._window,
            text=self.text,
            justify=tk.LEFT,
            background="#fff8d8",
            foreground="#222222",
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=6,
            wraplength=420,
        )
        label.pack()

    def _hide(self, _event: tk.Event | None = None) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if self._window is not None:
            self._window.destroy()
            self._window = None


class MyAgileKitManager(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("myAgileKit Manager")
        self.geometry("980x680")
        self.minsize(860, 580)

        self.selected_tool: ToolDefinition | None = None
        self.category_var = tk.StringVar(value="Todas")
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.running_process: subprocess.Popen[str] | None = None
        self.tool_tree_tooltip: Tooltip | None = None
        self.detail_title_tooltip: Tooltip | None = None
        self.detail_status_tooltip: Tooltip | None = None
        self.detail_text_tooltip: Tooltip | None = None
        self.launch_button_tooltip: Tooltip | None = None

        self._configure_style()
        self._create_widgets()
        self._load_tools()
        self.after(100, self._drain_output_queue)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        with contextlib.suppress(tk.TclError):
            style.theme_use("clam")

        style.configure(".", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", foreground="#555555")
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Ready.TLabel", foreground="#147a33")
        style.configure("Blocked.TLabel", foreground="#a33a20")

    def _create_widgets(self) -> None:
        header = ttk.Frame(self, padding=(18, 16, 18, 8))
        header.pack(fill=tk.X)
        title_label = ttk.Label(header, text="myAgileKit Manager", style="Title.TLabel")
        title_label.pack(anchor=tk.W)
        subtitle_label = ttk.Label(
            header,
            text="Gerencie launchers, ferramentas de midia, utilitarios de sistema e checks do projeto.",
            style="Subtitle.TLabel",
        )
        subtitle_label.pack(anchor=tk.W, pady=(4, 0))
        Tooltip(
            title_label,
            "GUI principal do myAgileKit. Ela centraliza os mini sistemas do projeto, "
            "mostra o status de dependencias e abre cada ferramenta pelo catalogo.",
        )
        Tooltip(
            subtitle_label,
            "Use esta janela para escolher uma categoria, selecionar um projeto, "
            "executar a ferramenta, rodar testes ou abrir o diagnostico do ambiente.",
        )

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=18, pady=10)

        list_frame = ttk.Frame(body, padding=(0, 0, 12, 0))
        body.add(list_frame, weight=2)

        filter_row = ttk.Frame(list_frame)
        filter_row.pack(fill=tk.X, pady=(0, 8))
        category_label = ttk.Label(filter_row, text="Categoria")
        category_label.pack(side=tk.LEFT)
        self.category_filter = ttk.Combobox(
            filter_row,
            textvariable=self.category_var,
            values=("Todas", *tool_groups()),
            state="readonly",
            width=18,
        )
        self.category_filter.pack(side=tk.LEFT, padx=(8, 0))
        self.category_filter.bind("<<ComboboxSelected>>", self._on_filter_changed)
        Tooltip(category_label, "Filtra a lista de projetos pelo tipo de ferramenta.")
        Tooltip(
            self.category_filter,
            "Mostra todos os projetos ou apenas os grupos como Midia, Sistema, Editor, "
            "Windows, Jogos, Instalacao e Verificacao.",
        )

        columns = ("group", "status")
        self.tool_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse",
        )
        self.tool_tree.heading("#0", text="Ferramenta")
        self.tool_tree.heading("group", text="Grupo")
        self.tool_tree.heading("status", text="Status")
        self.tool_tree.column("#0", width=260, minwidth=220)
        self.tool_tree.column("group", width=120, anchor=tk.CENTER)
        self.tool_tree.column("status", width=110, anchor=tk.CENTER)
        self.tool_tree.pack(fill=tk.BOTH, expand=True)
        self.tool_tree.bind("<<TreeviewSelect>>", self._on_tool_selected)
        self.tool_tree.bind("<Motion>", self._on_tool_tree_motion, add="+")
        self.tool_tree_tooltip = Tooltip(
            self.tool_tree,
            "Passe o mouse sobre um projeto para ver o que ele faz e como sera aberto.",
        )

        detail_frame = ttk.Frame(body)
        body.add(detail_frame, weight=3)

        self.detail_title = ttk.Label(detail_frame, text="Selecione uma ferramenta", style="Title.TLabel")
        self.detail_title.pack(anchor=tk.W)

        self.detail_status = ttk.Label(detail_frame, text="")
        self.detail_status.pack(anchor=tk.W, pady=(4, 8))

        self.detail_text = tk.Text(detail_frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        self.detail_title_tooltip = Tooltip(
            self.detail_title,
            "Nome do projeto selecionado no catalogo.",
        )
        self.detail_status_tooltip = Tooltip(
            self.detail_status,
            "Mostra se a ferramenta selecionada pode ser executada agora.",
        )
        self.detail_text_tooltip = Tooltip(
            self.detail_text,
            "Resumo do projeto selecionado: funcao, grupo, arquivo de entrada, "
            "comando padrao, teste associado e pendencias encontradas.",
        )

        button_row = ttk.Frame(detail_frame)
        button_row.pack(fill=tk.X, pady=(10, 8))
        self.launch_button = ttk.Button(
            button_row,
            text="Executar selecionado",
            style="Action.TButton",
            command=self._launch_selected_tool,
            state=tk.DISABLED,
        )
        self.launch_button.pack(side=tk.LEFT)
        selected_test_button = ttk.Button(
            button_row,
            text="Teste selecionado",
            command=self._run_selected_tool_test,
        )
        selected_test_button.pack(side=tk.LEFT, padx=8)
        all_tests_button = ttk.Button(
            button_row,
            text="Todos os testes",
            command=self._run_test_suite,
        )
        all_tests_button.pack(side=tk.LEFT)
        diagnostic_button = ttk.Button(
            button_row,
            text="Diagnostico",
            command=self._run_environment_check,
        )
        diagnostic_button.pack(side=tk.LEFT, padx=8)
        refresh_button = ttk.Button(
            button_row,
            text="Atualizar status",
            command=self._load_tools,
        )
        refresh_button.pack(side=tk.LEFT)
        self.launch_button_tooltip = Tooltip(
            self.launch_button,
            "Abre o projeto selecionado usando o comando padrao mostrado no painel.",
        )
        Tooltip(
            selected_test_button,
            "Executa o teste/check configurado para o projeto selecionado.",
        )
        Tooltip(
            all_tests_button,
            "Executa a suite completa de testes unitarios centralizada em tests/.",
        )
        Tooltip(
            diagnostic_button,
            "Roda o diagnostico do instalador para conferir ambiente, dependencias "
            "Python e comandos de sistema.",
        )
        Tooltip(
            refresh_button,
            "Recarrega o catalogo visual e recalcula o status das ferramentas.",
        )

        log_frame = ttk.LabelFrame(self, text="Saida", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=18, pady=(0, 14))
        self.output_text = tk.Text(log_frame, height=9, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        Tooltip(
            self.output_text,
            "Area de saida dos testes, diagnosticos e comandos executados pela GUI.",
        )

    def _load_tools(self) -> None:
        selected = self.selected_tool.identifier if self.selected_tool else None
        self.tool_tree.delete(*self.tool_tree.get_children())
        visible_tools = filter_tools_by_group(self.category_var.get())

        for tool in visible_tools:
            ready, _ = check_tool(tool)
            item_id = tool.identifier
            self.tool_tree.insert(
                "",
                tk.END,
                iid=item_id,
                text=tool.name,
                values=(tool.group, "OK" if ready else "Pendente"),
            )
            if selected == item_id:
                self.tool_tree.selection_set(item_id)

        if not self.tool_tree.selection() and visible_tools:
            first = visible_tools[0].identifier
            self.tool_tree.selection_set(first)
            self.tool_tree.focus(first)
            self._on_tool_selected()
        elif not visible_tools:
            self.selected_tool = None
            self.launch_button.config(state=tk.DISABLED)
            self.detail_status.config(text="")
            self.detail_title.config(text="Nenhuma ferramenta nesta categoria")
            self._set_detail_text("Selecione outra categoria para ver ferramentas.")

    def _on_filter_changed(self, _event: tk.Event | None = None) -> None:
        self._load_tools()

    def _on_tool_tree_motion(self, event: tk.Event) -> None:
        if self.tool_tree_tooltip is None:
            return

        identifier = self.tool_tree.identify_row(event.y)
        tool = next((item for item in TOOL_CATALOG if item.identifier == identifier), None)
        if tool is None:
            self.tool_tree_tooltip.set_text(
                "Lista dos projetos registrados. Passe o mouse sobre uma linha para "
                "ver a funcao da ferramenta, comando de abertura e pendencias."
            )
            return

        self.tool_tree_tooltip.set_text(self._format_tool_tooltip(tool))

    def _on_tool_selected(self, _event: tk.Event | None = None) -> None:
        selection = self.tool_tree.selection()
        if not selection:
            return

        identifier = selection[0]
        self.selected_tool = next((tool for tool in TOOL_CATALOG if tool.identifier == identifier), None)
        if self.selected_tool is None:
            return

        ready, problems = check_tool(self.selected_tool)
        command = " ".join(build_launch_command(self.selected_tool))
        test_target = self.selected_tool.test_target or "sem teste especifico"

        self.detail_title.config(text=self.selected_tool.name)
        if ready:
            self.detail_status.config(text="Status: pronto para executar", style="Ready.TLabel")
            self.launch_button.config(state=tk.NORMAL)
        else:
            self.detail_status.config(text="Status: precisa de ajuste", style="Blocked.TLabel")
            self.launch_button.config(state=tk.DISABLED)

        lines = [
            self.selected_tool.description,
            "",
            f"Grupo: {self.selected_tool.group}",
            f"Entrada: {self.selected_tool.entrypoint}",
            f"Comando padrao: {command}",
            f"Teste/check: {test_target}",
        ]
        if self.selected_tool.group == "Windows" and not self.selected_tool.supports_current_platform():
            lines.extend(["", "Aviso: ferramenta Windows indisponivel neste sistema."])
        if problems:
            lines.extend(["", "Pendencias:"])
            lines.extend(f"- {problem}" for problem in problems)

        self._set_detail_text("\n".join(lines))
        tooltip_text = self._format_tool_tooltip(self.selected_tool)
        if self.detail_title_tooltip is not None:
            self.detail_title_tooltip.set_text(tooltip_text)
        if self.detail_status_tooltip is not None:
            self.detail_status_tooltip.set_text(
                "Status da ferramenta selecionada.\n\n" + tooltip_text
            )
        if self.detail_text_tooltip is not None:
            self.detail_text_tooltip.set_text(tooltip_text)
        if self.launch_button_tooltip is not None:
            self.launch_button_tooltip.set_text(
                "Executa este projeto:\n\n" + tooltip_text
            )

    def _format_tool_tooltip(self, tool: ToolDefinition) -> str:
        ready, problems = check_tool(tool)
        status = "pronto para executar" if ready else "precisa de ajuste"
        command = " ".join(build_launch_command(tool))
        test_target = tool.test_target or "sem teste especifico"
        lines = [
            tool.name,
            tool.description,
            "",
            f"Grupo: {tool.group}",
            f"Status: {status}",
            f"Entrada: {tool.entrypoint}",
            f"Comando: {command}",
            f"Teste/check: {test_target}",
        ]
        if problems:
            lines.extend(["", "Pendencias:"])
            lines.extend(f"- {problem}" for problem in problems)
        return "\n".join(lines)

    def _set_detail_text(self, text: str) -> None:
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, text)
        self.detail_text.config(state=tk.DISABLED)

    def _append_output(self, text: str) -> None:
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def _launch_selected_tool(self) -> None:
        if self.selected_tool is None:
            return

        ready, problems = check_tool(self.selected_tool)
        if not ready:
            messagebox.showwarning("Pendencias", "\n".join(problems))
            return

        command = build_launch_command(self.selected_tool)
        self._append_output(f"\n$ {' '.join(command)}\n")
        try:
            subprocess.Popen(command, cwd=self.selected_tool.working_dir_path)
            self._record_history("launch", command, self.selected_tool)
        except OSError as exc:
            messagebox.showerror("Erro ao executar", str(exc))

    def _run_selected_tool_test(self) -> None:
        if self.selected_tool is None:
            return
        if self.running_process is not None:
            messagebox.showinfo("Em execucao", "Ja existe um processo rodando.")
            return

        command = build_tool_test_command(self.selected_tool)
        self._append_output(f"\n$ {' '.join(command)}\n")
        self._record_history("tool-test", command, self.selected_tool)
        thread = threading.Thread(target=self._run_command_capture, args=(command,), daemon=True)
        thread.start()

    def _run_test_suite(self) -> None:
        if self.running_process is not None:
            messagebox.showinfo("Em execucao", "Ja existe um processo de testes rodando.")
            return

        command = build_test_command()
        self._append_output(f"\n$ {' '.join(command)}\n")
        self._record_history("test-suite", command)
        thread = threading.Thread(target=self._run_command_capture, args=(command,), daemon=True)
        thread.start()

    def _run_environment_check(self) -> None:
        if self.running_process is not None:
            messagebox.showinfo("Em execucao", "Ja existe um processo rodando.")
            return

        command = build_environment_check_command()
        self._append_output(f"\n$ {' '.join(command)}\n")
        self._record_history("diagnostic", command)
        thread = threading.Thread(target=self._run_command_capture, args=(command,), daemon=True)
        thread.start()

    def _run_command_capture(self, command: list[str]) -> None:
        try:
            self.running_process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert self.running_process.stdout is not None
            for line in self.running_process.stdout:
                self.output_queue.put(line)
            return_code = self.running_process.wait()
            self.output_queue.put(f"\nProcesso finalizado com codigo {return_code}.\n")
        except OSError as exc:
            self.output_queue.put(f"\nErro: {exc}\n")
        finally:
            self.running_process = None

    def _record_history(
        self,
        action: str,
        command: list[str],
        tool: ToolDefinition | None = None,
    ) -> None:
        event = {
            "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
            "action": action,
            "tool": tool.identifier if tool else None,
            "command": command,
        }
        history_path = logs_directory() / "execution_history.jsonl"
        with contextlib.suppress(OSError), history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _drain_output_queue(self) -> None:
        while True:
            try:
                self._append_output(self.output_queue.get_nowait())
            except queue.Empty:
                break
        self.after(100, self._drain_output_queue)


def main() -> None:
    app = MyAgileKitManager()
    app.mainloop()


if __name__ == "__main__":
    main()
