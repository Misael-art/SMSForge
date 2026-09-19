#!/usr/bin/env python3
"""Prova minima: DAP continue, entrar na luta, Right, ler probe_px."""
import os, sys, time, subprocess
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


def main():
    os.makedirs(OUT, exist_ok=True)
    if not require_no_stale(why="hamoopig walk"):
        return 2
    logf = open(os.path.join(OUT, "walk_emu.log"), "w")
    proc = subprocess.Popen(
        ["java", "-jar", JAR, "-remotedebug", "4901", "-set", "Update=0", ROM],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        for _ in range(40):
            time.sleep(0.5)
            if CE._main_window_id():
                break
        time.sleep(5.0)
        dap = None
        for _ in range(4):
            cand = wait_port(timeout_s=20)
            if cand is None:
                break
            try:
                cand.start_session()
                cand.cont()
                time.sleep(2.0)
                cand.pause()
                if cand.read_byte(0xC7F6) is not None:
                    dap = cand
                    break
            except (ConnectionError, AssertionError):
                pass
            cand.close()
            time.sleep(2.0)
        if dap is None:
            print("FAIL DAP")
            return 2
        dap.cont()
        time.sleep(3.0)
        EI.press_spec("a=180")
        time.sleep(0.6)
        EI.press_spec("a=180")
        time.sleep(1.5)
        dap.pause()
        scene = dap.read_byte(0xC7F6)
        px0 = dap.read_byte(0xC7FA)
        print(f"pre scene={scene} px={px0}")
        dap.cont()
        EI.press_spec("Right=800")
        time.sleep(0.2)
        dap.pause()
        px1 = dap.read_byte(0xC7FA)
        keys = dap.read_byte(0xC7F8)
        scene = dap.read_byte(0xC7F6)
        print(f"post scene={scene} px={px1} keys={keys} dx={(px1 or 0)-(px0 or 0)}")
        import json
        json.dump({
            "scene": scene, "px0": px0, "px1": px1, "keys": keys,
            "dx": (px1 or 0) - (px0 or 0),
            "rom_sha256": "9e3cc240b915b50c5f118cdc8741f8d91eef871a60aa9b28fa4fed28a0dd9a4d"
        }, open(os.path.join(OUT, "walk_probe.json"), "w"), indent=2)
        dap.close()
        ok = scene == 10 and px0 is not None and px1 is not None and (px1 - px0) >= 8
        print("PASS walk" if ok else "FAIL walk")
        return 0 if ok else 1
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
