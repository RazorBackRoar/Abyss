# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


APP_NAME = "Abyss"
project_root = Path.cwd()
src_path = project_root / "src"
pyproject = project_root / "pyproject.toml"


def get_project_version(default: str = "0.0.0") -> str:
    if not pyproject.exists():
        return default
    try:
        with pyproject.open("rb") as fp:
            data = tomllib.load(fp)
        return data["project"]["version"]
    except Exception:
        return default


APP_VERSION = get_project_version("1.0.0")
BUNDLE_ID = "com.razorbackroar.abyss.app"

datas = []
binaries = []
hiddenimports = []

for asset_name in ("abyss window.png", "Abyss Icns.png", "AppIcon.icns"):
    asset_path = project_root / "assets" / asset_name
    if asset_path.exists():
        datas.append((str(asset_path), "assets"))

license_path = project_root / "LICENSE"
if license_path.exists():
    datas.append((str(license_path), "."))

for package in ("av", "PIL", "pillow_heif"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports


a = Analysis(
    ["src/abyss/__main__.py"],
    pathex=[str(src_path)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy.tests",
        "pytest",
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

icon_path = project_root / "assets" / "AppIcon.icns"

app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon=str(icon_path) if icon_path.exists() else None,
    bundle_identifier=BUNDLE_ID,
    info_plist={
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "14.0",
        "LSRequiresNativeExecution": True,
        "LSApplicationCategoryType": "public.app-category.utilities",
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeName": "Media Files",
                "CFBundleTypeRole": "Editor",
                "LSHandlerRank": "Alternate",
                "LSItemContentTypes": [
                    "public.image",
                    "public.movie",
                    "public.video",
                    "public.folder",
                    "public.data",
                ],
            }
        ],
    },
)
