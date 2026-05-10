"""Small process helpers shared by GUI and installer code."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

from .paths import PROJECT_ROOT

OutputWriter = Callable[[str], None]


def run_streamed(
    command: list[str],
    *,
    cwd: Path = PROJECT_ROOT,
    output: OutputWriter | None = None,
    log_file: Path | None = None,
) -> int:
    if output is not None:
        output("$ " + " ".join(command) + "\n")
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write("$ " + " ".join(command) + "\n")

    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    assert process.stdout is not None
    for line in process.stdout:
        if output is not None:
            output(line)
        if log_file is not None:
            with log_file.open("a", encoding="utf-8") as handle:
                handle.write(line)

    return process.wait()
