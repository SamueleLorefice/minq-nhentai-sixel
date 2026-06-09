import builtins
import io
import threading
from typing import Any, TypeVar

_input: Any = builtins.input

T = TypeVar("T")


def input(msg: str, if_interrupted: T) -> str | T:
    try:
        result: str = _input(msg)
        return result
    except KeyboardInterrupt:
        return if_interrupted


_print: Any = builtins.print
_print_tmp_last_msg: str = ""
_print_tmp_last_count: int = 1
_print_tmp_last_len: int = 0
_print_tmp_lock: threading.Lock = threading.Lock()


def _clear_tmp_line_if_any() -> None:
    global _print_tmp_last_len
    if _print_tmp_last_len > 0:
        _print(" " * _print_tmp_last_len, end="\r")


def print(*a: Any, **kw: Any) -> None:
    _print_tmp_lock.acquire()
    global _print_tmp_last_msg
    global _print_tmp_last_count
    global _print_tmp_last_len
    fake_stdout = io.StringIO()
    file_bak = kw.get("file")
    _print(*a, **kw, file=fake_stdout)
    if file_bak is not None:
        kw["file"] = file_bak
    _clear_tmp_line_if_any()
    _print_tmp_last_msg = ""
    _print_tmp_last_count = 1
    _print_tmp_last_len = 0
    _print(*a, **kw)
    _print_tmp_lock.release()


def print_tmp(msg: str) -> None:
    _print_tmp_lock.acquire()
    global _print_tmp_last_msg
    global _print_tmp_last_count
    global _print_tmp_last_len
    msg = msg.replace("\n", " ")

    _clear_tmp_line_if_any()
    _print_tmp_last_len = len(msg)

    if msg == _print_tmp_last_msg:
        _print_tmp_last_count += 1
        _print(f"({_print_tmp_last_count}) ", end="")
        _print_tmp_last_len += 3 + len(str(_print_tmp_last_count))
    else:
        _print_tmp_last_count = 1

    _print_tmp_last_msg = msg

    _print(msg, end="")
    _print("\r", end="", flush=True)

    _print_tmp_lock.release()


def alert(msg: str = "") -> None:
    print(msg)
    input("PRESS ENTER TO CONTINUE", -1)
