The desktop bundle includes these upstream license texts:

- Python: [CPython v3.11.14 LICENSE](https://github.com/python/cpython/blob/v3.11.14/LICENSE), SHA-256 `3b2f81fe21d181c499c59a256c8e1968455d6689d269aa85373bfb6af41da3bf`.
- Tcl: [8.6.16 license.terms](https://github.com/tcltk/tcl/blob/core-8-6-16/license.terms), SHA-256 `c0a69a2bfd757361ec7e6143973b103c90409316b49e9c88db26ad6388e79f16`.
- Tk: [8.6.16 license.terms](https://github.com/tcltk/tk/blob/core-8-6-16/license.terms), SHA-256 `2cde822b93ca16ae535c954b7dfe658b4ad10df2a193628d1b358f1765e8b198`.

The build script also copies the license/notice files supplied by installed NumPy, OpenCV, PyInstaller, and Linux input dependencies into `licenses/`. Model licenses live beside the models inside the application. `BUILD-VERSIONS.txt` records the native build's Python and runtime package versions.

The unmodified python-xlib Python source files are also included under `third-party-source/python-xlib/` in Linux bundles. The source installation described in the project README provides a normal Python environment in which this dependency can be replaced.
