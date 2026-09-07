#!/usr/bin/env python3
"""Gera inc/font_tiles.h — fonte 8x8 SMS-nativa (4bpp planar, cor 1).

A ROM nao tinha fonte alguma: o HUD do MVP pedia "nomes, barras, timer,
rounds" (doc/11-gdd.md) e so as barras existiam. Glifos sao autorais,
desenhados aqui em ASCII-art; nada vem de art_src_base/.

Charset (indice do tile = posicao na string CHARSET):
  0-9  A-Z  . ! : - espaco
"""
import os

CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.!:- "

# 8x8, '#' = pixel aceso. 6px de largura util + 2 de avanco.
GLYPHS = {
    "0": ("..###...", ".#...#..", ".#..##..", ".#.#.#..", ".##..#..", ".#...#..", "..###...", "........"),
    "1": ("...#....", "..##....", "...#....", "...#....", "...#....", "...#....", "..###...", "........"),
    "2": ("..###...", ".#...#..", ".....#..", "....#...", "...#....", "..#.....", ".#####..", "........"),
    "3": (".#####..", "....#...", "...#....", "....#...", ".....#..", ".#...#..", "..###...", "........"),
    "4": ("....##..", "...#.#..", "..#..#..", ".#...#..", ".#####..", ".....#..", ".....#..", "........"),
    "5": (".#####..", ".#......", ".####...", ".....#..", ".....#..", ".#...#..", "..###...", "........"),
    "6": ("..###...", ".#...#..", ".#......", ".####...", ".#...#..", ".#...#..", "..###...", "........"),
    "7": (".#####..", ".....#..", "....#...", "...#....", "..#.....", "..#.....", "..#.....", "........"),
    "8": ("..###...", ".#...#..", ".#...#..", "..###...", ".#...#..", ".#...#..", "..###...", "........"),
    "9": ("..###...", ".#...#..", ".#...#..", "..####..", ".....#..", ".#...#..", "..###...", "........"),
    "A": ("..###...", ".#...#..", ".#...#..", ".#####..", ".#...#..", ".#...#..", ".#...#..", "........"),
    "B": (".####...", ".#...#..", ".#...#..", ".####...", ".#...#..", ".#...#..", ".####...", "........"),
    "C": ("..###...", ".#...#..", ".#......", ".#......", ".#......", ".#...#..", "..###...", "........"),
    "D": (".####...", ".#...#..", ".#...#..", ".#...#..", ".#...#..", ".#...#..", ".####...", "........"),
    "E": (".#####..", ".#......", ".#......", ".####...", ".#......", ".#......", ".#####..", "........"),
    "F": (".#####..", ".#......", ".#......", ".####...", ".#......", ".#......", ".#......", "........"),
    "G": ("..###...", ".#...#..", ".#......", ".#..##..", ".#...#..", ".#...#..", "..###...", "........"),
    "H": (".#...#..", ".#...#..", ".#...#..", ".#####..", ".#...#..", ".#...#..", ".#...#..", "........"),
    "I": ("..###...", "...#....", "...#....", "...#....", "...#....", "...#....", "..###...", "........"),
    "J": ("...####.", ".....#..", ".....#..", ".....#..", ".....#..", ".#...#..", "..###...", "........"),
    "K": (".#...#..", ".#..#...", ".#.#....", ".##.....", ".#.#....", ".#..#...", ".#...#..", "........"),
    "L": (".#......", ".#......", ".#......", ".#......", ".#......", ".#......", ".#####..", "........"),
    "M": (".#...#..", ".##.##..", ".#.#.#..", ".#...#..", ".#...#..", ".#...#..", ".#...#..", "........"),
    "N": (".#...#..", ".##..#..", ".#.#.#..", ".#..##..", ".#...#..", ".#...#..", ".#...#..", "........"),
    "O": ("..###...", ".#...#..", ".#...#..", ".#...#..", ".#...#..", ".#...#..", "..###...", "........"),
    "P": (".####...", ".#...#..", ".#...#..", ".####...", ".#......", ".#......", ".#......", "........"),
    "Q": ("..###...", ".#...#..", ".#...#..", ".#...#..", ".#.#.#..", ".#..#...", "..##.#..", "........"),
    "R": (".####...", ".#...#..", ".#...#..", ".####...", ".#.#....", ".#..#...", ".#...#..", "........"),
    "S": ("..####..", ".#......", ".#......", "..###...", ".....#..", ".....#..", ".####...", "........"),
    "T": (".#####..", "...#....", "...#....", "...#....", "...#....", "...#....", "...#....", "........"),
    "U": (".#...#..", ".#...#..", ".#...#..", ".#...#..", ".#...#..", ".#...#..", "..###...", "........"),
    "V": (".#...#..", ".#...#..", ".#...#..", ".#...#..", ".#...#..", "..#.#...", "...#....", "........"),
    "W": (".#...#..", ".#...#..", ".#...#..", ".#.#.#..", ".#.#.#..", ".##.##..", ".#...#..", "........"),
    "X": (".#...#..", ".#...#..", "..#.#...", "...#....", "..#.#...", ".#...#..", ".#...#..", "........"),
    "Y": (".#...#..", ".#...#..", "..#.#...", "...#....", "...#....", "...#....", "...#....", "........"),
    "Z": (".#####..", ".....#..", "....#...", "...#....", "..#.....", ".#......", ".#####..", "........"),
    ".": ("........", "........", "........", "........", "........", "...##...", "...##...", "........"),
    "!": ("...#....", "...#....", "...#....", "...#....", "...#....", "........", "...#....", "........"),
    ":": ("........", "...##...", "...##...", "........", "...##...", "...##...", "........", "........"),
    "-": ("........", "........", "........", "..####..", "........", "........", "........", "........"),
    " ": ("........",) * 8,
}


def tile_bytes(rows, color=1, edge=15):
    """4bpp planar SMS: 4 bytes por linha (plano0..3).

    '#' = cor principal, 'o' = cor da moldura, '.' = transparente.
    """
    out = bytearray()
    for row in rows:
        planes = [0, 0, 0, 0]
        for bit, ch in enumerate(row):
            c = color if ch == "#" else (edge if ch == "o" else None)
            if c is None:
                continue
            for p in range(4):
                if c & (1 << p):
                    planes[p] |= 0x80 >> bit
        out += bytes(planes)
    return out


# Tiles de barra de vida. Antes o HUD reaproveitava tiles do palco ("tile 8
# (trim) e 6"), entao a barra do 1P saia azul-ceu e a do 2P saia listrada.
# Duas cores da pal_bg: 14 = amarelo (0x0F), 13 = vermelho (0x03).
#
# Com moldura escura, nao bloco chapado. Chapada, a barra virava o retangulo
# mais saturado da tela e o detector de gameplay do harness (maior blob
# saturado com forma de sprite) travava NELA em vez do lutador: o eixo
# reprovava por deslocamento zero mesmo com o input funcionando. A moldura na
# cor 15 (cinza, dessaturada) corta a conexao entre tiles vizinhos e devolve
# a leitura ao Ken. De quebra parece barra de luta, e nao uma tarja.
BAR_ROWS = ("oooooooo", "o######o", "o######o", "o######o",
            "o######o", "o######o", "oooooooo", "........")
BARS = [("BAR_FULL", 14), ("BAR_EMPTY", 13)]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, os.pardir, "inc", "font_tiles.h")
    data = bytearray()
    for ch in CHARSET:
        rows = GLYPHS[ch]
        assert len(rows) == 8 and all(len(r) == 8 for r in rows), ch
        data += tile_bytes(rows)

    lines = [
        "/* gerado por tools/make_font.py — NAO editar a mao. */",
        "#ifndef FONT_TILES_H",
        "#define FONT_TILES_H",
        f"#define FONT_TILES_COUNT {len(CHARSET)}",
        f'#define FONT_CHARSET "{CHARSET}"',
    ]
    for i, (name, color) in enumerate(BARS):
        data += tile_bytes(BAR_ROWS, color)
        lines.append(f"#define {name}_OFFSET {len(CHARSET) + i}")
    lines += [
        f"#define FONT_TILES_TOTAL {len(CHARSET) + len(BARS)}",
        f"#define FONT_TILES_SIZE {len(data)}",
        f"extern const unsigned char font_tiles[{len(data)}];",
        "#endif",
        "",
    ]
    open(dest, "w").write("\n".join(lines))

    src = os.path.join(here, os.pardir, "src", "font_data.c")
    body = []
    for i in range(0, len(data), 16):
        body.append("    " + ", ".join(f"0x{b:02X}" for b in data[i:i + 16]) + ",")
    open(src, "w").write(
        "/* gerado por tools/make_font.py — NAO editar a mao. */\n"
        '#include "font_tiles.h"\n\n'
        f"const unsigned char font_tiles[{len(data)}] = {{\n" + "\n".join(body) + "\n};\n"
    )
    print(f"[OK] {len(CHARSET)} glifos, {len(data)} bytes -> inc/font_tiles.h + src/font_data.c")


if __name__ == "__main__":
    main()
