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
            # APROVACAO E CAMPO ESTRUTURADO, NUNCA PROSA.
            # Calibracao 2026-08-31: a deteccao antiga era substring ("final",
            # "aprovado") e a nota "arte autoral FINAL PENDENTE" — que diz o
            # OPOSTO — liberava o asset. Falso negativo: block.png e target.png
            # passaram a quarentena por acidente durante toda a F4.
            if a.get("release_approved") is not True:
                problems.append(
                    f"{a['file']}: role='{role}' (placeholder/procedural) sem "
                    f"aprovacao explicita -> NAO pode ser tratado como asset de "
                    f"entrega (exige \"release_approved\": true + approved_by)")
            elif not a.get("approved_by"):
                problems.append(
                    f"{a['file']}: release_approved=true sem 'approved_by' — "
                    "aprovacao precisa de responsavel nomeado")
    return problems

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--check-release", action="store_true",
                    help="modo entrega: placeholder em quarentena REPROVA")
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
        # case: aprovacao ESTRUTURADA com responsavel -> passa
        json.dump({"assets": [{"file": "res/bg/block.png", "role": "outro",
                               "note": "revisado", "origin": "x", "author": "y",
                               "sha256": "abc", "release_approved": True,
                               "approved_by": "lead de arte"}]},
                  open(os.path.join(d, "doc", "asset_provenance_manifest.json"), "w"))
        assert not audit(d), "aprovacao estruturada deveria liberar"
        # ARMADILHA REAL: nota que diz o OPOSTO de aprovado nao pode liberar.
        # "arte autoral final pendente" liberava block.png/target.png por substring.
        json.dump({"assets": [{"file": "res/bg/block.png", "role": "outro",
                               "note": "arte autoral final pendente", "origin": "x",
                               "author": "y", "sha256": "abc"}]},
                  open(os.path.join(d, "doc", "asset_provenance_manifest.json"), "w"))
        assert audit(d), "'final pendente' NAO e aprovacao (falso negativo historico)"
        # aprovado sem responsavel nomeado -> reprova
        json.dump({"assets": [{"file": "res/bg/block.png", "role": "outro",
                               "note": "x", "origin": "x", "author": "y",
                               "sha256": "abc", "release_approved": True}]},
                  open(os.path.join(d, "doc", "asset_provenance_manifest.json"), "w"))
        assert audit(d), "aprovacao sem approved_by deveria reprovar"
        print("[SELF-CHECK OK] placeholder_quarantine (aprovacao estruturada; "
              "prosa como 'final pendente' nao libera)")
        return 0
    problems = audit(args.project)
    if not problems:
        print("[PASS] nenhum placeholder promovido sem aprovacao")
        return 0
    # Placeholder em quarentena e LEGITIMO durante o desenvolvimento; so
    # reprova quando o projeto se declara pronto para entrega.
    if args.check_release:
        for p in problems:
            print(f"[FAIL] {p}")
        print(f"[FAIL] {len(problems)} placeholder(s) em quarentena bloqueiam a "
              "ENTREGA. Substitua por arte autoral ou aprove explicitamente.")
        return 1
    for p in problems:
        print(f"[QUARENTENA] {p}")
    print(f"[PASS] {len(problems)} asset(s) em quarentena — ok em desenvolvimento; "
          "rode --check-release antes de entregar.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
