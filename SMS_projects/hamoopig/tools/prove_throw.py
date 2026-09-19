#!/usr/bin/env python3
"""B1+B2 no contrato de 2 botoes = throw (dano 10, ignora guarda)."""
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
    if not require_no_stale(why="hamoopig throw"):
        return 2
    logf = open(os.path.join(OUT, "throw_emu.log"), "w")
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
        time.sleep(3.0)
        EI.press_spec("a=180")
        time.sleep(0.5)
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
        dap.pause()
        rec["before"] = {
            "hp2": dap.read_byte(0xC7F4),
            "gap": dap.read_byte(0xC7E7),
            "state": dap.read_byte(0xC7E6),
        }
        print("before", rec["before"], flush=True)
        dap.cont()
        EI.press_chord(["a", "z"], ms=220)
        time.sleep(0.4)
        dap.pause()
        rec["after"] = {
            "hp2": dap.read_byte(0xC7F4),
            "gap": dap.read_byte(0xC7E7),
            "state": dap.read_byte(0xC7E6),
        }
        print("after", rec["after"], flush=True)
        json.dump(rec, open(os.path.join(OUT, "throw_probe.json"), "w"), indent=2)
        d = (rec["before"]["hp2"] or 0) - (rec["after"]["hp2"] or 0)
        ok = d == 10
        print("PASS throw" if ok else "FAIL throw", "delta", d)
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
