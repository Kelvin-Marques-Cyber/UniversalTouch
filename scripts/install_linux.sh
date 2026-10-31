#!/usr/bin/env bash
# Install the checked-out application for this user; never invoke sudo.
set -euo pipefail

source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
install_dir="${XDG_DATA_HOME:-${HOME}/.local/share}/universaltouch"
bin_dir="${HOME}/.local/bin"
python_bin="${PYTHON_BIN:-python3}"
with_wayland=0
print_deps=0

usage() {
    cat <<'TXT'
Usage: bash scripts/install_linux.sh [--with-wayland] [--prefix DIR] [--bin-dir DIR] [--print-system-deps]
Installs this local source checkout into a private virtual environment and adds
an application-menu shortcut. Does not install OS packages or input permissions.
Set PYTHON_BIN to select Python >=3.10. --with-wayland builds the evdev extra.
TXT
}
while (($#)); do
    case "$1" in
        --with-wayland) with_wayland=1; shift ;;
        --prefix) install_dir="${2:?--prefix requires a directory}"; shift 2 ;;
        --bin-dir) bin_dir="${2:?--bin-dir requires a directory}"; shift 2 ;;
        --print-system-deps) print_deps=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

system_deps() {
    local distro_id="" distro_like=""
    if [[ -r /etc/os-release ]]; then
        # Standard local OS metadata, supplied by the installed distribution.
        distro_id="$(. /etc/os-release; printf '%s' "${ID:-}")"
        distro_like="$(. /etc/os-release; printf '%s' "${ID_LIKE:-}")"
    fi
    case " $distro_id $distro_like " in
        *ubuntu*|*debian*|*linuxmint*|*pop*)
            printf '%s\n' 'sudo apt install python3 python3-venv python3-tk libglib2.0-0'
            ((with_wayland == 0)) || printf '%s\n' 'For Wayland compilation: sudo apt install build-essential python3-dev linux-libc-dev'
            ;;
        *fedora*|*rhel*|*centos*)
            printf '%s\n' 'sudo dnf install python3 python3-tkinter glib2'
            ((with_wayland == 0)) || printf '%s\n' 'For Wayland compilation: sudo dnf install gcc python3-devel kernel-headers'
            ;;
        *arch*|*manjaro*)
            printf '%s\n' 'sudo pacman -S python tk glib2'
            ((with_wayland == 0)) || printf '%s\n' 'For Wayland compilation: sudo pacman -S base-devel linux-api-headers'
            ;;
        *opensuse*|*suse*|*sles*)
            printf '%s\n' 'sudo zypper install python3 python3-tk python3-pip libglib-2_0-0'
            ((with_wayland == 0)) || printf '%s\n' 'For Wayland compilation: sudo zypper install gcc python3-devel linux-glibc-devel'
            ;;
        *)
            printf '%s\n' 'Install Python >=3.10 with venv/pip, Tk, and GLib using your distribution package manager.'
            ((with_wayland == 0)) || printf '%s\n' 'Wayland compilation also needs a C compiler, Python development headers, and Linux input headers.'
            ;;
    esac
    return 0
}
if ((print_deps)); then system_deps; exit 0; fi
if [[ "$EUID" == 0 ]]; then
    printf '%s\n' 'Run this installer as your regular desktop user.' >&2
    exit 1
fi
if [[ "$install_dir" != /* || "$bin_dir" != /* ]]; then
    printf '%s\n' '--prefix and --bin-dir must be absolute paths.' >&2
    exit 2
fi
if ! "$python_bin" -c 'import sys, tkinter, venv; assert sys.version_info >= (3,10), "Python >=3.10 required"'; then
    printf '%s\n' 'Install the missing system dependencies, then rerun:' >&2
    system_deps >&2
    exit 1
fi
"$python_bin" "$source_dir/scripts/fetch_models.py"
mkdir -p -- "$install_dir" "$bin_dir"
"$python_bin" -m venv "$install_dir/venv"
package="$source_dir"
if ((with_wayland)); then package="${source_dir}[wayland]"; fi
"$install_dir/venv/bin/python" -m pip install "$package"
"$install_dir/venv/bin/python" -m universal_touch --self-test
launcher="$bin_dir/universaltouch"
printf '#!/usr/bin/env bash\nexec %q -m universal_touch "$@"\n' "$install_dir/venv/bin/python" > "$launcher"
chmod 755 -- "$launcher"
applications_dir="${XDG_DATA_HOME:-${HOME}/.local/share}/applications"
mkdir -p -- "$applications_dir"
"$python_bin" - "$source_dir/packaging/universal-touch.desktop" "$applications_dir/universaltouch.desktop" "$launcher" <<'PY'
from pathlib import Path
import sys
source, target, launcher = sys.argv[1:]
# Desktop Entry escaping is separate from shell quoting.
escaped = launcher.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
text = Path(source).read_text(encoding='utf-8').replace('Exec=universaltouch', f'Exec="{escaped}"')
Path(target).write_text(text, encoding='utf-8')
PY
printf 'Installed. Open UniversalTouch from the application menu or run: %s\n' "$launcher"
if ((with_wayland)); then
    printf '%s\n' 'Wayland input also requires the optional administrator setup in packaging/README.md.'
fi
