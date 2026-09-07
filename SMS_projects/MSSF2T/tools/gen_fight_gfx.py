#!/usr/bin/env python3
"""Gera inc/fight_gfx.h a partir das folhas em inc/*_tiles.h.

Existe porque o tamanho de cada folha estava escrito em DOIS lugares: no
header da própria folha e à mão em `fight_gfx.h`. `fight.c` só enxerga o
segundo. Quando o `repack_sheets.py` encolheu as folhas do Ken, só o primeiro
foi atualizado e os dois passaram a divergir — `fight_gfx.h` continuou
dizendo 1024 para uma folha de 832 B. Resultado: `pose_size()` devolvia mais
do que existe e o streamer lia até 192 bytes ALÉM do fim do array, subindo
lixo para a VRAM (invisível, porque o metasprite não referencia esses tiles,
mas é leitura fora dos limites e VBlank gasto à toa).

Com o header gerado, a folha é a única fonte da verdade. Rodar sempre que
uma folha for criada, encolhida ou removida.

Uso: python3 tools/gen_fight_gfx.py [--check]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INC = os.path.join(HERE, os.pardir, "inc")

# Ordem de declaração; `_l` ficou fora do build (ver doc/15-tdd.md, seção Flip).
FOLHAS = ["ken_idle", "ken_walk", "ken_punch", "ken_special", "ken_hit",
          "ken_ko", "ken_crouch", "ken_jump",
          "guile_idle", "guile_walk", "guile_punch", "guile_special",
          "guile_hit", "guile_ko", "guile_crouch", "guile_jump",
          "hadouken", "sonicboom"]


def tamanho(nome):
    src = open(os.path.join(INC, nome + "_tiles.h")).read()
    m = re.search(r"_tiles\[(\d+)\]", src)
    d = re.search(rf"#define {nome.upper()}_TILES_SIZE (\d+)", src)
    if not m:
        raise SystemExit(f"[FAIL] {nome}: array não encontrado")
    real = int(m.group(1))
    if d and int(d.group(1)) != real:
        raise SystemExit(f"[FAIL] {nome}: o próprio header já diverge "
                         f"({d.group(1)} != {real})")
    return real


def main():
    linhas = [
        "/* gerado por tools/gen_fight_gfx.py — NAO editar a mao.",
        " * Os tamanhos saem das proprias folhas: escrever de novo aqui foi o",
        " * que deixou fight_gfx.h dizendo 1024 para uma folha de 832 B. */",
        "#ifndef FIGHT_GFX_H",
        "#define FIGHT_GFX_H",
        '#include "stage_ken_tiles.h"',
        "",
        "/* Apenas as folhas que olham para a ESQUERDA: o facing direito e",
        " * espelhado em runtime (bitrev + dx-mirror). Ver doc/15-tdd.md. */",
    ]
    for n in FOLHAS:
        linhas.append(f"extern const unsigned char {n}_tiles[];")
        linhas.append(f"extern const signed char {n}_meta[];")
    linhas.append("extern const unsigned char stage_ken_map[24][32];")
    linhas.append("")
    total = 0
    for n in FOLHAS:
        t = tamanho(n)
        total += t
        linhas.append(f"#define {n.upper()}_TILES_SIZE {t}")
    linhas += ["", "#endif", ""]
    texto = "\n".join(linhas)

    dest = os.path.join(INC, "fight_gfx.h")
    atual = open(dest).read() if os.path.exists(dest) else ""
    if "--check" in sys.argv:
        print("[OK] em dia" if atual == texto else "[FAIL] fight_gfx.h desatualizado")
        return 0 if atual == texto else 1
    open(dest, "w").write(texto)
    print(f"[OK] fight_gfx.h: {len(FOLHAS)} folhas, {total} B de tiles de sprite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
