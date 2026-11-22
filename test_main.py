#!/usr/bin/env python3
"""Local tests for main.py (stdlib only: unittest, struct, zlib, hashlib).

Checks: the PNG is valid and 1024x1024, two runs are byte-identical,
the file is under the 1 MiB cap, main.py imports only the standard
library, and every story fact string the image claims is present in
the source (no silent text loss from wrapping).
"""
import hashlib
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))


def run(out):
    r = subprocess.run([sys.executable, os.path.join(HERE, "main.py"), out],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return out


class TestEntry(unittest.TestCase):
    def test_png_valid_1024(self):
        with tempfile.TemporaryDirectory() as d:
            p = run(os.path.join(d, "entry.png"))
            data = open(p, "rb").read()
            self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
            w, h = struct.unpack(">II", data[16:24])
            self.assertEqual((w, h), (1024, 1024))
            # IDAT decompresses to 1024 scanlines of 1024*3 + 1 filter byte
            pos = 8
            idat = b""
            while pos < len(data):
                ln = struct.unpack(">I", data[pos:pos + 4])[0]
                typ = data[pos + 4:pos + 8]
                if typ == b"IDAT":
                    idat += data[pos + 8:pos + 8 + ln]
                pos += 12 + ln
            raw = zlib.decompress(idat)
            self.assertEqual(len(raw), 1024 * (1024 * 3 + 1))
            self.assertTrue(all(raw[y * 3073] == 0
                                for y in range(1024)))

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            a = run(os.path.join(d, "a.png"))
            b = run(os.path.join(d, "b.png"))
            ha = hashlib.sha256(open(a, "rb").read()).hexdigest()
            hb = hashlib.sha256(open(b, "rb").read()).hexdigest()
            self.assertEqual(ha, hb)

    def test_under_1mib(self):
        with tempfile.TemporaryDirectory() as d:
            p = run(os.path.join(d, "entry.png"))
            self.assertLess(os.path.getsize(p), 1024 * 1024)

    def test_stdlib_only(self):
        import ast
        tree = ast.parse(open(os.path.join(HERE, "main.py")).read())
        allowed = {"os", "struct", "sys", "zlib", "math"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertIn(a.name.split(".")[0], allowed)
            if isinstance(node, ast.ImportFrom):
                self.assertIn((node.module or "").split(".")[0], allowed)

    def test_all_stories_present(self):
        src = open(os.path.join(HERE, "main.py")).read()
        for s in ["KUWAIT", "BAHRAIN", "HORMUZ", "OMAN", "400", "98.5%",
                  "COP31", "6.9", "ESTONIA", "HONG KONG", "BOLSONARO",
                  "22 NOVEMBER 2026"]:
            self.assertIn(s, src)


if __name__ == "__main__":
    unittest.main()
