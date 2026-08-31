#!/usr/bin/env python3
"""audit_sprite_mode.py — impede a recorrencia do L006 (sprite invisivel).

LICAO PAGA (laboratorio_01, 2026-08-25..30): o projeto tentou desenhar uma
entidade 16x16 com `SMS_setSpriteMode(SPRITEMODE_TALL)` e passou dias com o
sprite invisivel. Causa-raiz: **TALL no VDP do Master System e 8x16, nao 16x16.**
A matriz de maestria (S03) dizia "8x8 ou 16x16" e induziu o erro.

Geometria real do VDP (reg 1: bit1 = tamanho, bit0 = zoom):
  SPRITEMODE_NORMAL       8x8
  SPRITEMODE_TALL         8x16      <- NAO e 16x16
  SPRITEMODE_ZOOMED       16x16     (8x8 com zoom x2; dobra o pixel, nao a arte)
  SPRITEMODE_TALL_ZOOMED  16x32

Consequencia: entidade 16x16 com ARTE de 16x16 exige **metasprite**
(`SMS_addMetaSprite`), em qualquer modo. Nenhum modo desenha um tile 16x16.

Este gate cruza o modo declarado no fonte com a largura dos assets de sprite.

Uso:
  audit_sprite_mode.py --project <dir> [--sprite <png>...] [--json <out>]
  audit_sprite_mode.py --self-check
Exit: 0 coerente | 1 incoerencia geometrica | 3 uso
"""
import sys, os, re, glob, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from png_io import png_size, PngError  # noqa: E402

MODE_GEOMETRY = {
    "SPRITEMODE_NORMAL": (8, 8),
    "SPRITEMODE_TALL": (8, 16),
    "SPRITEMODE_ZOOMED": (16, 16),
    "SPRITEMODE_TALL_ZOOMED": (16, 32),
}

def declared_mode(sources):
    """Ultimo SMS_setSpriteMode encontrado no fonte (None se ausente)."""
    mode = None
    for src in sources:
        try:
            text = open(src, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in re.finditer(r"SMS_setSpriteMode\s*\(\s*(SPRITEMODE_[A-Z_]+)", text):
            mode = m.group(1)
    return mode

def uses_metasprite(sources):
    for src in sources:
        try:
            text = open(src, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if re.search(r"SMS_addMetaSprite(_f)?\s*\(", text):
            return True
    return False

def analyze(mode, sprite_sizes, has_metasprite):
    """(problems, report). Pura — o self-check exercita ESTA funcao."""
    problems = []
    report = {"mode": mode, "has_metasprite": has_metasprite,
              "sprites": [{"path": p, "w": w, "h": h} for p, w, h in sprite_sizes]}
    if mode is None:
        # sem modo declarado, o hardware assume NORMAL (8x8)
        mode = "SPRITEMODE_NORMAL"
        report["mode_assumed"] = mode
    if mode not in MODE_GEOMETRY:
        return [f"modo desconhecido no fonte: {mode}"], report
    mw, mh = MODE_GEOMETRY[mode]
    report["geometry"] = [mw, mh]

    for path, w, h in sprite_sizes:
        name = os.path.basename(path)
        # Nenhum modo desenha arte mais larga que 8px sem metasprite:
        # ZOOMED dobra o PIXEL, nao a arte (o tile continua 8x8).
        if w > 8 and not has_metasprite:
            problems.append(
                f"{name}: arte {w}x{h} com modo {mode} ({mw}x{mh}) e SEM "
                "SMS_addMetaSprite — nenhum modo de sprite do SMS desenha tile "
                "mais largo que 8px (ZOOMED dobra o pixel, nao a arte). "
                "Este e o L006: sprite fica invisivel ou corrompido.")
        elif h > mh and not has_metasprite:
            problems.append(
                f"{name}: arte {w}x{h} mais alta que o modo {mode} ({mw}x{mh}) "
                "e sem metasprite — a metade de baixo nao sera desenhada.")
    report["coherent"] = not problems
    return problems, report

def collect_sprites(project, explicit):
    out = []
    paths = list(explicit)
    if not paths:
        paths = [p for p in glob.glob(os.path.join(project, "res", "**", "*.png"),
                                      recursive=True) if "sprite" in p.lower()]
    for p in paths:
        try:
            w, h = png_size(p)
        except (PngError, OSError):
            continue
        out.append((p, w, h))
    return out

def _self_check():
    # REPROVA: o caso exato do L006 (arte 16x16 em TALL, sem metasprite)
    p, r = analyze("SPRITEMODE_TALL", [("hero.png", 16, 16)], False)
    assert any("L006" in x for x in p), f"faltou reprovar o caso L006: {p}"
    assert r["geometry"] == [8, 16], "TALL tem que ser 8x16, nao 16x16"

    # APROVA: mesma arte COM metasprite
    p, _ = analyze("SPRITEMODE_TALL", [("hero.png", 16, 16)], True)
    assert not p, f"16x16 com metasprite e a solucao canonica: {p}"

    # APROVA: arte 8x8 em modo NORMAL
    p, _ = analyze("SPRITEMODE_NORMAL", [("blip.png", 8, 8)], False)
    assert not p, f"8x8 em NORMAL nao deveria reprovar: {p}"

    # REPROVA: arte 8x16 em NORMAL (metade de baixo some)
    p, _ = analyze("SPRITEMODE_NORMAL", [("tall.png", 8, 16)], False)
    assert any("mais alta" in x for x in p), f"faltou pegar altura excedente: {p}"

    # APROVA: 8x16 em TALL (uso correto do modo)
    assert not analyze("SPRITEMODE_TALL", [("tall.png", 8, 16)], False)[0]

    # REPROVA: ZOOMED nao "vira" 16x16 de arte
    p, _ = analyze("SPRITEMODE_ZOOMED", [("hero.png", 16, 16)], False)
    assert any("dobra o pixel" in x for x in p), \
        f"ZOOMED dobra o pixel, nao a arte — deveria reprovar: {p}"

    # Sem sprites nao reprova (nao inventa problema)
    assert not analyze(None, [], False)[0]
    print("[SELF-CHECK OK] sprite_mode (reprova o caso L006, altura excedente e "
          "a ilusao do ZOOMED; aceita metasprite e uso correto de TALL)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--sprite", action="append", default=[])
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()

    sources = sorted(glob.glob(os.path.join(a.project, "src", "*.c")))
    sprites = collect_sprites(a.project, a.sprite)
    problems, report = analyze(declared_mode(sources), sprites,
                               uses_metasprite(sources))
    if a.json:
        json.dump({"problems": problems, **report}, open(a.json, "w"), indent=2)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print(f"[PASS] geometria de sprite coerente "
          f"(modo {report.get('mode') or report.get('mode_assumed')}, "
          f"{len(sprites)} asset(s))")
    return 0

if __name__ == "__main__":
    sys.exit(main())
