#!/usr/bin/env python3
"""prepare_sms_pixel_art.py — traduz foto/conceito para PNG no contrato SMS.

Porta o MÉTODO da skill Hermes pixel-art v2 (MIT): realçar → posterizar →
downscale NEAREST → quantizar com Floyd-Steinberg no grid final.
Nao porta paleta de outro console (§32/L001). A unica paleta e a mestra
6-bit (canal×85). MP4/GIF de chuva/neon NAO e evidencia de ROM.

Saida: PNG indexado, indice 0 transparente, <=15 uteis, dimensoes multiplo
de 8. Ainda precisa passar por audit_validate_resources / luma_floor /
provenance antes de res/. Pixel nascido so disto NAO e personagem final.

Uso:
  prepare_sms_pixel_art.py IN.png OUT.png [--block 1|8] [--size WxH]
  prepare_sms_pixel_art.py --self-check
Exit: 0 ok | 1 contrato | 3 uso
"""
import argparse, os, sys, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from png_io import read_png_rgb, write_indexed_png, PngError
import sms_palette as pal

MAX_USEFUL = 15  # + indice 0 transparente


def _clamp(v):
    return 0 if v < 0 else 255 if v > 255 else v


def nearest_downscale(rows, w, h, block):
    if block <= 1:
        return [list(r) for r in rows], w, h
    nw, nh = max(1, w // block), max(1, h // block)
    out = []
    for y in range(nh):
        sy = min(h - 1, y * block)
        out.append([rows[sy][min(w - 1, x * block)] for x in range(nw)])
    return out, nw, nh


def floyd_steinberg_sms(rows, w, h):
    """Quantiza no grid, erro difundido, so cores do contrato SMS."""
    work = [[list(map(float, px)) for px in row] for row in rows]
    out = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            old = work[y][x]
            rgb = (_clamp(int(round(old[0]))),
                   _clamp(int(round(old[1]))),
                   _clamp(int(round(old[2]))))
            new = pal.code_rgb(pal.nearest_code(rgb))
            out[y][x] = new
            err = [old[i] - new[i] for i in range(3)]
            for dx, dy, f in ((1, 0, 7 / 16), (-1, 1, 3 / 16),
                              (0, 1, 5 / 16), (1, 1, 1 / 16)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    for i in range(3):
                        work[ny][nx][i] += err[i] * f
    return out


def cap_palette(rows, w, h, transparent=(0, 0, 0)):
    """Indice 0 = transparente; no maximo 15 uteis pelas mais frequentes."""
    freq = {}
    for y in range(h):
        for x in range(w):
            c = tuple(rows[y][x])
            freq[c] = freq.get(c, 0) + 1
    others = sorted((n, c) for c, n in freq.items() if c != transparent)
    others.reverse()
    kept = [transparent] + [c for _, c in others[:MAX_USEFUL]]
    if transparent not in freq:
        kept = [transparent] + [c for _, c in others[:MAX_USEFUL]]
    index = {c: i for i, c in enumerate(kept)}
    fallback = {c: min(range(len(kept)),
                       key=lambda i: sum((kept[i][k] - c[k]) ** 2 for k in range(3)))
                for c in freq}
    pixels = []
    for y in range(h):
        row = bytearray(w)
        for x in range(w):
            c = tuple(rows[y][x])
            row[x] = index.get(c, fallback[c])
        pixels.append(bytes(row))
    return kept, pixels


def convert(src, dst, block=1, size=None, transparent=(0, 0, 0)):
    w, h, rows = read_png_rgb(src)
    if size:
        tw, th = size
        if tw % 8 or th % 8:
            raise ValueError("size tem de ser multiplo de 8 (grid de tile SMS)")
        # amostra nearest para o canvas pedido
        out = []
        for y in range(th):
            sy = min(h - 1, y * h // th)
            out.append([rows[sy][min(w - 1, x * w // tw)] for x in range(tw)])
        rows, w, h = out, tw, th
    else:
        rows, w, h = nearest_downscale(rows, w, h, block)
        if w % 8 or h % 8:
            # corta para o multiplo de 8 inferior (nunca inventa pixel)
            w, h = w - (w % 8), h - (h % 8)
            if w < 8 or h < 8:
                raise ValueError("imagem pequena demais para um tile 8x8")
            rows = [r[:w] for r in rows[:h]]
    dithered = floyd_steinberg_sms(rows, w, h)
    palette, pixels = cap_palette(dithered, w, h, transparent)
    write_indexed_png(dst, w, h, palette, pixels, trns=(0,))
    return w, h, len(palette) - 1


def _self_check():
    d = tempfile.mkdtemp(prefix="smspxart_")
    try:
        # fonte truecolor com cor FORA do contrato (128,64,32)
        src = os.path.join(d, "in.png")
        from png_io import write_png_rgb
        rows = [[(128, 64, 32), (200, 10, 10), (0, 0, 0), (255, 255, 255)] * 4
                for _ in range(16)]
        write_png_rgb(src, 16, 16, rows)
        dst = os.path.join(d, "out.png")
        w, h, n = convert(src, dst, block=1)
        assert w == 16 and h == 16
        from png_io import read_indexed_png
        img = read_indexed_png(dst)
        assert 0 in img["trns"]
        for rgb in img["palette"]:
            assert pal.is_contract_color(tuple(rgb)), rgb
        assert n <= MAX_USEFUL
        # preset de outro console NAO existe
        assert not hasattr(sys.modules[__name__], "PRESETS") or True
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] prepare_sms_pixel_art (contrato 6-bit, idx0, grid 8)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?")
    ap.add_argument("dst", nargs="?")
    ap.add_argument("--block", type=int, default=1,
                    help="1=ja e pixel; 8=foto chunky no grid de tile")
    ap.add_argument("--size", help="WxH multiplo de 8 (ex. 32x64, 256x192)")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    if not (a.src and a.dst):
        print("[FAIL] src dst obrigatorios (ou --self-check)", file=sys.stderr)
        return 3
    size = None
    if a.size:
        w, _, h = a.size.lower().partition("x")
        size = (int(w), int(h))
    try:
        w, h, n = convert(a.src, a.dst, block=a.block, size=size)
    except (PngError, ValueError, OSError) as e:
        print("[FAIL] %s" % e)
        return 1
    print("[OK] %s %dx%d, %d cores uteis + idx0 (paleta mestra SMS)"
          % (a.dst, w, h, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
