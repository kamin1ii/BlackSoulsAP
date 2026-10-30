"""Builds an Archipelago ready copy of a BLACK SOULS install."""
import io
import json
import os
import random
import shutil
import struct
import zipfile
import zlib
from pathlib import Path

try:
    from .icon import extract_icon_png
except ImportError:
    from icon import extract_icon_png

SCRIPTS_NAME = "Data/Scripts.rvdata2"
# RPGMaker VX Ace AP by EggSlashEther, MIT licensed, pinned so updates cannot break installs
KIT_COMMIT = "801c818f86b80a334bd4f2dbdf2e3bf219a7790a"
KIT_URL = f"https://codeload.github.com/EggSlashEther/RPGMaker-VX-Ace-AP/zip/{KIT_COMMIT}"
KIT_FILES = ["mkxp-z.exe", "libcrypto-3-x64.dll", "libssl-3-x64.dll", "x64-msvcrt-ruby310.dll", "zlib1.dll"]
DIRECT_EXE = "Game_Archipelago.exe"
MOD_SCRIPT_TITLE = "Archipelago"


def read_archive(archive: Path):
    with open(archive, "rb") as f:
        raw = f.read()
    if raw[:8] != b"RGSSAD\x00\x03":
        raise ValueError("Game.rgss3a is not an RGSS3 archive")
    seed = struct.unpack_from("<I", raw, 8)[0]
    key = (seed * 9 + 3) & 0xFFFFFFFF
    kb = struct.pack("<I", key)
    entries = []
    pos = 12
    while True:
        offset, size, file_key, name_len = (v ^ key for v in struct.unpack_from("<4I", raw, pos))
        pos += 16
        if offset == 0:
            break
        name = bytes(b ^ kb[i % 4] for i, b in enumerate(raw[pos:pos + name_len]))
        pos += name_len
        entries.append([name, file_key, raw[offset:offset + size]])
    return seed, entries


def read_archive_file(archive: Path, wanted: str) -> bytes:
    for name, file_key, blob in read_archive(archive)[1]:
        if name.decode("utf-8").replace("\\", "/") == wanted:
            return decrypt(blob, file_key)
    raise FileNotFoundError(wanted)


def write_archive(path: Path, seed: int, entries) -> None:
    key = (seed * 9 + 3) & 0xFFFFFFFF
    kb = struct.pack("<I", key)
    offset = 12 + sum(16 + len(name) for name, _, _ in entries) + 16
    with open(path, "wb") as f:
        f.write(b"RGSSAD\x00\x03" + struct.pack("<I", seed))
        for name, file_key, blob in entries:
            f.write(struct.pack("<4I", offset ^ key, len(blob) ^ key, file_key ^ key, len(name) ^ key))
            f.write(bytes(b ^ kb[i % 4] for i, b in enumerate(name)))
            offset += len(blob)
        f.write(struct.pack("<4I", key, key, key, key))
        for _, _, blob in entries:
            f.write(blob)


def decrypt(data: bytes, key: int) -> bytes:
    out = bytearray(len(data))
    padded = data + bytes(-len(data) % 4)
    for i in range(0, len(padded), 4):
        (word,) = struct.unpack_from("<I", padded, i)
        n = min(4, len(data) - i)
        out[i:i + n] = struct.pack("<I", word ^ key)[:n]
        key = (key * 7 + 3) & 0xFFFFFFFF
    return bytes(out)


class _Reader:
    def __init__(self, data: bytes):
        self.d = data
        self.p = 2
        self.syms = []

    def byte(self) -> int:
        b = self.d[self.p]
        self.p += 1
        return b

    def long(self) -> int:
        c = struct.unpack_from("b", self.d, self.p)[0]
        self.p += 1
        if c == 0:
            return 0
        if 5 <= c <= 127:
            return c - 5
        if -128 <= c <= -5:
            return c + 5
        n = abs(c)
        v = int.from_bytes(self.d[self.p:self.p + n], "little")
        self.p += n
        return v if c > 0 else v - (1 << (8 * n))

    def raw(self) -> bytes:
        n = self.long()
        b = self.d[self.p:self.p + n]
        self.p += n
        return b

    def sym(self) -> str:
        t = chr(self.byte())
        if t == ":":
            s = self.raw().decode("utf-8", "replace")
            self.syms.append(s)
            return s
        if t == ";":
            return self.syms[self.long()]
        raise ValueError("unexpected symbol type " + t)

    def read(self):
        t = chr(self.byte())
        if t == "i":
            return self.long()
        if t == "I":
            v = self.read()
            for _ in range(self.long()):
                self.sym()
                self.read()
            return v
        if t == '"':
            return self.raw()
        if t == "[":
            return [self.read() for _ in range(self.long())]
        if t in "TF0":
            return {"T": True, "F": False, "0": None}[t]
        raise ValueError("unexpected marshal type " + t)


def _w_long(n: int) -> bytes:
    if n == 0:
        return b"\x00"
    if 0 < n < 123:
        return struct.pack("b", n + 5)
    if -124 < n < 0:
        return struct.pack("b", n - 5)
    for size in range(1, 5):
        if 0 < n < (1 << (8 * size)):
            return struct.pack("b", size) + n.to_bytes(size, "little")
        if -(1 << (8 * size)) <= n < 0:
            return struct.pack("b", -size) + (n + (1 << (8 * size))).to_bytes(size, "little")
    raise ValueError("number too large")


def _dump_scripts(scripts) -> bytes:
    out = bytearray(b"\x04\x08[") + _w_long(len(scripts))
    sym_written = False

    def utf8(value: bytes) -> bytes:
        nonlocal sym_written
        part = b'I"' + _w_long(len(value)) + value + _w_long(1)
        part += b";" + _w_long(0) if sym_written else b":" + _w_long(1) + b"E"
        sym_written = True
        return part + b"T"

    for sid, name, code in scripts:
        out += b"[" + _w_long(3)
        out += b"i" + _w_long(sid) if isinstance(sid, int) else utf8(sid)
        out += utf8(name)
        out += b'"' + _w_long(len(code)) + code
    return bytes(out)


def build_scripts(original: bytes, mod_source: str) -> bytes:
    scripts = _Reader(original).read()
    scripts = [entry for entry in scripts if entry[1] != MOD_SCRIPT_TITLE.encode()]
    entry = [str(random.randint(10000000, 99999999)).encode(), MOD_SCRIPT_TITLE.encode(),
             zlib.compress(mod_source.replace("\r\n", "\n").encode("utf-8"))]
    scripts.insert(len(scripts) - 1, entry)
    return _dump_scripts(scripts)


def find_game_root(folder: Path) -> Path:
    if (folder / "Game.rgss3a").exists():
        return folder
    for child in folder.iterdir():
        if child.is_dir() and (child / "Game.rgss3a").exists():
            return child
    raise FileNotFoundError(f"No Game.rgss3a found in {folder}, point /install at the folder that holds Game.exe and Game.rgss3a")


def game_version(folder: Path) -> int:
    data = read_archive_file(find_game_root(Path(folder)) / "Game.rgss3a", "Data/System.rvdata2")
    at = data.find(b"@version_id")
    if at < 0 or data[at + 11:at + 12] != b"i":
        return 0
    reader = _Reader(data)
    reader.p = at + 12
    return reader.long()


def patch_game(source: Path, target: Path, mod_source: str, copy: bool = True) -> Path:
    source = find_game_root(Path(source))
    target = Path(target)
    if copy and source.resolve() != target.resolve():
        def skip(_dir, names):
            return [n for n in names if n.lower().startswith("save") and ".rvdata2" in n.lower()]
        shutil.copytree(source, target, ignore=skip, dirs_exist_ok=True)
    else:
        target = source
    seed, entries = read_archive(source / "Game.rgss3a")
    for entry in entries:
        name, file_key, blob = entry
        if name.decode("utf-8").replace("\\", "/") == SCRIPTS_NAME:
            entry[2] = decrypt(build_scripts(decrypt(blob, file_key), mod_source), file_key)
            break
    else:
        raise FileNotFoundError(SCRIPTS_NAME)
    write_archive(target / "Game.rgss3a.tmp", seed, entries)
    os.replace(target / "Game.rgss3a.tmp", target / "Game.rgss3a")
    shutil.copy2(source / "Game.ini", target / "Game.ini")
    leftover = target / "Data" / "ScriptsAP.rvdata2"
    if leftover.exists():
        os.remove(leftover)
    (target / "Archipelago").mkdir(exist_ok=True)
    for name in ("session.txt", "inbox.txt", "checks.txt"):
        path = target / "Archipelago" / name
        if path.exists():
            os.remove(path)
    return target


def find_rtp():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Enterbrain\RGSS3\RTP") as key:
            return winreg.QueryValueEx(key, "RPGVXAce")[0]
    except OSError:
        return None


def install_direct(target: Path, kit_zip: bytes, data: dict) -> Path:
    target = Path(target)
    with zipfile.ZipFile(io.BytesIO(kit_zip)) as z:
        root = z.namelist()[0].split("/")[0]
        for member in z.namelist():
            rel = member[len(root) + 1:]
            if not rel or member.endswith("/"):
                continue
            if rel in KIT_FILES or rel == "LICENSE.txt" or rel.startswith("Ruby/"):
                name = {"mkxp-z.exe": DIRECT_EXE, "LICENSE.txt": "LICENSE RPGMaker-VX-Ace-AP.txt"}.get(rel, rel)
                dest = target / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(member))
    ap_dir = target / "Archipelago"
    ap_dir.mkdir(exist_ok=True)
    (ap_dir / "data.json").write_text(json.dumps(data), encoding="utf-8")
    config = {"rgssVersion": 3, "windowTitle": "BLACK SOULS Archipelago", "fontSub": ["UmePlus Gothic>VL Gothic"]}
    rtp = find_rtp()
    if rtp:
        config["RTP"] = [rtp.replace("\\", "/")]
    icon = extract_icon_png(target / "Game.exe")
    if icon:
        (ap_dir / "icon.png").write_bytes(icon)
        config["iconPath"] = "Archipelago/icon.png"
    (target / "mkxp.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    connect = target / "archipelago.json"
    if not connect.exists():
        connect.write_text(json.dumps({"hostname": "archipelago.gg", "port": 38281, "name": "Player", "password": ""},
                                      indent=2), encoding="utf-8")
    return target / DIRECT_EXE
