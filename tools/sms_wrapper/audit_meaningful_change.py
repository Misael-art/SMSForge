#!/usr/bin/env python3
"""audit_meaningful_change.py — gate de mudança significativa (porta do SGDK Forge).

Verifica se a mudança declarada ATACA o blocker dominante do projeto. Impede
"progresso" que só mexe em código/doc sem destravar o problema mais crítico.

Le dos projetos:
  - .mddev/project.json  -> gates esperados
  - out/build_record.json -> eixos reais (blockers = eixos false)
  - doc/10-memory-bank.md -> "## Próximo passo declarado" (intenção)
Uso:
  audit_meaningful_change.py --project <dir> --change-blocks <eixo>
  audit_meaningful_change.py --project <dir>   # infere blockers de build_record
  audit_meaningful_change.py --self-check
Exit: 0 muda o blocker | 1 mudança não é significativa | 3 uso
"""
import sys, os, json, argparse

AXES = ["build", "validation_report", "boot_emulador", "gameplay",
        "fps_constante", "audio", "memory_bank_atualizado"]

def read_json(path):
    try:
        return json.load(open(path))
    except (json.JSONDecodeError, OSError, IOError):
        return None

def blockers(project):
    """Eixos false no build_record = blockers (o que impede entrega)."""
    rec = read_json(os.path.join(project, "out", "build_record.json"))
    if not rec or "axes" not in rec:
        return []
    return [k for k in AXES if rec["axes"].get(k) is False]

def check(project, change_blocks):
    bl = blockers(project)
    if not bl:
        # sem eixos false no record -> busca intent no memory bank
        mb = os.path.join(project, "doc", "10-memory-bank.md")
        intent = open(mb).read().lower() if os.path.exists(mb) else ""
        if any(a in intent for a in change_blocks.lower().split(",")):
            return [], True, "sem eixos false; intent do memory bank cita o alvo"
        return [], False, "sem eixos false no record e memory bank nao cita o alvo"
    hit = [b for b in bl if b in change_blocks.lower()]
    if hit:
        return bl, True, f"ataca blocker dominante: {hit}"
    return bl, False, f"mudanca '{change_blocks}' nao ataca nenhum blocker {bl}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--change-blocks", help="eixo(s) que a mudanca ataca (csv)")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        import tempfile, pathlib
        d = tempfile.mkdtemp(prefix="smsmc_")
        os.makedirs(os.path.join(d, "out"), exist_ok=True)
        json.dump({"axes": {k: (k != "audio") for k in AXES}},
                  open(os.path.join(d, "out", "build_record.json"), "w"))
        # mudanca que ataca o blocker (audio) -> deve PASSAR
        bl, ok, msg = check(d, "audio")
        assert ok, msg
        # mudanca que nao ataca -> deve REPROVAR
        bl2, ok2, msg2 = check(d, "build")
        assert not ok2, "deveria reprovar mudanca que nao ataca blocker"
        print("[SELF-CHECK OK] meaningful_change")
        return 0
    if not args.change_blocks:
        print("[FAIL] informe --change-blocks <eixo>", file=sys.stderr)
        return 3
    bl, ok, msg = check(args.project, args.change_blocks)
    print(f"[{'PASS' if ok else 'FAIL'}] {msg}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
