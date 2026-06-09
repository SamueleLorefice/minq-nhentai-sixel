import dataclasses
import enum
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from .constants import IMAGE_BACKEND_AUTO, IMAGE_BACKEND_DEFAULT, IMAGE_BACKEND_SIXEL, IMAGE_BACKEND_VIU
from .ui import print


class ImageBackend(enum.Enum):
    AUTO = "auto"
    SIXEL = "sixel"
    VIU = "viu"


@dataclasses.dataclass
class _BackendState:
    requested: str = IMAGE_BACKEND_DEFAULT
    resolved: str | None = None
    fallback_done: bool = False


_state: _BackendState = _BackendState()


def _is_webp(path: str) -> bool:
    try:
        header: bytes = Path(path).read_bytes()[:12]
    except OSError:
        return False

    return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"


def _render_with_webp_transcode_fallback(path: str, backend: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path: str = tmp.name

    try:
        with Image.open(path) as img:
            img.save(tmp_path, format="PNG")

        if backend == IMAGE_BACKEND_SIXEL:
            cmd: list[str] = ["img2sixel", tmp_path]
        elif backend == IMAGE_BACKEND_VIU:
            cmd = ["viu", tmp_path]
        else:
            raise RuntimeError(f"Unsupported image backend: {backend}")

        subprocess.run(cmd, check=True, capture_output=False)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _env_truthy(name: str) -> bool:
    value: str | None = os.getenv(name)
    if value is None:
        return False
    return value.strip().lower() in ("1", "true", "yes", "on")


def terminal_supports_sixel() -> bool:
    if _env_truthy("MINQ_NHENTAI_NO_SIXEL"):
        return False
    if _env_truthy("MINQ_NHENTAI_SIXEL"):
        return True

    term: str = (os.getenv("TERM") or "").lower()
    term_program: str = (os.getenv("TERM_PROGRAM") or "").lower()

    if "sixel" in term:
        return True
    if term.startswith("mlterm"):
        return True
    if "yaft" in term:
        return True
    if term_program in ("wezterm", "mintty"):
        return True
    return bool(os.getenv("WT_SESSION"))


def _has_bin(name: str) -> bool:
    return shutil.which(name) is not None


def _resolve_image_backend(requested: str) -> str:
    if requested == IMAGE_BACKEND_VIU:
        if not _has_bin("viu"):
            raise RuntimeError("Requested image backend viu, but executable was not found in PATH")
        return IMAGE_BACKEND_VIU

    if requested == IMAGE_BACKEND_SIXEL:
        if not _has_bin("img2sixel"):
            raise RuntimeError("Requested image backend sixel, but img2sixel was not found in PATH")
        if not terminal_supports_sixel():
            raise RuntimeError("Requested image backend sixel, but terminal does not look sixel-capable")
        return IMAGE_BACKEND_SIXEL

    if requested != IMAGE_BACKEND_AUTO:
        raise RuntimeError(f"Unknown image backend: {requested}")

    if _has_bin("img2sixel") and terminal_supports_sixel():
        return IMAGE_BACKEND_SIXEL
    if _has_bin("viu"):
        return IMAGE_BACKEND_VIU
    if _has_bin("img2sixel"):
        return IMAGE_BACKEND_SIXEL

    raise RuntimeError("No supported image backend found. Install viu or img2sixel (libsixel).")


def configure_image_backend(requested: str) -> None:
    _state.requested = requested
    _state.resolved = _resolve_image_backend(requested)
    _state.fallback_done = False
    print(f"Using image backend: {_state.resolved} (requested: {requested})")


def _render_with_backend(path: str, backend: str) -> None:
    if backend == IMAGE_BACKEND_SIXEL:
        cmd = ["img2sixel", path]
    elif backend == IMAGE_BACKEND_VIU:
        cmd = ["viu", path]
    else:
        raise RuntimeError(f"Unsupported image backend: {backend}")

    try:
        subprocess.run(cmd, check=True, capture_output=False)
    except subprocess.CalledProcessError:
        if _is_webp(path):
            _render_with_webp_transcode_fallback(path, backend)
            return
        raise


def render_image(path: str) -> None:
    if _state.resolved is None:
        configure_image_backend(IMAGE_BACKEND_DEFAULT)
    resolved: str | None = _state.resolved
    if resolved is None:
        raise RuntimeError("Image backend not configured")

    try:
        _render_with_backend(path, resolved)
    except subprocess.CalledProcessError as exc:
        if (
            _state.requested == IMAGE_BACKEND_AUTO
            and resolved == IMAGE_BACKEND_SIXEL
            and not _state.fallback_done
            and _has_bin("viu")
        ):
            _state.fallback_done = True
            _state.resolved = IMAGE_BACKEND_VIU
            print("Sixel render failed in auto mode, falling back to viu")
            _render_with_backend(path, _state.resolved)
            return
        raise RuntimeError(f"Image backend {resolved} failed with exit code {exc.returncode}") from exc
