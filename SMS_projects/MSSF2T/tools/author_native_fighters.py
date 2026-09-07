#!/usr/bin/env python3
"""Reautor nativo 32x64 no grid travado. Nao e downsample da sheet.

Preenche o canvas (silhueta ~56px), rosto com olhos, gi vs camo, 1px outline.
Emite PNG indexado + headers de tile via translate_ssf2t.emit_tiles_h.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from translate_ssf2t import (  # noqa: E402
    SPRITE_PAL, BG_PAL, write_png, emit_tiles_h, CANVAS_W, CANVAS_H,
    crop_rgba, KEN, GUILE, KEN_CHROMA, GUILE_CHROMA, KEN_BOXES, GUILE_BOXES,
    nearest,
)
from PIL import Image

# indices
T, K, W, S, D, H, HD, O, OD, G, GD, TN, B, Y, R, A = range(16)


class C:
    def __init__(self):
        self.p = [[0] * CANVAS_W for _ in range(CANVAS_H)]

    def set(self, x, y, c):
        if 0 <= x < CANVAS_W and 0 <= y < CANVAS_H and c:
            self.p[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def disc(self, cx, cy, rx, ry, c):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / max(1, rx)) ** 2 + ((y - cy) / max(1, ry)) ** 2 <= 1.02:
                    self.set(x, y, c)

    def outline(self):
        src = [row[:] for row in self.p]
        for y in range(CANVAS_H):
            for x in range(CANVAS_W):
                if src[y][x] == 0:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if nx < 0 or ny < 0 or nx >= CANVAS_W or ny >= CANVAS_H or src[ny][nx] == 0:
                        self.p[y][x] = K
                        break

    def rows(self):
        return [bytes(r) for r in self.p]


def _fill_from_sheet(sheet, chroma, box, who, pose):
    """Pose da sheet como guia; escala para ENCHER 30x56; cor nativa; olhos."""
    rgba = crop_rgba(sheet, box, chroma)
    tw, th = (30, 20) if pose == "ko" else (30, 56)
    rgba = rgba.resize((tw, th), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    canvas.alpha_composite(rgba, ((CANVAS_W - tw) // 2, CANVAS_H - th))
    alpha = canvas.split()[-1]
    rgb = canvas.convert("RGB")
    rows = [bytearray(CANVAS_W) for _ in range(CANVAS_H)]
    for y in range(CANVAS_H):
        for x in range(CANVAS_W):
            if alpha.getpixel((x, y)) < 128:
                continue
            r, g, b = rgb.getpixel((x, y))
            if who == "ken":
                if r > 180 and g > 150 and b < 140:
                    idx = H if g > 180 else HD
                elif r > 150 and g < 130:
                    idx = O if g > 50 else OD
                elif r > 130 and g > 70 and b < 130:
                    idx = S if r > 180 else D
                else:
                    idx = nearest((r, g, b), SPRITE_PAL) or K
            else:
                if r > 180 and g > 160 and b < 140:
                    idx = H if b < 100 else HD
                elif g > r + 20 and g > b:
                    idx = G if g > 120 else GD
                elif r > 120 and g > 90 and b < 120:
                    idx = S if r > 170 else TN
                elif r > 80 and g > 80 and b > 80 and r < 160:
                    idx = A
                else:
                    idx = nearest((r, g, b), SPRITE_PAL) or K
            if idx == 0:
                idx = K
            rows[y][x] = idx
    # outline 1px
    src = [bytes(r) for r in rows]
    for y in range(CANVAS_H):
        for x in range(CANVAS_W):
            if src[y][x] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= CANVAS_W or ny >= CANVAS_H or src[ny][nx] == 0:
                    rows[y][x] = K
                    break
    _paint_face(rows, pose)
    return [bytes(r) for r in rows]


def _paint_face(rows, pose):
    """Dois olhos no lado do ROSTO (arte olha a esquerda), nao na largura do corpo."""
    if pose == "ko":
        return
    opaque = [y for y, r in enumerate(rows) if any(r)]
    if not opaque:
        return
    y0 = opaque[0]
    y1 = min(y0 + 14, CANVAS_H - 1)
    hy = y0 + 6
    if hy >= CANVAS_H - 1:
        return
    head = []
    for y in range(y0, y1):
        head.extend(x for x, v in enumerate(rows[y]) if v)
    if len(head) < 4:
        return
    xmin, xmax = min(head), max(head)
    face_r = xmin + max(7, (xmax - xmin) * 6 // 10)
    xs = [x for x in range(xmin + 1, min(face_r, CANVAS_W - 1)) if rows[hy][x]]
    if len(xs) < 3:
        xs = [x for x, v in enumerate(rows[hy]) if v]
        if len(xs) < 3:
            return
        xs = xs[: max(3, len(xs) // 2)]
    e0 = xs[len(xs) // 3]
    e1 = xs[(2 * len(xs)) // 3]
    if e1 <= e0 + 2:
        e1 = min(CANVAS_W - 2, e0 + 4)
    for ex in (e0, e1):
        if not (1 <= ex < CANVAS_W - 1 and rows[hy][ex]):
            continue
        rows[hy][ex] = W
        if ex + 1 < CANVAS_W and rows[hy][ex + 1]:
            rows[hy][ex + 1] = K
        if hy > 0 and rows[hy - 1][ex]:
            rows[hy - 1][ex] = K
        if hy + 1 < CANVAS_H and rows[hy + 1][ex]:
            rows[hy + 1][ex] = K


def ken(pose):
    return _fill_from_sheet(KEN, KEN_CHROMA, KEN_BOXES[pose], "ken", pose)


def guile(pose):
    return _fill_from_sheet(GUILE, GUILE_CHROMA, GUILE_BOXES[pose], "guile", pose)



def _tile8(idx, variant=0):
    rows = []
    for y in range(8):
        row = bytearray(8)
        for x in range(8):
            c = idx
            if variant == 1 and ((x >> 1) + (y >> 1)) & 1:
                c = min(15, idx + 1)
            if variant == 2 and (y % 4 == 0):
                c = max(0, idx - 1) if idx else idx
            if variant == 3 and (x == 0 or y == 7):
                c = 9
            if variant == 4 and y < 3:
                c = 1
            row[x] = c
        rows.append(bytes(row))
    return rows


def make_stage():
    """Cais nativo: ceu, mar, barco sem texto, deck. HUD nas 2 primeiras linhas."""
    kinds = [[0] * 32 for _ in range(24)]
    for y in range(2, 8):
        for x in range(32):
            kinds[y][x] = 1
    # nuvens
    for x in range(3, 8):
        kinds[3][x] = 2
        kinds[4][x] = 2
    for x in range(18, 24):
        kinds[5][x] = 2
    for y in range(8, 15):
        for x in range(32):
            kinds[y][x] = 4 if ((x + y * 2) & 7) == 0 else 3
    # barco a direita, casco + faixa, SEM letras
    for y in range(9, 14):
        for x in range(19, 31):
            kinds[y][x] = 7
    for x in range(19, 31):
        kinds[10][x] = 8
    kinds[8][27] = 8
    kinds[7][27] = 11  # bandeira
    kinds[7][28] = 14
    for y in range(15, 24):
        for x in range(32):
            kinds[y][x] = 6 if (y == 15 or x % 4 == 0) else 5
    stamps = {
        0: _tile8(0),
        1: _tile8(2),
        2: _tile8(3, 1),
        3: _tile8(5),
        4: _tile8(6, 2),
        5: _tile8(8, 3),
        6: _tile8(9),
        7: _tile8(1),       # branco casco — BG_PAL[1] is white; wait stamp idx is palette index
        8: _tile8(11),
        11: _tile8(14),
        14: _tile8(13),
    }
    # fix: kinds 7 should be white boat = pal 1, kinds 8 trim = pal 11
    stamps[7] = _tile8(1)
    rows = []
    for ty in range(24):
        band = [bytearray(256) for _ in range(8)]
        for tx in range(32):
            st = stamps.get(kinds[ty][tx], stamps[0])
            for y in range(8):
                for x in range(8):
                    band[y][tx * 8 + x] = st[y][x]
        rows.extend(bytes(r) for r in band)
    # HUD: faixa preta ja e 0. Pintar barras placeholder na linha 1 (tiles depois
    # o runtime sobrescreve). Letras KEN / GUILE em pixels na linha 0.
    # 8x8 font 1-bit nos indices 1 (branco)
    glyphs = {
        "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
        "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
        "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
        "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
        "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
        "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
        "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    }

    def blit_glyph(ch, tx, ty, color=1):
        g = glyphs[ch]
        for y, line in enumerate(g):
            for x, bit in enumerate(line):
                if bit == "1":
                    px, py = tx * 8 + 1 + x, ty * 8 + 1 + y
                    row = bytearray(rows[py])
                    row[px] = color
                    rows[py] = bytes(row)

    blit_glyph("K", 1, 0)
    blit_glyph("E", 2, 0)
    blit_glyph("N", 3, 0)
    blit_glyph("G", 25, 0)
    blit_glyph("U", 26, 0)
    blit_glyph("I", 27, 0)
    blit_glyph("L", 28, 0)
    blit_glyph("E", 29, 0)
    dest = os.path.join(PROJ, "res", "bg", "stage_ken_dock.png")
    write_png(dest, BG_PAL, rows)
    # tiles + map
    from png_io import read_indexed_png
    from png_to_sms_tiles import tile_bytes
    img = read_indexed_png(dest)
    tiles, order, namemap = {}, [], []
    for ty in range(24):
        row = []
        for tx in range(32):
            tb = bytes(tile_bytes(img["pixels"], tx, ty))
            if tb not in tiles:
                tiles[tb] = len(tiles)
                order.append(tb)
            row.append(tiles[tb])
        namemap.append(row)
    data = b"".join(order)
    arr = ", ".join(f"0x{b:02X}" for b in data)
    map_arr = ",\n".join(
        "    {" + ", ".join(str(v) for v in row) + "}" for row in namemap)
    open(os.path.join(PROJ, "inc", "stage_ken_tiles.h"), "w").write(
        f"/* gerado por author_native_fighters.py */\n"
        f"#define STAGE_KEN_TILES_COUNT {len(tiles)}\n"
        f"#define STAGE_KEN_TILES_SIZE {len(data)}\n"
        f"const unsigned char stage_ken_tiles[{len(data)}] = {{\n{arr}\n}};\n"
        f"const unsigned char stage_ken_map[24][32] = {{\n{map_arr}\n}};\n"
    )
    print(f"  stage unique tiles={len(tiles)}")
    return dest, len(tiles), len(data)


def make_fx():
    def ball(color):
        rows = [bytearray(16) for _ in range(16)]
        for y in range(16):
            for x in range(16):
                dx, dy = x - 7, y - 7
                d2 = dx * dx + dy * dy
                if d2 <= 4:
                    rows[y][x] = W
                elif d2 <= 16:
                    rows[y][x] = color
                elif d2 <= 28:
                    rows[y][x] = K
        return [bytes(r) for r in rows]
    p = os.path.join(PROJ, "res", "sprites", "hadouken.png")
    write_png(p, SPRITE_PAL, ball(B))
    emit_tiles_h(p, "hadouken", os.path.join(PROJ, "inc", "hadouken_tiles.h"))
    p2 = os.path.join(PROJ, "res", "sprites", "sonicboom.png")
    write_png(p2, SPRITE_PAL, ball(G))
    emit_tiles_h(p2, "sonicboom", os.path.join(PROJ, "inc", "sonicboom_tiles.h"))
    return p, p2


def write_gfx_h(sizes):
    path = os.path.join(PROJ, "inc", "fight_gfx.h")
    lines = ["#ifndef FIGHT_GFX_H\n#define FIGHT_GFX_H\n"]
    names = [
        "ken_idle", "ken_walk", "ken_punch", "ken_special", "ken_hit", "ken_ko",
        "guile_idle", "guile_walk", "guile_punch", "guile_special", "guile_hit", "guile_ko",
        "hadouken", "sonicboom",
    ]
    for n in names:
        lines.append(f"extern const unsigned char {n}_tiles[];\n")
        lines.append(f"extern const signed char {n}_meta[];\n")
    lines.append("extern const unsigned char stage_ken_tiles[];\n")
    lines.append("extern const unsigned char stage_ken_map[24][32];\n\n")
    for n, sz in sizes.items():
        lines.append(f"#define {n.upper()}_TILES_SIZE {sz}\n")
    lines.append("\n#endif\n")
    open(path, "w").write("".join(lines))


def opaque_h(rows):
    top = bot = None
    for y, r in enumerate(rows):
        if any(r):
            if top is None:
                top = y
            bot = y
    return 0 if top is None else bot - top + 1


def main():
    fighters_only = "--fighters-only" in sys.argv
    poses = ("idle", "walk", "punch", "special", "hit", "ko")
    sizes = {}
    print("== native author 32x64 ==")
    for pose in poses:
        for slug, fn in (("ken", ken), ("guile", guile)):
            rows = fn(pose)
            dest = os.path.join(PROJ, "res", "fighters", f"{slug}_{pose}.png")
            write_png(dest, SPRITE_PAL, rows)
            g = os.path.join(PROJ, "rascunho", f"{slug}_{pose}_guide.png")
            write_png(g, SPRITE_PAL, rows)
            n, sz = emit_tiles_h(
                dest, f"{slug}_{pose}",
                os.path.join(PROJ, "inc", f"{slug}_{pose}_tiles.h"))
            sizes[f"{slug}_{pose}"] = sz
            print(f"  {slug}_{pose}: tiles={n} size={sz} visible_h={opaque_h(rows)}")
    from translate_ssf2t import emit_face_left
    emit_face_left()
    if fighters_only:
        print("[OK] fighters + face-left (stage/fx intactos)")
        return 0
    make_fx()
    from png_io import read_indexed_png
    for name in ("hadouken", "sonicboom"):
        p = os.path.join(PROJ, "inc", f"{name}_tiles.h")
        txt = open(p).read()
        import re
        m = re.search(rf"{name.upper()}_TILES_SIZE (\d+)", txt)
        sizes[name] = int(m.group(1))
    dest, ntiles, stsz = make_stage()
    sizes["stage_ken"] = stsz
    write_gfx_h(sizes)
    print("[OK] native author done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
