"""Shared Rich console instance and output helpers for vm_tool CLI."""

from rich.console import Console
from rich.theme import Theme

_theme = Theme(
    {
        "success": "bold green",
        "error": "bold red",
        "warning": "yellow",
        "info": "cyan",
        "dim": "dim white",
        "host": "bold magenta",
        "highlight": "bold white",
    }
)

console = Console(theme=_theme)


def success(msg: str) -> None:
    console.print(f"[success]✅ {msg}[/success]")


def error(msg: str) -> None:
    console.print(f"[error]❌ {msg}[/error]")


def warning(msg: str) -> None:
    console.print(f"[warning]⚠️  {msg}[/warning]")


def info(msg: str) -> None:
    console.print(f"[info]{msg}[/info]")
