"""Static entry point so PyInstaller can discover application imports."""
from universal_touch.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
