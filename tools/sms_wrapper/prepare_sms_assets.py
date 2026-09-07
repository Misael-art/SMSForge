#!/usr/bin/env python3
"""Prepara fontes raster para um demonstrador SMS.

Este utilitario e deliberadamente mecanico: nao desenha formas nem escolhe
composicao. Ele faz crop/escala, quantiza para a grade de cor do SMS, escreve
PNGs indexados auditaveis e deduplica tiles 8x8 para um header C.
"""
import argparse
import os
import sys
from collections import OrderedDict

from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from png_io import write_indexed_png

SMS_RGB = [(r * 85, g * 85, b * 85)
           for r in range(4) for g in range(4) for b in range(4)]

# Uma unica subpaleta para hero, sentinela e FX. Os indices dos headers gerados
# passam a significar a mesma cor em qualquer entidade.
SPRITE_PALETTE = [
    (0, 0, 0), (0, 0, 0), (85, 0, 85), (170, 85, 170),
    (0, 85, 85), (0, 85, 170), (0, 255, 255), (85, 85, 85),
    (255, 255, 255), (170, 170, 85), (255, 255, 170), (85, 0, 85),
    (170, 0, 170), (170, 85, 170), (255, 85, 85), (170, 85, 85),
]


def nearest_sms(rgb):
    return min(SMS_RGB, key=lambda p: sum((p[i] - rgb[i]) ** 2 for i in range(3)))


def compact_palette(image, colors=15):
    rgb = image.convert("RGB")
    q = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                     dither=Image.Dither.NONE).convert("RGB")
    ranked = OrderedDict()
    for c in q.getdata():
        sms = nearest_sms(c)
        ranked[sms] = ranked.get(sms, 0) + 1
    selected = sorted(ranked, key=ranked.get, reverse=True)[:colors]
    return [(0, 0, 0)] + selected


def indexed_from_rgba(im, size, sprite, dilate_sprite=False, bg_brightness=1.0,
                      bg_logical=(64, 48)):
    rgba = im.convert("RGBA")
    alpha = rgba.getchannel("A")
    if sprite:
        bbox = alpha.point(lambda a: 255 if a >= 128 else 0).getbbox()
        if bbox:
            rgba = rgba.crop(bbox)
        scale = min((size - 2) / max(1, rgba.width),
                    (size - 2) / max(1, rgba.height))
        nw = max(1, int(round(rgba.width * scale)))
        nh = max(1, int(round(rgba.height * scale)))
        rgba = rgba.resize((nw, nh), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.alpha_composite(rgba, ((size - nw) // 2, (size - nh) // 2))
        rgba = canvas
    else:
        # O VDP nao tem compressao de tile. Uma reducao logica 4x4 cria
        # clusters nativos e mede o custo real antes de aceitar o fundo.
        logical = rgba.convert("RGB").resize(bg_logical, Image.Resampling.BOX)
        rgba = logical.resize((256, 192), Image.Resampling.NEAREST).convert("RGBA")

    binary_alpha = rgba.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    if sprite:
        # A fonte autoral já chega com matte binário confiável. Dilation aqui
        # criava um halo/matte navy nos vazios do recorte e transformava
        # personagens em blocos azuis no modo ZOOMED. Se uma fonte futura
        # precisar de fechamento, isso deve ser uma decisão visual registrada,
        # nunca um efeito implícito do conversor.
        if dilate_sprite:
            binary_alpha = binary_alpha.filter(ImageFilter.MaxFilter(5))
        rgba.putalpha(binary_alpha)
    rgb = rgba.convert("RGB")
    if not sprite and bg_brightness != 1.0:
        rgb = ImageEnhance.Brightness(rgb).enhance(bg_brightness)
    if sprite:
        palette = SPRITE_PALETTE
        first_useful = 1
    else:
        # O text renderer do SMSlib usa BG[1] como tinta. Reserva-lo evita
        # que a fonte da arena seja repintada de branco na inicializacao.
        palette = [(0, 0, 0), (255, 255, 255)] + compact_palette(rgb, 14)[1:]
        first_useful = 2
    rows = []
    for y in range(rgba.height):
        row = bytearray()
        for x in range(rgba.width):
            if sprite and binary_alpha.getpixel((x, y)) == 0:
                row.append(0)
                continue
            c = rgb.getpixel((x, y))
            if sprite and c == (0, 0, 0):
                # Preto interno da fonte e alpha transparente compartilham
                # RGB=0. Dentro da silhueta ele vira navy para que o corpo
                # continue legível no fundo navy e forme um bloco mensurável.
                c = (0, 0, 170)
            # index 0 e reservado para transparencia; visual solida com a
            # mesma cor recebe o primeiro slot util.
            idx = min(range(first_useful, len(palette)),
                      key=lambda i: sum((palette[i][k] - c[k]) ** 2 for k in range(3)))
            row.append(idx)
        rows.append(bytes(row))
    return rgba.width, rgba.height, palette, rows


def prepare_png(source, dest, sprite, size=16, dilate_sprite=False, bg_brightness=1.0,
                bg_logical=(64, 48)):
    im = Image.open(source)
    w, h, palette, rows = indexed_from_rgba(im, size, sprite, dilate_sprite,
                                             bg_brightness, bg_logical)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    write_indexed_png(dest, w, h, palette, rows, trns=(0,))
    print(f"[OK] {os.path.relpath(dest)} {w}x{h} cores={len(set(sum((list(r) for r in rows), [])))-1}")


def prepare_boss_quadrants(source, root, prefix="boss"):
    """Traduz um boss 32x32 em quatro assets 16x16 nativos.

    O runtime monta os quadrantes como uma metasprite de 16 celulas 8x8.
    Assim o auditor de recursos continua medindo PNGs no grid suportado pelo
    SMS, enquanto a identidade visual pode ocupar uma massa maior na tela.
    """
    im = Image.open(source)
    w, h, palette, rows = indexed_from_rgba(im, 32, True)
    if (w, h) != (32, 32):
        raise SystemExit("boss deve resultar em canvas 32x32")
    for label, x0, y0 in (("tl", 0, 0), ("tr", 16, 0),
                          ("bl", 0, 16), ("br", 16, 16)):
        quadrant = [row[x0:x0 + 16] for row in rows[y0:y0 + 16]]
        dest = os.path.join(root, f"res/sprites/{prefix}_{label}.png")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        write_indexed_png(dest, 16, 16, palette, quadrant, trns=(0,))
        used = len({v for row in quadrant for v in row if v})
        print(f"[OK] {os.path.relpath(dest)} 16x16 cores={used}")


def tile_bytes(rows, tx, ty):
    out = bytearray()
    for y in range(8):
        planes = [0, 0, 0, 0]
        for x in range(8):
            c = rows[ty * 8 + y][tx * 8 + x] & 15
            bit = 7 - x
            for p in range(4):
                planes[p] |= ((c >> p) & 1) << bit
        out.extend(planes)
    return bytes(out)


def build_bg_header(png_path, header_path, prefix="arena", tile_base=64, max_tiles=192):
    from png_io import read_indexed_png
    img = read_indexed_png(png_path)
    if (img["w"], img["h"]) != (256, 192):
        raise SystemExit("fundo deve ser 256x192")
    unique = OrderedDict()
    tilemap = []
    for ty in range(24):
        for tx in range(32):
            raw = tile_bytes(img["pixels"], tx, ty)
            if raw not in unique:
                unique[raw] = len(unique)
            tilemap.append(tile_base + unique[raw])
    if len(unique) > max_tiles:
        raise SystemExit(f"fundo exige {len(unique)} tiles, limite reservado {max_tiles}")
    data = b"".join(unique.keys())
    os.makedirs(os.path.dirname(header_path), exist_ok=True)
    with open(header_path, "w", encoding="utf-8") as f:
        upper = prefix.upper()
        f.write(f"/* gerado por prepare_sms_assets.py; fundo derivado de {prefix}.png */\n")
        f.write(f"#define {upper}_BG_TILE_BASE {tile_base}\n")
        f.write(f"#define {upper}_BG_TILE_COUNT {len(unique)}\n")
        f.write(f"#define {upper}_BG_TILE_BYTES {len(data)}\n")
        f.write(f"const unsigned char {prefix}_bg_tiles[{upper}_BG_TILE_BYTES] = {{\n")
        f.write(",".join(f"0x{b:02X}" for b in data))
        f.write("\n};\n")
        f.write(f"const unsigned char {prefix}_bg_map[32 * 24 * 2] = {{\n")
        # SMSlib escreve cada entrada do mapa como tile de 16 bits; a arena
        # fica abaixo de 256, entao o byte alto permanece zero.
        f.write(",".join(str(v & 0xFF) + ",0" for v in tilemap))
        f.write("\n};\n")
    print(f"[OK] {os.path.relpath(header_path)} unique_tiles={len(unique)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hero", required=True)
    ap.add_argument("--enemy", required=True)
    ap.add_argument("--boss", required=True)
    ap.add_argument("--hero-walk")
    ap.add_argument("--hero-walk-1")
    ap.add_argument("--hero-walk-2")
    ap.add_argument("--hero-walk-3")
    ap.add_argument("--hero-left")
    ap.add_argument("--boss-charge")
    ap.add_argument("--boss-hurt")
    ap.add_argument("--boss-dead")
    ap.add_argument("--impact")
    ap.add_argument("--impact-0")
    ap.add_argument("--impact-2")
    ap.add_argument("--shot", required=True)
    ap.add_argument("--counter", required=True)
    ap.add_argument("--arena", required=True)
    ap.add_argument("--title")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = args.out
    prepare_png(args.hero, os.path.join(root, "res/sprites/hero.png"), True)
    if args.hero_walk:
        prepare_png(args.hero_walk, os.path.join(root, "res/sprites/hero_walk.png"), True)
        # Pose 0 mantém o nome legado; as demais poses são assets separados
        # na ROM e entram no mesmo HERO_TILE por streaming.
        for pose, source in enumerate((args.hero_walk, args.hero_walk_1,
                                        args.hero_walk_2, args.hero_walk_3)):
            if source:
                prepare_png(source, os.path.join(root, f"res/sprites/hero_walk_{pose}.png"), True)
    if args.hero_left:
        prepare_png(args.hero_left, os.path.join(root, "res/sprites/hero_left.png"), True)
    prepare_png(args.enemy, os.path.join(root, "res/sprites/enemy.png"), True)
    prepare_boss_quadrants(args.boss, root)
    if args.boss_charge:
        prepare_boss_quadrants(args.boss_charge, root, prefix="boss_charge")
    if args.boss_hurt:
        prepare_boss_quadrants(args.boss_hurt, root, prefix="boss_hurt")
    if args.boss_dead:
        prepare_boss_quadrants(args.boss_dead, root, prefix="boss_dead")
    # Ataques 8x8 precisam preservar a direção e os vazios do recorte; a
    # dilatação das silhuetas grandes transforma um projétil em bloco.
    prepare_png(args.shot, os.path.join(root, "res/sprites/shot.png"),
                True, 8, dilate_sprite=False)
    if args.impact:
        # FX pequeno precisa manter alpha nos cantos; a dilatacao usada nas
        # silhuetas de personagens transformaria o burst em um quadrado cheio.
        prepare_png(args.impact, os.path.join(root, "res/sprites/impact.png"),
                    True, 8, dilate_sprite=False)
        for frame, source in ((0, args.impact_0), (1, args.impact),
                              (2, args.impact_2)):
            if source:
                prepare_png(source, os.path.join(root, f"res/sprites/impact_{frame}.png"),
                            True, 8, dilate_sprite=False)
    prepare_png(args.counter, os.path.join(root, "res/sprites/counter.png"),
                True, 8, dilate_sprite=False)
    prepare_png(args.arena, os.path.join(root, "res/bg/arena.png"), False)
    build_bg_header(os.path.join(root, "res/bg/arena.png"),
                    os.path.join(root, "inc/arena_bg_tiles.h"), prefix="arena")
    if args.title:
        prepare_png(args.title, os.path.join(root, "res/bg/title.png"), False,
                    bg_brightness=2.5, bg_logical=(32, 24))
        build_bg_header(os.path.join(root, "res/bg/title.png"),
                        os.path.join(root, "inc/title_bg_tiles.h"), prefix="title")


if __name__ == "__main__":
    main()
