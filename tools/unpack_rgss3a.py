# Unpacks an RGSS3A archive into a folder
import struct
import sys
from pathlib import Path


def unpack(archive, out_dir, only_data=True):
    raw = Path(archive).read_bytes()
    if raw[:8] != b"RGSSAD\x00\x03":
        raise ValueError("not an RGSS3A archive")
    key = (struct.unpack_from("<I", raw, 8)[0] * 9 + 3) & 0xFFFFFFFF
    pos = 12
    count = 0
    while True:
        offset, size, file_key, name_len = (v ^ key for v in struct.unpack_from("<4I", raw, pos))
        pos += 16
        if offset == 0:
            break
        kb = struct.pack("<I", key)
        name = bytes(b ^ kb[i % 4] for i, b in enumerate(raw[pos:pos + name_len])).decode("utf-8")
        pos += name_len
        name = name.replace("\\", "/")
        if only_data and not name.startswith("Data/"):
            continue
        dest = Path(out_dir) / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(decrypt(raw[offset:offset + size], file_key))
        count += 1
    return count


def decrypt(data, key):
    out = bytearray(len(data))
    padded = data + b"\x00" * (-len(data) % 4)
    for i in range(0, len(padded), 4):
        (word,) = struct.unpack_from("<I", padded, i)
        chunk = struct.pack("<I", word ^ key)
        n = min(4, len(data) - i)
        out[i:i + n] = chunk[:n]
        key = (key * 7 + 3) & 0xFFFFFFFF
    return bytes(out)


if __name__ == "__main__":
    print(unpack(sys.argv[1], sys.argv[2]), "files")
