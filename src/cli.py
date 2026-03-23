"""Интерфейс командной строки для обработчика задач.""" 
from pathlib import Path
from typing import Any

import typer
from typer import Typer

from src.inbox.core import TaskProcessor
from src.sources.repository import REGISTRY

cli = Typer(no_args_is_help=True)


@cli.command("plugins")
def plugins_list() -> None:
    """Показать список доступных плагинов источников задач."""
    typer.echo("Available plugins:")
    for name in sorted(REGISTRY):
        typer.echo(name)


def _build_sources(stdin: bool, jsonl: list[Path]) -> list[Any]:
    """Создать экземпляры источников на основе аргументов командной строки."""
    sources: list[Any] = []
    if stdin:
        sources.append(REGISTRY["stdin"]())
    for path in jsonl:
        sources.append(REGISTRY["file-jsonl"](path))
    return sources


@cli.command("read")
def read(
    stdin: bool = typer.Option(False, "--stdin", help="Read messages from stdin"),
    jsonl: list[Path] = typer.Option(
        help="Read messages from stdin",
        default_factory=list,
        exists=True,
        dir_okay=False,
        readable=True,
    ),
    contains: str | None = typer.Option(None, "--contains", help="Substring filter"),
)->None:
    """Обработать задачи из указанных источников."""
    raw_sources = _build_sources(stdin, jsonl)
    inbox = TaskProcessor(raw_sources)
    numbers = 0
    for task in inbox.iter_task():  
        if contains and contains not in str(task.payload):
            continue
        numbers += 1
        typer.echo(f"[{task.id}] {task.payload}")
    typer.echo(f"\nTotal tasks: {numbers}")
