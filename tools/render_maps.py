"""Draws RPG Maker VX Ace maps from the game's Data folder and its tileset, character and parallax images.
python tools/render_maps.py <Data folder> <Graphics folder or folders separated by ;> <map id> <out.png>"""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rbmarshal import load, loads, text  # noqa: E402

TILE = 32
HALF = TILE // 2

# which quarters of an autotile block make each of its shapes, the same tables RPG Maker MV uses for this format
FLOOR = [
    [[2, 4], [1, 4], [2, 3], [1, 3]], [[2, 0], [1, 4], [2, 3], [1, 3]], [[2, 4], [3, 0], [2, 3], [1, 3]], [[2, 0], [3, 0], [2, 3], [1, 3]],
    [[2, 4], [1, 4], [2, 3], [3, 1]], [[2, 0], [1, 4], [2, 3], [3, 1]], [[2, 4], [3, 0], [2, 3], [3, 1]], [[2, 0], [3, 0], [2, 3], [3, 1]],
    [[2, 4], [1, 4], [2, 1], [1, 3]], [[2, 0], [1, 4], [2, 1], [1, 3]], [[2, 4], [3, 0], [2, 1], [1, 3]], [[2, 0], [3, 0], [2, 1], [1, 3]],
    [[2, 4], [1, 4], [2, 1], [3, 1]], [[2, 0], [1, 4], [2, 1], [3, 1]], [[2, 4], [3, 0], [2, 1], [3, 1]], [[2, 0], [3, 0], [2, 1], [3, 1]],
    [[0, 4], [1, 4], [0, 3], [1, 3]], [[0, 4], [3, 0], [0, 3], [1, 3]], [[0, 4], [1, 4], [0, 3], [3, 1]], [[0, 4], [3, 0], [0, 3], [3, 1]],
    [[2, 2], [1, 2], [2, 3], [1, 3]], [[2, 2], [1, 2], [2, 3], [3, 1]], [[2, 2], [1, 2], [2, 1], [1, 3]], [[2, 2], [1, 2], [2, 1], [3, 1]],
    [[2, 4], [3, 4], [2, 3], [3, 3]], [[2, 4], [3, 4], [2, 1], [3, 3]], [[2, 0], [3, 4], [2, 3], [3, 3]], [[2, 0], [3, 4], [2, 1], [3, 3]],
    [[2, 4], [1, 4], [2, 5], [1, 5]], [[2, 0], [1, 4], [2, 5], [1, 5]], [[2, 4], [3, 0], [2, 5], [1, 5]], [[2, 0], [3, 0], [2, 5], [1, 5]],
    [[0, 4], [3, 4], [0, 3], [3, 3]], [[2, 2], [1, 2], [2, 5], [1, 5]], [[0, 2], [1, 2], [0, 3], [1, 3]], [[0, 2], [1, 2], [0, 3], [3, 1]],
    [[2, 2], [3, 2], [2, 3], [3, 3]], [[2, 2], [3, 2], [2, 1], [3, 3]], [[2, 4], [3, 4], [2, 5], [3, 5]], [[2, 0], [3, 4], [2, 5], [3, 5]],
    [[0, 4], [1, 4], [0, 5], [1, 5]], [[0, 4], [3, 0], [0, 5], [1, 5]], [[0, 2], [3, 2], [0, 3], [3, 3]], [[0, 2], [1, 2], [0, 5], [1, 5]],
    [[0, 4], [3, 4], [0, 5], [3, 5]], [[2, 2], [3, 2], [2, 5], [3, 5]], [[0, 2], [3, 2], [0, 5], [3, 5]], [[0, 0], [1, 0], [0, 1], [1, 1]],
]
WALL = [
    [[2, 2], [1, 2], [2, 1], [1, 1]], [[0, 2], [1, 2], [0, 1], [1, 1]], [[2, 0], [1, 0], [2, 1], [1, 1]], [[0, 0], [1, 0], [0, 1], [1, 1]],
    [[2, 2], [3, 2], [2, 1], [3, 1]], [[0, 2], [3, 2], [0, 1], [3, 1]], [[2, 0], [3, 0], [2, 1], [3, 1]], [[0, 0], [3, 0], [0, 1], [3, 1]],
    [[2, 2], [1, 2], [2, 3], [1, 3]], [[0, 2], [1, 2], [0, 3], [1, 3]], [[2, 0], [1, 0], [2, 3], [1, 3]], [[0, 0], [1, 0], [0, 3], [1, 3]],
    [[2, 2], [3, 2], [2, 3], [3, 3]], [[0, 2], [3, 2], [0, 3], [3, 3]], [[2, 0], [3, 0], [2, 3], [3, 3]], [[0, 0], [3, 0], [0, 3], [3, 3]],
]
WATERFALL = [[[2, 0], [1, 0], [2, 1], [1, 1]], [[0, 0], [1, 0], [0, 1], [1, 1]], [[2, 0], [3, 0], [2, 1], [3, 1]], [[0, 0], [3, 0], [0, 1], [3, 1]]]


def table(raw):
    """RGSS Table, a header of dimensions then 16 bit cells."""
    import struct
    _dim, xs, ys, zs, n = struct.unpack_from("<5i", raw, 0)
    cells = struct.unpack_from(f"<{n}h", raw, 20)
    return xs, ys, zs, cells


class Archive:
    """Reads files straight out of a Game.rgss3a without unpacking it."""

    def __init__(self, path):
        import struct
        self.raw = Path(path).read_bytes()
        key = (struct.unpack_from("<I", self.raw, 8)[0] * 9 + 3) & 0xFFFFFFFF
        kb = struct.pack("<I", key)
        self.index = {}
        pos = 12
        while True:
            offset, size, file_key, name_len = (v ^ key for v in struct.unpack_from("<4I", self.raw, pos))
            pos += 16
            if offset == 0:
                break
            name = bytes(b ^ kb[i % 4] for i, b in enumerate(self.raw[pos:pos + name_len])).decode("utf-8")
            pos += name_len
            self.index[name.replace("\\", "/").lower()] = (offset, size, file_key)

    def read(self, name):
        from unpack_rgss3a import decrypt
        hit = self.index.get(name.lower())
        if not hit:
            return None
        offset, size, file_key = hit
        return decrypt(self.raw[offset:offset + size], file_key)


class Images:
    def __init__(self, roots):
        self.roots = [Archive(r) if str(r).lower().endswith(".rgss3a") else Path(r) for r in roots]
        self.cache = {}

    def find(self, root, folder, name):
        import io
        for ext in (".png", ".jpg", ".bmp"):
            if isinstance(root, Archive):
                data = root.read(f"Graphics/{folder}/{name}{ext}")
                if data:
                    return Image.open(io.BytesIO(data)).convert("RGBA")
            else:
                p = root / folder / (name + ext)
                if p.is_file():
                    return Image.open(p).convert("RGBA")
        return None

    def get(self, folder, name):
        key = (folder, name)
        if key not in self.cache:
            self.cache[key] = None
            for root in self.roots:
                self.cache[key] = self.find(root, folder, name)
                if self.cache[key] is not None:
                    break
        return self.cache[key]


class Renderer:
    """data is a Data folder or a Game.rgss3a, graphics are folders or archives searched in order."""

    def __init__(self, data, graphics_roots):
        self.archive = Archive(data) if str(data).lower().endswith(".rgss3a") else None
        self.data = Path(data)
        self.images = Images(graphics_roots)
        self.tilesets = self.load("Tilesets.rvdata2")
        self.missing = set()

    def load(self, name):
        if self.archive:
            return loads(self.archive.read("Data/" + name))
        return load(self.data / name)

    def sheet(self, names, index):
        name = text(names[index]) if index < len(names) else ""
        if not name:
            return None
        img = self.images.get("Tilesets", name)
        if img is None:
            self.missing.add(name)
        return img

    def draw_normal(self, canvas, names, tile_id, x, y):
        index = 4 if 1536 <= tile_id < 2048 else 5 + tile_id // 256
        img = self.sheet(names, index)
        if img is None:
            return
        sx = ((tile_id // 128) % 2 * 8 + tile_id % 8) * TILE
        sy = ((tile_id % 256) // 8 % 16) * TILE
        canvas.alpha_composite(img.crop((sx, sy, sx + TILE, sy + TILE)), (x, y))

    def draw_auto(self, canvas, names, tile_id, x, y):
        kind = (tile_id - 2048) // 48
        shape = (tile_id - 2048) % 48
        tx, ty = kind % 8, kind // 8
        layout = FLOOR
        if tile_id < 2816:
            index = 0
            if kind == 0:
                bx, by = 0, 0
            elif kind == 1:
                bx, by = 0, 3
            elif kind == 2:
                bx, by = 6, 0
            elif kind == 3:
                bx, by = 6, 3
            else:
                bx = tx // 4 * 8
                by = ty * 6 + tx // 2 % 2 * 3
                if kind % 2 == 1:
                    bx += 6
                    layout = WATERFALL
        elif tile_id < 4352:
            index, bx, by = 1, tx * 2, (ty - 2) * 3
        elif tile_id < 5888:
            index, bx, by, layout = 2, tx * 2, (ty - 6) * 2, WALL
        else:
            index, bx = 3, tx * 2
            by = int((ty - 10) * 2.5 + (0.5 if ty % 2 == 1 else 0))
            if ty % 2 == 1:
                layout = WALL
        img = self.sheet(names, index)
        if img is None or shape >= len(layout):
            return
        for i, (qx, qy) in enumerate(layout[shape]):
            sx, sy = (bx * 2 + qx) * HALF, (by * 2 + qy) * HALF
            canvas.alpha_composite(img.crop((sx, sy, sx + HALF, sy + HALF)), (x + i % 2 * HALF, y + i // 2 * HALF))

    def draw_tile(self, canvas, names, tile_id, x, y):
        if tile_id <= 0:
            return
        if tile_id >= 2048:
            self.draw_auto(canvas, names, tile_id, x, y)
        else:
            self.draw_normal(canvas, names, tile_id, x, y)

    def draw_event(self, canvas, names, page, x, y):
        g = page["graphic"]
        if not g:
            return
        if g["tile_id"]:
            self.draw_tile(canvas, names, g["tile_id"], x * TILE, y * TILE)
            return
        name = text(g["character_name"])
        if not name:
            return
        img = self.images.get("Characters", name)
        if img is None:
            return
        single = "$" in name[:2]
        fw = img.width // (3 if single else 12)
        fh = img.height // (4 if single else 8)
        idx = 0 if single else g["character_index"]
        col = (idx % 4) * 3 + g["pattern"]
        row = (idx // 4) * 4 + (g["direction"] // 2 - 1)
        frame = img.crop((col * fw, row * fh, col * fw + fw, row * fh + fh))
        shift = 0 if name.startswith("!") or "!" in name[:2] else 4
        canvas.alpha_composite(frame, (x * TILE + HALF - fw // 2, y * TILE + TILE - fh - shift))

    def render(self, map_id, events=True):
        m = self.load(f"Map{map_id:03d}.rvdata2")
        tileset = self.tilesets[m["tileset_id"]]
        names = tileset["tileset_names"]
        xs, ys, zs, cells = table(m["data"].data)
        canvas = Image.new("RGBA", (xs * TILE, ys * TILE), (0, 0, 0, 255))
        parallax = text(m["parallax_name"])
        if parallax and m["parallax_show"]:
            img = self.images.get("Parallaxes", parallax)
            if img is not None:
                for py in range(0, canvas.height, img.height):
                    for px in range(0, canvas.width, img.width):
                        canvas.alpha_composite(img, (px, py))
        shade = Image.new("RGBA", (HALF, HALF), (0, 0, 0, 128))
        for y in range(ys):
            for x in range(xs):
                for z in range(3):
                    self.draw_tile(canvas, names, cells[x + y * xs + z * xs * ys], x * TILE, y * TILE)
                bits = cells[x + y * xs + 3 * xs * ys] & 0x0F
                for q in range(4):
                    if bits & (1 << q):
                        canvas.alpha_composite(shade, (x * TILE + q % 2 * HALF, y * TILE + q // 2 * HALF))
        if events:
            for ev in sorted((m["events"] or {}).values(), key=lambda e: e["y"]):
                if ev["pages"]:
                    self.draw_event(canvas, names, ev["pages"][0], ev["x"], ev["y"])
        return canvas.convert("RGB")


if __name__ == "__main__":
    r = Renderer(sys.argv[1], sys.argv[2].split(";"))
    r.render(int(sys.argv[3])).save(sys.argv[4])
    if r.missing:
        print("missing tilesets", sorted(r.missing))
