#!/usr/bin/env python3
"""Reempacota as folhas de lutador: menos tiles, menos sprites por pose.

Depois que fix_sprite_transparency.py removeu o retangulo placeholder, boa
parte dos sprites 8x16 do Ken ficou 100% transparente, mas continuava
ocupando ROM, ocupando VRAM e — pior — gastando um dos 8 sprites por
scanline do VDP. Este passo:

  1. descarta a entrada de metasprite cujo par de tiles e todo transparente;
  2. deduplica PARES de tiles iguais (par, nao tile solto: SPRITEMODE_TALL
     exige que o segundo tile seja o primeiro + 1);
  3. renumera os indices e reescreve tiles, meta, _COUNT e _SIZE.

O canvas renderizado e comparado antes/depois: se um pixel mudar, o arquivo
nao e gravado. Menos bytes por pose tambem significa pose na tela em menos
frames, porque o stream e limitado por STREAM_BYTES por frame.

Uso: python3 tools/repack_sheets.py [--check]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INC = os.path.join(HERE, os.pardir, "inc")

SHEETS = ["ken_idle", "ken_walk", "ken_punch", "ken_special", "ken_hit",
          "ken_ko", "guile_idle", "guile_walk", "guile_punch",
          "guile_special", "guile_hit", "guile_ko"]
BLANK = tuple([0] * 32)


def parse(path):
    src = open(path).read()
    tm = re.search(r"(\w+)_tiles\[(\d+)\] = \{(.*?)\};", src, re.S)
    mm = re.search(r"(\w+)_meta\[\] = \{(.*?)\};", src, re.S)
    vals = [int(x, 0) for x in re.findall(r"0x[0-9a-fA-F]+", tm.group(3))]
    tiles = [tuple(vals[i:i + 32]) for i in range(0, len(vals), 32)]
    nums = [int(x) for x in re.findall(r"-?\d+", mm.group(2))]
    ent = []
    for i in range(0, len(nums) - 2, 3):
        if nums[i] == 128:
            break
        ent.append((nums[i], nums[i + 1], nums[i + 2]))
    return src, tm, mm, tiles, ent


def render(tiles, ent):
    """Canvas -> cor, do jeito que o VDP monta (cada entrada = 8x16)."""
    px = {}
    for dx, dy, t in ent:
        for half in (0, 1):
            td = tiles[t + half]
            for y in range(8):
                planes = [td[y * 4 + p] for p in range(4)]
                for bit in range(8):
                    c = sum((1 << p) for p in range(4)
                            if planes[p] & (0x80 >> bit))
                    if c:
                        px[(dx + bit, dy + half * 8 + y)] = c
    return px


def main():
    check = "--check" in sys.argv
    old_total = new_total = 0
    for name in SHEETS:
        path = os.path.join(INC, name + "_tiles.h")
        src, tm, mm, tiles, ent = parse(path)
        before = render(tiles, ent)

        pairs, new_ent = [], []
        for dx, dy, t in ent:
            pair = (tiles[t], tiles[t + 1])
            if pair == (BLANK, BLANK):
                continue
            if pair in pairs:
                idx = pairs.index(pair)
            else:
                idx = len(pairs)
                pairs.append(pair)
            new_ent.append((dx, dy, idx * 2))

        new_tiles = [t for pair in pairs for t in pair]
        if render(new_tiles, new_ent) != before:
            print(f"{name:15s} [ABORT] o canvas mudou — nao gravado")
            continue

        old_total += len(tiles) * 32
        new_total += len(new_tiles) * 32
        print(f"{name:15s} sprites {len(ent):2d}->{len(new_ent):2d}  "
              f"tiles {len(tiles):2d}->{len(new_tiles):2d}  "
              f"{len(tiles) * 32:5d}B->{len(new_tiles) * 32:5d}B")
        if check:
            continue

        flat = [b for t in new_tiles for b in t]
        body = "\n".join(
            "    " + ", ".join(f"0x{b:02X}" for b in flat[i:i + 16]) + ","
            for i in range(0, len(flat), 16))
        meta_body = "\n".join(f"    {dx}, {dy}, {t}," for dx, dy, t in new_ent)
        meta_body += "\n    METASPRITE_END"

        out = src
        out = out[:mm.start(2)] + "\n" + meta_body + "\n" + out[mm.end(2):]
        # recalcula as posicoes do bloco de tiles apos mexer no meta
        tm2 = re.search(r"(\w+)_tiles\[(\d+)\] = \{(.*?)\};", out, re.S)
        out = out[:tm2.start(3)] + "\n" + body + "\n" + out[tm2.end(3):]
        out = out.replace(f"_tiles[{tm.group(2)}]", f"_tiles[{len(flat)}]")
        up = name.upper()
        out = re.sub(rf"#define {up}_TILES_COUNT \d+",
                     f"#define {up}_TILES_COUNT {len(new_tiles)}", out)
        out = re.sub(rf"#define {up}_TILES_SIZE \d+",
                     f"#define {up}_TILES_SIZE {len(flat)}", out)
        open(path, "w").write(out)

    print(f"[{'CHECK' if check else 'OK'}] {old_total}B -> {new_total}B "
          f"(economia {old_total - new_total}B)")


if __name__ == "__main__":
    main()
