#!/usr/bin/env python3
"""Verify the lossless, chunked Balthrix GLB shipped to the web/PWA game."""
from pathlib import Path
import hashlib
import struct

root = Path(__file__).resolve().parents[1]
assets = root / "www/proto3d/models-new"
parts = [assets / f"Balthrix-10x.glb.part{i:02}" for i in range(1, 5)]
sizes = [1843200, 1843200, 1843200, 1749588]
for path, size in zip(parts, sizes):
    assert path.is_file(), f"Missing Balthrix model chunk: {path.name}"
    assert path.stat().st_size == size, f"Wrong size for {path.name}"
data = b"".join(p.read_bytes() for p in parts)
assert data[:4] == b"glTF", "Not a binary glTF file"
assert struct.unpack_from("<I", data, 4)[0] == 2, "Unexpected glTF version"
assert struct.unpack_from("<I", data, 8)[0] == len(data) == 7279188, "GLB length mismatch"
assert hashlib.sha256(data).hexdigest() == "6f5c5a3da2bcee916fb874691d7b24a720ce484fea4e5ced1c50b35ed298d526", "Balthrix GLB content mismatch"
main = (root / "www/proto3d/main.js").read_text()
config = (root / "www/proto3d/charscale.js").read_text()
for model in ("n:balthrix_10x", "n:balthrix_50x"):
    assert model in main and model in config, f"Missing model slot {model}"
assert "native: 10 * HERO_M" in config and "height: 50 * HERO_M" in config
print("PASS: Balthrix full-quality GLB is complete, unmodified, and registered for 10x / 50x")
