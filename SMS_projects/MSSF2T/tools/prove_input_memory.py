#!/usr/bin/env python3
"""Prova que o INPUT move o JOGADOR — lendo a RAM, nao os pixels.

Por que existe: o detector de gameplay do capture_evidence procura o maior
blob saturado com "forma de sprite" e mede o deslocamento dele. Neste jogo
isso e ambiguo por construcao:

  - Ken e Guile geram blobs do MESMO tamanho (309 px, 22x42): o detector nao
    distingue um do outro;
  - de pe no deck, o laranja do gi do Ken encosta no tom quente das tabuas e
    os dois viram um unico componente de 36 mil pixels, reprovado pelo filtro
    de forma — nesses frames o jogador simplesmente some do detector;
  - interaction_verdict() so testa abs(dx) >= 8: NAO confere direcao nem
    identidade. Uma corrida do Guile (CPU) fecha o eixo mesmo com o comando
    apontando para o outro lado.

Foi exatamente o que aconteceu: com "Right" o objeto rastreado andou 32 px
para a ESQUERDA e o gate deu PASS. Isso prova movimento na tela, nao que o
controle do jogador funciona.

Aqui a pergunta e respondida onde ela tem resposta unica (licao L035, a mesma
do measure_runtime_probe): P[0].x mora em probe_px (0xC7FA). Pressiona-se uma
direcao pelo teclado e le-se a variavel do jogador 1 antes e depois.

Uso: prove_input_memory.py --rom <rom.sms> [--project D] [-o saida.json]
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

PROBE_PX = 0xC7FA
PROBE_KEYS = 0xC7F8
PROBE_FRAME = 0xC7F0
PROBE_HP = 0xC7F2
PROBE_BOSS = 0xC7F4
PROBE_STATE = 0xC7F6
PROBE_WAVE = 0xC7F7
GS = {0: "ROUND", 1: "FIGHT", 2: "KO", 3: "RESULT"}
SETTLE = 3.0          # deixa passar o banner de ROUND antes de comandar
HOLD_MS = 600


def run(rom, project, out_name):
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
        # Mesma sequencia do measure_runtime_probe: conectar antes do boot
        # deixa a sessao stale (L035), entao ele espera e valida o canario.
        dap = MRP._connect_live()
        if dap is None:
            print("[FAIL] canal DAP nao ficou vivo")
            return 1, None

        wid = CE._main_window_id()
        if not wid:
            print("[FAIL_AMBIENTE] janela do emulador nao encontrada")
            return 2, None

        dap.cont()
        time.sleep(SETTLE)
        dap.pause()
        x0 = dap.read_byte(PROBE_PX)
        f0 = dap.read_word(PROBE_FRAME)

        iid = CE._input_window_id(wid)
        # Teste do CANAL, separado do teste do MAPEAMENTO: ctrl+BACK_SPACE e
        # o atalho de reset do proprio Emulicious (KeyPresets/bgb.ini). Se o
        # frame zerar, a tecla CHEGA no emulador e o problema seria so o
        # mapeamento do direcional. Se nao zerar, o canal esta morto.
        CE._run(["xdotool", "windowactivate", "--sync", str(wid)])
        time.sleep(0.3)
        foco = CE._run(["xdotool", "getwindowfocus", "getwindowname"])
        print(f"       foco antes do input: {(foco.stdout or '').strip()!r}")
        dap.cont()
        fa = None
        CE._run(["xdotool", "key", "ctrl+BackSpace"])
        time.sleep(1.0)
        dap.pause()
        fb = dap.read_word(PROBE_FRAME)
        canal_vivo = fb is not None and f0 is not None and fb < f0
        print(f"       reset ctrl+BackSpace: frame {f0} -> {fb} "
              f"=> canal {'VIVO' if canal_vivo else 'MORTO'}")

        samples = []
        for key, expect in (("Right", +1), ("Left", -1)):
            # Foco antes de tudo (L007): sem isso a tecla vai para outra janela.
            for _ in range(5):
                CE._run(["xdotool", "windowactivate", "--sync", str(wid)])
                CE._run(["xdotool", "windowraise", str(wid)])
                CE._run(["xdotool", "windowfocus", "--sync", str(iid)])
                time.sleep(0.3)
                f = CE._run(["xdotool", "getwindowfocus"])
                if f and f.stdout.strip() in (str(wid), str(iid)):
                    break
            dap.cont()
            prev = samples[-1]["x_depois"] if samples else x0
            # XTEST (sem --window), nao XSendEvent. `xdotool --window` manda
            # evento SINTETICO, e o AWT/Swing do Emulicious (Java) descarta
            # eventos com send_event=True: a tecla nunca chegava a ROM.
            CE._run(["xdotool", "keydown", key])
            time.sleep(HOLD_MS / 1000.0)
            # Pausa COM A TECLA AINDA PRESSIONADA: probe_keys so vale enquanto
            # o botao esta em baixo. Lendo depois do keyup daria sempre 0 e
            # nao distinguiria "input nao chegou" de "input chegou e acabou".
            dap.pause()
            x = dap.read_byte(PROBE_PX)
            k = dap.read_byte(PROBE_KEYS)
            st = dap.read_byte(PROBE_STATE)
            hp = dap.read_byte(PROBE_HP)
            bo = dap.read_byte(PROBE_BOSS)
            tm = dap.read_byte(PROBE_WAVE)
            print(f"         estado={GS.get(st, st)} hp={hp} guile_hp={bo} timer={tm}")
            dap.cont()
            CE._run(["xdotool", "keyup", key])
            dap.pause()
            samples.append({"tecla": key, "sentido_esperado": expect,
                            "x_antes": prev, "x_depois": x,
                            "dx": (x - prev) if (x is not None and prev is not None) else None,
                            "probe_keys_durante": k})
            print(f"       {key:5s}: P[0].x {prev} -> {x}  "
                  f"(dx={samples[-1]['dx']:+}) probe_keys(durante)=0x{(k or 0):02X}")

        f1 = dap.read_word(PROBE_FRAME)
        # Prova = deslocamento >= 8 px NA DIRECAO COMANDADA, nos dois sentidos.
        ok = all(s["dx"] is not None and s["dx"] * s["sentido_esperado"] >= 8
                 for s in samples)
        metrics = {
            "schema": "input_memory_v1",
            "rom": rom,
            "rom_sha256": hashlib.sha256(open(rom, "rb").read()).hexdigest(),
            "probe_px_addr": hex(PROBE_PX),
            "x_inicial": x0,
            "frames": {"antes": f0, "depois": f1},
            "amostras": samples,
            "input_provado": ok,
            "canal_teclado_vivo": canal_vivo,
            "criterio": "dx >= 8 px NA DIRECAO COMANDADA, nos dois sentidos",
            "por_que_memoria": ("pixels sao ambiguos aqui: Ken e Guile dao "
                                "blobs identicos de 309 px e o gi do Ken funde "
                                "com o deck; interaction_verdict nao confere "
                                "direcao nem identidade"),
            "chain_of_custody": [
                f"launch: java -jar {os.path.basename(jar)} -remotedebug {PORT}",
                "attach DAP; leitura com a emulacao PAUSADA",
                "input: xdotool keydown/keyup na janela do emulador (L007)",
                f"leitura: @{hex(PROBE_PX)} = P[0].x (main.c: probe_px)",
            ],
        }
        json.dump(metrics, open(os.path.join(out_dir, f"{out_name}.json"), "w"),
                  indent=1)
        print(f"[{'PASS' if ok else 'FAIL'}] input->jogador "
              f"{'provado' if ok else 'NAO provado'} na memoria")
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
    ap.add_argument("--out", default="input_memory")
    a = ap.parse_args()
    code, _ = run(a.rom, os.path.abspath(a.project), a.out)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
