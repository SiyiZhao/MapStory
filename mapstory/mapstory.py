#!/usr/bin/env python3
"""MapStory 兼容入口模块。"""

from . import EventStore, InputValidationError, interactive, main

__all__ = ["EventStore", "InputValidationError", "main", "interactive"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        interactive()
    else:
        main()
