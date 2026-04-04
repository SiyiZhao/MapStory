"""CLI 子包。"""

from .interactive import interactive
from .main import build_parser, dispatch, main

__all__ = ["build_parser", "dispatch", "interactive", "main"]
