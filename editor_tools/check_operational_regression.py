"""CLI guard for myAgileKit operational regressions."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_unittest_command(*, pattern: str = "test*.py") -> list[str]:
    return [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        pattern,
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Valida a saude operacional dos mini sistemas do myAgileKit.",
    )
    parser.add_argument(
        "--pattern",
        default="test*.py",
        help="Padrao de arquivos de teste usado pelo unittest discovery.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o comando de validacao sem executar.",
    )
    args = parser.parse_args(argv)

    command = build_unittest_command(pattern=args.pattern)
    if args.dry_run:
        print(" ".join(command))
        return 0

    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
