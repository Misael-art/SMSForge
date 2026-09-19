#!/usr/bin/env python3
"""measure_worst_frame.py — mede o worst-frame de VBlank NA ROM (L061).

Orçamento de cena "declarado" (ex.: doc/13-spec-cenas.md) não fecha eixo
nenhum até existir instrumento NA ROM. Padrão do probe SMRT (aditivo,
schema 1):
  - probe_vline (0xC7EA): VCounter lido NO FIM do trabalho do frame, antes
    do SMS_waitForVBlank. Valor >= limiar (0xC0 = linha 192 NTSC) = o
    trabalho do frame derramou no VBlank — o tempo do streaming de VRAM.
  - probe_vovf (0xC7EB, word): contador não saturante de frames com vline >=
    limiar. Delta de leituras = evidência dura, imune a amostragem e ao antigo
    falso teto em 255.
  - probe_phase (0xC7ED): última fase observada (1 simulação, 2 preparação,
    3 antes do VBlank, 4 após upload/render); probe_missed (0xC7EE) conta os
    frames que alcançaram o início do VBlank.
A janela medida é o MODO ATRAÇÃO da ROM (CPU x CPU: especiais, projéteis,
trocas de pose com stream de ~1 KB, HUD e banners) — o pior caso real do
golden slice. Derrame não derruba fps: espreme o streaming de VRAM, então
"fps 60" não absolve orçamento estourado.

Pré-requisito do projeto: probe SMRT com probe_vline/probe_vovf nos
endereços acima (molde: MSSF2T src/main.c) e modo atração que exercite o
pior caminho.

Uso:
  measure_worst_frame.py --project SMS_projects/MSSF2T \
      --rom SMS_projects/MSSF2T/out/rom/MSSF2T.sms [--seconds 45]

Exit:
  0  pass — nenhum frame derramou no VBlank (vovf não avançou)
  1  reprova — vovf avançou (derramou) ou leitura sem lastro
  2  ambiente ausente (java/emulador/DAP)
  3  uso (argumentos)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import capture_evidence as CE                                    # noqa: E402
import measure_runtime_probe as MRP                              # noqa: E402
from emulicious_dap import PORT                                  # noqa: E402

PROBE_VLINE = 0xC7EA
PROBE_VOVF = 0xC7EB
PROBE_PHASE = 0xC7ED
PROBE_MISSED = 0xC7EE
PROBE_STATE = 0xC7F6
VLIMIAR = 0xC0            # linha 192 NTSC: inicio do VBlank
GS = {0: "ROUND", 1: "FIGHT", 2: "KO", 3: "RESULT", 4: "TITLE"}


# ---------------------------------------------------------------- logica pura
def analyze(samples, vovf_inicio, vovf_fim, limiar=VLIMIAR):
    """Veredito do worst-frame a partir de amostras + delta do contador.

    - vovf_delta > 0: REPROVA — frames com trabalho dentro do VBlank,
      contados pela própria ROM (imune a amostragem).
    - vovf_delta == 0 e vline_max >= limiar: contradição por construção
      (vovf conta exatamente esses frames) — leitura sem lastro.
    - leitura None não conta como amostra; sem amostra nenhuma, sem
      veredito.
    """
    vline_max = None
    validos = [s for s in samples if s.get("vline") is not None]
    for s in validos:
        if vline_max is None or s["vline"] > vline_max:
            vline_max = s["vline"]
    if vovf_inicio is None or vovf_fim is None:
        return {"verdicto": "sem_lastro", "vline_max": vline_max,
                "vovf_delta": None, "amostras": len(validos)}
    if not validos:
        return {"verdicto": "sem_lastro", "vline_max": None,
                "vovf_delta": vovf_fim - vovf_inicio, "amostras": 0}
    delta = vovf_fim - vovf_inicio
    if delta > 0:
        return {"verdicto": "derramou", "vline_max": vline_max,
                "vovf_delta": delta, "amostras": len(validos)}
    if vline_max >= limiar:
        return {"verdicto": "sem_lastro", "vline_max": vline_max,
                "vovf_delta": delta, "amostras": len(validos)}
    return {"verdicto": "pass", "vline_max": vline_max,
            "vovf_delta": 0, "amostras": len(validos)}


# ---------------------------------------------------------------- ambiente
def measure(rom, project, seconds=45.0, out_name="worst_frame"):
    jar = CE.resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado (resolve_jar)")
        return 2, None
    if not shutil.which("java"):
        print("[FAIL_AMBIENTE] java ausente")
        return 2, None
    if not MRP._zombie_guard() or not MRP._port_free():
        return 2, None
    out_dir = os.path.join(project, "out", "evidence")
    os.makedirs(out_dir, exist_ok=True)
    logf = open(os.path.join(out_dir, out_name + "_emu.log"), "w")
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", str(PORT), os.path.abspath(rom)],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        dap = MRP._connect_live()
        if dap is None:
            print("[FAIL] canal DAP nao ficou vivo (porta %s)" % PORT)
            return 1, None
        try:
            return _session(dap, out_dir, out_name, seconds)
        finally:
            dap.close()
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        logf.close()


def _session(dap, out_dir, out_name, seconds):
    # Espera o titulo assentar e o modo atracao assumir a luta (ninguem
    # toca no controle: qualquer tecla mata g_attract na ROM).
    time.sleep(15.0)
    samples = []
    vovf_inicio = None
    fim = time.time() + seconds
    while time.time() < fim:
        dap.pause()
        vl = dap.read_byte(PROBE_VLINE)
        vf = dap.read_word(PROBE_VOVF)
        ph = dap.read_byte(PROBE_PHASE)
        ms = dap.read_byte(PROBE_MISSED)
        st = dap.read_byte(PROBE_STATE)
        dap.cont()
        if vf is not None and vovf_inicio is None:
            vovf_inicio = vf
        samples.append({"t": round(seconds - (fim - time.time()), 1),
                        "vline": vl, "vovf": vf, "phase": ph, "missed": ms,
                        "estado": GS.get(st, st)})
        time.sleep(1.0)
    dap.pause()
    vovf_fim = dap.read_word(PROBE_VOVF)
    dap.cont()
    res = analyze(samples, vovf_inicio, vovf_fim, VLIMIAR)
    res["janela_s"] = seconds
    res["vovf_inicio"] = vovf_inicio
    res["vovf_fim"] = vovf_fim
    res["estados_vistos"] = sorted({str(s["estado"]) for s in samples})
    res["amostras_brutas"] = samples
    with open(os.path.join(out_dir, out_name + ".json"), "w") as f:
        json.dump(res, f, indent=1)
    print("[worst-frame] veredito=%s vovf_delta=%s vline_max=%s "
          "amostras=%d estados=%s"
          % (res["verdicto"], res["vovf_delta"], res["vline_max"],
             res["amostras"], res["estados_vistos"]))
    return (0 if res["verdicto"] == "pass" else 1), res


# ---------------------------------------------------------------- self-check
def self_check():
    ok = []

    r = analyze([{"vline": 0x50}, {"vline": 0x3F}], 7, 7)
    ok.append(("pass sem derrame", r["verdicto"] == "pass"
               and r["vovf_delta"] == 0 and r["vline_max"] == 0x50))
    r = analyze([{"vline": 0x50}, {"vline": 0xC5}], 7, 9)
    ok.append(("derrame reprovado pelo contador", r["verdicto"] == "derramou"
               and r["vovf_delta"] == 2))
    r = analyze([{"vline": None}], None, None)
    ok.append(("leitura perdida = sem lastro", r["verdicto"] == "sem_lastro"))
    r = analyze([], 3, 3)
    ok.append(("zero amostras = sem lastro", r["verdicto"] == "sem_lastro"))
    # vline alto com contador parado é contradição — não pode passar
    r = analyze([{"vline": 0xC8}], 5, 5)
    ok.append(("vline alto sem contador = sem lastro",
               r["verdicto"] == "sem_lastro"))
    r = analyze([{"vline": 0xBF}], 255, 255)
    ok.append(("contador saturado em 0 derrames passa",
               r["verdicto"] == "pass"))
    for nome, bom in ok:
        print("  %-42s %s" % (nome, "ok" if bom else "FALHOU"))
    if not all(b for _, b in ok):
        print("[SELF-CHECK FAIL] worst-frame")
        return 1
    print("[SELF-CHECK OK] measure_worst_frame")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--rom")
    ap.add_argument("--seconds", type=float, default=45.0)
    ap.add_argument("--out", default="worst_frame")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return self_check()
    if not args.rom or not os.path.isfile(args.rom):
        print("[FAIL_AMBIENTE] ROM obrigatoria e inexistente: %s" % args.rom)
        return 3
    code, _ = measure(args.rom, args.project, args.seconds, args.out)
    return code


if __name__ == "__main__":
    sys.exit(main())
