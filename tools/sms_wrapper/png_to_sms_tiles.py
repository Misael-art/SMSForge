#!/usr/bin/env python3
"""png_to_sms_tiles.py — converte PNG indexado (contrato SMSForge) em tiles SMS 4bpp.

Formato de tile SMS: **4 planos de bits**, 4 bytes por linha
(plano0..plano3 = bits 0..3 do indice de cor), MSB-first => **32 bytes por tile**.
Isso casa com `SMS_loadTiles(src,tilefrom,size)`, que e
`SMS_VRAMmemcpy((tilefrom)*32, src, size)` — SMSlib.h:130 e a autoridade.

CORRECAO 2026-08-31 (raiz profunda do L006): esta ferramenta emitia 2 planos
(16 bytes/tile) enquanto o projeto carregava com SMS_loadTiles (caminho 4bpp).
Cada par de "tiles" de 16B era lido como UM tile de 32B, embaralhando quadrantes
e planos — a arte nunca chegava intacta a VRAM. Sintoma: sprite invisivel ou
corrompido, atribuido por semanas ao modo de sprite.
Para dados de 2 planos existe caminho proprio: `SMS_load2bppTiles` (SMSlib.h:132).

Um sprite 16x16 consome 4 tiles sequenciais (quadrantes TL,TR,BL,BR);
um 8x8 consome 1. BG idem por tile.

Uso: png_to_sms_tiles.py <in.png> [--name hero_tiles] [-o saida.h]
     png_to_sms_tiles.py --self-check
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png_io import read_indexed_png, PngError

def tile_bytes(px_rows, tx, ty):
    """Extrai tile 8x8 em (tx,ty) [em tiles] e codifica os 4 planos (32 bytes)."""
    out = bytearray()
    for y in range(8):
        row = px_rows[ty * 8 + y]
        planes = [0, 0, 0, 0]
        for x in range(8):
            c = row[tx * 8 + x] & 15          # 16 cores por subpaleta
            bit = 7 - x
            for p in range(4):
                planes[p] |= ((c >> p) & 1) << bit
        out += bytes(planes)
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
        # 8x8 = UM tile = 32 bytes (4 planos x 8 linhas). 16 seria 2bpp (L006).
        assert len(tb) == 32, f"tile 8x8 deve ter 32B (4bpp), veio {len(tb)}B"
        # linha 0: cor 1 em x0 -> plano0 bit7; cor 2 em x7 -> plano1 bit0
        assert tb[0] == 0b10000000, tb[:4].hex()
        assert tb[1] == 0b00000001, tb[:4].hex()
        assert tb[2] == 0 and tb[3] == 0, "cores 1 e 2 nao acendem planos 2/3"

        # REGRESSAO 4bpp: indice 15 tem que acender os QUATRO planos.
        # Com o bug antigo (c & 3) a cor 15 virava 3 e os planos 2/3 ficavam zerados.
        px15 = [bytes([15] * 8)] + [bytes([0] * 8) for _ in range(7)]
        p15 = os.path.join(d, "t15.png")
        write_indexed_png(p15, 8, 8, [(0, 0, 0)] * 16, px15)
        t15 = convert(p15)
        assert t15[0:4] == b"\xff\xff\xff\xff", \
            f"cor 15 deve acender os 4 planos (4bpp), veio {t15[0:4].hex()}"

        # 16x16 = 4 tiles = 128 bytes
        px16 = [bytes([1] * 16) for _ in range(16)]
        p16 = os.path.join(d, "t16.png")
        write_indexed_png(p16, 16, 16, pal, px16)
        assert len(convert(p16)) == 128, "16x16 deve render 4 tiles (128B)"

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
