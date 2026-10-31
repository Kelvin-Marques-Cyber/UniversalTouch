#!/usr/bin/env python3
"""Read the release version and reject a Git tag that differs from pyproject.toml."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def check_android_version(path: Path, version: str) -> None:
    match = re.search(r"^\s*versionName\s+['\"]([^'\"]+)['\"]", path.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None or match.group(1) != version:
        raise ValueError("Android versionName must match project.version before creating release artifacts.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-output", action="store_true")
    args = parser.parse_args()
    with (ROOT / "pyproject.toml").open("rb") as source:
        version = tomllib.load(source)["project"]["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?", version):
        parser.error("Expected a numeric semantic version, optionally with an a/b/rc prerelease suffix.")
    try:
        check_android_version(ROOT / "android" / "app" / "build.gradle", version)
    except ValueError as exc:
        parser.error(str(exc))
    if os.environ.get("GITHUB_REF_TYPE") == "tag" and os.environ.get("GITHUB_REF_NAME") != f"v{version}":
        parser.error("The release tag must exactly match v + project.version.")
    print(f"version={version}" if args.github_output else version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
