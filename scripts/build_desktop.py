#!/usr/bin/env python3
"""Build and smoke-test the native desktop bundle on its target operating system."""
from __future__ import annotations

import argparse
import importlib.metadata
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from fetch_models import ASSETS, fetch_asset
from release_artifacts import archive_directory

ROOT = Path(__file__).resolve().parents[1]


def copy_licenses(bundle: Path) -> None:
    destination = bundle / "licenses"
    shutil.copytree(ROOT / "packaging" / "licenses", destination, dirs_exist_ok=True)
    # Include license files shipped in every distribution contributing runtime code
    # or the PyInstaller bootloader, and record exact installed versions.
    names = ["numpy", "opencv-python-headless", "pyinstaller"]
    if sys.platform == "linux":
        names += ["python-xlib", "six", "evdev"]
    versions = [f"Python {platform.python_version()}", platform.platform(), f"libc {platform.libc_ver()}"]
    for name in names:
        distribution = importlib.metadata.distribution(name)
        versions.append(f"{name} {distribution.version}")
        for item in distribution.files or ():
            parts = [part.lower() for part in item.parts]
            filename = item.name.lower()
            is_license = any(part in {"licenses", "license", "copyright"} for part in parts)
            is_license |= filename.startswith(("license", "copying", "copyright", "notice"))
            if name == "python-xlib" and item.suffix == ".py" and item.parts[0] == "Xlib":
                source_path = bundle / "third-party-source" / name / item
                source_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(distribution.locate_file(item), source_path)
            if is_license and distribution.locate_file(item).is_file():
                relative = Path(item.name) if item.is_absolute() or ".." in item.parts else item
                path = destination / name / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(distribution.locate_file(item), path)
    (bundle / "BUILD-VERSIONS.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "releases")
    parser.add_argument("--work-dir", type=Path, default=ROOT / "build" / "desktop")
    parser.add_argument("--local-build", action="store_true", help="Allow a non-release host/interpreter; label the archive as local validation only.")
    args = parser.parse_args()
    if sys.platform not in {"linux", "win32"}:
        parser.error("Only native Linux and Windows desktop builds are supported.")
    if platform.machine().lower() not in {"amd64", "x86_64"}:
        parser.error("The current portable release profile is x86-64 only; use a source install on other architectures.")
    if not args.local_build and sys.version_info[:2] != (3, 11):
        parser.error("Portable releases use Python 3.11. Use --local-build for host-only validation.")
    libc_name, libc_version = platform.libc_ver()
    if sys.platform == "linux" and not args.local_build:
        if libc_name != "glibc" or tuple(map(int, libc_version.split(".")[:2])) > (2, 35):
            parser.error("Build Linux releases on Ubuntu 22.04 / glibc 2.35 or older. Use --local-build for host-only validation.")
    for asset in ASSETS:
        fetch_asset(asset, ROOT / "universal_touch" / "models", check=True)
    version = importlib.metadata.version("universaltouch")
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, PYINSTALLER_CONFIG_DIR=str(work / "pyinstaller-cache"))
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
        "--distpath", str(work / "dist"), "--workpath", str(work / "analysis"),
        str(ROOT / "packaging" / "UniversalTouch.spec"),
    ], cwd=ROOT, env=environment, check=True)
    bundle = work / "dist" / "UniversalTouch"
    for name in ("README.md", "LICENSE", "NOTICE", "PRIVACY.md", "THIRD_PARTY_NOTICES.md"):
        path = ROOT / name
        if path.is_file():
            shutil.copy2(path, bundle / name)
    shutil.copy2(ROOT / "packaging" / "README.md", bundle / "PORTABLE-README.md")
    (bundle / "packaging").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "packaging" / "README.md", bundle / "packaging" / "README.md")
    shutil.copytree(ROOT / "packaging" / "licenses", bundle / "packaging" / "licenses", dirs_exist_ok=True)
    if (ROOT / "docs").is_dir():
        for source_path in (ROOT / "docs").rglob("*.md"):
            target = bundle / "docs" / source_path.relative_to(ROOT / "docs")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target)
    if (ROOT / "android" / "README.md").is_file():
        (bundle / "android").mkdir(exist_ok=True)
        shutil.copy2(ROOT / "android" / "README.md", bundle / "android" / "README.md")
    if sys.platform == "linux":
        shutil.copy2(ROOT / "packaging" / "70-universaltouch-uinput.rules", bundle)
        shutil.copy2(ROOT / "packaging" / "70-universaltouch-uinput.rules", bundle / "packaging")
    copy_licenses(bundle)
    executable = bundle / ("UniversalTouch.exe" if sys.platform == "win32" else "UniversalTouch")
    subprocess.run([str(executable), "--self-test"], cwd=bundle, check=True, timeout=120)
    suffix = "windows-x86_64.zip" if sys.platform == "win32" else "linux-x86_64.tar.gz"
    if args.local_build:
        suffix = suffix.replace("linux-x86_64", f"linux-x86_64-local-{libc_name}{libc_version}").replace("windows-x86_64", "windows-x86_64-local")
        portable_readme = bundle / "PORTABLE-README.md"
        portable_readme.write_text("LOCAL VALIDATION BUILD: built on " + platform.platform() + ".\nThis artifact does not establish the published Linux compatibility baseline.\n\n" + portable_readme.read_text(encoding="utf-8"), encoding="utf-8")
    archive = args.output.resolve() / f"UniversalTouch-v{version}-{suffix}"
    archive_directory(bundle, archive)
    print(f"Built and smoke-tested {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
