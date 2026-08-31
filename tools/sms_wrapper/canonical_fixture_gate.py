#!/usr/bin/env python3
"""canonical_fixture_gate.py — gate de fixture canonica (porta do SGDK Forge).

Avalia se uma fixture (probe de validação) tem escopo canonico declarado e nao
infere claims amplos. Fixtures servem para PROVAR um comportamento, nunca para
inflar claim de "jogo pronto".

Escopos validos:
  static_contract      -> contrato estatico (ex.: logica de colisao)
  runtime_observation  -> observacao de runtime (sem claim de qualidade)
  visual_semantic      -> verificacao visual
  hardware_state       -> estado de hardware
  feature_readiness    -> prontidao de feature (limitado)
Uma fixture SEM escopo declarado ou com claim amplo -> REPROVA.

Uso:
  canonical_fixture_gate.py --fixture <arquivo> [--claim-ok]
  canonical_fixture_gate.py --project <dir>
  canonical_fixture_gate.py --self-check
Exit: 0 fixture canonica | 1 claim amplo/escopo invalido | 3 uso
"""
import sys, os, re, argparse

VALID_SCOPES = {"static_contract", "runtime_observation", "visual_semantic",
                "hardware_state", "feature_readiness"}
AMPLO_CLAIM = re.compile(r"\b(AAA|jogo completo|pixel.?\s?perfect|60fps garantido|release pronto)\b",
                         re.IGNORECASE)

def check_source(source):
    """Analisa um fonte C/descriptor e devolve (ok, motivo)."""
    if not source:
        return False, "arquivo vazio"
    lower = source.lower()
    # sem escopo canonico declarado
    if not any(s in lower for s in VALID_SCOPES):
        return False, "fixture sem escopo canonico declarado (static_contract/runtime_observation/...)"
    # claim amplo presente
    for m in AMPLO_CLAIM.finditer(source):
        return False, f"claim amplo na fixture: '{m.group(0)}' — fixture existe p/ provar, nao p/ inflar"
    return True, "canonica"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="arquivo de fixture (C/descriptor)")
    ap.add_argument("--project", default=".")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        # fixture canonica (escopo correto, sem claim amplo) -> passa
        ok, _ = check_source("static_contract: valida colisao AABB\nint main(void){}")
        assert ok
        # sem escopo -> reprova
        ok2, _ = check_source("int main(void){}")
        assert not ok2
        # claim amplo -> reprova
        ok3, _ = check_source("static_contract\n// Este e um jogo AAA completo")
        assert not ok3
        print("[SELF-CHECK OK] canonical_fixture_gate")
        return 0
    if args.file:
        src = open(args.file).read() if os.path.exists(args.file) else ""
        ok, why = check_source(src)
        print(f"[{'PASS' if ok else 'FAIL'}] {why}")
        return 0 if ok else 1
    if args.project:
        probes_dir = os.path.join(args.project, "probes")
        if not os.path.isdir(probes_dir):
            print("[PASS] sem probes/fixtures para avaliar")
            return 0
        fai = False
        for fn in sorted(os.listdir(probes_dir)):
            # documentacao/geradores nao sao fixtures; focar em fontes de probe
            if fn.lower().startswith("readme") or fn.lower().endswith(".md"):
                continue
            if fn.endswith((".c", ".h", ".json", ".py")):
                src = open(os.path.join(probes_dir, fn)).read()
                # gerador de tooling (nao e probe) tambem nao precisa de escopo de fixture
                if "gen_" in fn and "def " in src:
                    continue
                ok, why = check_source(src)
                if not ok:
                    print(f"[FAIL] {fn}: {why}")
                    fai = True
        if fai:
            return 1
        print("[PASS] todas as fixtures com escopo canonico")
        return 0
    print("[FAIL] informe --file ou --project", file=sys.stderr)
    return 3

if __name__ == "__main__":
    sys.exit(main())
