#!/usr/bin/env python3
"""audit_placeholder_quarantine.py — gate de quarentena de placeholder (porta do SGDK Forge).

Detecta assets placeholder / procedurais (role=outro/placeholder/debug_lab) que
foram promovidos a entrega REAL sem aprovação explícita. Impede "arte de tela"
passar por final.

Lê doc/asset_provenance_manifest.json; role permitida para entrega = personagem,
inimigo, boss, cenario_final, ui, fonte (com model sheet/proveniência). Role
"outro"/placeholder/technical_lab/procedural_debug = PROIBIDA para entrega.

Uso:
  audit_placeholder_quarantine.py --project <dir> [--check-release]
  audit_placeholder_quarantine.py --self-check
Exit: 0 ok | 1 placeholder promovido | 3 uso
"""
import sys, os, json, argparse

BANNED_RELEASE_ROLES = {"outro", "placeholder", "technical_lab_asset",
                        "procedural_debug", "debug_lab_control", ""}
ALLOWED_RELEASE_ROLES = {"personagem", "inimigo", "boss", "cenario_final",
                         "ui", "fonte"}

def audit(project):
    man_path = os.path.join(project, "doc", "asset_provenance_manifest.json")
    if not os.path.exists(man_path):
        return []   # sem manifest = sem assets declarados
    try:
        man = json.load(open(man_path))
    except (json.JSONDecodeError, OSError):
        return ["manifest de proveniencia invalido/ilegivel"]
    problems = []
    for a in man.get("assets", []):
        role = a.get("role", "")
        note = (a.get("note", "") + " " + a.get("author", "")).lower()
        # placeholder/procedural sinalizado pode ser promovido apenas com aprovacao
        if role in BANNED_RELEASE_ROLES or "placeholder" in note or "proced" in note:
            approved = "aprovado" in note or "approved" in note or "final" in note
            if not approved:
                problems.append(
                    f"{a['file']}: role='{role}' (placeholder/procedural) sem "
                    f"aprovacao explicita -> NAO pode ser tratado como asset de entrega")
    return problems

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        import tempfile, pathlib
        d = tempfile.mkdtemp(prefix="smspq_")
        os.makedirs(os.path.join(d, "doc"), exist_ok=True)
        # case: placeholder promovido -> deve reprovar
        json.dump({"assets": [{"file": "res/bg/block.png", "role": "outro",
                               "note": "placeholder F4", "origin": "x", "author": "y",
                               "sha256": "abc"}]},
                  open(os.path.join(d, "doc", "asset_provenance_manifest.json"), "w"))
        assert audit(d), "deveria reprovar placeholder promovido"
        # case: aprovado explicitamente -> passa
        json.dump({"assets": [{"file": "res/bg/block.png", "role": "outro",
                               "note": "aprovado FINAL pelo lead", "origin": "x",
                               "author": "y", "sha256": "abc"}]},
                  open(os.path.join(d, "doc", "asset_provenance_manifest.json"), "w"))
        assert not audit(d), "aprovacao explicita deveria liberar"
        print("[SELF-CHECK OK] placeholder_quarantine")
        return 0
    problems = audit(args.project)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print("[PASS] nenhum placeholder promovido sem aprovacao")
    return 0

if __name__ == "__main__":
    sys.exit(main())
