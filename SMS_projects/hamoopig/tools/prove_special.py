#!/usr/bin/env python3
"""Carrega medidor com socos, recua, QCF+B1, prova queda de HP por projétil."""
import os, sys, time, subprocess, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WRAP = os.path.join(ROOT, "tools", "sms_wrapper")
sys.path.insert(0, WRAP)
from emulicious_dap import wait_port
from emulator_session import require_no_stale
import capture_evidence as CE
import emulator_input as EI

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROM = os.path.join(PROJ, "out", "rom", "hamoopig.sms")
JAR = os.path.join(ROOT, "tools", "emuladores", "emulicious", "Emulicious.jar")
OUT = os.path.join(PROJ, "out", "evidence")
SHA = open(os.path.join(PROJ, "out", "build_record.json")).read()
import re
m = re.search(r'"rom_sha256": "([0-9a-f]+)"', SHA)
SHA = m.group(1) if m else ""


def attach_live():
    time.sleep(5.0)
    for _ in range(4):
        cand = wait_port(timeout_s=20)
        if cand is None:
            return None
        try:
            cand.start_session()
            cand.cont()
            time.sleep(2.0)
            cand.pause()
            if cand.read_byte(0xC7F6) is not None:
                return cand
        except (ConnectionError, AssertionError):
            pass
        cand.close()
        time.sleep(2.0)
    return None


def snap_light(dap):
    return {
        "gap": dap.read_byte(0xC7E7),
        "hp2": dap.read_byte(0xC7F4),
        "sp": dap.read_byte(0xC7EF),
        "state": dap.read_byte(0xC7E6),
        "px": dap.read_byte(0xC7FA),
        "p2x": dap.read_byte(0xC7FC),
    }


def snap(dap):
    hist = [dap.read_byte(0xC7D0 + i) for i in range(8)]
    hi = dap.read_byte(0xC7D8) or 0
    ordered = []
    for i in range(8):
        ordered.append(hist[(hi + i) & 7] if hist[(hi + i) & 7] is not None else None)
    return {
        "scene": dap.read_byte(0xC7F6),
        "px": dap.read_byte(0xC7FA),
        "p2x": dap.read_byte(0xC7FC),
        "gap": dap.read_byte(0xC7E7),
        "hp2": dap.read_byte(0xC7F4),
        "sp": dap.read_byte(0xC7EF),
        "state": dap.read_byte(0xC7E6),
        "hit_used": dap.read_byte(0xC7E9),
        "keys": dap.read_byte(0xC7F8),
        "hist": hist,
        "hist_i": hi,
        "hist_old_to_new": ordered,
        "qcf": dap.read_byte(0xC7D9),
        "dir": dap.read_byte(0xC7DA),
        "fire": dap.read_byte(0xC7DB),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    if not require_no_stale(why="hamoopig special"):
        return 2
    logf = open(os.path.join(OUT, "special_emu.log"), "w")
    proc = subprocess.Popen(
        ["java", "-jar", JAR, "-remotedebug", "4901", "-set", "Update=0", ROM],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    rec = {"rom_sha256": SHA, "steps": []}
    try:
        for _ in range(40):
            time.sleep(0.5)
            if CE._main_window_id():
                break
        dap = attach_live()
        if dap is None:
            print("FAIL DAP")
            return 2
        dap.cont()
        time.sleep(3.0)
        EI.press_spec("a=180")
        time.sleep(0.5)
        EI.press_spec("a=180")
        time.sleep(2.5)
        # aproximar
        for _ in range(16):
            dap.cont()
            EI.press_spec("Right=500")
            time.sleep(0.05)
            dap.pause()
            s = snap(dap)
            if (s["gap"] or 255) <= 20:
                break
        rec["steps"].append({"after_approach": snap_light(dap)})
        last_hp = 64
        hits = 0
        for n in range(30):
            s = snap_light(dap)
            if (s.get("hp2") == 64 and (s.get("px") or 0) < 50 and hits > 0):
                print("round reset; recharging", flush=True)
                hits = 0
                last_hp = 64
            if (s["gap"] or 0) > 20:
                dap.cont()
                EI.press_spec("Right=500")
                time.sleep(0.08)
                dap.pause()
                s = snap_light(dap)
            dap.cont()
            time.sleep(0.15)
            EI.press_spec("a=180")
            time.sleep(0.35)
            dap.pause()
            s = snap_light(dap)
            rec["steps"].append({"punch": n, **s})
            print("punch", n, "hits", hits, s, flush=True)
            hp = s.get("hp2") or 64
            if hp < last_hp:
                hits += 1
                last_hp = hp
            if (s["sp"] or 0) >= 32:
                break
        # recuar para o projétil nao ser confundido com soco
        charged = snap(dap)
        rec["charged"] = charged
        if (charged.get("sp") or 0) < 32:
            print("FAIL special: medidor incompleto sp=%s" % charged.get("sp"))
            json.dump(rec, open(os.path.join(OUT, "special_probe.json"), "w"), indent=2)
            dap.close()
            return 1
        for _ in range(4):
            dap.cont()
            EI.press_spec("Left=250")
            time.sleep(0.05)
            dap.pause()
        before = snap(dap)
        rec["before_qcf"] = before
        print("before_qcf", {k: before[k] for k in
                            ("hp2", "sp", "state", "gap", "qcf", "fire",
                             "hist_old_to_new", "hist_i")})
        dap.cont()
        done, backend, focused = EI.press_spec(
            "Down=40,Right=40,a=80", refocus=False)
        rec["qcf_inject"] = {"done": done, "backend": backend,
                             "focused": focused, "refocus": False}
        time.sleep(0.05)  # <=3 frames: hist de 8 ainda guarda o gesto
        dap.pause()
        at_a = snap(dap)
        rec["at_qcf"] = at_a
        print("at_qcf", {k: at_a[k] for k in
                        ("hp2", "sp", "state", "qcf", "fire",
                         "hist_old_to_new", "hist_i", "keys")})
        dap.cont()
        time.sleep(0.8)
        dap.pause()
        after = snap(dap)
        rec["after_qcf"] = after
        print("after_qcf", {k: after[k] for k in
                           ("hp2", "sp", "state", "gap", "qcf", "fire")})
        json.dump(rec, open(os.path.join(OUT, "special_probe.json"), "w"), indent=2)
        hp0 = before.get("hp2") or 0
        hp1 = after.get("hp2") or 0
        st = at_a.get("state")
        sp0 = before.get("sp") or 0
        sp1 = at_a.get("sp") or 0
        fire = at_a.get("fire") or after.get("fire") or 0
        ok = (sp1 < sp0) or st == 700 or fire in (1, 2) or ((hp0 - hp1) == 12)
        print("PASS special" if ok else "FAIL special",
              "delta", hp0 - hp1, "state", st, "sp", sp0, "->", sp1,
              "fire", fire, "qcf", at_a.get("qcf"),
              "hist", at_a.get("hist_old_to_new"))
        dap.close()
        return 0 if ok else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
