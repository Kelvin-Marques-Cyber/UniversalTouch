#!/usr/bin/env python3
"""Create portable archives, source archives, and release SHA-256 manifests."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def archive_directory(directory: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.name.endswith(".tar.gz"):
        with tarfile.open(output, "w:gz") as archive:
            archive.add(directory, arcname=directory.name)
    elif output.suffix == ".zip":
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(directory.rglob("*")):
                if path.is_file():
                    archive.write(path, arcname=path.relative_to(directory.parent))
    else:
        raise ValueError("Portable archives must end in .tar.gz or .zip")
    return output


def write_checksums(directory: Path) -> Path:
    output = directory / "SHA256SUMS.txt"
    lines = []
    for path in sorted(directory.iterdir()):
        if path.is_file() and path != output:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.name}\n")
    output.write_text("".join(lines), encoding="utf-8", newline="\n")
    return output


def source_archive(version: str, directory: Path) -> Path:
    output = directory / f"UniversalTouch-v{version}-source.tar.gz"
    directory.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "archive", "--format=tar.gz", f"--prefix=UniversalTouch-{version}/", "-o", str(output.resolve()), "HEAD"], cwd=ROOT, check=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    checksums = commands.add_parser("checksums")
    checksums.add_argument("directory", type=Path)
    source = commands.add_parser("source")
    source.add_argument("version")
    source.add_argument("--output", type=Path, default=ROOT / "dist" / "releases")
    args = parser.parse_args()
    if args.command == "checksums":
        print(write_checksums(args.directory))
    else:
        print(source_archive(args.version, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
