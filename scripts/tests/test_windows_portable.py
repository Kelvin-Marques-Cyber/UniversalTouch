import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from build_windows_portable import extract_verified_zip, require_runtime, verify_x64


class WindowsAssemblyTests(unittest.TestCase):
    def test_archive_cannot_write_outside_bundle(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder)/'bad.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape.txt','bad')
            with self.assertRaises(ValueError):extract_verified_zip(archive,Path(folder)/'bundle')
            self.assertFalse((Path(folder)/'escape.txt').exists())

    def test_archive_keeps_runtime_subdirectories(self):
        with tempfile.TemporaryDirectory() as folder:
            archive=Path(folder)/'good.zip'
            with zipfile.ZipFile(archive,'w') as z:z.writestr('Lib/example.py','x=1\n')
            extract_verified_zip(archive,Path(folder)/'bundle')
            self.assertEqual((Path(folder)/'bundle/Lib/example.py').read_text(),'x=1\n')

    def test_incomplete_runtime_is_rejected_before_packaging(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):require_runtime(Path(folder))

    def test_wrong_cpu_architecture_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'wrong.pyd'
            data=bytearray(128)
            data[:2]=b'MZ'
            struct.pack_into('<I',data,0x3c,64)
            data[64:68]=b'PE\0\0'
            struct.pack_into('<H',data,68,0x14c)
            path.write_bytes(data)
            with self.assertRaises(RuntimeError):verify_x64(path)
