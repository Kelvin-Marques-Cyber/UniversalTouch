#!/usr/bin/env python3
"""Download only the pinned OpenCV Zoo model assets; never execute them."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "48b10fa505aeb51fbd127fc60a5c660040e823b7"


@dataclass(frozen=True)
class Asset:
    name: str
    url: str
    sha256: str
    size: int


ASSETS = (
    Asset("palm_detection_mediapipe_2023feb.onnx",
          f"https://media.githubusercontent.com/media/opencv/opencv_zoo/{COMMIT}/models/palm_detection_mediapipe/palm_detection_mediapipe_2023feb.onnx",
          "78ff51c38496b7fc8b8ebdb6cc8c1abb02fa6c38427c6848254cdaba57fcce7c", 3905734),
    Asset("handpose_estimation_mediapipe_2023feb.onnx",
          f"https://media.githubusercontent.com/media/opencv/opencv_zoo/{COMMIT}/models/handpose_estimation_mediapipe/handpose_estimation_mediapipe_2023feb.onnx",
          "db0898ae717b76b075d9bf563af315b29562e11f8df5027a1ef07b02bef6d81c", 4099621),
    Asset("LICENSE-palm_detection_mediapipe.txt",
          f"https://raw.githubusercontent.com/opencv/opencv_zoo/{COMMIT}/models/palm_detection_mediapipe/LICENSE",
          "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30", 11358),
    Asset("LICENSE-handpose_estimation_mediapipe.txt",
          f"https://raw.githubusercontent.com/opencv/opencv_zoo/{COMMIT}/models/handpose_estimation_mediapipe/LICENSE",
          "58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd", 11357),
)


class IntegrityError(RuntimeError):
    """A local or downloaded asset differs from the pinned model manifest."""


def verified(path: Path, asset: Asset) -> bool:
    if not path.is_file() or path.stat().st_size != asset.size:
        return False
    return hashlib.sha256(path.read_bytes()).hexdigest() == asset.sha256


def fetch_asset(asset: Asset, directory: Path, *, check: bool = False) -> Path:
    target = directory / asset.name
    if verified(target, asset):
        return target
    if check:
        raise IntegrityError(f"Missing or invalid asset: {target}. Run scripts/fetch_models.py to restore it.")
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        request = urllib.request.Request(asset.url, headers={"User-Agent": "UniversalTouch-model-fetcher/0.1"})
        with urllib.request.urlopen(request, timeout=90) as response:
            with tempfile.NamedTemporaryFile(dir=directory, suffix=".part", delete=False) as output:
                temporary = Path(output.name)
                remaining = asset.size + 1
                while remaining:
                    chunk = response.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    output.write(chunk)
                    remaining -= len(chunk)
        if not verified(temporary, asset):
            raise IntegrityError(f"Integrity check failed for {asset.name}; the existing file was preserved.")
        temporary.replace(target)
        return target
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify files without network access.")
    parser.add_argument("--directory", type=Path, default=ROOT / "universal_touch" / "models")
    args = parser.parse_args()
    try:
        for asset in ASSETS:
            path = fetch_asset(asset, args.directory, check=args.check)
            print(f"Verified {path.name} ({asset.size:,} bytes)")
    except (IntegrityError, OSError) as exc:
        parser.exit(1, f"{exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
