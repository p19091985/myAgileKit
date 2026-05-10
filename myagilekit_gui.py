"""Compatibility entrypoint for the myAgileKit manager GUI."""

from __future__ import annotations

from myagilekit.manager.gui import MyAgileKitManager, main

__all__ = ["MyAgileKitManager", "main"]


if __name__ == "__main__":
    main()
