#!/usr/bin/env python3
"""Gate CONTRASTE (luma floor) — piso de contraste entre cores do contrato.

Reprova pares fg/bg cuja diferenca de luma derivada dos codigos 6-bit fique
abaixo do piso. Adjetivo ("legivel", "bonito") nao e entrada; codigos sao.

Uso:
  audit_luma_floor.py --fg 255,255,255 --bg 0,0,0
  audit_luma_floor.py --scene scene.json      # {"pairs":[{"fg":[..],"bg":[..]}]}
  audit_luma_floor.py --self-check
Exit: 0 | 1 reprova | 3 uso
"""
import sys, json, argparse, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sms_palette as pal

def check_pair(fg, bg, floor=pal.LUMA_FLOOR_DEFAULT):
    fa = tuple(fg) if len(fg) == 3 else pal.code_rgb(tuple(fg))
    ba = tuple(bg) if len(bg) == 3 else pal.code_rgb(tuple(bg))
    for c in (fa, ba):
        if not pal.is_contract_color(c):
            return [f"cor {c} fora do contrato 6-bit"]
    dy = abs(pal.luma(fa) - pal.luma(ba))
    if dy < floor:
        return [f"contraste dY={dy} < piso {floor} entre {fa} e {ba}"]
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fg")
    ap.add_argument("--bg")
    ap.add_argument("--scene")
    ap.add_argument("--floor", type=int, default=pal.LUMA_FLOOR_DEFAULT)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        assert not check_pair(pal.code_rgb((3, 3, 3)), pal.code_rgb((0, 0, 0)))
        # par proximo real da paleta: dY ~16 < piso default
        assert check_pair(pal.code_rgb((1, 1, 0)), pal.code_rgb((0, 1, 1)))
        assert check_pair((128, 128, 128), (0, 0, 0))
        print("[SELF-CHECK OK] luma_floor")
        return 0
    pairs = []
    if args.scene:
        pairs += [(p["fg"], p["bg"]) for p in json.load(open(args.scene))["pairs"]]
    elif args.fg and args.bg:
        pairs.append(([int(x) for x in args.fg.split(",")],
                      [int(x) for x in args.bg.split(",")]))
    else:
        print("[FAIL] informe --fg/--bg ou --scene", file=sys.stderr)
        return 3
    errors = []
    for fg, bg in pairs:
        errors += check_pair(fg, bg, args.floor)
    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        return 1
    print("[PASS] contraste acima do piso")
    return 0

if __name__ == "__main__":
    sys.exit(main())
