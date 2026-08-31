#!/usr/bin/env python3
"""audit_doc_sync.py — reprova doc que afirma um estado que o repo contradiz.

A fabrica existe para impedir que narrativa vire evidencia. Este gate aplica a
mesma regra AOS PROPRIOS DOCUMENTOS: referencia quebrada e claim sem lastro.

Verifica (fatos checaveis, nao estilo):
  A) Ferramenta citada na tabela de gates do AGENTS.md EXISTE no wrapper.
  B) Ferramenta de medicao que existe no wrapper esta CITADA no AGENTS.md
     (ferramenta invisivel na doutrina nao e usada).
  C) Cada projeto em SMS_projects/ tem os arquivos da HIERARQUIA DE VERDADE
     que o AGENTS.md declara obrigatorios.
  D) Caminho de arquivo citado em .mddev/project.json (doc_authority) existe.

Uso: audit_doc_sync.py [--root <workspace>] [--json <saida>] [--self-check]
Exit: 0 sincronizado | 1 deriva detectada | 3 uso
"""
import sys, os, re, json, argparse

# Hierarquia de verdade que o AGENTS.md declara (niveis 1-7).
TRUTH_HIERARCHY = [
    "doc/10-memory-bank.md",
    "doc/11-gdd.md",
    "doc/13-spec-cenas.md",
    "doc/00-diretrizes-agente.md",
    ".mddev/project.json",
    "doc/12-roteiro.md",
    "doc/15-tdd.md",
]

MEASURE_PREFIXES = ("audit_", "validate_", "measure_", "capture_", "seal_", "reconcile_")
DOC_EXEMPT = {  # existem mas nao precisam figurar na tabela de gates
    "validate_measurement_tools.py",  # meta-gate (audita as ferramentas)
    "audit_doc_sync.py",              # este arquivo
}
TOOL_EXEMPT = {"build_inner.py", "gen_fixtures.py", "selftest.py", "png_io.py",
               "sms_palette.py", "png_to_sms_tiles.py"}

def _tools_in_wrapper(wrapper):
    return {fn for fn in os.listdir(wrapper)
            if fn.endswith(".py") and fn not in TOOL_EXEMPT
            and (fn.startswith(MEASURE_PREFIXES) or fn.endswith("_gate.py"))}

def audit(root):
    problems = []
    wrapper = os.path.join(root, "tools", "sms_wrapper")
    agents = os.path.join(root, "AGENTS.md")
    if not os.path.isdir(wrapper):
        return [f"wrapper ausente: {wrapper}"]
    if not os.path.isfile(agents):
        return [f"AGENTS.md ausente: {agents}"]

    text = open(agents, encoding="utf-8", errors="replace").read()
    cited = set(re.findall(r"([A-Za-z0-9_]+\.py)", text))
    present = _tools_in_wrapper(wrapper)

    # (A) citada mas inexistente
    for fn in sorted(cited):
        if fn in TOOL_EXEMPT or fn in DOC_EXEMPT:
            continue
        if fn.startswith(MEASURE_PREFIXES) or fn.endswith("_gate.py"):
            if not os.path.isfile(os.path.join(wrapper, fn)):
                problems.append(f"AGENTS.md cita '{fn}' que NAO existe no wrapper")

    # (B) existe mas nao citada
    for fn in sorted(present - cited - DOC_EXEMPT):
        problems.append(f"'{fn}' existe no wrapper mas NAO esta citada no AGENTS.md "
                        "(gate invisivel na doutrina)")

    # (C)/(D) hierarquia de verdade por projeto
    projects_dir = os.path.join(root, "SMS_projects")
    if os.path.isdir(projects_dir):
        for name in sorted(os.listdir(projects_dir)):
            proj = os.path.join(projects_dir, name)
            if not os.path.isdir(proj) or name.startswith("_"):
                continue
            for rel in TRUTH_HIERARCHY:
                if not os.path.isfile(os.path.join(proj, rel)):
                    problems.append(f"{name}: falta '{rel}' (hierarquia de verdade)")
            mf = os.path.join(proj, ".mddev", "project.json")
            if os.path.isfile(mf):
                try:
                    d = json.load(open(mf))
                except (json.JSONDecodeError, OSError) as e:
                    problems.append(f"{name}: .mddev/project.json ilegivel ({e})")
                    continue
                for rel in d.get("doc_authority", []):
                    if not os.path.isfile(os.path.join(proj, rel)):
                        problems.append(f"{name}: doc_authority aponta para "
                                        f"'{rel}' que nao existe")
    return problems

def _self_check():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="smsdocsync_")
    try:
        w = os.path.join(d, "tools", "sms_wrapper")
        os.makedirs(w)
        open(os.path.join(w, "audit_x.py"), "w").write("# --self-check\n")
        proj = os.path.join(d, "SMS_projects", "p1")
        os.makedirs(os.path.join(proj, "doc"))
        os.makedirs(os.path.join(proj, ".mddev"))
        for rel in TRUTH_HIERARCHY:
            p = os.path.join(proj, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w").write("{}" if p.endswith(".json") else "x")
        json.dump({"doc_authority": ["doc/11-gdd.md"]},
                  open(os.path.join(proj, ".mddev", "project.json"), "w"))
        agents = os.path.join(d, "AGENTS.md")

        # caso SINCRONIZADO
        open(agents, "w").write("tabela de gates: audit_x.py\n")
        p = audit(d)
        assert not p, f"repo sincronizado nao deveria reprovar: {p}"

        # (A) doc cita ferramenta inexistente
        open(agents, "w").write("gates: audit_x.py e audit_fantasma.py\n")
        p = audit(d)
        assert any("NAO existe no wrapper" in x for x in p), f"faltou pegar (A): {p}"

        # (B) ferramenta existe mas nao citada
        open(agents, "w").write("nenhum gate citado aqui\n")
        p = audit(d)
        assert any("NAO esta citada" in x for x in p), f"faltou pegar (B): {p}"

        # (C) hierarquia de verdade incompleta
        open(agents, "w").write("gates: audit_x.py\n")
        os.remove(os.path.join(proj, "doc", "11-gdd.md"))
        p = audit(d)
        assert any("hierarquia de verdade" in x for x in p), f"faltou pegar (C): {p}"
        # (D) doc_authority apontando para arquivo removido
        assert any("doc_authority" in x for x in p), f"faltou pegar (D): {p}"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] doc_sync (pega gate fantasma, gate invisivel, "
          "hierarquia incompleta e doc_authority quebrada)")
    return 0

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.normpath(os.path.join(here, "..", "..")))
    ap.add_argument("--json", help="grava relatorio machine-readable")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    if args.self_check:
        return _self_check()

    problems = audit(args.root)
    if args.json:
        json.dump({"problems": problems, "in_sync": not problems},
                  open(args.json, "w"), indent=2)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print(f"[FAIL] {len(problems)} deriva(s) doc<->repo. "
              "Documento que afirma estado falso e overclaim.")
        return 1
    print("[PASS] documentacao sincronizada com o repositorio")
    return 0

if __name__ == "__main__":
    sys.exit(main())
