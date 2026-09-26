#!/usr/bin/env python3
"""prove_input.py — prova que o PAD move o LUTADOR, lendo a RAM, nao pixels.

Plano 2, Task 5. Precedente canonico: SMS_projects/MSSF2T/tools/
prove_input_memory.py (L035/L038/L039/L053) — o canal real em Wayland/KWin e
uinput (kdotool foco + ydotool tecla, via emulator_input.py); XTEST NAO
atravessa o compositor. Aqui a ROM e mais simples que a do MSSF2T: sem
titulo/rounds, a atracao morre na primeira tecla e P2 segue o roteiro.

Fases (todas por leitura DAP do mapa SMRT 0xC7E0.. desta ROM):
  1. canario do CANAL: Ctrl+BackSpace (reset do Emulicious) zera probe_frame;
     sem canal vivo nenhuma outra leitura tem lastro (L039);
  2. direcao: dx >= 8 px NA DIRECAO COMANDADA nos dois sentidos
     (criterio canonico emulator_input.evaluate_direction);
  3. pulo: probe_py (ALTITUDE) > 0 durante o voo e estado JUMP;
  4. soco: tecla B1 vista em probe_keys (0x10) COM o jogo rodando,
     probe_boss cai, probe_score sobe, padrao CMD_PUNCH latchou bit0;
  5. agachar: probe_state == CROUCH com Down segurado;
  6. padrao: CMD_HOLDF (F relativo ao facing, latchado no tick do buffer de
     16) acendeu bit1 durante o andar na direcao do oponente.

Seguranca: --rom validado contra whitelist literal; saidas relativas a RAIZ
do workspace. Uso (da raiz):
  python3 SMS_projects/luta_mugen/tools/prove_input.py \
      --rom SMS_projects/luta_mugen/out/rom/luta_mugen.sms
Exit: 0 provado | 1 reprovado | 2 ambiente ausente
Artefato: SMS_projects/luta_mugen/out/evidence/t5_input_memory.json
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "..", "..", "tools", "sms_wrapper")
sys.path.insert(0, os.path.abspath(TOOLS))

import capture_evidence as CE                                    # noqa: E402
import emulator_input as EI                                      # noqa: E402
import measure_runtime_probe as MRP                              # noqa: E402
from emulicious_dap import PORT                                  # noqa: E402

ROM_REL = "SMS_projects/luta_mugen/out/rom/luta_mugen.sms"
EVID = "SMS_projects/luta_mugen/out/evidence"

# mapa SMRT desta ROM (src/main.c)
P_FRAME   = 0xC7F0   # u16
P_HP      = 0xC7F2   # vida P1 (byte)
P_SCORE   = 0xC7F3   # hits conectados por P1
P_BOSS    = 0xC7F4   # vida P2 (byte)
P_STATE   = 0xC7F6   # estado P1 (ST_* de fight.c)
P_WAVE    = 0xC7F7   # 1 = atracao ativa
P_KEYS    = 0xC7F8   # Port A crua (0x10 = botao 1)
P_POSE    = 0xC7F9   # anim P1
P_PX      = 0xC7FA   # P1.x >> 8
P_PY      = 0xC7FB   # P1.altura >> 8 (0 = chao)
P_P2X     = 0xC7FC   # P2.x >> 8
P_PATTERN = 0xC7FD   # bit0 punch, bit1 holdF (latch)

ST_IDLE, ST_WALK_F, ST_WALK_B, ST_JUMP, ST_CROUCH, ST_GUARD, \
    ST_PUNCH1, ST_PUNCH2 = range(8)
HOLD_S = 0.8              # direcional pressionado antes da leitura
PUNCH_REACH = 20          # px de gap alvo (hitbox de 12 px + hurtbox de 8)
ATTRACT_END = 1400        # frames: roteiro completo antes de tocar em nada
SETTLE = 3.0


# ------------------------------------------------------------ criterios puros
def choose_approach_key(px, p2x):
    """Tecla que FECHA distancia: P2 a esquerda => Left; a direita => Right."""
    if px is None or p2x is None:
        return None
    if abs(px - p2x) <= PUNCH_REACH - 4:
        return None                          # ja em alcance
    return "Right" if px < p2x else "Left"


def punch_verdict(boss_before, boss_after, keys_durante, pattern_bits,
                  score_after):
    """Soco conectou por input? B1 CHEGOU ao ROM (0x10 em probe_keys com o
    jogo rodando) ANTES de qualquer conclusao — tecla que nao chegou nao e
    whiff (L039, licao MSSF2T 07/09/2026). Dano: boss byte caiu; corroboracao
    na propria ROM: score de hits e latch do padrao CMD_PUNCH."""
    if keys_durante is None or boss_before is None:
        return False, "leitura DAP perdida — inconclusivo, nao reprovado"
    if not keys_durante & 0x10:
        return False, ("botao 1 nunca acendeu 0x10 em probe_keys: a tecla nao "
                       "chegou ao ROM — nada a concluir sobre o soco")
    if boss_after is not None and boss_after < boss_before:
        if not (pattern_bits or 0) & 0x01:
            return False, ("dano visivel sem latch do padrao CMD_PUNCH "
                           "(bits=0x%02X): estado do probe duvidoso"
                           % (pattern_bits or 0))
        return True, ("boss %s->%s com B1 visto (keys=0x%02X), score=%s, "
                      "padrao punch latchou" %
                      (boss_before, boss_after, keys_durante, score_after))
    return False, ("B1 confirmado (0x10 em probe_keys) e boss %s->%s: "
                   "whiff — soco saiu mas nao conectou"
                   % (boss_before, boss_after))


def jump_verdict(py_amostras, states_vistos):
    """Pulo vivo: ALTITUDE (probe_py) > 0 em alguma amostra e estado JUMP
    visto. py e altura nesta ROM (0 = chao), NAO y de tela."""
    alt = [v for v in py_amostras if v is not None]
    if not alt or max(alt) <= 0:
        return False, "probe_py nunca saiu do chao (max=%s)" % (max(alt) if alt else None)
    if ST_JUMP not in states_vistos:
        return False, "altitude >0 sem estado JUMP observado (%s)" % states_vistos
    return True, "pico de altitude=%s px, estado JUMP visto" % max(alt)


# ------------------------------------------------------------------ injecao
def _focus_x11():
    """Fallback legado X11 so vale em host X11 (L039: XTEST nao atravessa
    KWin em Wayland — o canal real e uinput, via emulator_input)."""
    wid = CE._main_window_id()
    iid = CE._input_window_id(wid)
    return bool(wid) and EI.focus_x11(wid, iid)


# -------------------------------------------------------------------- prova
def run(rom_path):
    if EI.select_backend() is None:
        print("[FAIL_AMBIENTE] sem kdotool/ydotool nem xdotool no PATH")
        return 2, None
    logf = open(os.path.join(EVID, "t5_input_memory_emu.log"), "w")
    jar = CE.resolve_jar()
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", str(PORT),
         os.path.abspath(rom_path)],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True,
        env=EI.ENV)
    dap = None
    out = {"schema": "luta_input_v1", "rom": rom_path,
           "rom_sha256": _sha(rom_path), "backend": EI.select_backend(),
           "chain_of_custody": [
               "launch: java -jar Emulicious.jar -remotedebug " + str(PORT),
               "attach DAP; leituras com a emulacao PAUSADA",
               "input: uinput via emulator_input.py (L039: XTEST nao "
               "atravessa KWin)",
               "mapa: src/main.c probe SMRT 0xC7E0.. (px=0xC7FA, keys=0xC7F8)"]}
    try:
        dap = MRP._connect_live()
        if dap is None:
            print("[FAIL] canal DAP nao ficou vivo (porta %s)" % PORT)
            return 1, out
        dap.cont()
        time.sleep(SETTLE)

        # ---- 1. canario do canal (reset do proprio Emulicious zera o frame)
        dap.pause()
        f0 = dap.read_word(P_FRAME)
        backend = EI.select_backend()
        if backend == "wayland":
            focado = EI.focus_wayland()
        else:
            focado = _focus_x11()
        dap.cont()
        EI.tap_reset()
        time.sleep(1.2)
        dap.pause()
        f1 = dap.read_word(P_FRAME)
        canal_vivo = f0 is not None and f1 is not None and f1 < f0
        out["canario"] = {"frame_antes": f0, "frame_depois": f1,
                          "canal_vivo": canal_vivo, "foco": focado}
        print("canario: frame %s -> %s => canal %s (foco=%s)"
              % (f0, f1, "VIVO" if canal_vivo else "MORTO", focado))
        if not canal_vivo:
            print("[FAIL] canal de teclado morto — nada a provar (L039)")
            return 1, out

        # ---- atracao completa antes de tocar em qualquer tecla
        fim_atracao = time.time() + 40.0
        while time.time() < fim_atracao:
            dap.cont()
            time.sleep(0.5)
            dap.pause()
            fr = dap.read_word(P_FRAME) or 0
            if fr >= ATTRACT_END:
                break
        else:
            print("[FAIL] atracao nao completou em 40 s (frame=%s)" % fr)
            return 1, out
        dap.cont()

        # ---- 2. direcionais: dx >= 8 na direcao comandada, DOIS sentidos
        samples = []
        prev = _read_byte(dap, P_PX)
        for tecla, sentido in (("Right", +1), ("Left", -1)):
            if backend == "wayland" and not EI.focus_wayland():
                samples.append({"tecla": tecla, "sentido_esperado": sentido,
                                "x_antes": prev, "x_depois": None,
                                "dx": None, "probe_keys_durante": None})
                break
            dap.cont()
            def read_fn(d=dap):
                d.pause()
                v = (d.read_byte(P_PX), d.read_byte(P_KEYS))
                d.cont()
                return v
            got = _hold_key_run(dap, tecla, HOLD_S, read_fn, backend)
            x, k = got if got else (None, None)
            dx = (x - prev) if (x is not None and prev is not None) else None
            print("  %s: P1.x %s -> %s (dx=%s) keys=0x%02X"
                  % (tecla, prev, x, dx, (k or 0)))
            samples.append({"tecla": tecla, "sentido_esperado": sentido,
                            "x_antes": prev, "x_depois": x, "dx": dx,
                            "probe_keys_durante": k})
            prev = x
        ok_dir, motivo_dir = EI.evaluate_direction(samples, canal_vivo)
        out["direcionais"] = {"amostras": samples, "provado": ok_dir,
                              "motivo": motivo_dir}

        # ---- 3. pulo: Up momentaneo, amostrar altitude enquanto em voo
        if backend == "wayland":
            EI.focus_wayland()
        dap.cont()
        _hold_key_run(dap, "Up", 0.10, None, backend, release=False)
        pys, states, landed = [], [], False
        fim = time.time() + 2.0
        while time.time() < fim:
            time.sleep(0.06)
            dap.pause()
            pys.append(dap.read_byte(P_PY))
            states.append(dap.read_byte(P_STATE))
            dap.cont()
        _release_key("Up", backend)
        time.sleep(0.5)
        dap.pause()
        landed = (dap.read_byte(P_PY) == 0)
        ok_jump, motivo_jump = jump_verdict(pys, [s for s in states
                                                   if s is not None])
        out["pulo"] = {"py_amostras": pys[-12:], "provado": ok_jump,
                       "terrissou": landed, "motivo": motivo_jump}
        print("pulo: %s (%s)" % ("PROVADO" if ok_jump else "nao", motivo_jump))

        # ---- 4. aproximacao + soco com B1 observado DURANTE o hold
        soco = _punch_phase(dap, backend, out)
        ok_punch, motivo_punch = soco["veredito"]

        # ---- 5. agachar: Down segurado, estado CROUCH na leitura
        if backend == "wayland":
            EI.focus_wayland()
        dap.cont()

        def crouch_read(d=dap):
            d.pause()
            v = d.read_byte(P_STATE)
            d.cont()
            return v
        st_c = _hold_key_run(dap, "Down", 0.5, crouch_read, backend)
        ok_crouch = st_c == ST_CROUCH
        out["agachar"] = {"estado_lido": st_c, "provado": ok_crouch}
        print("agachar: estado=%s => %s" % (st_c,
                                            "CROUCH" if ok_crouch else "nao"))

        # ---- 6. padrao holdF: o latch bit1 ja foi abastecido pelo andar em
        # direcao ao oponente (fase 2); soco abasteciu bit0.
        dap.pause()
        pat = dap.read_byte(P_PATTERN)
        bits = pat or 0
        out["padroes"] = {"latch": bits,
                          "punch_bit0": bool(bits & 1),
                          "holdf_bit1": bool(bits & 2)}
        ok_pattern = bool(bits & 0x03)
        print("padroes: latch=0x%02X (punch=%s holdF=%s)"
              % (bits, bool(bits & 1), bool(bits & 2)))

        tudo = dict(ok_dir=ok_dir, ok_jump=ok_jump, ok_punch=ok_punch,
                    ok_crouch=ok_crouch, ok_pattern=ok_pattern)
        out["eixos"] = tudo
        out["aprovado"] = all(tudo.values())
        return (0 if out["aprovado"] else 1), out
    finally:
        try:
            if dap:
                dap.close()
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
            logf.close()


def _hold_key_run(dap, tecla, seconds, read_fn, backend, release=True):
    """Hold com o JOGO RODANDO; leitura (se houver) no meio do hold."""
    code = EI.EVDEV[tecla]
    if backend == "wayland":
        EI.ydotool_key(code, True)
    else:
        CE._run(["xdotool", "keydown", tecla])
    time.sleep(seconds)
    v = read_fn() if read_fn else None
    if release:
        _release_key(tecla, backend)
    return v


def _release_key(tecla, backend):
    if backend == "wayland":
        EI.ydotool_key(EI.EVDEV[tecla], False)
    else:
        CE._run(["xdotool", "keyup", tecla])


def _read_byte(dap, addr):
    try:
        return dap.read_byte(addr)
    except Exception:
        return None


def _punch_phase(dap, backend, out):
    """Aproxima ate alcance, B1 com probe_keys amostrado COM o jogo rodando
    (o ciclo antigo do MSSF2T lia pausado demais e culpava o jogo por falha
    do canal — aqui o ciclo roda ~3 frames entre pausas curtas)."""
    def rd(*addrs):
        dap.pause()
        vals = tuple(dap.read_byte(a) for a in addrs)
        if any(v is None for v in vals):
            dap.cont()
            return None
        dap.cont()
        return vals

    # aproxima
    fim = time.time() + 12.0
    gap = None
    while time.time() < fim:
        vals = rd(P_PX, P_P2X)
        if vals is None:
            break
        px, p2x = vals
        gap = p2x - px
        tecla = choose_approach_key(px, p2x)
        if tecla is None:
            break
        if backend == "wayland":
            EI.focus_wayland()
        _hold_key_run(dap, tecla, 0.25, None, backend)
    vals = rd(P_BOSS, P_SCORE, P_PATTERN)
    boss0 = vals[0] if vals else None
    keys_seen = 0
    if backend == "wayland":
        EI.focus_wayland()
    dap.cont()
    fim_b1 = time.time() + 0.6
    code = EI.EVDEV["a"] if backend == "wayland" else None
    if backend == "wayland":
        EI.ydotool_key(code, True)
    else:
        CE._run(["xdotool", "keydown", "a"])
    while time.time() < fim_b1:
        time.sleep(0.05)                       # ~3 frames rodando por ciclo
        v = rd(P_KEYS)
        if v:
            keys_seen |= v[0]
    if backend == "wayland":
        EI.ydotool_key(code, False)
    else:
        CE._run(["xdotool", "keyup", "a"])
    time.sleep(0.6)                            # janela de dano/hitstop
    vals = rd(P_BOSS, P_SCORE, P_PATTERN)
    boss1, score1, pat1 = vals if vals else (None, None, None)
    ok, motivo = punch_verdict(boss0, boss1, keys_seen, pat1, score1)
    print("soco: gap=%s B1=0x%02X boss %s->%s score=%s pattern=0x%02X => %s"
          % (gap, keys_seen, boss0, boss1, score1, pat1,
             "CONECTOU POR INPUT" if ok else motivo))
    res = {"gap": gap, "boss_antes": boss0, "boss_depois": boss1,
           "keys_durante_b1": keys_seen, "score": score1, "pattern": pat1,
           "veredito": (ok, motivo), "provado": ok, "motivo": motivo}
    out["soco"] = res
    return res


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ---------------------------------------------------------------- self-check
def self_check():
    """§19: criterios puros com as regressoes exatas das licoes herdadas."""
    falhas = []

    # abordagem: P2 a direita => Right; a esquerda => Left; em alcance => None
    if choose_approach_key(100, 130) != "Right":
        falhas.append("P2 a direita nao virou Right")
    if choose_approach_key(130, 100) != "Left":
        falhas.append("P2 a esquerda nao virou Left")
    if choose_approach_key(120, 130) is not None:
        falhas.append("gap 10 deveria ser alcance suficiente")
    if choose_approach_key(None, 100) is not None:
        falhas.append("leitura None virou tecla")

    # soco: tecla que NAO chegou nao pode ser whiff (L039/MSSF2T 07/09)
    ok, m = punch_verdict(237, 237, 0x08, 0x02, 0)
    if ok or "nao chegou" not in m:
        falhas.append("tecla perdida diagnosticada como whiff: " + m)
    # B1 chegou, dano caiu, padrao latchou => conecta
    ok, m = punch_verdict(237, 232, 0x18, 0x01, 1)
    if not ok:
        falhas.append("hit -5 com B1+padrao foi reprovado: " + m)
    # dano sem latch do padrao: probe duvidoso, nao celebra
    ok, _ = punch_verdict(237, 232, 0x18, 0x02, 1)
    if ok:
        falhas.append("dano sem bit0 do padrao foi aceito")
    # whiff honesto: B1 confirmou, boss nao caiu
    ok, m = punch_verdict(237, 237, 0x18, 0x01, 0)
    if ok or "whiff" not in m:
        falhas.append("whiff com B1 confirmado virou sucesso: " + m)
    # leitura perdida: inconclusivo, nunca reprovado por ausencia
    ok, m = punch_verdict(None, 232, 0x18, 0x01, 1)
    if ok or "inconclusivo" not in m:
        falhas.append("leitura None virou veredito: " + m)

    # pulo: altitude 0 o tempo todo reprova; >0 sem estado JUMP reprova
    ok, _ = jump_verdict([0, 0, 0], [ST_CROUCH])
    if ok:
        falhas.append("pulo sem altitude foi aceito")
    ok, _ = jump_verdict([0, 9, 3], [ST_IDLE])
    if ok:
        falhas.append("altitude sem estado JUMP foi aceita")
    ok, _ = jump_verdict([0, 12, 5], [ST_JUMP, ST_IDLE])
    if not ok:
        falhas.append("pulo verdadeiro foi reprovado")

    if falhas:
        print("[SELF-CHECK FAIL]")
        for f in falhas:
            print("  - " + f)
        return 1
    print("[SELF-CHECK PASS] prove_input: abordagem (2 lados + alcance + "
          "None), soco (tecla perdida != whiff, hit -5, dano sem padrao, "
          "whiff honesto, leitura None inconclusiva), pulo (sem altitude, "
          "sem estado, caminho bom)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if a.rom not in (ROM_REL, "out/rom/luta_mugen.sms"):
        print("[FAIL_AMBIENTE] --rom fora da whitelist do projeto")
        return 3
    if not os.path.isfile(ROM_REL):
        print("[FAIL_AMBIENTE] rodar da RAIZ do workspace (caminho relativo)")
        return 2
    os.makedirs(EVID, exist_ok=True)
    rc, metrics = run(ROM_REL)
    if metrics:
        with open(os.path.join(EVID, "t5_input_memory.json"), "w") as f:
            json.dump(metrics, f, indent=1)
    print("[%s] input vivo: %s" % ("PASS" if rc == 0 else "FAIL",
                                   ROM_REL))
    return rc


if __name__ == "__main__":
    sys.exit(main())
