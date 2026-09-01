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

def cross_check(registry_path, matrix_path):
    """Toda tecnica citada na matriz HUMANA existe no registry?

    L003: o registry mantinha S05/S06 honestamente em `mapped` ("provar em
    emulador"), mas a matriz .md afirmava os numeros como NOTA DURA. Como
    nenhum gate lia o .md, dois fatos do Mega Drive circularam como lei do SMS
    ate serem refutados em emulador. Fato afirmado na matriz sem entrada no
    registry e claim invisivel.
    """
    import re
    if not os.path.exists(matrix_path):
        return []
    try:
        d = json.load(open(registry_path))
    except (json.JSONDecodeError, OSError):
        return []          # audit() ja reporta registry ilegivel
    ids = set()
    for _, m in (d.get("tracks", d)).items():
        for tech in (m if isinstance(m, dict) else {}):
            mm = re.match(r"([A-Z]\d{2})", tech)
            if mm:
                ids.add(mm.group(1))
    texto = open(matrix_path, encoding="utf-8", errors="replace").read()
    citadas = set(re.findall(r"^\|\s*([A-Z]\d{2})\s*\|", texto, re.M))
    # So cobra as FAMILIAS que o registry conhece (V/S/P/M/Z/B/A/I...). As secoes
    # de processo da matriz (E = estetica, Q = verificacao) nao sao tecnicas de
    # hardware, nao tem escada de proficiencia e sao governadas por outros gates.
    familias = {t[0] for t in ids}
    faltando = {t for t in citadas - ids if t[0] in familias}
    return [f"matriz cita '{t}' que NAO existe no registry "
            "(fato afirmado sem escada de proficiencia = claim invisivel)"
            for t in sorted(faltando)]

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
        # cross-check: tecnica citada na matriz sem entrada no registry reprova
        import tempfile as _tf
        d2 = _tf.mkdtemp(prefix="smsmx_")
        reg = os.path.join(d2, "01_registry_maestria_sms.json")
        mtx = os.path.join(d2, "00_matriz_maestria_sms.md")
        json.dump({"sprites": {"S01 x": {"level": "mapped", "evidence": "e"}}},
                  open(reg, "w"))
        open(mtx, "w").write("| S01 | ok |\n")
        assert not cross_check(reg, mtx), "tecnica presente nos dois nao reprova"
        open(mtx, "w").write("| S01 | ok |\n| S09 | fato duro sem registry |\n")
        assert cross_check(reg, mtx), "faltou pegar tecnica citada fora do registry"
        print("[SELF-CHECK OK] mastery_registry (overclaim + tecnica citada na "
              "matriz sem entrada no registry)")
        return 0
    problems = audit(args.registry)
    problems += cross_check(args.registry, os.path.join(
        os.path.dirname(args.registry), "00_matriz_maestria_sms.md"))
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print("[PASS] matriz de maestria sem overclaim")
    return 0

if __name__ == "__main__":
    sys.exit(main())
