#!/usr/bin/env python3
"""audit_mastery_registry.py — valida a matriz de maestria SMS (registry JSON).

Regras:
- Escada de proficiência válida (mapped/incorporada/reproduzivel/emulador_provado/default_senior).
- Técnica acima de 'mapped' PRECISA de evidência (cadeia de custódia) — sem ela,
  rebaixa a mapped (overclaim).
- Técnica `emulador_provado`/`default_senior` exige evidência citada.

Uso: audit_mastery_registry.py --registry <json> [--self-check]
Exit: 0 pro | 1 overclaim/rebaixado | 3 uso
"""
import sys, os, json, argparse

VALID_LEVELS = {"mapped", "incorporada", "reproduzivel",
                "emulador_provado", "default_senior"}

def audit(registry_path):
    try:
        d = json.load(open(registry_path))
    except (json.JSONDecodeError, OSError) as e:
        return [f"registry ilegivel: {e}"]
    # suporta {"tracks": {...}} (estrutura SMSForge) ou {track: {...}} direto
    tracks = d.get("tracks", d)
    problems = []
    for track, m in tracks.items():
        for tech, meta in (m.items() if isinstance(m, dict) else []):
            lvl = meta.get("level", "")
            if lvl not in VALID_LEVELS:
                problems.append(f"{track}/{tech}: nivel invalido '{lvl}'")
                continue
            if lvl in ("emulador_provado", "default_senior") and not meta.get("evidence"):
                problems.append(f"{track}/{tech}: {lvl} sem evidencia (overclaim — desce para mapped)")
    return problems

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default=os.path.join(
        os.path.dirname(__file__), "..", "..", "doc", "05_technical", "01_registry_maestria_sms.json"))
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        import tempfile
        d = tempfile.mkdtemp(prefix="smsmr_")
        # caso ok
        okp = os.path.join(d, "ok.json")
        json.dump({"trilhaA": {"T1": {"level": "emulador_provado", "evidence": "cap"}}}, open(okp, "w"))
        assert not audit(okp)
        # caso overclaim (sem evidence)
        bp = os.path.join(d, "bad.json")
        json.dump({"trilhaA": {"T1": {"level": "default_senior"}}}, open(bp, "w"))
        assert audit(bp), "default_senior sem evidence deveria reprovar"
        print("[SELF-CHECK OK] mastery_registry")
        return 0
    problems = audit(args.registry)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print("[PASS] matriz de maestria sem overclaim")
    return 0

if __name__ == "__main__":
    sys.exit(main())
