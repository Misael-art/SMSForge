#!/usr/bin/env python3
"""selftest.py — prova que os gates funcionam ANTES de medir qualquer projeto.

Regra §19/§20 (SMS_GLOBAL): ferramenta de medicao sem self-check nao e fonte;
gate precisa reprovar em teste conhecido e passar em fixture valida.

Bateria: cada gate roda --self-check, depois e desafiado com fixtures
validas (deve PASSAR) e invalidas (deve REPROVAR). Exit 0 so se TUDO verde.
"""
import sys, os, subprocess, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PY = sys.executable or "python3"

def run(args, expect_code, label):
    r = subprocess.run([PY] + args, capture_output=True, text=True, cwd=HERE)
    ok = r.returncode == expect_code
    detail = (r.stdout + r.stderr).strip().splitlines()
    tail = detail[-1][:90] if detail else ""
    print(f"  {'[OK ]' if ok else '[XX ]'} {label}  ({tail})")
    return ok

BOOTSTRAP_REQUIRED = (
    ".mddev/project.json", "doc/00-diretrizes-agente.md", "doc/10-memory-bank.md",
    "doc/11-gdd.md", "doc/12-roteiro.md", "doc/13-spec-cenas.md",
    "doc/15-tdd.md", "src/main.c", "build.sh",
)

def _check_bootstrap():
    """Cria um projeto descartavel e prova que a hierarquia de verdade materializa."""
    name = "_selftest_bootstrap_tmp"
    dest = os.path.normpath(os.path.join(HERE, "..", "..", "SMS_projects", name))
    script = os.path.join(HERE, "new_project.sh")
    if os.path.exists(dest):
        shutil.rmtree(dest, ignore_errors=True)
    try:
        r = subprocess.run(["bash", script, name], capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stdout + r.stderr).strip().splitlines()
            print(f"  [XX ] bootstrap new_project.sh falhou  ({tail[-1][:80] if tail else ''})")
            return False
        # ausente OU vazio conta como nao materializado
        bad = [f for f in BOOTSTRAP_REQUIRED
               if not (os.path.isfile(os.path.join(dest, f))
                       and os.path.getsize(os.path.join(dest, f)) > 0)]
        if bad:
            print(f"  [XX ] bootstrap sem hierarquia de verdade  (falta: {', '.join(bad[:3])})")
            return False
        leftover = subprocess.run(["grep", "-rl", "__PROJECT_NAME__", dest],
                                  capture_output=True, text=True)
        if leftover.returncode == 0:
            print("  [XX ] bootstrap deixou placeholder __PROJECT_NAME__ sem substituir")
            return False
        print(f"  [OK ] bootstrap materializa hierarquia de verdade  "
              f"({len(BOOTSTRAP_REQUIRED)} arquivos, sem placeholder)")
        return True
    finally:
        shutil.rmtree(dest, ignore_errors=True)

def main():
    import gen_fixtures
    results = []
    print("== Fase 1: self-check de cada gate ==")
    for g in ("audit_validate_resources.py", "audit_sprite_line_sim.py",
              "audit_luma_floor.py", "audit_provenance.py", "audit_claims.py",
              "capture_evidence.py",
              "audit_meaningful_change.py", "audit_placeholder_quarantine.py",
              "audit_deterministic_boot.py", "canonical_fixture_gate.py",
              "audit_mastery_registry.py",
              "audit_specialization.py",
              "audit_audio.py",
              "measure_fps.py",
              "validate_measurement_tools.py",
              "audit_doc_sync.py",
              "screenshot_semantic_gate.py",
              "seal_fresh_evidence_bundle.py",
              "reconcile_claims.py"):
        results.append(run([os.path.join(HERE, g), "--self-check"], 0,
                           f"selfcheck:{g}"))
    print("== Fase 2: fixtures geradas ==")
    tmp = tempfile.mkdtemp(prefix="smsforge_selftest_")
    fx = gen_fixtures.generate(tmp)
    R = os.path.join(HERE, "audit_validate_resources.py")
    S = os.path.join(HERE, "audit_sprite_line_sim.py")
    L = os.path.join(HERE, "audit_luma_floor.py")

    cases = [
        ([R, fx["valid_bg"]], 0, "bg valido aprovado"),
        ([R, fx["bad_grid"]], 1, "gate reprovou grid fora de 8x8"),
        ([R, fx["bad_color"]], 1, "gate reprovou cor fora dos codigos 6-bit"),
        ([R, fx["opaque_idx0"]], 1, "gate reprovou indice 0 opaco"),
        ([R, "--kind", "sprite", fx["valid_sprite"]], 0, "sprite 16x16 aprovado"),
        ([R, "--kind", "sprite", fx["bad_sprite"]], 1, "gate reprovou sprite 12x12"),
        ([S, fx["scene_ok"]], 0, "cena com 10 sprites dispersos aprovada"),
        ([S, fx["scene_bad_line"]], 1, "gate reprovou 9 sprites numa scanline"),
        ([S, fx["scene_bad_sat"]], 1, "gate reprovou SAT >64"),
        ([S, fx["scene_bad_d0"]], 1, "gate reprovou colisao com terminador 0xD0"),
        ([L, "--scene", fx["luma_ok"]], 0, "contraste branco/preto aprovado"),
        ([L, "--scene", fx["luma_bad"]], 1, "gate reprovou cinza sobre branco"),
    ]
    print("== Fase 3: bateria valida/reprova ==")
    for args, exp, label in cases:
        results.append(run(args, exp, label))

    print("== Fase 4: bootstrap materializa a hierarquia de verdade ==")
    # O contrato do new_project.sh: projeto novo nasce com os niveis 1-7 do
    # AGENTS.md e capaz de buildar. Provado criando um projeto DESCARTAVEL.
    results.append(_check_bootstrap())

    print("== Fase 5: build honesto (ambiente sem toolchain) ==")
    proj = os.environ.get("SMSFORGE_PROBE_PROJECT")
    proj_added = False
    if proj and os.path.isdir(proj):
        r = subprocess.run([PY, os.path.join(HERE, "build_inner.py"), "--project", proj],
                           capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip().splitlines()
        tail = out[-1][:90] if out else ""
        honest = (r.returncode == 2) or (r.returncode == 0)
        print(f"  [{'OK ' if honest else 'XX '}] probe build_inner (exit {r.returncode})  ({tail})")
        results.append(honest)
        proj_added = True
    else:
        print("  [--] probe de projeto ausente (SMSFORGE_PROBE_PROJECT); pulado")
    shutil.rmtree(tmp, ignore_errors=True)

    n_ok = sum(results)
    total = len(results)
    base = total - (1 if proj_added else 0)
    print(f"\nSELFTEST: {n_ok}/{total} verdes ({base} base + "
          f"{'1 probe de build' if proj_added else 'probe opcional nao rodado'})")
    for i, ok in enumerate(results):
        if not ok:
            pass
    if n_ok != total:
        print("[SELFTEST FAIL] ha gate mentindo. Corrigir antes de qualquer uso.")
        return 1
    print("[SELFTEST OK] todos os gates provados: aprovam o valido, reprovam o invalido.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
