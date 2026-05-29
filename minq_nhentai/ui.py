import builtins
import io
import threading

_input = builtins.input


def input(msg, if_interrupted):
    try:
        return _input(msg)
    except KeyboardInterrupt:
        return if_interrupted


_print = builtins.print
_print_tmp_last_msg = ""
_print_tmp_last_count = 1
_print_tmp_last_len = 0
_print_tmp_lock = threading.Lock()


def print(*a, **kw):
    _print_tmp_lock.acquire()
    global _print_tmp_last_msg
    global _print_tmp_last_count
    global _print_tmp_last_len
    fake_stdout = io.StringIO()
    file_bak = kw["file"] if "file" in kw else None
    _print(*a, **kw, file=fake_stdout)
    if file_bak is not None:
        kw["file"] = file_bak
    out = fake_stdout.getvalue()
    first_line_len = len(out.split("\n")[0])
    if first_line_len < _print_tmp_last_len:
        _print(" " * _print_tmp_last_len, end="\r")
    _print_tmp_last_msg = ""
    _print_tmp_last_count = 1
    _print_tmp_last_len = 0
    _print(*a, **kw)
    _print_tmp_lock.release()


def print_tmp(msg):
    _print_tmp_lock.acquire()
    global _print_tmp_last_msg
    global _print_tmp_last_count
    global _print_tmp_last_len
    assert "\n" not in msg

    last_len = _print_tmp_last_len
    _print_tmp_last_len = len(msg)

    if msg == _print_tmp_last_msg:
        _print_tmp_last_count += 1
        _print(f"({_print_tmp_last_count}) ", end="")
        _print_tmp_last_len += 3 + len(str(_print_tmp_last_count))
    else:
        _print_tmp_last_count = 1

    _print_tmp_last_msg = msg

    _print(msg, end="")
    if last_len > len(msg):
        _print(" " * (last_len - len(msg)), end="")
    _print("\r", end="", flush=True)

    _print_tmp_lock.release()


def alert(msg=""):
    print(msg)
    input("PRESS ENTER TO CONTINUE", -1)

