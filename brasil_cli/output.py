"""Rich output formatting for CLI results."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

_json_mode: bool = False


def set_json_mode(val: bool) -> None:
    global _json_mode
    _json_mode = val


def _dump(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_table(
    title: str,
    columns: list[str],
    rows: list[list[str]],
    *,
    caption: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    if _json_mode:
        out: dict[str, Any] = {"title": title, "data": [dict(zip(columns, row)) for row in rows]}
        if meta:
            out["_pagination"] = meta
        _dump(out)
        return
    table = Table(title=title, caption=caption, show_lines=True, border_style="dim")
    for col in columns:
        table.add_column(col, style="cyan", overflow="fold")
    for row in rows:
        table.add_row(*[str(v) for v in row])
    console.print(table)


def print_kv(title: str, data: dict[str, Any]) -> None:
    if _json_mode:
        _dump({"title": title, "data": data})
        return
    lines: list[str] = []
    for k, v in data.items():
        lines.append(f"[bold]{k}:[/bold] {v}")
    console.print(Panel("\n".join(lines), title=title, border_style="blue"))


def print_series(title: str, items: list[dict[str, str]], key_data: str = "data", key_valor: str = "valor") -> None:
    if _json_mode:
        _dump({"title": title, "data": items})
        return
    if not items:
        console.print(f"[yellow]Nenhum dado encontrado para '{title}'[/yellow]")
        return
    table = Table(title=title, show_lines=False, border_style="dim")
    table.add_column("Data", style="cyan")
    table.add_column("Valor", style="green", justify="right")
    for item in items:
        table.add_row(item.get(key_data, ""), item.get(key_valor, ""))
    console.print(table)


def print_list(title: str, items: list[dict[str, Any]], fields: list[str]) -> None:
    if _json_mode:
        _dump({"title": title, "data": items})
        return
    if not items:
        console.print(f"[yellow]Nenhum resultado para '{title}'[/yellow]")
        return
    table = Table(title=title, show_lines=True, border_style="dim")
    for f in fields:
        table.add_column(f, overflow="fold")
    for item in items:
        table.add_row(*[str(item.get(f, "")) for f in fields])
    console.print(table)


def print_error(msg: str) -> None:
    if _json_mode:
        _dump({"error": msg})
        return
    console.print(f"[bold red]Erro:[/bold red] {msg}")


def print_success(msg: str) -> None:
    if _json_mode:
        _dump({"success": msg})
        return
    console.print(f"[bold green]✓[/bold green] {msg}")


def print_info(msg: str) -> None:
    if _json_mode:
        _dump({"info": msg})
        return
    console.print(f"[dim]{msg}[/dim]")
