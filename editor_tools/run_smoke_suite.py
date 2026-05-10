"""Local smoke runner for the myAgileKit test suite."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = PROJECT_ROOT / "tests"


def build_smoke_command(*, use_xvfb: bool = True) -> list[str]:
    unittest_command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(TESTS_DIR.relative_to(PROJECT_ROOT)),
    ]

    if use_xvfb and platform.system() == "Linux" and shutil.which("xvfb-run"):
        return ["xvfb-run", "-a", *unittest_command]
    return unittest_command


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Executa a smoke suite local do myAgileKit.")
    parser.add_argument(
        "--no-xvfb",
        action="store_true",
        help="Nao usar xvfb-run mesmo quando estiver disponivel no Linux.",
    )
    args = parser.parse_args(argv)

    command = build_smoke_command(use_xvfb=not args.no_xvfb)
    return subprocess.run(command, cwd=PROJECT_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
