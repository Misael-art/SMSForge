#!/usr/bin/env python3
"""Autora o cais do Ken — pixel art SMS-nativa, 256x192, 4bpp.

REGRA: nenhum pixel de art_src_base/ entra aqui. Aquelas sheets sao
`reference_only` (Capcom, rip da comunidade) e a lei do workspace
(SMS_GLOBAL §15/§39, repetida no README do projeto, no GDD e no
provenance_manifest.json) manda que a arte da ROM seja autoral SMS-nativa
DERIVADA da referencia, nunca o rip. A referencia foi usada como REGUA:
linha do horizonte, proporcao ceu/mar/deck, iate atracado a direita,
tabuas em perspectiva. Todo pixel abaixo e desenhado por este script.

Bandas (linhas de tela) — casam com o parallax por raster em fight.c:
     0..15    HUD            (H-scroll travado no VDP)
    16..63    ceu + nuvens   (scroll lento)
    64..111   mar longe + iate atracado (estatico: barco nao desliza)
   112..127   mar perto      (scroll mais rapido)
  128..191    deck           (estatico)

Uso: python3 tools/author_stage_ken.py [--preview]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, os.pardir)

W, H = 256, 192
COLS, ROWS = 32, 24

# Indices 0, 1, 13 e 14 sao travados: HUD preto, fonte branca, barra
# vermelha/amarela (src/hud.c). O resto e a paleta do cais.
PAL = [
    0x00,  # 0  preto (HUD)
    0x3F,  # 1  branco (fonte, casco, espuma)
    0x39,  # 2  ceu
    0x3E,  # 3  nuvem / ceu palido
    0x35,  # 4  ceu alto
    0x28,  # 5  mar medio
    0x20,  # 6  mar fundo
    0x2D,  # 7  mar claro / brilho
    0x1B,  # 8  madeira media
    0x06,  # 9  madeira escura (junta)
    0x2F,  # 10 madeira clara
    0x07,  # 11 laranja (friso, barril)
    0x2A,  # 12 cinza (cabine, metal)
    0x03,  # 13 vermelho (barra) — travado
    0x0F,  # 14 amarelo (barra) — travado
    0x15,  # 15 cinza escuro (contorno)
]

SKY_Y0, SKY_Y1 = 16, 63
SEA_Y0, SEA_Y1 = 64, 111
NEAR_Y0, NEAR_Y1 = 112, 127
DECK_Y0 = 128


def new_canvas():
    return [[0] * W for _ in range(H)]


def px(c, x, y, v):
    if 0 <= y < H:
        c[y][x % W] = v          # wrap: bandas com scroll nao podem ter costura


def hline(c, x0, x1, y, v):
    for x in range(x0, x1 + 1):
        px(c, x, y, v)


def rect(c, x0, y0, x1, y1, v):
    for y in range(y0, y1 + 1):
        hline(c, x0, x1, y, v)


def blob(c, cx, cy, rx, ry, v):
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            dx = (x - cx) / float(rx)
            dy = (y - cy) / float(ry)
            if dx * dx + dy * dy <= 1.0:
                px(c, x, y, v)


def draw_sky(c):
    # Trocas de cor em multiplos de 8 para nao criar uma linha de tiles so
    # por causa da fronteira.
    for y in range(SKY_Y0, SKY_Y1 + 1):
        hline(c, 0, W - 1, y, 4 if y < 32 else 2)
    for y in range(56, SKY_Y1 + 1):
        hline(c, 0, W - 1, y, 3 if y >= 61 else 2)

    # Duas formas de nuvem, repetidas em x MULTIPLO DE 8: instancias iguais
    # caem no mesmo grid e o dedup de tiles reaproveita todas. Nuvens em
    # posicoes livres custavam ~45 tiles; assim custam ~15.
    def cloud(cx, cy, rx, ry):
        blob(c, cx, cy, rx, ry, 3)
        blob(c, cx - 8, cy - 1, rx // 2, max(1, ry - 2), 1)

    for cx in (32, 128, 224):
        cloud(cx, 32, 20, 5)
    for cx in (72, 168, 248):
        cloud(cx, 40, 12, 4)


def draw_sea(c):
    """Mar: perspectiva por densidade de crista.

    O padrao e PERIODICO a cada 32 px de proposito. Cristas em posicoes
    livres davam 323 tiles unicos — nem cabia no mapa de bytes, muito menos
    na ROM. Com periodo 32 cada faixa gasta no maximo 4 tiles.
    """
    PERIOD = 32
    for y in range(SEA_Y0, NEAR_Y1 + 1):
        t = (y - SEA_Y0) / float(NEAR_Y1 - SEA_Y0)
        hline(c, 0, W - 1, y, 5 if t < 0.55 else 6)
    hline(c, 0, W - 1, SEA_Y0, 7)          # linha do horizonte
    hline(c, 0, W - 1, SEA_Y0 + 1, 3)

    y = SEA_Y0 + 4
    step = 3
    while y <= NEAR_Y1:
        t = (y - SEA_Y0) / float(NEAR_Y1 - SEA_Y0)
        dash = 2 + int(t * 6)
        col = 7 if t < 0.6 else 1
        # duas cristas por periodo, deslocadas conforme a faixa
        for base in (0, PERIOD // 2):
            off = (base + (y * 8) % PERIOD) % PERIOD
            for x in range(off, W + PERIOD, PERIOD):
                hline(c, x, x + dash - 1, y, col)
        y += step
        step = 3 + int(t * 3)


def draw_boat(c):
    """Iate atracado a direita — silhueta autoral, sem marca nem texto."""
    bx, by = 150, 70          # canto do casco
    # casco: trapezio branco com friso laranja e linha d'agua escura
    for i, y in enumerate(range(by + 20, by + 34)):
        inset = int(i * 1.6)
        hline(c, bx + inset, bx + 96 - inset // 2, y, 1)
    hline(c, bx + 2, bx + 95, by + 22, 11)
    hline(c, bx + 2, bx + 95, by + 23, 11)
    for i, y in enumerate(range(by + 31, by + 34)):
        inset = int((i + 11) * 1.6)
        hline(c, bx + inset, bx + 96 - (i + 11) // 2, y, 15)
    # convés e cabine
    rect(c, bx + 22, by + 8, bx + 74, by + 19, 1)
    rect(c, bx + 26, by + 4, bx + 66, by + 8, 12)
    for wx in range(bx + 28, bx + 66, 8):
        rect(c, wx, by + 11, wx + 4, by + 15, 15)
    # ponte e mastro
    rect(c, bx + 44, by - 6, bx + 56, by + 4, 1)
    rect(c, bx + 47, by - 3, bx + 53, by, 15)
    rect(c, bx + 62, by - 18, bx + 63, by + 4, 15)
    rect(c, bx + 64, by - 18, bx + 72, by - 13, 13)   # galhardete
    rect(c, bx + 64, by - 13, bx + 72, by - 10, 1)
    # reflexo do casco na agua
    for y in range(by + 34, by + 40):
        if (y + by) % 2 == 0:
            hline(c, bx + 24, bx + 88, y, 7)


def draw_deck(c):
    """Tabuas em perspectiva.

    Cada tabua ocupa uma LINHA DE TILE inteira e as juntas verticais caem em
    multiplos de 32: assim cada faixa do deck gasta 2 tiles (liso + junta) em
    vez de dezenas. A perspectiva vem da cor e do passo da junta, nao de
    alturas quebradas que nao fecham no grid de 8 px.
    """
    for n, y in enumerate(range(DECK_Y0, H, 8)):
        bottom = min(H - 1, y + 7)
        rect(c, 0, y, W - 1, bottom, 10 if n % 2 == 0 else 8)
        hline(c, 0, W - 1, y, 9)                     # junta entre tabuas
        # Tabua de cais e LONGA. Com passo 32 e uma junta grossa o deck lia
        # como parede de tijolo; passo 128 e uma linha fina de 1 px devolvem
        # a leitura de madeira comprida.
        pitch = 128
        off = (n * 32) % pitch
        for x in range(off, W + pitch, pitch):
            for yy in range(y + 1, bottom + 1):
                px(c, x, yy, 9)
        # veio da madeira: risco claro a meia altura, tambem periodico
        for x in range(((n * 24) % 64), W + 64, 64):
            hline(c, x, x + 15, y + 4, 8 if n % 2 == 0 else 10)
    hline(c, 0, W - 1, DECK_Y0, 15)                  # quina do cais
    hline(c, 0, W - 1, DECK_Y0 + 1, 9)


def draw_props(c):
    """Barris na quina do deck — atras dos lutadores, sem roubar a leitura.

    Ambos em x multiplo de 8 e com o mesmo desenho: os dois barris dividem
    exatamente o mesmo conjunto de tiles.
    """
    for bx in (16, 224):
        # Base bem dentro do deck: com a base na quina (DECK_Y0) o barril
        # ficava metade na agua e lia como boia, nao como carga no cais.
        top, bot = DECK_Y0 - 8, DECK_Y0 + 15
        # Barril de MADEIRA (9/8), nao laranja vivo. Duas razoes, a mesma
        # raiz: cenario nao pode competir com o lutador. Em laranja saturado
        # ele virava o objeto mais vivo da tela, roubando a leitura do Ken —
        # e o detector de gameplay do harness, que procura o maior blob
        # saturado com forma de sprite, travava no barril (parado) em vez do
        # jogador, e o eixo de gameplay reprovava por deslocamento zero.
        rect(c, bx + 1, top, bx + 14, bot, 9)           # corpo
        rect(c, bx, top + 1, bx, bot - 1, 15)           # aro esquerdo
        rect(c, bx + 15, top + 1, bx + 15, bot - 1, 15)
        hline(c, bx + 1, bx + 14, top, 15)              # tampo
        hline(c, bx + 1, bx + 14, top + 1, 8)
        for yy in (top + 6, top + 7, top + 15, top + 16):
            hline(c, bx, bx + 15, yy, 15)               # cintas
        rect(c, bx + 3, top + 2, bx + 4, bot - 1, 8)    # brilho
        hline(c, bx, bx + 15, bot, 15)                  # sombra no deck


def pack(canvas):
    """Corta em tiles 8x8, deduplica e devolve (tiles, mapa)."""
    tiles, index, tmap = [], {}, []
    for ty in range(ROWS):
        row = []
        for tx in range(COLS):
            key = tuple(canvas[ty * 8 + y][tx * 8 + x]
                        for y in range(8) for x in range(8))
            if key not in index:
                index[key] = len(tiles)
                tiles.append(key)
            row.append(index[key])
        tmap.append(row)
    return tiles, tmap


def to_4bpp(tile):
    """4bpp planar: 4 bytes por linha (plano 0..3)."""
    out = bytearray()
    for y in range(8):
        planes = [0, 0, 0, 0]
        for x in range(8):
            col = tile[y * 8 + x]
            for p in range(4):
                if col & (1 << p):
                    planes[p] |= 0x80 >> x
        out += bytes(planes)
    return out


def main():
    c = new_canvas()
    rect(c, 0, 0, W - 1, 15, 0)          # faixa do HUD
    draw_sky(c)
    draw_sea(c)
    draw_boat(c)
    draw_deck(c)
    draw_props(c)

    tiles, tmap = pack(c)
    if len(tiles) > 255:
        print(f"[FAIL] {len(tiles)} tiles unicos > 255 (mapa e byte)")
        return 1
    data = b"".join(to_4bpp(t) for t in tiles)

    arr = "\n".join(
        "    " + ", ".join(f"0x{b:02X}" for b in data[i:i + 16]) + ","
        for i in range(0, len(data), 16))
    map_arr = "\n".join(
        "    {" + ", ".join(str(v) for v in row) + "}," for row in tmap)
    open(os.path.join(PROJ, "inc", "stage_ken_tiles.h"), "w").write(
        "/* gerado por tools/author_stage_ken.py — NAO editar a mao.\n"
        " * Pixel art autoral SMS-nativa. Nenhum pixel de art_src_base/. */\n"
        "#ifndef STAGE_KEN_TILES_H\n#define STAGE_KEN_TILES_H\n"
        f"#define STAGE_KEN_TILES_COUNT {len(tiles)}\n"
        f"#define STAGE_KEN_TILES_SIZE {len(data)}\n"
        f"extern const unsigned char stage_ken_tiles[{len(data)}];\n"
        "extern const unsigned char stage_ken_map[24][32];\n"
        "#endif\n")
    open(os.path.join(PROJ, "src", "stage_data.c"), "w").write(
        "/* gerado por tools/author_stage_ken.py — NAO editar a mao. */\n"
        '#include "stage_ken_tiles.h"\n\n'
        f"const unsigned char stage_ken_tiles[{len(data)}] = {{\n{arr}\n}};\n\n"
        f"const unsigned char stage_ken_map[24][32] = {{\n{map_arr}\n}};\n")

    print(f"[OK] {len(tiles)} tiles unicos, {len(data)} B de tiles "
          f"+ {ROWS * COLS} B de mapa")

    if "--preview" in sys.argv:
        from PIL import Image
        # PNG INDEXADO (color type 3). O gate de recursos do wrapper recusa
        # RGB: em res/ o que vale e o indice de paleta, nao a cor final.
        im = Image.new("P", (W, H))
        pal = []
        for v in PAL:
            pal += [(v & 3) * 85, ((v >> 2) & 3) * 85, ((v >> 4) & 3) * 85]
        im.putpalette(pal + [0] * (768 - len(pal)))
        im.putdata([c[y][x] for y in range(H) for x in range(W)])
        out = os.path.join(PROJ, "res", "bg", "stage_ken_dock.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        # O contrato de res/ exige indice 0 transparente (tRNS). Vale para o
        # PNG de revisao; na ROM o indice 0 e o preto do HUD.
        im.save(out, bits=8, transparency=0)
        print(f"     preview -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
