#!/usr/bin/env python3
"""audit_hscroll_blank.py — H-scroll ao vivo exige LEFTCOLBLANK (L043/§6).

SMS_setBGScrollX(0) (e INLINE equivalente) nao e scroll ao vivo.
Qualquer outro argumento, sem VDPFEATURE_LEFTCOLBLANK no projeto, reprova:
os 8 px da esquerda mostram lixo do tile que ainda nao foi buscado.

Uso:
  audit_hscroll_blank.py --project DIR
  audit_hscroll_blank.py --self-check
Exit: 0 ok | 1 contrato violado | 3 uso
"""
import argparse, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
# Argumento que NAO e zero literal: scroll ao vivo (variavel, expressao, constante).
LIVE = re.compile(
    r"(?:INLINE_)?SMS_setBGScrollX\s*\(\s*(?!0\s*\))([^)]*)\)"
)
ZERO = re.compile(r"(?:INLINE_)?SMS_setBGScrollX\s*\(\s*0\s*\)")
BLANK = re.compile(r"VDPFEATURE_LEFTCOLBLANK")


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


def audit_project(project):
    live, blank, notes = [], False, []
    for src in _sources(project):
        try:
            text = open(src, encoding="utf-8", errors="replace").read()
        except OSError as e:
            notes.append(f"{src}: ilegivel ({e})")
            continue
        rel = os.path.relpath(src, project)
        if BLANK.search(text):
            blank = True
        for m in LIVE.finditer(text):
            arg = m.group(1).strip()
            live.append(f"{rel}: SMS_setBGScrollX({arg})")
    if notes:
        return notes
    if live and not blank:
        return [f"H-scroll ao vivo sem LEFTCOLBLANK ({'; '.join(live[:3])}) (L043)"]
    return []


def _self_check():
    d = tempfile.mkdtemp(prefix="smshscr_")
    try:
        os.makedirs(os.path.join(d, "src"))
        open(os.path.join(d, "src", "a.c"), "w").write(
            "SMS_setBGScrollX(0);\nSMS_setBGScrollY(0);\n")
        assert not audit_project(d), "scroll zero nao exige blank"

        open(os.path.join(d, "src", "b.c"), "w").write(
            "SMS_setBGScrollX(scrollx);\n")
        p = audit_project(d)
        assert p and "LEFTCOLBLANK" in p[0], f"faltou pegar H-scroll vivo: {p}"

        open(os.path.join(d, "src", "c.c"), "w").write(
            "SMS_VDPturnOnFeature(VDPFEATURE_LEFTCOLBLANK);\n"
            "INLINE_SMS_setBGScrollX(scr_near);\n")
        assert not audit_project(d), "com LEFTCOLBLANK deveria passar"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] hscroll_blank (zero passa, vivo sem blank reprova, "
          "vivo com blank passa)")
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
    problems = audit_project(os.path.abspath(a.project))
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print("[FAIL] H-scroll sem LEFTCOLBLANK (L043).")
        return 1
    print("[PASS] contrato H-scroll/LEFTCOLBLANK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
