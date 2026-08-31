#!/usr/bin/env python3
"""Gate RECURSOS — valida PNGs de res/ contra o contrato visual SMS.

Reprova:
- PNG fora do grid 8x8 (BG) ou tamanho fora de {8x8,16x16} (sprite)
- cor fora dos codigos 6-bit (contrato canal*85)
- >15 cores uteis por subpaleta (indice 0 = transparente, nao conta como util)
- indice 0 opaco (sem tRNS)

Uso: audit_validate_resources.py --project <dir> [--kind bg|sprite] <png...>
     audit_validate_resources.py --self-check
Exit: 0 aprova | 1 reprova (gate funcionou) | 3 uso invalido
"""
import sys, os, argparse, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png_io import read_indexed_png, PngError
import sms_palette as pal

MAX_USEFUL = 15

def check_png(path, kind):
    errors = []
    try:
        img = read_indexed_png(path)
    except PngError as e:
        return [str(e)]
    w, h = img["w"], img["h"]
    if w % 8 or h % 8:
        errors.append(f"grid 8x8 violado: {w}x{h}")
    if kind == "sprite":
        if (w, h) not in ((8, 8), (16, 16)):
            errors.append(f"sprite {w}x{h} fora de {{8x8,16x16}}")
        else:
            errors += _palette_errors(path, img)
            return errors
    else:
        errors += _palette_errors(path, img)
    return errors

def _palette_errors(path, img):
    errors = []
    plte = img["palette"] or []
    for idx, rgb in enumerate(plte):
        if not pal.is_contract_color(tuple(rgb)):
            errors.append(f"{path}: paleta[{idx}] rgb{tuple(rgb)} fora dos codigos 6-bit "
                          f"(mais proximo: {pal.nearest_code(tuple(rgb))})")
    used = set()
    for row in img["pixels"]:
        used.update(row)
    useful = len([i for i in used if i != 0])
    if useful > MAX_USEFUL:
        errors.append(f"{path}: {useful} cores uteis > {MAX_USEFUL} (indice 0 nao conta)")
    if 0 not in img["trns"]:
        errors.append(f"{path}: indice 0 deve ser transparente (tRNS)")
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--kind", choices=("bg", "sprite"), default="bg")
    ap.add_argument("pngs", nargs="*")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    if args.self_check:
        import tempfile
        from png_io import write_indexed_png
        good = [(0, 0, 0)] + [pal.code_rgb(c) for c in
               ((3, 3, 3), (0, 0, 3), (0, 3, 0), (3, 0, 0), (3, 3, 0))]
        px = [bytes([1] * 32) for _ in range(24)]
        d = tempfile.mkdtemp(prefix="smsres_")
        okp = os.path.join(d, "ok.png"); write_indexed_png(okp, 32, 24, good, px)
        badp = os.path.join(d, "bad.png"); write_indexed_png(badp, 250, 100, good, [bytes([1] * 250)] * 100)
        e1, e2 = check_png(okp, "bg"), check_png(badp, "bg")
        assert not e1, f"self-check falhou em fixture valida: {e1}"
        assert any("grid" in x for x in e2), "self-check: gate nao reprovou grid invalido"
        print("[SELF-CHECK OK] validate_resources")
        return 0

    if not args.pngs:
        print("[FAIL] nenhum PNG informado", file=sys.stderr)
        return 3
    all_errors = []
    for p in args.pngs:
        all_errors += check_png(p, args.kind)
    if all_errors:
        for e in all_errors:
            print(f"[FAIL] {e}")
        return 1
    print(f"[PASS] {len(args.pngs)} PNG(s) dentro do contrato")
    return 0

if __name__ == "__main__":
    sys.exit(main())
