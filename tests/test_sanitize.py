from pathlib import Path

from abyss.sanitize import (
    resolve_drop_path,
    safe_temp_path,
    safe_unique_output_path,
    sanitize_stem,
)


def test_sanitize_stem_replaces_bad_chars_and_whitespace() -> None:
    value = "  my:/bad*name   "
    assert sanitize_stem(value) == "my_bad_name"


def test_sanitize_stem_uses_fallback_for_empty_or_hidden() -> None:
    assert sanitize_stem("...") == "file"
    assert sanitize_stem(".hidden") == "hidden"


def test_safe_unique_output_path_appends_counter_when_taken(tmp_path: Path) -> None:
    first = tmp_path / "sample.jpg"
    first.write_bytes(b"x")

    output = safe_unique_output_path(tmp_path, "sample", ".jpg")
    assert output.name == "sample-001.jpg"


def test_safe_temp_path_uses_same_directory(tmp_path: Path) -> None:
    final_path = tmp_path / "photo.jpg"
    temp_path = safe_temp_path(final_path)

    assert temp_path.parent == tmp_path
    assert temp_path.name.startswith(".photo.abyss-tmp-")
    assert temp_path.suffix == ".jpg"


def test_resolve_drop_path_for_file_and_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "image.jpg"
    file_path.write_bytes(b"data")
    dir_path = tmp_path / "folder"
    dir_path.mkdir()

    assert resolve_drop_path(str(file_path)) == file_path.resolve()
    assert resolve_drop_path(str(dir_path)) == dir_path.resolve()
    assert resolve_drop_path(str(tmp_path / "missing")) is None
