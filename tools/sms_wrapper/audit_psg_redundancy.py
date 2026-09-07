#!/usr/bin/env python3
"""audit_psg_redundancy.py — stream PSGlib nao e N copias do mesmo frame (L051).

PSGlib volta ao inicio no PSGEnd. 240 copias byte a byte do mesmo frame de
12 B ocupavam 2881 B e nao tocavam nada extra. Antes de sacrificar feature
por espaco, medir a redundancia.

Reprova so o caso pago: um unico payload de frame, repetido >= 8 vezes.
Ostinato com notas distintas (varios payloads) passa.

Uso:
  audit_psg_redundancy.py --project DIR
  audit_psg_redundancy.py --self-check
Exit: 0 ok/skip | 1 redundante | 3 uso
"""
import argparse, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WAIT, END = 0x38, 0x00
MIN_DUP_FRAMES = 8
HEX = re.compile(r"0x([0-9A-Fa-f]{2})")


def frames_of(blob):
    """Lista de payloads entre WAIT; ignora o END final."""
    if not blob:
        return []
    data = bytes(blob)
    if data[-1] == END:
        data = data[:-1]
    out, cur = [], bytearray()
    for b in data:
        if b == WAIT:
            out.append(bytes(cur))
            cur = bytearray()
        else:
            cur.append(b)
    if cur:
        out.append(bytes(cur))
    return out


def verdict(blob, label):
    fr = frames_of(blob)
    if len(fr) < MIN_DUP_FRAMES:
        return None
    uniq = set(fr)
    if len(uniq) == 1:
        return (f"{label}: {len(fr)} frames identicos "
                f"({len(fr[0])} B cada); PSGlib ja faz loop (L051)")
    return None


def _load_psg_sources(project):
    found = []
    audio = os.path.join(project, "res", "audio")
    if os.path.isdir(audio):
        for fn in sorted(os.listdir(audio)):
            if fn.endswith(".psg"):
                path = os.path.join(audio, fn)
                found.append((os.path.relpath(path, project),
                              open(path, "rb").read()))
    inc = os.path.join(project, "inc")
    if os.path.isdir(inc):
        for fn in sorted(os.listdir(inc)):
            if not (fn.startswith("music_") or fn.startswith("sfx_")):
                continue
            if not fn.endswith(".h"):
                continue
            path = os.path.join(inc, fn)
            text = open(path, encoding="utf-8", errors="replace").read()
            hx = HEX.findall(text)
            if hx:
                found.append((os.path.relpath(path, project),
                              bytes(int(x, 16) for x in hx)))
    return found


def audit_project(project):
    items = _load_psg_sources(project)
    if not items:
        return [], "skip: sem .psg nem inc/music_*|sfx_*"
    problems = []
    for label, blob in items:
        msg = verdict(blob, label)
        if msg:
            problems.append(msg)
    return problems, None


def _self_check():
    d = tempfile.mkdtemp(prefix="smspsgred_")
    try:
        inc = os.path.join(d, "inc")
        os.makedirs(inc)
        frame = [0x80, 0x4A, 0x91]
        fat = []
        for _ in range(12):
            fat.extend(frame)
            fat.append(WAIT)
        fat.append(END)
        open(os.path.join(inc, "music_battle.h"), "w").write(
            "static const unsigned char music_battle[] = { "
            + ",".join(f"0x{b:02X}" for b in fat) + " };\n")
        p, _ = audit_project(d)
        assert p and "identicos" in p[0], f"faltou pegar 12 copias: {p}"

        mixed = []
        for i in range(12):
            mixed.extend([0x80, 0x40 + i, 0x91])
            mixed.append(WAIT)
        mixed.append(END)
        open(os.path.join(inc, "music_battle.h"), "w").write(
            "static const unsigned char music_battle[] = { "
            + ",".join(f"0x{b:02X}" for b in mixed) + " };\n")
        p, _ = audit_project(d)
        assert not p, f"ostinato com notas distintas reprovou: {p}"

        short = frame + [WAIT] + frame + [WAIT] + [END]
        open(os.path.join(inc, "sfx_shot.h"), "w").write(
            "static const unsigned char sfx_shot[] = { "
            + ",".join(f"0x{b:02X}" for b in short) + " };\n")
        os.remove(os.path.join(inc, "music_battle.h"))
        p, _ = audit_project(d)
        assert not p, f"SFX curto identico nao e o caso pago: {p}"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] psg_redundancy (12 copias reprovam, ostinato distinto "
          "e SFX curto passam)")
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
        print(f"[FAIL] {len(problems)} stream(s) PSG redundante(s) (L051).")
        return 1
    print("[PASS] streams PSG sem copia inutil do mesmo frame")
    return 0


if __name__ == "__main__":
    sys.exit(main())
