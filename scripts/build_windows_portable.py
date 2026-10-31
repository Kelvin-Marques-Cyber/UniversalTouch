#!/usr/bin/env python3
"""Assemble verified Windows binaries without claiming a native Windows test."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import struct
import tempfile
import urllib.request
import zipfile

from fetch_models import ASSETS, fetch_asset
from release_artifacts import archive_directory

ROOT=Path(__file__).resolve().parents[1]


def extract_verified_zip(archive,destination):
    with zipfile.ZipFile(archive) as source:
        for member in source.infolist():
            path=PurePosixPath(member.filename.replace('\\','/'))
            if path.is_absolute() or '..' in path.parts or any(':' in p for p in path.parts):
                raise ValueError('Archive path escapes the output directory')
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Archive symlinks are not allowed')
        source.extractall(destination)


def verify_x64(path):
    with path.open('rb') as stream:
        if stream.read(2)!=b'MZ':raise RuntimeError(f'Not a Windows PE binary: {path.name}')
        stream.seek(0x3c)
        raw=stream.read(4)
        if len(raw)!=4:raise RuntimeError('Truncated PE header')
        stream.seek(struct.unpack('<I',raw)[0])
        if stream.read(4)!=b'PE\0\0' or stream.read(2)!=b'\x64\x86':
            raise RuntimeError(f'Expected a Windows x86-64 binary: {path.name}')


def require_runtime(runtime):
    required=['python.exe','pythonw.exe','python313.dll','vcruntime140.dll',
              'DLLs/_tkinter.pyd','DLLs/tcl86t.dll','DLLs/tk86t.dll',
              'Lib/tkinter/__init__.py','tcl/tcl8.6/init.tcl','tcl/tk8.6/tk.tcl','LICENSE.txt']
    missing=[name for name in required if not (runtime/name).is_file()]
    if missing:raise RuntimeError('Incomplete official Python/Tk runtime: '+', '.join(missing))


def fetch(row,cache):
    target=cache/row['filename']
    def valid(path):return path.is_file() and path.stat().st_size==row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    if valid(target):return target
    cache.mkdir(parents=True,exist_ok=True)
    temporary=target.with_suffix(target.suffix+'.part')
    try:
        with urllib.request.urlopen(row['url'],timeout=90) as response,temporary.open('wb') as output:
            shutil.copyfileobj(response,output)
        if not valid(temporary):raise RuntimeError('Windows input hash/size mismatch: '+row['filename'])
        temporary.replace(target)
    finally:temporary.unlink(missing_ok=True)
    return target


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=ROOT/'build/windows-inputs')
    parser.add_argument('--work-dir',type=Path,default=ROOT/'build/windows-portable')
    parser.add_argument('--output',type=Path,default=ROOT/'dist/releases')
    args=parser.parse_args()
    inputs=json.loads((ROOT/'packaging/windows-inputs.json').read_text())
    for asset in ASSETS:fetch_asset(asset,ROOT/'universal_touch/models',check=True)
    # A fresh staging directory prevents stale code or old models leaking into a ZIP.
    args.work_dir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.work_dir) as folder:
        bundle=Path(folder)/'UniversalTouch-Windows'
        runtime=bundle/'runtime'
        runtime.mkdir(parents=True)
        extract_verified_zip(fetch(inputs[0],args.cache),runtime)
        require_runtime(runtime)
        # pip's vendored distlib carries launchers for several architectures.
        # This offline application needs no package installer or its launchers.
        for installer in [runtime/'Lib/site-packages/pip',*list((runtime/'Lib/site-packages').glob('pip-*.dist-info'))]:
            if installer.is_dir():shutil.rmtree(installer)
        for row in inputs[1:]:extract_verified_zip(fetch(row,args.cache),runtime/'Lib/site-packages')
        for pattern in ['*.exe','*.dll','*.pyd']:
            for path in runtime.rglob(pattern):verify_x64(path)
        for required in ['numpy/__init__.py','cv2/__init__.py','cv2/cv2.pyd']:
            if not (runtime/'Lib/site-packages'/required).is_file():raise RuntimeError('Missing Windows dependency: '+required)
        shutil.copytree(ROOT/'universal_touch',bundle/'universal_touch',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name in ['README.md','LICENSE','NOTICE','PRIVACY.md']:shutil.copy2(ROOT/name,bundle/name)
        shutil.copytree(ROOT/'docs',bundle/'docs')
        (bundle/'packaging').mkdir()
        shutil.copy2(ROOT/'packaging/README.md',bundle/'packaging/README.md')
        shutil.copy2(ROOT/'packaging/windows-inputs.json',bundle/'WINDOWS-INPUTS.json')
        (bundle/'launch.py').write_text('''from pathlib import Path
import os,sys,traceback
base=Path(__file__).resolve().parent
sys.path.insert(0,str(base))
os.environ['TCL_LIBRARY']=str(base/'runtime/tcl/tcl8.6')
os.environ['TK_LIBRARY']=str(base/'runtime/tcl/tk8.6')
try:
    from universal_touch.__main__ import main
    raise SystemExit(main())
except Exception:
    if sys.stderr is not None: traceback.print_exc()
    else:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None,traceback.format_exc(),'UniversalTouch: falha ao abrir',0x10)
    raise SystemExit(1)
''',encoding='utf-8')
        (bundle/'Iniciar UniversalTouch.cmd').write_bytes(b'@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n"%~dp0runtime\\pythonw.exe" -I "%~dp0launch.py" %*\r\n')
        (bundle/'Diagnosticar.cmd').write_bytes(b'@echo off\r\nsetlocal\r\ncd /d "%~dp0"\r\n"%~dp0runtime\\python.exe" -I "%~dp0launch.py" --self-test\r\npause\r\n')
        (bundle/'LEIA-PRIMEIRO.txt').write_text('''UniversalTouch para Windows 10/11 x64 - PREVIA

Extraia esta pasta inteira. Abra "Iniciar UniversalTouch.cmd".
O tutorial abre antes do primeiro uso. Nao precisa instalar Python.
Para verificar modelos/dependencias, abra "Diagnosticar.cmd".

Este pacote foi montado no Linux com Python oficial do python.org e
binarios Windows do PyPI com hashes verificados. Tcl/Tk, VC runtime,
NumPy, OpenCV, modelos e licencas estao incluidos.
AINDA NAO FOI EXECUTADO EM UM WINDOWS REAL. A precisao da camera,
os atalhos, multiplos monitores e permissao de entrada precisam de teste.
Nao e uma compilacao PyInstaller nativa. O nome do ZIP preserva esse limite.
O uso de memoria medido no Linux nao e garantia no Windows.
''',encoding='utf-8')
        import tomllib
        version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
        archive=args.output/f'UniversalTouch-v{version}-windows-x86_64-preview-untested.zip'
        archive_directory(bundle,archive)
        print('Assembled with SHA256 and PE x64 checks; NOT executed on Windows:',archive)
    return 0


if __name__=='__main__':raise SystemExit(main())
