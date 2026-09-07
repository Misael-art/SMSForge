#!/usr/bin/env python3
"""Descartavel: qual bit do joypad cada tecla fisica acende?

Le probe_keys (0xC7F8) com a tecla SEGURA (o registro so vale com o botao
em baixo), entre resets. Hipotese sob teste: a tecla A acende PORT_B_KEY_1
(bit alto, truncado em probe_keys=unsigned char) — o titulo sai porque a
mascara dele aceita os dois portes, mas control(0,...) so le PORT_A, e por
isso o soco do Ken nunca sai.
"""
import subprocess
import sys
import time

sys.path.insert(0, "/mnt/sdcard/Projects/SMSForge/tools/sms_wrapper")

import emulator_input as EI                                      # noqa: E402
import measure_runtime_probe as MRP                              # noqa: E402
from emulicious_dap import PORT                                  # noqa: E402

CANDIDATOS = [("A", 30), ("Z", 44), ("X", 45), ("S", 31), ("D", 32),
              ("Q", 16), ("W", 17), ("Space", 57), ("Return", 28)]


def main():
    proc = subprocess.Popen(
        ["java", "-jar",
         "/mnt/sdcard/Projects/SMSForge/tools/emuladores/emulicious/Emulicious.jar",
         "-remotedebug", str(PORT),
         "/mnt/sdcard/Projects/SMSForge/SMS_projects/MSSF2T/out/rom/MSSF2T.sms"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True, env=EI.ENV)
    dap = None
    try:
        dap = MRP._connect_live()
        if dap is None:
            print("DAP morto")
            return 2
        EI.ensure_ydotool_daemon()
        time.sleep(2.5)
        for nome, code in CANDIDATOS:
            EI.focus_wayland()
            dap.cont()
            EI.tap_reset()
            time.sleep(2.0)
            EI.ydotool_key(code, True)
            time.sleep(0.35)
            dap.pause()
            k = dap.read_byte(0xC7F8)
            st = dap.read_byte(0xC7F6)
            EI.ydotool_key(code, False)
            print("%-7s -> probe_keys=0x%02X estado=%s" % (nome, k or 0, st))
        return 0
    finally:
        try:
            if dap:
                dap.close()
        finally:
            proc.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
