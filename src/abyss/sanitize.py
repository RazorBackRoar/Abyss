from __future__ import annotations

import re
import unicodedata
from pathlib import Path


CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")
WHITESPACE_RE = re.compile(r"\s+")
UNDERSCORE_RE = re.compile(r"_+")

# macOS forbids "/" and NUL in file names. Finder also treats ":" specially.
BAD_FILENAME_CHARS = {
    "/",
    "\x00",
    ":",
    "\\",
    "|",
    "?",
    "*",
    "<",
    ">",
    '"',
}


def sanitize_stem(value: str, *, fallback: str = "file", max_length: int = 160) -> str:
    """Return a filesystem-safe filename stem without an extension."""
    text = unicodedata.normalize("NFKC", value)
    text = CONTROL_CHARS_RE.sub("", text)

    cleaned_chars: list[str] = []
    for char in text:
        if char in BAD_FILENAME_CHARS:
            cleaned_chars.append("_")
        else:
            cleaned_chars.append(char)

    text = "".join(cleaned_chars)
    text = WHITESPACE_RE.sub("_", text)
    text = UNDERSCORE_RE.sub("_", text)
    text = text.strip(" ._")

    if not text:
        text = fallback

    # Avoid creating hidden dotfiles from user media names.
    text = text.lstrip(".")

    if not text:
        text = fallback

    if len(text) > max_length:
        text = text[:max_length].rstrip(" ._")

    return text or fallback


def safe_unique_output_path(directory: Path, stem: str, suffix: str) -> Path:
    """Return a unique output path in directory."""
    directory = directory.resolve()
    clean_stem = sanitize_stem(stem)
    suffix = suffix.lower()

    candidate = directory / f"{clean_stem}{suffix}"
    if not candidate.exists():
        return candidate

    for index in range(1, 10_000):
        candidate = directory / f"{clean_stem}-{index:03d}{suffix}"
        if not candidate.exists():
            return candidate

    raise RuntimeError(f"Could not create unique output path for {directory / clean_stem}")


def safe_temp_path(final_path: Path) -> Path:
    """Return a temporary path in the same directory as final_path."""
    parent = final_path.parent
    stem = final_path.stem
    suffix = final_path.suffix

    for index in range(1, 10_000):
        temp = parent / f".{stem}.abyss-tmp-{index:03d}{suffix}"
        if not temp.exists():
            return temp

    raise RuntimeError(f"Could not create temporary path for {final_path}")


def resolve_drop_path(path_text: str) -> Path | None:
    """Convert a dropped path string into a resolved Path."""
    try:
        path = Path(path_text).expanduser().resolve()
    except OSError:
        return None

    if not path.exists():
        return None

    if not path.is_file() and not path.is_dir():
        return None

    return path
