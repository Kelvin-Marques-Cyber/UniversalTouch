# Desktop packages and builds

The Windows ZIP targets Windows 10/11 x86-64. Extract the whole `UniversalTouch` folder before opening `UniversalTouch.exe`. It includes Python, Tk, OpenCV, NumPy, and the models. The executable is unsigned; no certificate or reputation bypass is included.

The Linux archive targets x86-64 systems with **glibc 2.35 or newer**. GitHub Actions builds it on Ubuntu 22.04. Extract the whole folder, then run `./UniversalTouch`. A desktop session, a working camera driver, and basic X11/Tk/GLib libraries are required. Ubuntu 22.04/24.04, recent Debian, Fedora, Arch, and openSUSE are candidates within that baseline; a successful build on Ubuntu does not certify every distribution. Alpine/musl, older glibc, ARM, and 32-bit Linux should use a compatible source environment rather than this archive.

X11 input uses python-xlib. On Wayland the Linux build includes evdev, but the desktop must permit virtual pointer/keyboard input. Cursor positioning, compositor behavior, and access policy vary. A source install with `--with-wayland` provides the same optional backend. Actual gesture control needs a physical camera and an interactive desktop; CI's no-camera self-test checks model inference and application packaging.

## Install a local source checkout

Use Python 3.10 or newer. Review the local installer first:

```bash
bash scripts/install_linux.sh --print-system-deps
bash scripts/install_linux.sh
# Optional Wayland dependency; C compilation tools may be needed:
bash scripts/install_linux.sh --with-wayland --print-system-deps
bash scripts/install_linux.sh --with-wayland
```

The first command prints distribution-specific package suggestions. Install any missing OS packages yourself. The installer never calls `sudo`. It downloads the two pinned model files and their license texts from OpenCV Zoo, verifies SHA-256, installs the package/dependencies into `~/.local/share/universaltouch/venv`, and creates `~/.local/bin/universaltouch` plus an application-menu shortcut. `--prefix` and `--bin-dir` select other absolute paths. Existing input device permissions are unchanged.

To uninstall the default installation, remove `~/.local/share/universaltouch`, `~/.local/bin/universaltouch`, and `~/.local/share/applications/universaltouch.desktop` after checking those paths. There is no system package or background service to remove.

## Optional Wayland administrator setup

`/dev/uinput` allows software to generate pointer and keyboard events. If you choose to enable the Wayland backend, review `70-universaltouch-uinput.rules`, then have an administrator install this local rule:

```bash
sudo install -m 0644 packaging/70-universaltouch-uinput.rules /etc/udev/rules.d/70-universaltouch-uinput.rules
sudo modprobe uinput
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=misc --sysname-match=uinput
```

For a portable archive, omit `packaging/` from the rule's source path. The `uaccess` rule grants access to the active local seat through the distribution's session manager; log out and back in if necessary. It is ordered before `73-seat-late.rules`. It does not grant access to physical keyboard event devices and does not make a device world-writable. Systems without a compatible logind/udev seat setup require distribution-specific configuration. Reboot may remove an unloaded `uinput` module; load it again when needed. Removing the rule and logging out revokes the session grant.

## Repeat the desktop build

Build natively on each target OS; this is not cross-compilation. Python 3.11 is the release build interpreter. For Linux distribution portability, use Ubuntu 22.04 rather than your newest workstation distribution. Install Tk plus a compiler/Linux input headers for evdev, then:

```bash
python -m venv .venv-build
# Linux: source .venv-build/bin/activate
# Windows PowerShell: .venv-build\Scripts\Activate.ps1
python -m pip install -r packaging/requirements-build.txt
python scripts/fetch_models.py
python -m pip install --no-build-isolation .
python -m unittest discover -s tests -v
python -m unittest discover -s scripts/tests -v
python scripts/build_desktop.py
```

`build_desktop.py` verifies model hashes without downloading, runs PyInstaller's directory build, copies documentation/licenses, launches the frozen application with `--self-test`, and creates an archive in `dist/releases/`. `BUILD-VERSIONS.txt` records the runtime/build versions. The release profile requires Python 3.11 and refuses a Linux host newer than glibc 2.35; `--local-build` permits host-only validation and marks the resulting archive accordingly. The scripts provide repeatable build inputs; native binary outputs are not claimed to be bit-for-bit reproducible across machines.

`python scripts/fetch_models.py --check` verifies all model assets offline. Model URLs and hashes are pinned to OpenCV Zoo commit `48b10fa505aeb51fbd127fc60a5c660040e823b7`. A source archive contains the fetcher rather than the large models; building from source needs the initial download. An installed portable bundle works offline.

## GitHub release procedure

1. Set `project.version` and Android's version consistently, run local checks, and commit the complete source.
2. Push a matching tag such as `v0.1.0`. The workflow rejects tags that differ from `project.version`.
3. All Python matrix checks, native Linux/Windows builds and frozen self-tests, and the Android gesture/lint/APK build must pass before the release job runs.
4. GitHub publishes desktop archives, an Android preview APK, a source archive, and `SHA256SUMS.txt`. Versions starting with `0.` are marked prereleases.

The source archive is produced from the tagged commit. Actions are pinned to official release commit hashes. No camera frame, local configuration, keystore, or credential is packaged. Standard build artifacts are also available on successful non-tag CI runs.

The Android APK is explicitly a **preview**, signed with the Android build's debug key and using a preview application ID. It can be installed for evaluation, but a new ephemeral CI key may require uninstalling an earlier preview before updating. Production signing is a separate maintained-key release process; this workflow does not load signing secrets. Desktop applications are also unsigned.

Verify a download with `sha256sum -c SHA256SUMS.txt` on Linux, or compare `(Get-FileHash .\<filename> -Algorithm SHA256).Hash` with the matching entry on Windows PowerShell. Hash verification detects changed downloads; it does not supply code-signing identity.
