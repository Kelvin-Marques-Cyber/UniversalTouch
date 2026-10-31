# Build on the target OS; PyInstaller does not cross-compile.
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = Path(SPECPATH).parent
hidden = collect_submodules("universal_touch")
if sys.platform == "linux":
    hidden += collect_submodules("Xlib") + collect_submodules("evdev")

a = Analysis(
    [str(root / "packaging" / "desktop_launcher.py")],
    pathex=[str(root)],
    binaries=[],
    datas=collect_data_files("universal_touch"),
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["torch", "tensorflow", "mediapipe", "matplotlib", "PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="UniversalTouch",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="UniversalTouch")
