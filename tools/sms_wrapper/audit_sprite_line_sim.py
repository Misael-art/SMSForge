#!/usr/bin/env python3
"""Gate SPRITES/SCANLINE — simulador VDP de Master System.

Le um manifest JSON de cena (schema sprite_scene_manifest_v1) e reprova:
- >64 sprites ativos na SAT
- >8 sprites cobrindo a mesma scanline (excesso descartado; SMS1 corrompe display)
- sprite com Y armazenado == 0xD0 (colide com terminador da SAT)

Fisica aplicada (fonte: docs smspower/devkitSMS; leis em .agent/rules/SMS_GLOBAL.md):
- sprite_size global '8x8'|'8x16'|'16x16' (+ zoom opcional que DOBRA o footprint)
- stored_y = y + 1 no SMS (VDP compara linha seguinte); aqui trabalhamos com y logico
  e checamos colisao com 208 no valor armazenado.

Uso: audit_sprite_line_sim.py <manifest.json> [--self-check]
Exit: 0 | 1 reprova | 3 uso
"""
import sys, json, argparse

SPRITE_H = {"8x8": 8, "8x16": 16, "16x16": 16}
SAT_MAX = 64
PER_LINE_MAX = 8
TERMINATOR_Y = 0xD0

def simulate(manifest):
    errors = []
    size = manifest.get("sprite_size", "8x8")
    zoom = bool(manifest.get("zoomed", False))
    h = SPRITE_H[size] * (2 if zoom else 1)
    sprites = manifest.get("sprites", [])
    if len(sprites) > SAT_MAX:
        errors.append(f"SAT overflow: {len(sprites)} sprites > {SAT_MAX}")
    lines = {}
    for s in sprites:
        y, x = int(s["y"]), int(s["x"])
        if y + 1 == TERMINATOR_Y:
            errors.append(f"sprite em ({x},{y}): Y armazenado colide com terminador 0xD0")
        for ly in range(y, min(y + h, manifest.get("screen_h", 192))):
            lines.setdefault(ly, []).append(x)
    over = {ly: v for ly, v in sorted(lines.items()) if len(v) > PER_LINE_MAX}
    for ly, xs in list(over.items())[:5]:
        errors.append(f"scanline {ly}: {len(xs)} sprites > {PER_LINE_MAX} (SMS1: display corrompido)")
    peak = max((len(v) for v in lines.values()), default=0)
    report = {"sprites": len(sprites), "peak_per_line": peak,
              "violations": errors}
    return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        ok = {"sprite_size": "16x16", "zoomed": False,
              "sprites": [{"y": 10 + i * 20, "x": 40, "tile": i} for i in range(8)],
              "screen_h": 192}
        tall_pair = {"sprite_size": "8x16", "zoomed": False,
                     "sprites": [{"y": y, "x": fighter_x + col * 8,
                                  "tile": n}
                                 for fighter_x in (48, 176)
                                 for y in (96, 112, 128)
                                 for col in range(4)
                                 for n in (fighter_x + y + col,)],
                     "screen_h": 192}
        bad = {"sprite_size": "8x8",
               "sprites": [{"y": 50, "x": 16 + i * 4, "tile": i} for i in range(9)],
               "screen_h": 192}
        sat = {"sprite_size": "8x8",
               "sprites": [{"y": i % 192, "x": 40, "tile": 0} for i in range(65)],
               "screen_h": 192}
        r_ok, r_tall, r_bad, r_sat = (simulate(ok), simulate(tall_pair),
                                      simulate(bad), simulate(sat))
        assert not r_ok["violations"], r_ok
        assert not r_tall["violations"] and r_tall["peak_per_line"] == 8, r_tall
        assert any("scanline" in v for v in r_bad["violations"]), r_bad
        assert any("SAT" in v for v in r_sat["violations"]), r_sat
        print("[SELF-CHECK OK] sprite_line_sim")
        return 0
    if not args.manifest:
        print("[FAIL] manifest obrigatorio", file=sys.stderr)
        return 3
    rep = simulate(json.load(open(args.manifest)))
    print(json.dumps(rep))
    if rep["violations"]:
        for v in rep["violations"]:
            print(f"[FAIL] {v}")
        return 1
    print(f"[PASS] {rep['sprites']} sprites, pico {rep['peak_per_line']}/linha")
    return 0

if __name__ == "__main__":
    sys.exit(main())
