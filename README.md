# Abyss

Abyss is a macOS drag-and-drop app for stripping metadata from photos and
videos. It is built with Python 3.14, PySide6, Pillow, pillow-heif, PyAV, and
PyInstaller.

![Abyss window](assets/abyss%20window.png)

## What It Does

Abyss accepts files and folders dropped onto its window. Folders are processed
recursively. Supported media files are rewritten into clean output formats:

| Input | Output |
| --- | --- |
| Images | metadata-free `.jpg` |
| Videos | metadata-free `.mp4` |
| Unsupported files | skipped |

The app does not create backup copies. It only removes an original after the
replacement file has been written, moved into place, and verified as non-empty.
If conversion fails, the original remains in place and the error is logged.

## Metadata Removal Policy

For images, Abyss opens the file with Pillow, applies EXIF orientation to the
pixels, converts the result to RGB, and writes a fresh JPEG without passing
EXIF, XMP, IPTC, ICC, PNG text chunks, or other source metadata through to the
output.

For videos, Abyss first tries to remux compatible audio/video streams into a new
MP4 container without re-encoding. This strips container and stream metadata
while preserving the original media bytes when possible. If remuxing fails, it
tries a high-quality H.264/AAC re-encode. If that also fails, the original file
is left untouched.

## Safety Rules

- Paths are resolved before processing.
- Missing paths, non-files, and non-folders are rejected.
- File names are normalized and sanitized.
- Temporary files are written in the same directory as the final output.
- Final replacement uses an atomic move.
- Originals are deleted only after the replacement exists and has a nonzero
  size.

Use disposable copies for first tests because successful conversions remove the
source files.

## Supported Extensions

Images:

```text
.jpg .jpeg .png .gif .bmp .tif .tiff .webp .heic .heif .avif
```

Videos:

```text
.mov .mp4 .m4v .avi .mkv .webm .mts .m2ts .3gp .3g2
```

Extension matching is case-insensitive.

## Run From Source

```zsh
cd /Users/home/Workspace/Apps/Abyss
uv sync
uv run abyss
```

## Build The macOS App

```zsh
cd /Users/home/Workspace/Apps/Abyss
./build_app.zsh
open dist/Abyss.app
```

The build script creates and ad-hoc signs:

```text
dist/Abyss.app
```

## Validate The Bundle

```zsh
codesign --verify --deep --strict --verbose=2 dist/Abyss.app
file dist/Abyss.app/Contents/MacOS/Abyss
```

The executable should report `arm64`.

## Workspace Commands

Abyss is wired into the RazorBackRoar `.razorcore` workflow.

```zsh
pushabyss
```

`pushabyss` saves and pushes only the Abyss app folder through `.razorcore`:

```text
/Users/home/Workspace/Apps/Abyss
```

The existing `.razorcore` `pushall` command remains available for the broader
workspace save flow and now includes Abyss as a managed Apps project.

For the shared DMG build used by the Apps workspace:

```zsh
cd /Users/home/Workspace/Apps/.razorcore
./universal-build.sh Abyss
```

That script uses the locked workspace DMG layout:

```text
window: 600 x 350
position: 200, 120
icon size: 100
app icon: 175, 150
Applications icon: 425, 150
format: UDZO
```

It builds with Python 3.14, PySide6, PyInstaller, ad-hoc signing, and the same
DMG window sizing as the other RazorBackRoar apps.

## Install Locally

```zsh
mkdir -p ~/Applications
ditto dist/Abyss.app ~/Applications/Abyss.app
open ~/Applications/Abyss.app
```

If macOS blocks the local unsigned app:

```zsh
xattr -dr com.apple.quarantine ~/Applications/Abyss.app
open ~/Applications/Abyss.app
```

## Manual Metadata Checks

Image outputs can be inspected with macOS metadata tooling:

```zsh
mdls path/to/output.jpg
```

Video container and stream metadata can be checked with PyAV:

```zsh
python - <<'PY'
from pathlib import Path
import av

path = Path("path/to/output.mp4")

with av.open(str(path)) as container:
    print("container metadata:", dict(container.metadata))
    for stream in container.streams:
        print(stream.type, stream.index, dict(stream.metadata))
PY
```

Some MP4 muxers create structural tags required for playback. Those are not the
same as preserving camera GPS, creation metadata, user tags, EXIF, XMP, or IPTC.
