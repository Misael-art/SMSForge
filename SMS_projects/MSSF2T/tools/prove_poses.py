#!/usr/bin/env python3
"""Prova que AGACHAR e PULAR viram pose de verdade — lendo a RAM.

Por que não por screenshot: cada estado dura ~20 frames e o
`capture_evidence` não é exato em contagem de frames (a mesma chamada caiu na
luta numa execução e no título em outra). Fotografar a pose certa é sorteio.
Aqui a pergunta é feita onde tem resposta única, como no `prove_input_memory`:

  probe_pose (0xC7F9) = P[0].pose   -> qual folha está carregada
  probe_py   (0xC7FB) = P[0].y      -> altura; no chão é GROUND_Y (112)

Critério: durante a vitrine da atração, a pose tem de assumir POSE_CROUCH e
POSE_JUMP, e no frame em que a pose é JUMP o y tem de estar ACIMA do chão —
senão a pose de pulo estaria aparecendo com o lutador plantado.

Uso: prove_poses.py --rom <rom.sms> [--project D] [--seconds 25]
Exit: 0 provado | 1 reprovado | 2 ambiente ausente
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WRAPPER = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, os.pardir,
                                       "tools", "sms_wrapper"))
sys.path.insert(0, WRAPPER)

import capture_evidence as CE                                    # noqa: E402
from emulicious_dap import PORT                                  # noqa: E402
import measure_runtime_probe as MRP                              # noqa: E402

PROBE_POSE = 0xC7F9
PROBE_PY = 0xC7FB
PROBE_PX = 0xC7FA
PROBE_P2X = 0xC7FC
PROBE_STATE = 0xC7F6
GROUND_Y = 112
NOMES = {0: "IDLE", 1: "WALK", 2: "PUNCH", 3: "SPECIAL", 4: "HIT",
         5: "KO", 6: "CROUCH", 7: "JUMP"}


def run(rom, project, seconds, out_name):
    jar = CE.resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado")
        return 2, None
    out_dir = os.path.join(project, "out", "evidence")
    os.makedirs(out_dir, exist_ok=True)
    logf = open(os.path.join(out_dir, f"{out_name}_emu.log"), "w")
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", str(PORT), os.path.abspath(rom)],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    dap = None
    try:
        dap = MRP._connect_live()
        if dap is None:
            print("[FAIL] canal DAP nao ficou vivo")
            return 1, None

        vistos = {}
        faces = set()
        traco = []
        amostras = []
        fim = time.time() + seconds
        while time.time() < fim:
            dap.cont()
            time.sleep(0.12)          # ~7 frames: mais rapido que a pose muda
            dap.pause()
            raw = dap.read_byte(PROBE_POSE)
            pose = None if raw is None else (raw & 0x7F)
            facing = None if raw is None else (raw >> 7)
            py = dap.read_byte(PROBE_PY)
            gs = dap.read_byte(PROBE_STATE)
            px = dap.read_byte(PROBE_PX)
            p2x = dap.read_byte(PROBE_P2X)
            if px is not None and p2x is not None:
                traco.append((pose, py, px, p2x, facing))
            if pose is None:
                continue
            amostras.append({"pose": pose, "y": py, "gs": gs, "facing": facing})
            faces.add(facing)
            # Guarda o menor y visto por pose: para o pulo isso e o apice.
            if pose not in vistos or (py is not None and py < vistos[pose]):
                vistos[pose] = py

        poses = sorted(vistos)
        for p in poses:
            print(f"       pose {NOMES.get(p, p):8s} vista; menor y = {vistos[p]}")

        pulos = [t for t in traco if t[0] == 7]
        if pulos:
            print("       durante o pulo (pose, y, ken_x, guile_x, facing):")
            for t in pulos[:8]:
                print(f"         {NOMES.get(t[0]):6s} y={t[1]:3} ken_x={t[2]:3} "
                      f"guile_x={t[3]:3} facing={t[4]}")
        flip_visto = len(faces - {None}) > 1
        print(f"       facing observado: {sorted(faces - {None})} "
              f"-> troca de lado {'SIM' if flip_visto else 'nao ocorreu na amostra'}")
        tem_crouch = 6 in vistos
        tem_jump = 7 in vistos
        # No apice do pulo o lutador tem de estar acima do chao.
        jump_no_ar = tem_jump and vistos[7] is not None and vistos[7] < GROUND_Y
        ok = tem_crouch and tem_jump and jump_no_ar
        if not tem_crouch:
            print("       [FAIL] POSE_CROUCH nunca apareceu")
        if not tem_jump:
            print("       [FAIL] POSE_JUMP nunca apareceu")
        elif not jump_no_ar:
            print(f"       [FAIL] POSE_JUMP apareceu mas y nunca subiu "
                  f"(menor={vistos[7]}, chao={GROUND_Y})")

        metrics = {
            "schema": "poses_v1",
            "rom": rom,
            "rom_sha256": hashlib.sha256(open(rom, "rb").read()).hexdigest(),
            "probe_pose_addr": hex(PROBE_POSE),
            "amostras": len(amostras),
            "poses_vistas": {NOMES.get(p, str(p)): vistos[p] for p in poses},
            "crouch_provado": tem_crouch,
            "facing_observado": sorted(faces - {None}),
            "troca_de_lado_observada": flip_visto,
            "jump_provado": bool(jump_no_ar),
            "ground_y": GROUND_Y,
            "criterio": ("POSE_CROUCH e POSE_JUMP tem de aparecer; no pulo o y "
                         "tem de ficar acima do chao"),
            "por_que_memoria": ("cada estado dura ~20 frames e capture_evidence "
                                "nao e exato em frames — screenshot da pose "
                                "certa e sorteio"),
        }
        json.dump(metrics, open(os.path.join(out_dir, f"{out_name}.json"), "w"),
                  indent=1)
        print(f"[{'PASS' if ok else 'FAIL'}] agachar/pular "
              f"{'provados' if ok else 'NAO provados'} na memoria")
        return (0 if ok else 1), metrics
    finally:
        try:
            if dap:
                dap.close()
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--project", default=".")
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--out", default="poses")
    a = ap.parse_args()
    code, _ = run(a.rom, os.path.abspath(a.project), a.seconds, a.out)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
