#!/usr/bin/env python3
"""png_to_sms_tiles.py — converte PNG indexado (contrato SMSForge) em tiles SMS 4bpp.

Formato de tile SMS: por linha, 2 bytes (plano0=bit baixo da cor, plano1=bit alto),
MSB-first. Um sprite 16x16 consome 4 tiles sequenciais (quadrantes TL,TR,BL,BR);
um 8x8 consome 1. BG idem por tile.

Uso: png_to_sms_tiles.py <in.png> [--name hero_tiles] [-o saida.h]
     png_to_sms_tiles.py --self-check
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png_io import read_indexed_png, PngError

def tile_bytes(px_rows, tx, ty):
    """Extrai tile 8x8 em (tx,ty) [em pixels*8] e codifica 2 planos."""
    out = bytearray()
    for y in range(8):
        row = px_rows[ty * 8 + y]
        p0 = p1 = 0
        for x in range(8):
            c = row[tx * 8 + x] & 3
            bit = 7 - x
            p0 |= ((c & 1) << bit)
            p1 |= ((c >> 1) << bit)
        out += bytes([p0, p1])
    return out

def convert(path):
    img = read_indexed_png(path)
    w, h = img["w"], img["h"]
    if (w, h) not in ((8, 8), (16, 16)):
        raise PngError(f"{path}: sprite deve ser 8x8 ou 16x16")
    order = [(0, 0)] if w == 8 else [(0, 0), (1, 0), (0, 1), (1, 1)]
    data = bytearray()
    for tx, ty in order:
        data += tile_bytes(img["pixels"], tx, ty)
    return bytes(data)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("png", nargs="?")
    ap.add_argument("--name", default="hero_tiles")
    ap.add_argument("-o", "--out")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        import tempfile
        from png_io import write_indexed_png
        d = tempfile.mkdtemp(prefix="smstile_")
        pal = [(0, 0, 0), (255, 255, 255), (170, 170, 170)]
        px = []
        for y in range(8):
            px.append(bytes([(1 if x == y else (2 if x == 7 - y else 0)) for x in range(8)]))
        p = os.path.join(d, "t.png")
        write_indexed_png(p, 8, 8, pal, px)
        tb = convert(p)
        assert len(tb) == 16
        # linha 0: branco em x0 -> plano0 bit7; vermelho em x7 -> plano1 bit0
        assert tb[0] == 0b10000000 and tb[1] == 0b00000001, tb[:2].hex()
        shutil_rmtree_safe(d)
        print("[SELF-CHECK OK] png_to_sms_tiles")
        return 0
    if not a.png:
        print("[FAIL] informe o png", file=sys.stderr)
        return 3
    data = convert(a.png)
    if a.out:
        arr = ", ".join(f"0x{b:02X}" for b in data)
        open(a.out, "w").write(
            f"/* gerado por png_to_sms_tiles.py a partir de {os.path.basename(a.png)} */\n"
            f"#define {a.name.upper()}_SIZE {len(data)}\n"
            f"const unsigned char {a.name}[{len(data)}] = {{\n{arr}\n}};\n")
        print(f"[OK] {len(data)}B -> {a.out}")
    else:
        print(data.hex())
    return 0

def shutil_rmtree_safe(d):
    import shutil
    shutil.rmtree(d, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(main())
