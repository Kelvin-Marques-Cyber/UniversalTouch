Preview release of UniversalTouch: local webcam hand control for Windows and Linux, plus an Android Accessibility preview.

- Windows: extract the complete ZIP and run `UniversalTouch.exe` (Windows 10/11 x86-64).
- Linux: extract the complete archive and run `./UniversalTouch` (x86-64, glibc 2.35+; X11, or optional Wayland setup described in the included README).
- Android: the `android-preview.apk` is debug-signed and uses a preview application ID. A changed preview signing key can require uninstalling an earlier preview. Review camera and Accessibility access on the device.
- Source: models are fetched and SHA-256 verified using `scripts/fetch_models.py` before building.

Desktop executables are unsigned. These are preview builds; camera behavior, gesture thresholds, and native desktop input still need checking on each target device. CI verifies model inference without a camera, unit tests, frozen desktop startup, and the Android build. SHA-256 checksums accompany the downloads.
