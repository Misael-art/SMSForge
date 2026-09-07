#!/usr/bin/env python3
"""Deriva as poses de AGACHAR e PULAR a partir das folhas que já estão na ROM.

Por que não usar o `author_native_fighters.py`: ele chama `_fill_from_sheet`,
que recorta de `art_src_base/` — sheet `reference_only` da Capcom. Arte nova
não pode nascer dali (SMS_GLOBAL §15/§39). Aqui a entrada é `inc/*_tiles.h`,
ou seja, a arte que o projeto já autorou e já entrega; o que se faz é
remodelar a silhueta, não copiar pixel de fora.

O remapeamento é por FAIXA, não um esmagamento uniforme — esmagar tudo por
igual encolhe a cabeça junto e o lutador vira chibi. Tronco e pernas andam
com fatores diferentes:

  agachar: tronco desce e comprime pouco; pernas dobram (23 linhas -> 17).
           Os pés continuam na linha 63, então ele agacha no chão.
  pular:   tronco sobe um pouco; pernas recolhem para cima (joelho no peito),
           deixando a base do canvas vazia — é o que dá leitura de salto.

Uso: python3 tools/author_pose_variants.py [--check] [--preview]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, os.pardir)
INC = os.path.join(PROJ, "inc")

CANVAS_W, CANVAS_H = 32, 64
BLANK = tuple([0] * 32)

# (destino, base, transformacao)
JOBS = [("ken_crouch", "ken_idle", "crouch"),
        ("ken_jump", "ken_idle", "jump"),
        ("guile_crouch", "guile_idle", "crouch"),
        ("guile_jump", "guile_idle", "jump")]


def parse(nome):
    src = open(os.path.join(INC, nome + "_tiles.h")).read()
    tm = re.search(r"_tiles\[\d+\] = \{(.*?)\};", src, re.S)
    mm = re.search(r"_meta\[\] = \{(.*?)\};", src, re.S)
    vals = [int(x, 0) for x in re.findall(r"0x[0-9a-fA-F]+", tm.group(1))]
    tiles = [vals[i:i + 32] for i in range(0, len(vals), 32)]
    nums = [int(x) for x in re.findall(r"-?\d+", mm.group(2 - 1))]
    ent = []
    for i in range(0, len(nums) - 2, 3):
        if nums[i] == 128:
            break
        ent.append((nums[i], nums[i + 1], nums[i + 2]))
    return tiles, ent


def render(tiles, ent):
    cv = [[0] * CANVAS_W for _ in range(CANVAS_H)]
    for dx, dy, t in ent:
        for half in (0, 1):
            td = tiles[t + half]
            for y in range(8):
                planes = [td[y * 4 + p] for p in range(4)]
                oy = dy + half * 8 + y
                if not (0 <= oy < CANVAS_H):
                    continue
                for bit in range(8):
                    ox = dx + bit
                    if not (0 <= ox < CANVAS_W):
                        continue
                    c = sum((1 << p) for p in range(4)
                            if planes[p] & (0x80 >> bit))
                    if c:
                        cv[oy][ox] = c
    return cv


def band_map(out_y, bands):
    """Inverso do remapeamento por faixa: linha de saída -> (origem, escala_x)."""
    for (o0, o1, s0, s1, hx) in bands:
        if o0 <= out_y < o1:
            if o1 == o0:
                return s0, hx
            t = (out_y - o0) / float(o1 - o0)
            return int(round(s0 + t * (s1 - s0))), hx
    return None, 1.0


def reshape(cv, modo):
    """Topo real da figura manda: silhuetas diferentes começam em linhas
    diferentes, e fixar um valor deixaria uma das duas cortada."""
    ocupadas = [y for y in range(CANVAS_H) if any(cv[y])]
    if not ocupadas:
        return None
    topo, base = min(ocupadas), max(ocupadas)
    quadril = topo + int((base - topo) * 0.62)   # ~62% da altura = quadril

    # (linha_ini, linha_fim, origem_ini, origem_fim, escala_horizontal)
    if modo == "crouch":
        # tronco desce 18 px e comprime pouco; pernas dobram; pés no chão
        bands = [(topo + 18, 46, topo, quadril, 1.0),
                 (46, base + 1, quadril, base, 1.0)]
    else:  # jump
        # Pernas comprimidas TAMBEM na horizontal (0.6): so achatar na
        # vertical deixava o lutador de pernas abertas e plantadas, com cara
        # de idle esticado. Juntar as pernas e o que da leitura de joelho
        # recolhido. A base do canvas fica vazia — ele esta no ar.
        bands = [(topo + 6, 32, topo, quadril, 1.0),
                 (32, 46, quadril, base, 0.60)]

    cx = CANVAS_W // 2
    out = [[0] * CANVAS_W for _ in range(CANVAS_H)]
    for oy in range(CANVAS_H):
        sy, hx = band_map(oy, bands)
        if sy is None or not (0 <= sy < CANVAS_H):
            continue
        if hx == 1.0:
            out[oy] = list(cv[sy])
            continue
        for ox in range(CANVAS_W):
            sx = int(round(cx + (ox - cx) / hx))
            if 0 <= sx < CANVAS_W:
                out[oy][ox] = cv[sy][sx]
    return out


def pack(cv):
    """Canvas -> (tiles, meta) em SPRITEMODE_TALL, sem sprite vazio."""
    pares, ent = [], []
    for dy in range(0, CANVAS_H, 16):
        for dx in range(0, CANVAS_W, 8):
            par = []
            for half in (0, 1):
                t = bytearray(32)
                for y in range(8):
                    oy = dy + half * 8 + y
                    for x in range(8):
                        c = cv[oy][dx + x]
                        for p in range(4):
                            if c & (1 << p):
                                t[y * 4 + p] |= 0x80 >> x
                par.append(tuple(t))
            if par[0] == BLANK and par[1] == BLANK:
                continue
            key = (par[0], par[1])
            if key in pares:
                idx = pares.index(key)
            else:
                idx = len(pares)
                pares.append(key)
            ent.append((dx, dy, idx * 2))
    tiles = [t for par in pares for t in par]
    return tiles, ent


def emit(nome, tiles, ent):
    flat = [b for t in tiles for b in t]
    arr = "\n".join("    " + ", ".join(f"0x{b:02X}" for b in flat[i:i + 16]) + ","
                    for i in range(0, len(flat), 16))
    meta = "\n".join(f"    {dx}, {dy}, {t}," for dx, dy, t in ent) + \
           "\n    METASPRITE_END"
    up = nome.upper()
    open(os.path.join(INC, nome + "_tiles.h"), "w").write(
        f"/* gerado por tools/author_pose_variants.py a partir de {nome.split('_')[0]}_idle.\n"
        " * Remodelagem da silhueta que a ROM ja entrega. NENHUM pixel de\n"
        " * art_src_base/ (reference_only). NAO editar a mao. */\n"
        f"#define {up}_TILES_COUNT {len(tiles)}\n"
        f"#define {up}_TILES_SIZE {len(flat)}\n"
        f"const unsigned char {nome}_tiles[{len(flat)}] = {{\n{arr}\n}};\n"
        f"const signed char {nome}_meta[] = {{\n{meta}\n}};\n")
    return len(flat)


def main():
    check = "--check" in sys.argv
    total = 0
    previews = {}
    for dest, base, modo in JOBS:
        tiles, ent = parse(base)
        cv = reshape(render(tiles, ent), modo)
        if cv is None:
            print(f"{dest:14s} [SKIP] base vazia")
            continue
        nt, ne = pack(cv)
        n = len(nt) * 32
        total += n
        print(f"{dest:14s} <- {base:12s} {modo:6s}  "
              f"{len(ne):2d} sprites, {len(nt):2d} tiles, {n} B")
        previews[dest] = cv
        if not check:
            emit(dest, nt, ne)
    print(f"[{'CHECK' if check else 'OK'}] {total} B de arte nova")

    if "--preview" in sys.argv:
        from PIL import Image
        cols = list(previews)
        im = Image.new("P", (CANVAS_W * len(cols), CANVAS_H))
        pal = []
        for v in (0x00, 0x00, 0x3F, 0x1B, 0x06, 0x1F, 0x0A, 0x07,
                  0x02, 0x08, 0x04, 0x1A, 0x34, 0x0F, 0x03, 0x15):
            pal += [(v & 3) * 85, ((v >> 2) & 3) * 85, ((v >> 4) & 3) * 85]
        im.putpalette(pal + [0] * (768 - len(pal)))
        px = []
        for y in range(CANVAS_H):
            for c in cols:
                px += previews[c][y]
        im.putdata(px)
        out = os.path.join(PROJ, "rascunho", "pose_variants.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(out)
        print(f"     preview ({', '.join(cols)}) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
