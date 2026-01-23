from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

THEME = Theme(
    {
        "info": "bold cyan",
        "warn": "bold yellow",
        "err": "bold red",
        "ok": "bold green",
        "dim": "dim",
    }
)

console = Console(theme=THEME)
