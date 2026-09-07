#!/usr/bin/env python3
"""Traduz sheets reference_only de SSF2T para pixel SMS-nativo 32x64 / palco 256x192.

Nao promove o rip. Recorta, escala NEAREST, quantiza no grid 6-bit, aplica
contorno 1px e clusters. Saida: rascunho/ (guia) + res/ (candidato nativo).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, ".."))
SRC = os.path.join(PROJ, "art_src_base")
sys.path.insert(0, os.path.join(PROJ, "..", "..", "tools", "sms_wrapper"))
from png_io import write_indexed_png  # noqa: E402
from png_to_sms_tiles import tile_bytes  # noqa: E402

CANVAS_W, CANVAS_H = 32, 64
SMS_RGB = [(r * 85, g * 85, b * 85)
           for r in range(4) for g in range(4) for b in range(4)]

# Subpaleta de SPRITE compartilhada (Ken + Guile + FX). Indice 0 = transparente.
SPRITE_PAL = [
    (0, 0, 0),          # 0 transparent / unused
    (0, 0, 0),          # 1 outline
    (255, 255, 255),    # 2 white
    (255, 170, 85),     # 3 skin
    (170, 85, 0),       # 4 skin dark
    (255, 255, 85),     # 5 hair
    (170, 170, 0),      # 6 hair dark
    (255, 85, 0),       # 7 ken gi
    (170, 0, 0),        # 8 ken gi dark
    (0, 170, 0),        # 9 guile green
    (0, 85, 0),         # 10 guile green dark
    (170, 170, 85),     # 11 tan / camo light
    (0, 85, 255),       # 12 projectile
    (255, 255, 0),      # 13 spark
    (255, 0, 0),        # 14 hit
    (85, 85, 85),       # 15 gray
]

BG_PAL = [
    (0, 0, 0),
    (255, 255, 255),
    (85, 170, 255),     # sky
    (170, 255, 255),    # cloud
    (0, 0, 170),        # sea dark
    (0, 85, 170),       # sea
    (0, 170, 255),      # sea light
    (170, 85, 0),       # wood
    (255, 170, 85),     # wood light
    (85, 0, 0),         # wood dark
    (255, 255, 255),    # boat
    (255, 85, 0),       # boat trim
    (170, 170, 170),    # boat gray
    (255, 0, 0),        # hud red
    (255, 255, 0),      # hud yellow
    (0, 85, 85),        # hud teal
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def nearest(rgb, pal):
    return min(range(len(pal)),
               key=lambda i: sum((pal[i][c] - rgb[c]) ** 2 for c in range(3)))


def crop_rgba(path, box, chroma):
    im = Image.open(path).convert("RGBA")
    crop = im.crop(box)
    px = crop.load()
    w, h = crop.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 128 or (abs(r - chroma[0]) + abs(g - chroma[1]) + abs(b - chroma[2]) < 40):
                px[x, y] = (0, 0, 0, 0)
    # trim
    bbox = crop.split()[-1].point(lambda a: 255 if a >= 128 else 0).getbbox()
    if bbox:
        crop = crop.crop(bbox)
    return crop


def fit_canvas(rgba):
    """Scale NEAREST to fit 32x64, bottom-center, binary alpha."""
    w, h = rgba.size
    scale = min((CANVAS_W - 2) / max(1, w), (CANVAS_H - 2) / max(1, h))
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    rgba = rgba.resize((nw, nh), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    canvas.alpha_composite(rgba, ((CANVAS_W - nw) // 2, CANVAS_H - nh))
    return canvas


def to_indexed(rgba, pal, outline=True):
    w, h = rgba.size
    alpha = rgba.split()[-1]
    rgb = rgba.convert("RGB")
    rows = [bytearray(w) for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if alpha.getpixel((x, y)) < 128:
                rows[y][x] = 0
            else:
                idx = nearest(rgb.getpixel((x, y)), pal)
                if idx == 0:
                    idx = 1
                rows[y][x] = idx
    if outline:
        src = [bytes(r) for r in rows]
        for y in range(h):
            for x in range(w):
                if src[y][x] == 0:
                    continue
                edge = False
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if nx < 0 or ny < 0 or nx >= w or ny >= h or src[ny][nx] == 0:
                        edge = True
                        break
                if edge:
                    rows[y][x] = 1
    # drop isolated pixels
    src = [bytes(r) for r in rows]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if src[y][x] == 0:
                continue
            n = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if src[y + dy][x + dx] != 0)
            if n == 0:
                rows[y][x] = 0
    # Olhos: dois pontos no terco superior da silhueta (identidade a 32x64).
    opaque_ys = [y for y, r in enumerate(rows) if any(r)]
    if opaque_ys:
        hy = opaque_ys[0] + 6
        if hy < h:
            xs = [x for x, v in enumerate(rows[hy]) if v]
            if len(xs) >= 4:
                c = (xs[0] + xs[-1]) // 2
                for ex in (c - 2, c + 2):
                    if 0 <= ex < w and rows[hy][ex]:
                        rows[hy][ex] = 2
                        if hy + 1 < h and rows[hy + 1][ex]:
                            rows[hy + 1][ex] = 1
    return [bytes(r) for r in rows]


def write_png(path, pal, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_indexed_png(path, len(rows[0]), len(rows), pal, rows, trns=(0,))


def _pack_tiles(pixels, w, h):
    tw, th = w // 8, h // 8
    data = bytearray()
    meta = []
    tile_i = 0
    # SPRITEMODE_TALL: um sprite 8x16 = dois tiles 8x8 consecutivos (par=topo).
    zeros = bytes(32)
    for ty in range(0, th, 2):
        for tx in range(tw):
            top = bytes(tile_bytes(pixels, tx, ty))
            bot = bytes(tile_bytes(pixels, tx, ty + 1)) if ty + 1 < th else zeros
            if all(b == 0 for b in top) and all(b == 0 for b in bot):
                continue
            data += top + bot
            meta.append((tx * 8, ty * 8, tile_i))
            tile_i += 2
    return data, meta, tile_i


def emit_tiles_h(png_path, name, out_h):
    from png_io import read_indexed_png
    img = read_indexed_png(png_path)
    w, h = img["w"], img["h"]
    data, meta, tile_i = _pack_tiles(img["pixels"], w, h)
    arr = ", ".join(f"0x{b:02X}" for b in data)
    meta_l = []
    for dx, dy, ti in meta:
        meta_l.append(f"    {dx}, {dy}, {ti}")
    body = (
        f"/* gerado por translate_ssf2t.py a partir de {os.path.basename(png_path)} */\n"
        f"#define {name.upper()}_TILES_COUNT {tile_i}\n"
        f"#define {name.upper()}_TILES_SIZE {len(data)}\n"
        f"const unsigned char {name}_tiles[{len(data)}] = {{\n{arr}\n}};\n"
        f"const signed char {name}_meta[] = {{\n" +
        ",\n".join(meta_l) + ",\n    METASPRITE_END\n};\n"
    )
    open(out_h, "w").write(body)
    return tile_i, len(data)


def emit_hflip_tiles_h(png_path, name, out_h):
    """Espelho horizontal no PNG, depois retile. Sem bitrev no Z80."""
    from png_io import read_indexed_png
    img = read_indexed_png(png_path)
    w, h = img["w"], img["h"]
    flipped = [bytes(reversed(row)) for row in img["pixels"]]
    data, meta, tile_i = _pack_tiles(flipped, w, h)
    arr = ", ".join(f"0x{b:02X}" for b in data)
    meta_l = [f"    {dx}, {dy}, {ti}" for dx, dy, ti in meta]
    uname = name.upper()
    body = (
        f"/* gerado por translate_ssf2t.py H-flip de {os.path.basename(png_path)} */\n"
        f"#define {uname}_TILES_COUNT {tile_i}\n"
        f"#define {uname}_TILES_SIZE {len(data)}\n"
        f"const unsigned char {name}_tiles[{len(data)}] = {{\n{arr}\n}};\n"
        f"const signed char {name}_meta[] = {{\n" +
        ",\n".join(meta_l) + ",\n    METASPRITE_END\n};\n"
    )
    open(out_h, "w").write(body)
    return tile_i, len(data)


def emit_face_left():
    """Guile (P2) sempre nasce olhando esquerda. Ken _l so idle/walk."""
    jobs = []
    for pose in ("idle", "walk", "punch", "special", "hit", "ko"):
        jobs.append((f"res/fighters/guile_{pose}.png", f"guile_{pose}_l"))
    jobs.append(("res/fighters/ken_idle.png", "ken_idle_l"))
    jobs.append(("res/fighters/ken_walk.png", "ken_walk_l"))
    jobs.append(("res/fighters/ken_punch.png", "ken_punch_l"))
    jobs.append(("res/fighters/ken_special.png", "ken_special_l"))
    jobs.append(("res/sprites/sonicboom.png", "sonicboom_l"))
    jobs.append(("res/sprites/hadouken.png", "hadouken_l"))
    total = 0
    for rel, name in jobs:
        png = os.path.join(PROJ, rel)
        out_h = os.path.join(PROJ, "inc", f"{name}_tiles.h")
        n, nbytes = emit_hflip_tiles_h(png, name, out_h)
        total += nbytes
        print(f"  {name}: {n} tiles, {nbytes}B -> {out_h}")
    print(f"[OK] face-left {total}B de tiles extra")
    return total


KEN = os.path.join(SRC, "sprites", "ken_arcade_st_v1.png")
GUILE = os.path.join(SRC, "sprites", "guile_arcade_st_v1.png")
STAGE = os.path.join(SRC, "backgrounds", "stages", "stage_ken_arcade_v1.png")
KEN_CHROMA = (0, 85, 127)
GUILE_CHROMA = (67, 70, 181)

# Recortes medidos na sheet (reference_only).
KEN_BOXES = {
    "idle": (1, 900, 81, 991),
    "walk": (82, 900, 162, 991),
    "punch": (244, 900, 324, 991),
    "special": (325, 900, 405, 991),
    "hit": (325, 992, 405, 1088),
    "ko": (1, 1412, 113, 1508),
}
GUILE_BOXES = {
    "idle": (22, 393, 97, 483),
    "walk": (17, 553, 101, 644),
    "punch": (430, 394, 506, 483),
    "special": (485, 554, 545, 644),
    "hit": (415, 712, 498, 811),
    "ko": (25, 713, 95, 811),
}


def translate_fighter(sheet, chroma, boxes, slug):
    out = {}
    for pose, box in boxes.items():
        rgba = crop_rgba(sheet, box, chroma)
        guide = fit_canvas(rgba)
        gpath = os.path.join(PROJ, "rascunho", f"{slug}_{pose}_guide.png")
        os.makedirs(os.path.dirname(gpath), exist_ok=True)
        guide.save(gpath)
        rows = to_indexed(guide, SPRITE_PAL, outline=True)
        dest = os.path.join(PROJ, "res", "fighters", f"{slug}_{pose}.png")
        write_png(dest, SPRITE_PAL, rows)
        emit_tiles_h(dest, f"{slug}_{pose}",
                     os.path.join(PROJ, "inc", f"{slug}_{pose}_tiles.h"))
        out[pose] = dest
        print(f"  {slug}_{pose}: {dest}")
    return out


def make_fx():
    # hadouken 16x16 (2x2 tiles) — blue disk with white core
    rows = [bytearray(16) for _ in range(16)]
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7, y - 7
            d2 = dx * dx + dy * dy
            if d2 <= 4:
                rows[y][x] = 2
            elif d2 <= 16:
                rows[y][x] = 12
            elif d2 <= 25:
                rows[y][x] = 1
            else:
                rows[y][x] = 0
    p = os.path.join(PROJ, "res", "sprites", "hadouken.png")
    write_png(p, SPRITE_PAL, [bytes(r) for r in rows])
    emit_tiles_h(p, "hadouken", os.path.join(PROJ, "inc", "hadouken_tiles.h"))
    # sonic boom — green crescent
    rows = [bytearray(16) for _ in range(16)]
    for y in range(16):
        for x in range(16):
            dx, dy = x - 6, y - 7
            d2 = dx * dx + dy * dy
            if 9 <= d2 <= 25 and dx >= -2:
                rows[y][x] = 9 if d2 > 16 else 2
            elif d2 <= 8:
                rows[y][x] = 0
            elif abs(dx) + abs(dy) == 6:
                rows[y][x] = 1
    p2 = os.path.join(PROJ, "res", "sprites", "sonicboom.png")
    write_png(p2, SPRITE_PAL, [bytes(r) for r in rows])
    emit_tiles_h(p2, "sonicboom", os.path.join(PROJ, "inc", "sonicboom_tiles.h"))
    return p, p2


def _tile8(color_idx, variant=0):
    rows = []
    for y in range(8):
        row = bytearray(8)
        for x in range(8):
            c = color_idx
            if variant == 1 and ((x + y) & 3) == 0:
                c = min(15, color_idx + 1)
            if variant == 2 and (y & 1):
                c = max(0, color_idx - 1) if color_idx else color_idx
            if variant == 3 and x in (0, 7):
                c = 8  # wood dark grout
            row[x] = c
        rows.append(bytes(row))
    return rows


def make_stage():
    """OBSOLETO — nao chamar. Ver a nota em main(): esta funcao escreve pixel
    reference_only da Capcom em inc/stage_ken_tiles.h. Mantida so como
    registro do caminho que foi abandonado."""
    """Palco nativo por metatile. Sem wordmark, sem 552 tiles unicos."""
    # map 32x24 of tile kinds (not unique pixels)
    # 0 black HUD, 1 sky, 2 cloud, 3 sea, 4 sea hi, 5 wood, 6 wood grout,
    # 7 boat, 8 trim, 9 waterline
    kinds = [[0] * 32 for _ in range(24)]
    for y in range(3, 8):
        for x in range(32):
            kinds[y][x] = 2 if (y == 4 and 4 <= x <= 8) or (y == 5 and 18 <= x <= 22) else 1
    for y in range(8, 15):
        for x in range(32):
            kinds[y][x] = 4 if ((x + y) & 3) == 0 else 3
    # boat silhouette right side, no letters
    for y in range(9, 14):
        for x in range(20, 31):
            kinds[y][x] = 7
    for x in range(20, 31):
        kinds[9][x] = 8
    kinds[8][28] = 8  # flag
    kinds[7][28] = 14
    for y in range(15, 24):
        for x in range(32):
            kinds[y][x] = 6 if (y == 15 or (x & 3) == 0) else 5
    # rasterize from 8x8 kind stamps
    stamps = {
        0: _tile8(0),
        1: _tile8(2),
        2: _tile8(3, 1),
        3: _tile8(5, 2),
        4: _tile8(6, 1),
        5: _tile8(8, 3),
        6: _tile8(9),
        7: _tile8(10),
        8: _tile8(11),
        14: _tile8(14),
    }
    rows = []
    for ty in range(24):
        band = [bytearray(256) for _ in range(8)]
        for tx in range(32):
            st = stamps.get(kinds[ty][tx], stamps[0])
            for y in range(8):
                for x in range(8):
                    band[y][tx * 8 + x] = st[y][x]
        rows.extend(bytes(r) for r in band)
    dest = os.path.join(PROJ, "res", "bg", "stage_ken_dock.png")
    write_png(dest, BG_PAL, rows)
    # tile-dedup BG
    from png_io import read_indexed_png
    img = read_indexed_png(dest)
    tiles = {}
    order = []
    namemap = []
    for ty in range(24):
        row = []
        for tx in range(32):
            tb = bytes(tile_bytes(img["pixels"], tx, ty))
            if tb not in tiles:
                tiles[tb] = len(tiles)
                order.append(tb)
            row.append(tiles[tb])
        namemap.append(row)
    if len(tiles) > 96:
        print(f"[WARN] stage unique tiles {len(tiles)} > 96 (budget BG 0-95)")
    data = b"".join(order)
    arr = ", ".join(f"0x{b:02X}" for b in data)
    map_arr = ",\n".join(
        "    {" + ", ".join(str(v) for v in row) + "}" for row in namemap)
    open(os.path.join(PROJ, "inc", "stage_ken_tiles.h"), "w").write(
        f"/* gerado por translate_ssf2t.py */\n"
        f"#define STAGE_KEN_TILES_COUNT {len(tiles)}\n"
        f"#define STAGE_KEN_TILES_SIZE {len(data)}\n"
        f"const unsigned char stage_ken_tiles[{len(data)}] = {{\n{arr}\n}};\n"
        f"const unsigned char stage_ken_map[24][32] = {{\n{map_arr}\n}};\n"
    )
    print(f"  stage: {len(tiles)} unique tiles -> {dest}")
    return dest, len(tiles)


def main():
    if "--face-left" in sys.argv:
        emit_face_left()
        return 0
    print("== translate MSSF2T ==")
    ken = translate_fighter(KEN, KEN_CHROMA, KEN_BOXES, "ken")
    guile = translate_fighter(GUILE, GUILE_CHROMA, GUILE_BOXES, "guile")
    fx = make_fx()
    # make_stage() NAO e mais chamado. Ele reamostrava o PNG do palco direto
    # de art_src_base/ para inc/stage_ken_tiles.h, ou seja: punha pixel da
    # Capcom na ROM, contra SMS_GLOBAL §15/§39, o README do projeto, o GDD e
    # o provenance_manifest.json ("reference_only"). Ficou como codigo morto e
    # era uma armadilha: bastava rodar este script para sobrescrever o cais
    # autoral. O palco de entrega vem de tools/author_stage_ken.py.
    emit_face_left()
    print("[OK] translation done "
          "(palco NAO gerado aqui — use tools/author_stage_ken.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
