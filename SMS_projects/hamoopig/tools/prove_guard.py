#!/usr/bin/env python3
"""P2 BLOCK (B2 no select), P1 soca, espera chip 2."""
import os, sys, time, subprocess, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "sms_wrapper"))
from emulicious_dap import wait_port
from emulator_session import require_no_stale
import capture_evidence as CE
import emulator_input as EI

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROM = os.path.join(PROJ, "out", "rom", "hamoopig.sms")
JAR = os.path.join(ROOT, "tools", "emuladores", "emulicious", "Emulicious.jar")
OUT = os.path.join(PROJ, "out", "evidence")


def sha():
    import re
    t = open(os.path.join(PROJ, "out", "build_record.json")).read()
    m = re.search(r'"rom_sha256": "([0-9a-f]+)"', t)
    return m.group(1) if m else ""


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


def main():
    os.makedirs(OUT, exist_ok=True)
    if not require_no_stale(why="hamoopig guard"):
        return 2
    logf = open(os.path.join(OUT, "guard_emu.log"), "w")
    proc = subprocess.Popen(
        ["java", "-jar", JAR, "-remotedebug", "4901", "-set", "Update=0", ROM],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    rec = {"rom_sha256": sha()}
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
        time.sleep(3.5)
        for _ in range(25):
            dap.pause()
            sc = dap.read_byte(0xC7F6)
            print("scene", sc, flush=True)
            if sc == 2:
                dap.cont()
                break
            if sc == 1:
                dap.cont()
                EI.press_spec("a=150")
                time.sleep(0.4)
                continue
            dap.cont()
            time.sleep(0.2)
        EI.press_spec("Down=200")
        time.sleep(0.2)
        EI.press_spec("a=180")
        time.sleep(2.5)
        for _ in range(16):
            dap.pause()
            gap = dap.read_byte(0xC7E7) or 255
            if gap <= 20:
                break
            dap.cont()
            EI.press_spec("Right=500")
            time.sleep(0.08)
        dap.cont()
        time.sleep(0.2)
        hp0 = None
        dap.pause()
        hp0 = dap.read_byte(0xC7F4)
        g0 = dap.read_byte(0xC7DC)
        rec["before"] = {"hp2": hp0, "p2g": g0, "gap": dap.read_byte(0xC7E7),
                         "ctrl": dap.read_byte(0xC7DD)}
        print("before", rec["before"], flush=True)
        dap.cont()
        EI.press_spec("a=180")
        time.sleep(0.35)
        dap.pause()
        rec["after"] = {
            "hp2": dap.read_byte(0xC7F4),
            "p2g": dap.read_byte(0xC7DC),
            "state": dap.read_byte(0xC7E6),
            "gap": dap.read_byte(0xC7E7),
        }
        print("after", rec["after"], flush=True)
        json.dump(rec, open(os.path.join(OUT, "guard_probe.json"), "w"), indent=2)
        hp1 = rec["after"]["hp2"] or 0
        delta = (hp0 or 0) - hp1
        ok = delta == 2 and rec["before"].get("p2g") == 1
        print("PASS guard" if ok else "FAIL guard", "delta", delta, "p2g", rec["before"].get("p2g"))
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
