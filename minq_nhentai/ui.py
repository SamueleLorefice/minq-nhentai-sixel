import threading
from typing import Any, TypeVar

from rich.console import Console
from rich.prompt import Prompt

console = Console(stderr=False)

T = TypeVar("T")


def input(msg: str, if_interrupted: T) -> str | T:
    try:
        result: str = Prompt.ask(msg)
        return result
    except KeyboardInterrupt:
        return if_interrupted


_print_tmp_last_msg: str = ""
_print_tmp_last_count: int = 1
_print_tmp_last_len: int = 0
_print_tmp_lock: threading.Lock = threading.Lock()


def _clear_tmp_line_if_any() -> None:
    global _print_tmp_last_len
    if _print_tmp_last_len > 0:
        console.print(" " * _print_tmp_last_len, end="\r", markup=False)


def print(*a: Any, **kw: Any) -> None:
    with _print_tmp_lock:
        global _print_tmp_last_msg
        global _print_tmp_last_count
        global _print_tmp_last_len
        _clear_tmp_line_if_any()
        _print_tmp_last_msg = ""
        _print_tmp_last_count = 1
        _print_tmp_last_len = 0
        console.print(*a, **kw)


def print_tmp(msg: str) -> None:
    with _print_tmp_lock:
        global _print_tmp_last_msg
        global _print_tmp_last_count
        global _print_tmp_last_len
        msg = msg.replace("\n", " ")

        _clear_tmp_line_if_any()
        _print_tmp_last_len = len(msg)

        if msg == _print_tmp_last_msg:
            _print_tmp_last_count += 1
            count_prefix: str = f"({_print_tmp_last_count}) "
            console.print(count_prefix, end="", markup=False)
            _print_tmp_last_len += len(count_prefix)
        else:
            _print_tmp_last_count = 1

        _print_tmp_last_msg = msg

        console.print(msg, end="\r", markup=False, highlight=False)


def alert(msg: str = "") -> None:
    print(msg)
    input("[bold yellow]PRESS ENTER TO CONTINUE[/]", -1)


def error(msg: str) -> None:
    print(f"[bold red]\u2718 {msg}[/]")


def warn(msg: str) -> None:
    print(f"[bold yellow]\u26a0 {msg}[/]")


def success(msg: str) -> None:
    print(f"[bold green]\u2714 {msg}[/]")


def info(msg: str) -> None:
    print(f"[bold blue]\u2139 {msg}[/]")


def hint(msg: str) -> None:
    print(f"[dim italic]{msg}[/]")
