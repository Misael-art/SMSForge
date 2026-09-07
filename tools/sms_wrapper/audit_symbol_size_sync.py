#!/usr/bin/env python3
"""audit_symbol_size_sync.py — tamanho de asset nao se escreve em dois lugares (L052).

O consumidor leu fight_gfx.h (1024) enquanto a folha ja tinha 832 B: o
streamer leu 192 B alem do array. Sem sintoma visivel. Este gate confere
#define NOME_SIZE contra o array e contra o mesmo define em outro header.

Uso:
  audit_symbol_size_sync.py --project DIR
  audit_symbol_size_sync.py --self-check
Exit: 0 ok/skip | 1 diverge | 3 uso
"""
import argparse, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEF_SIZE = re.compile(r"#define\s+([A-Z][A-Z0-9_]*_SIZE)\s+(\d+)")
# `const unsigned char ken_idle_tiles[832]`
ARRAY_SIMPLE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*(\d+)\s*\]"
)


def _sources(project):
    out = []
    for sub in ("src", "inc"):
        d = os.path.join(project, sub)
        if not os.path.isdir(d):
            continue
        for dirpath, _, files in os.walk(d):
            for fn in files:
                if fn.endswith((".c", ".h")):
                    out.append(os.path.join(dirpath, fn))
    return out


def _macro_to_array(macro):
    stem = macro[:-5] if macro.endswith("_SIZE") else macro
    return stem.lower()


def audit_project(project):
    macros = {}   # name -> [(file, value)]
    arrays = {}   # name -> [(file, value)]
    problems = []
    files = _sources(project)
    if not files:
        return [], "skip: sem src/inc"
    for src in files:
        try:
            text = open(src, encoding="utf-8", errors="replace").read()
        except OSError as e:
            problems.append(f"{src}: ilegivel ({e})")
            continue
        rel = os.path.relpath(src, project)
        for m in DEF_SIZE.finditer(text):
            macros.setdefault(m.group(1), []).append((rel, int(m.group(2))))
        for m in ARRAY_SIMPLE.finditer(text):
            name, n = m.group(1), int(m.group(2))
            # ignora indexacao de uso (p[0], map[24]) sem ser declaracao
            # de array: so conta se o nome aparece com tipo ou define irmao.
            arrays.setdefault(name, []).append((rel, n))
    for name, occs in macros.items():
        vals = {v for _, v in occs}
        if len(vals) > 1:
            detalhe = ", ".join(f"{f}={v}" for f, v in occs)
            problems.append(
                f"{name} diverge entre headers ({detalhe}) (L052)")
        want = next(iter(vals))
        arr = _macro_to_array(name)
        if arr in arrays:
            for f, n in arrays[arr]:
                if n != want:
                    problems.append(
                        f"{name}={want} mas {arr}[{n}] em {f} (L052)")
    return problems, None


def _self_check():
    d = tempfile.mkdtemp(prefix="smssz_")
    try:
        inc = os.path.join(d, "inc")
        os.makedirs(inc)
        open(os.path.join(inc, "leaf.h"), "w").write(
            "#define KEN_IDLE_TILES_SIZE 832\n"
            "const unsigned char ken_idle_tiles[832] = {0};\n")
        open(os.path.join(inc, "gfx.h"), "w").write(
            "#define KEN_IDLE_TILES_SIZE 832\n")
        p, _ = audit_project(d)
        assert not p, f"match nao deveria reprovar: {p}"

        open(os.path.join(inc, "gfx.h"), "w").write(
            "#define KEN_IDLE_TILES_SIZE 1024\n")
        p, _ = audit_project(d)
        assert any("diverge" in x or "1024" in x for x in p), \
            f"faltou pegar 1024 vs 832: {p}"

        e = tempfile.mkdtemp(prefix="smssz2_")
        try:
            os.makedirs(os.path.join(e, "src"))
            p, skip = audit_project(e)
            assert not p
        finally:
            shutil.rmtree(e, ignore_errors=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] symbol_size_sync (match passa, 1024 vs 832 reprova)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    if not a.project:
        print("[FAIL] --project obrigatorio (ou --self-check)", file=sys.stderr)
        return 3
    problems, skip = audit_project(os.path.abspath(a.project))
    if skip and not problems:
        print(f"[PASS] {skip}")
        return 0
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print(f"[FAIL] {len(problems)} tamanho(s) duplicado(s) divergente(s) (L052).")
        return 1
    print("[PASS] tamanhos de simbolo coerentes entre define e array")
    return 0


if __name__ == "__main__":
    sys.exit(main())
