"""Project verification pipeline for myAgileKit."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent


def _run(command: list[str]) -> int:
    print("$ " + " ".join(command))
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Executa a pipeline local do myAgileKit.")
    parser.add_argument(
        "--with-ruff",
        action="store_true",
        help="Depois dos testes, executa Ruff incremental se estiver instalado.",
    )
    parser.add_argument(
        "--no-xvfb",
        action="store_true",
        help="Nao usar xvfb-run na smoke suite.",
    )
    args = parser.parse_args(argv)

    smoke_command = [
        sys.executable,
        str(SCRIPT_DIR / "run_smoke_suite.py"),
        *(("--no-xvfb",) if args.no_xvfb else ()),
    ]
    result = _run(smoke_command)
    if result != 0:
        return result

    if args.with_ruff:
        ruff_command = [sys.executable, str(SCRIPT_DIR / "run_incremental_ruff.py")]
        return _run(ruff_command)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
