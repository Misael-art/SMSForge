#!/usr/bin/env python3
"""audit_specialization.py — valida especializacao de genero (porta do SGDK Forge).

Lê doc/game-design/matriz_genero.json e o `genre` declarado no projeto
(.mddev/project.json -> specialization). Verifica se o projeto cumpre os eixos
congelados do gênero. Um projeto SEM genero declarado = sem requisitos (passa).

Uso: audit_specialization.py --project <dir> [--self-check]
Exit: 0 cumpre | 1 falta eixo congelado | 3 uso
"""
import sys, os, json, argparse

def read_json(path):
    try:
        return json.load(open(path))
    except (json.JSONDecodeError, OSError):
        return None

def audit(project):
    gen_mat = read_json(os.path.join(os.path.dirname(__file__), "..", "..",
                                     "doc", "game-design", "matriz_genero.json"))
    if not gen_mat:
        return [], "sem matriz de genero"
    proj = read_json(os.path.join(project, ".mddev", "project.json"))
    if not proj:
        return [], "sem project.json"
    gen = proj.get("specialization") or proj.get("genre")
    if not gen:
        return [], "sem genero declarado (sem requisitos — ok)"
    fam = gen_mat.get("familias", {}).get(gen)
    if not fam:
        return [], f"genero '{gen}' fora da matriz"
    blockers = fam.get("blockers_aaa", [])
    gaps = []
    # busca por presença dos eixos no GDD do projeto (indicador de cumprimento)
    gdd = os.path.join(project, "doc", "11-gdd.md")
    gdd_txt = open(gdd).read().lower() if os.path.exists(gdd) else ""
    for eixo in fam.get("eixos", []):
        if eixo not in gdd_txt:
            gaps.append(f"eixo '{eixo}' ausente no GDD")
    return gaps if gaps else [], f"genero '{gen}' — eixos presentes no GDD"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        import tempfile
        d = tempfile.mkdtemp(prefix="smsspec_")
        os.makedirs(os.path.join(d, ".mddev"), exist_ok=True)
        os.makedirs(os.path.join(d, "doc"), exist_ok=True)
        json.dump({"name": "t", "specialization": "puzzle"},
                  open(os.path.join(d, ".mddev", "project.json"), "w"))
        # puzzle exige 'logica_deterministica' etc no GDD; sem GDD -> gaps
        gaps, msg = audit(d)
        assert gaps, "sem GDD deveria acusar gaps"
        # declarar genero ausente -> passa sem requisitos
        json.dump({"name": "t"}, open(os.path.join(d, ".mddev", "project.json"), "w"))
        gaps2, _ = audit(d)
        assert not gaps2, "sem genero = sem requisitos"
        print("[SELF-CHECK OK] specialization")
        return 0
    gaps, msg = audit(args.project)
    print(f"[{'FAIL' if gaps else 'PASS'}] {msg}")
    for g in gaps:
        print(f"   - {g}")
    return 1 if gaps else 0

if __name__ == "__main__":
    sys.exit(main())
