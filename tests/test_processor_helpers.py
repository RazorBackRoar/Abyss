from pathlib import Path

from abyss.processor import is_image, is_video, iter_media_files


def test_is_image_and_is_video_are_case_insensitive() -> None:
    assert is_image(Path("photo.JPG"))
    assert is_video(Path("clip.MOV"))
    assert not is_image(Path("notes.txt"))
    assert not is_video(Path("notes.txt"))


def test_iter_media_files_includes_files_and_directory_contents(tmp_path: Path) -> None:
    file_direct = tmp_path / "direct.jpg"
    file_direct.write_bytes(b"x")

    folder = tmp_path / "folder"
    folder.mkdir()
    nested_file = folder / "nested.mov"
    nested_file.write_bytes(b"y")
    nested_subdir = folder / "sub"
    nested_subdir.mkdir()
    nested_deep_file = nested_subdir / "deep.png"
    nested_deep_file.write_bytes(b"z")

    found = list(iter_media_files([file_direct, folder]))
    expected = [file_direct, nested_file, nested_deep_file]

    assert found == expected
