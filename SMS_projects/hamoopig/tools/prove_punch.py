#!/usr/bin/env python3
"""Aproxima P1 do dummy e tenta soco; le probe_boss (HP P2) e estado."""
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
SHA = "550f7c99e0ddf897af50eb5ccaf6c6985cc6dee3ab2fa70bd834767c44d99977"


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
    if not require_no_stale(why="hamoopig punch"):
        return 2
    logf = open(os.path.join(OUT, "punch_emu.log"), "w")
    proc = subprocess.Popen(
        ["java", "-jar", JAR, "-remotedebug", "4901", "-set", "Update=0", ROM],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
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
        time.sleep(2.5)  # ROUND+FIGHT lock = 90 frames; nao andar durante g_lock
        gap = 255
        px = 0
        p2x = 0
        for _ in range(16):
            dap.cont()
            EI.press_spec("Right=500")
            time.sleep(0.05)
            dap.pause()
            px = dap.read_byte(0xC7FA) or 0
            p2x = dap.read_byte(0xC7FC) or 0
            gap = dap.read_byte(0xC7E7) or 255
            print(f"approach px={px} p2x={p2x} gap={gap}")
            if gap <= 24:
                break
        hp0 = dap.read_byte(0xC7F4)
        st = dap.read_byte(0xC7E6)
        print(f"pre hp2={hp0} px={px} p2x={p2x} gap={gap} state={st}")
        dap.cont()
        EI.press_spec("a=150")
        time.sleep(0.12)  # amostrar na janela ativa (~4 frames)
        dap.pause()
        hp1 = dap.read_byte(0xC7F4)
        st1 = dap.read_byte(0xC7E6)
        used = dap.read_byte(0xC7E9)
        rec = {
            "rom_sha256": SHA,
            "hp0": hp0, "hp1": hp1, "px": px, "p2x": p2x, "gap": gap,
            "state_pre": st, "state_post": st1, "hit_used": used,
            "delta": (hp0 or 0) - (hp1 or 0)
        }
        json.dump(rec, open(os.path.join(OUT, "punch_probe.json"), "w"), indent=2)
        print(rec)
        ok = hp0 == 64 and hp1 is not None and hp1 < hp0
        print("PASS punch" if ok else "FAIL punch")
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
