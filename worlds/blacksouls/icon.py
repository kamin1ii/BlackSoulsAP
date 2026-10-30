"""Pulls the main icon out of a Windows exe and saves it as PNG."""
import struct
import zlib
from pathlib import Path
from typing import Optional

RT_ICON = 3
RT_GROUP_ICON = 14


def _resources(data: bytes):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    sections = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    dirs = opt + (96 if magic == 0x10B else 112)
    rsrc_rva = struct.unpack_from("<I", data, dirs + 2 * 8)[0]
    table = opt + opt_size
    for i in range(sections):
        s = table + i * 40
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, s + 8)
        if vaddr <= rsrc_rva < vaddr + max(vsize, rawsize):
            return rawptr + (rsrc_rva - vaddr), vaddr, rawptr
    raise ValueError("no resource section")


def _entries(data, base, offset):
    named, ids = struct.unpack_from("<HH", data, offset + 12)
    for i in range(named + ids):
        name, target = struct.unpack_from("<II", data, offset + 16 + i * 8)
        yield name, target


def _leaf(data, base, target):
    while target & 0x80000000:
        target = next(_entries(data, base, base + (target & 0x7FFFFFFF)))[1]
    return target


def _collect(data):
    base, vaddr, rawptr = _resources(data)
    found = {}
    for type_id, target in _entries(data, base, base):
        if type_id not in (RT_ICON, RT_GROUP_ICON) or not target & 0x80000000:
            continue
        for res_id, sub in _entries(data, base, base + (target & 0x7FFFFFFF)):
            leaf = _leaf(data, base, sub)
            rva, size = struct.unpack_from("<II", data, base + leaf)
            start = rawptr + (rva - vaddr)
            found[(type_id, res_id)] = data[start:start + size]
    return found


def _png(width, height, rgba):
    rows = b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def _dib_to_png(dib):
    header = struct.unpack_from("<I", dib, 0)[0]
    width, height2, _, bits = struct.unpack_from("<iiHH", dib, 4)
    height = height2 // 2
    if bits != 32:
        return None
    pixels = dib[header:header + width * height * 4]
    rgba = bytearray()
    for y in range(height - 1, -1, -1):
        row = pixels[y * width * 4:(y + 1) * width * 4]
        for x in range(width):
            b, g, r, a = row[x * 4:x * 4 + 4]
            rgba += bytes((r, g, b, a))
    return _png(width, height, bytes(rgba))


def extract_icon_png(exe: Path) -> Optional[bytes]:
    data = Path(exe).read_bytes()
    found = _collect(data)
    groups = [v for (t, _), v in sorted(found.items()) if t == RT_GROUP_ICON]
    if not groups:
        return None
    group = groups[0]
    count = struct.unpack_from("<H", group, 4)[0]
    best = None
    for i in range(count):
        w, h, _, _, _, bits, _, icon_id = struct.unpack_from("<BBBBHHIH", group, 6 + i * 14)
        size = (w or 256) * (h or 256)
        if best is None or (size, bits) > best[0]:
            best = ((size, bits), icon_id)
    image = found.get((RT_ICON, best[1]))
    if image is None:
        return None
    if image.startswith(b"\x89PNG"):
        return image
    return _dib_to_png(image)
