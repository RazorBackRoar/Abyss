# Abyss

Abyss is a macOS drag-and-drop media metadata scrubber built with Python,
PySide6, Pillow, pillow-heif, PyAV, and PyInstaller.

The app launches with the Abyss artwork in `assets/abyss window.png` and uses
the generated `assets/AppIcon.icns` icon in the macOS bundle.

It is intentionally destructive after successful conversion:

- dropped folders are processed recursively,
- dropped files are processed directly,
- supported images are rewritten as metadata-free `.jpg`,
- supported videos are rewritten as metadata-free `.mp4`,
- originals are removed only after the replacement output exists and has a
  nonzero size,
- unsupported files are skipped,
- failed conversions leave the original in place.

Use disposable copies for first tests.

## Requirements

- macOS on Apple Silicon
- Python 3.14, preferably `/opt/homebrew/bin/python3.14`

Python packages are listed in `requirements.txt`.

## Run From Source

```zsh
cd /Users/home/Workspace/Apps/Abyss
uv sync
uv run abyss
```

If Python 3.14 is available as `python3.14` instead of the Homebrew path, use
that interpreter for the virtual environment.

## Build The App

```zsh
cd /Users/home/Workspace/Apps/Abyss
./build_app.zsh
open dist/Abyss.app
```

The build script creates `dist/Abyss.app` and ad-hoc signs it for local use.

## Validate The Bundle

```zsh
test -d dist/Abyss.app && echo "app exists"
codesign --verify --deep --strict --verbose=2 dist/Abyss.app
file dist/Abyss.app/Contents/MacOS/Abyss
```

The architecture output should include `arm64`.

## Recommended First Test

```zsh
mkdir -p ~/Desktop/Abyss-Test/Input
mkdir -p ~/Desktop/Abyss-Test/Originals
cp ~/Pictures/* ~/Desktop/Abyss-Test/Input/ 2>/dev/null || true
cp ~/Movies/* ~/Desktop/Abyss-Test/Input/ 2>/dev/null || true
cp -R ~/Desktop/Abyss-Test/Input/. ~/Desktop/Abyss-Test/Originals/
```

Open the app, then drag `~/Desktop/Abyss-Test/Input` into the drop area.
Compare the results against `~/Desktop/Abyss-Test/Originals`.

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

## Metadata Checks

Images:

```zsh
mdls path/to/output.jpg
```

Videos:

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

Some MP4 muxers create structural playback tags. Those are not the same as
preserving camera GPS, creation metadata, user tags, EXIF, XMP, or IPTC.
