# Abyss

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-arm64-brightgreen.svg)](https://support.apple.com/en-us/HT211814)
[![PySide6](https://img.shields.io/badge/PySide6-Qt6-orange.svg)](https://doc.qt.io/qtforpython/)

```text
 █████╗ ██████╗ ██╗   ██╗███████╗███████╗
██╔══██╗██╔══██╗╚██╗ ██╔╝██╔════╝██╔════╝
███████║██████╔╝ ╚████╔╝ ███████╗███████╗
██╔══██║██╔══██╗  ╚██╔╝  ╚════██║╚════██║
██║  ██║██████╔╝   ██║   ███████║███████║
╚═╝  ╚═╝╚═════╝    ╚═╝   ╚══════╝╚══════╝
```

> **Native macOS metadata stripper for photos and videos.**
> Drop files or folders onto the window and Abyss rewrites them clean — no EXIF, no GPS, no timestamps.

---

## Features

- **Drag and Drop** — drop files or entire folders; folders are processed recursively
- **Images** — rewrites to metadata-free JPEG (EXIF orientation applied to pixels before stripping)
- **Videos** — remuxes to a clean MP4 container without re-encoding when possible; falls back to H.264/AAC re-encode
- **Atomic Replacement** — originals are only removed after the new file is verified non-empty
- **Safe Failure** — if conversion fails, the original stays in place and the error is logged
- **Apple Silicon Native** — arm64 build optimized for M1/M2/M3/M4 chips

---

## Supported Formats

| Type | Extensions |
|---|---|
| Images | `.jpg` `.jpeg` `.png` `.gif` `.bmp` `.tif` `.tiff` `.webp` `.heic` `.heif` `.avif` |
| Videos | `.mov` `.mp4` `.m4v` `.avi` `.mkv` `.webm` `.mts` `.m2ts` `.3gp` `.3g2` |

Extension matching is case-insensitive. Unsupported files are skipped without modification.

---

## Installation

1. Download the latest `Abyss.dmg` from [Releases](https://github.com/RazorBackRoar/Abyss/releases)
2. Open the DMG and drag `Abyss.app` to `/Applications`
3. First launch — right-click the app → **Open** to bypass Gatekeeper on the ad-hoc signed build

---

## Usage

1. **Launch Abyss**
2. **Drop** files or folders onto the window
3. Processing begins immediately — progress and any errors appear in the live log

> **Warning:** Abyss modifies files in place. Successful conversions remove the source file. Test on disposable copies first.

---

## Development

### Requirements

- Python 3.14
- macOS 12.0+
- [uv](https://github.com/astral-sh/uv)

### Setup

```bash
git clone https://github.com/RazorBackRoar/Abyss.git
cd Abyss
uv sync
uv run abyss
```

### Build

```bash
razorbuild Abyss
# Output: dist/Abyss.dmg
```

### Lint & Test

```bash
uv run ruff check .
uv run ty check src --python-version 3.14
uv run pytest tests/ -q
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.
Copyright © 2026 RazorBackRoar

<!-- razorcore:runtime:start -->
## Runtime Requirements

For users:
- Download the macOS `.dmg` or `.app` release. Python does not need to be installed.

For developers:
- Primary development/build target: Python 3.14 with `uv`.
- Source compatibility goal: Python 3.12-3.14 (best effort).
- Setup: `uv sync`
- Run: `uv run python -m abyss`
<!-- razorcore:runtime:end -->
