#!/usr/bin/env python3
"""Torna transparente o fundo das folhas do Ken.

As folhas do Ken sairam do translate_ssf2t.py com o fundo do canvas na cor
12 da paleta de sprites (pal_spr[12] = 0x34, azul), nao na cor 0. Como a cor
0 e a unica transparente em sprite no VDP do SMS, o Ken aparecia dentro de um
retangulo azul opaco de 32x64 — visivel na evidencia de gameplay desde antes
desta sessao. As folhas do Guile ja usavam a cor 0 e estavam certas.

O placeholder e um retangulo solido da cor 12 com moldura de 1px na cor 1, e
o Ken foi desenhado POR CIMA dele. Apagamos exatamente esse retangulo e essa
moldura; a moldura so e removida se estiver 100% na cor 1, para nao comer
arte de verdade caso outra folha nao siga o padrao.

Uso: python3 tools/fix_sprite_transparency.py [--check]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INC = os.path.join(HERE, os.pardir, "inc")

SHEETS = ["ken_idle", "ken_walk", "ken_punch", "ken_special", "ken_hit", "ken_ko"]
BG_COLOR = 12


def parse(path):
    src = open(path).read()
    tm = re.search(r"_tiles\[\d+\] = \{(.*?)\};", src, re.S)
    mm = re.search(r"_meta\[\] = \{(.*?)\};", src, re.S)
    vals = [int(x, 0) for x in re.findall(r"0x[0-9a-fA-F]+", tm.group(1))]
    tiles = [vals[i:i + 32] for i in range(0, len(vals), 32)]
    nums = [int(x) for x in re.findall(r"-?\d+", mm.group(1))]
    ent = []
    for i in range(0, len(nums) - 2, 3):
        if nums[i] == 128:
            break
        ent.append((nums[i], nums[i + 1], nums[i + 2]))
    return src, tm, tiles, ent


def px_get(tile, x, y):
    return sum((1 << p) for p in range(4) if tile[y * 4 + p] & (0x80 >> x))


def px_clear(tile, x, y):
    for p in range(4):
        tile[y * 4 + p] &= ~(0x80 >> x) & 0xFF


def main():
    check = "--check" in sys.argv
    total = 0
    for name in SHEETS:
        path = os.path.join(INC, name + "_tiles.h")
        src, tm, tiles, ent = parse(path)

        # canvas -> (tile, x, y); SPRITEMODE_TALL: cada entrada = 8x16 (t, t+1)
        pos = {}
        for dx, dy, t in ent:
            for half in (0, 1):
                for y in range(8):
                    for x in range(8):
                        pos[(dx + x, dy + half * 8 + y)] = (t + half, x, y)

        xs = [p[0] for p in pos]
        ys = [p[1] for p in pos]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)

        def col(p):
            t, tx, ty = pos[p]
            return px_get(tiles[t], tx, ty)

        # O placeholder e um retangulo solido da cor de fundo, cercado por
        # uma moldura de 1px na cor 1 — o Ken foi desenhado POR CIMA dele.
        fill = [p for p in pos if col(p) == BG_COLOR]
        if not fill:
            print(f"{name:14s} sem cor{BG_COLOR} — nada a fazer")
            continue
        fx0 = min(p[0] for p in fill); fx1 = max(p[0] for p in fill)
        fy0 = min(p[1] for p in fill); fy1 = max(p[1] for p in fill)

        ring = [p for p in pos
                if fx0 - 1 <= p[0] <= fx1 + 1 and fy0 - 1 <= p[1] <= fy1 + 1
                and (p[0] in (fx0 - 1, fx1 + 1) or p[1] in (fy0 - 1, fy1 + 1))]
        frame = [p for p in ring if col(p) == 1]
        # A moldura tem de ser solida; se nao for, a folha nao segue o padrao
        # e apagar a cor 1 comeria arte de verdade.
        if len(frame) != len(ring):
            print(f"{name:14s} [SKIP] moldura nao solida "
                  f"({len(frame)}/{len(ring)} px na cor 1)")
            continue

        seen = set(fill) | set(frame)
        inner = 0
        print(f"{name:14s} placeholder={len(fill):5d}px  moldura={len(frame):3d}px  "
              f"caixa=({fx0},{fy0})-({fx1},{fy1})")
        total += len(seen)
        if check:
            continue

        for (cx, cy) in seen:
            t, tx, ty = pos[(cx, cy)]
            px_clear(tiles[t], tx, ty)

        flat = [b for t in tiles for b in t]
        body = "\n".join(
            "    " + ", ".join(f"0x{b:02X}" for b in flat[i:i + 16]) + ","
            for i in range(0, len(flat), 16))
        open(path, "w").write(src[:tm.start(1)] + "\n" + body + "\n" + src[tm.end(1):])

    print(f"[{'CHECK' if check else 'OK'}] {total} pixels de fundo")


if __name__ == "__main__":
    main()
