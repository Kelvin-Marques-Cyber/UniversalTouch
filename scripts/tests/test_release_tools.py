"""Integrity and archive behavior that must hold for a release."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


class FetchModelTests(unittest.TestCase):
    def setUp(self):
        if not (SCRIPTS / "fetch_models.py").is_file():
            self.fail("model fetcher is missing")
        import fetch_models
        self.fetcher = fetch_models
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "upstream.onnx"
        self.source.write_bytes(b"verified model data")
        self.asset = fetch_models.Asset(
            "example.onnx", self.source.as_uri(),
            hashlib.sha256(self.source.read_bytes()).hexdigest(),
            self.source.stat().st_size,
        )
        self.target = self.root / "models"

    def test_download_checks_bytes_before_replacing_file(self):
        self.target.mkdir()
        previous = self.target / self.asset.name
        previous.write_bytes(b"previous known local file")
        self.source.write_bytes(b"tampered model data")
        with self.assertRaises(self.fetcher.IntegrityError):
            self.fetcher.fetch_asset(self.asset, self.target)
        self.assertEqual(previous.read_bytes(), b"previous known local file")
        self.assertEqual(list(self.target.glob("*.part")), [])

    def test_verified_download_and_offline_check_work(self):
        path = self.fetcher.fetch_asset(self.asset, self.target)
        self.source.unlink()
        self.assertEqual(self.fetcher.fetch_asset(self.asset, self.target, check=True), path)
        self.assertEqual(path.read_bytes(), b"verified model data")

    def test_check_mode_rejects_missing_and_corrupted_files(self):
        with self.assertRaises(self.fetcher.IntegrityError):
            self.fetcher.fetch_asset(self.asset, self.target, check=True)
        self.target.mkdir()
        (self.target / self.asset.name).write_bytes(b"git-lfs pointer")
        with self.assertRaises(self.fetcher.IntegrityError):
            self.fetcher.fetch_asset(self.asset, self.target, check=True)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        if not (SCRIPTS / "release_artifacts.py").is_file():
            self.fail("artifact builder is missing")
        import release_artifacts
        self.builder = release_artifacts
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_checksums_use_release_filenames_and_exclude_checksum_itself(self):
        (self.root / "b.zip").write_bytes(b"release two")
        (self.root / "a.apk").write_bytes(b"release one")
        path = self.builder.write_checksums(self.root)
        self.assertEqual(path.read_text(),
            f"{hashlib.sha256(b'release one').hexdigest()}  a.apk\n"
            f"{hashlib.sha256(b'release two').hexdigest()}  b.zip\n")
        self.assertEqual(self.builder.write_checksums(self.root).read_text(), path.read_text())

    @unittest.skipIf(sys.platform == "win32", "POSIX executable permissions are checked by the Linux job")
    def test_portable_archive_contains_top_level_folder_and_executable(self):
        import tarfile
        bundle = self.root / "UniversalTouch"
        bundle.mkdir()
        (bundle / "UniversalTouch").write_text("executable")
        (bundle / "UniversalTouch").chmod(0o755)
        archive = self.builder.archive_directory(bundle, self.root / "release.tar.gz")
        with tarfile.open(archive) as source:
            executable = source.getmember("UniversalTouch/UniversalTouch")
            self.assertEqual(executable.mode & 0o111, 0o111)
            self.assertEqual(source.extractfile(executable).read(), b"executable")


    def test_windows_archive_preserves_application_folder(self):
        import zipfile
        bundle = self.root / "UniversalTouch"
        bundle.mkdir()
        (bundle / "UniversalTouch.exe").write_bytes(b"portable executable")
        archive = self.builder.archive_directory(bundle, self.root / "release.zip")
        with zipfile.ZipFile(archive) as source:
            self.assertEqual(source.namelist(), ["UniversalTouch/UniversalTouch.exe"])
            self.assertEqual(source.read(source.namelist()[0]), b"portable executable")

    def test_source_archive_uses_committed_files_and_excludes_untracked_secrets(self):
        import subprocess
        import tarfile
        repository = self.root / "repository"
        repository.mkdir()
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        (repository / "README.md").write_text("project source")
        subprocess.run(["git", "add", "README.md"], cwd=repository, check=True)
        subprocess.run(["git", "-c", "user.name=Release test", "-c", "user.email=test@example.invalid", "commit", "-qm", "test source"], cwd=repository, check=True)
        (repository / "private.keystore").write_bytes(b"untracked local data")
        original_root = self.builder.ROOT
        self.builder.ROOT = repository
        try:
            archive = self.builder.source_archive("0.1.0", self.root / "release")
        finally:
            self.builder.ROOT = original_root
        with tarfile.open(archive) as source:
            self.assertIn("UniversalTouch-0.1.0/README.md", source.getnames())
            self.assertNotIn("UniversalTouch-0.1.0/private.keystore", source.getnames())


class ReleaseVersionTests(unittest.TestCase):
    def test_android_base_version_must_match_desktop_release(self):
        import release_version
        self.assertTrue(hasattr(release_version, "check_android_version"), "Android version validation is missing")
        with tempfile.TemporaryDirectory() as temporary:
            build = Path(temporary) / "build.gradle"
            build.write_text("versionName '0.1.0'\n")
            release_version.check_android_version(build, "0.1.0")
            with self.assertRaises(ValueError):
                release_version.check_android_version(build, "0.2.0")


if __name__ == "__main__":
    unittest.main()
