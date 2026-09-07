#!/usr/bin/env python3
"""Prova que o INPUT move o JOGADOR — lendo a RAM, nao os pixels.

Por que existe: o detector de gameplay do capture_evidence procura o maior
blob saturado com "forma de sprite" e mede o deslocamento dele. Neste jogo
isso e ambiguo por construcao (L038): Ken e Guile geram blobs identicos de
309 px, o gi do Ken funde com as tabuas do deck, e interaction_verdict()
so testa abs(dx) >= 8 — com "Right" o objeto rastreado andou 32 px para a
ESQUERDA e o gate antigo deu PASS.

Aqui a pergunta e respondida onde ela tem resposta unica (L035): P[0].x mora
em probe_px (0xC7FA). Pressiona-se uma direcao pelo teclado e le-se a
variavel do jogador antes e depois, exigindo deslocamento NA DIRECAO
COMANDADA nos dois sentidos.

Canal de teclado (L039 -> resolvido): o host e KDE/Wayland. xdotool/XTEST
nao atravessa o KWin (getwindowfocus vazio, probe_keys 0x00). O canal real
e kdotool (foco via KWin/DBus) + ydotool (uinput, nivel kernel — o evento
nasce dentro do kernel e o KWin entrega a quem estiver focado). O caminho
legado xdotool so valeria em host X11.

Seguranca: --rom e validado contra whitelist literal da raiz do projeto;
qualquer outra coisa reprova com exit 2 sem tocar em arquivo.
Rodar a partir da raiz do workspace (os caminhos de saida sao relativos).

Uso: prove_input_memory.py --rom SMS_projects/MSSF2T/out/rom/MSSF2T.sms
     prove_input_memory.py --self-check
Exit: 0 provado | 1 reprovado | 2 ambiente ausente
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, "/mnt/sdcard/Projects/SMSForge/tools/sms_wrapper")

import capture_evidence as CE                                    # noqa: E402
import emulator_input as EI                                      # noqa: E402
import measure_runtime_probe as MRP                              # noqa: E402
from emulicious_dap import PORT                                  # noqa: E402

PROBE_PX = 0xC7FA
PROBE_KEYS = 0xC7F8
PROBE_FRAME = 0xC7F0
PROBE_HP = 0xC7F2
PROBE_BOSS = 0xC7F4
PROBE_STATE = 0xC7F6
PROBE_P2X = 0xC7FC
PROBE_PY = 0xC7FB
PROBE_POSE = 0xC7F9
GS = {0: "ROUND", 1: "FIGHT", 2: "KO", 3: "RESULT", 4: "TITLE"}
GS_FIGHT = 1
GROUND_Y = 112            # chao da luta (airborne = py < GROUND_Y)
FACE_BIT = 0x80           # probe_pose bit 7 = facing (0xC7F9)

ROM_REL = "SMS_projects/MSSF2T/out/rom/MSSF2T.sms"
YDOTOOL_SOCKET = "/tmp/.ydotool_socket_smsforge"
ENV = dict(os.environ, YDOTOOL_SOCKET=YDOTOOL_SOCKET)

SETTLE = 3.0             # boot + titulo estavel
HOLD_S = 0.8             # direcional pressionado durante a leitura
FIGHT_TIMEOUT = 15.0     # ROUND(120f) + FIGHT(40f) de banner
PUNCH_REACH = 24         # caixa do soco conecta com gap < 24 (fight.c collide)
PUSH_W = 20              # corpos param a 20 px (separate) — dentro do alcance


# ---------------------------------------------------------------- logica pura
def evaluate(samples, canal_vivo):
    """Criterio canonico: emulator_input.evaluate_direction (L038/L039)."""
    return EI.evaluate_direction(samples, canal_vivo)


def evaluate_swap(before, flight, after):
    """Criterio canonico: emulator_input.evaluate_swap (L053)."""
    return EI.evaluate_swap(before, flight, after, ground_y=GROUND_Y)


def evaluate_punch(before, punch, after):
    """Soco conecta por input: B1 com canal vivo, Ken a alcance
    (gap < PUNCH_REACH, lido antes do golpe) e guile_hp caiu. Hit (-7),
    chip de guarda (-2) e KO (0) sao conexoes; 64->64 e whiff — a
    regressao exata da amostra selada."""
    if not punch.get("canal_vivo"):
        return False, "canal de teclado morto: nenhuma leitura tem lastro"
    b0 = before.get("guile_hp")
    if b0 is None:
        return False, "leitura do guile_hp inicial falhou"
    if not punch.get("gap_no_limite"):
        return False, ("Ken nao ficou a alcance do soco "
                       "(gap=%s, alcance<%d)" % (punch.get("gap"),
                                                 PUNCH_REACH))
    # Tecla que nao chegou nao e whiff. A versao antiga nao sabia distinguir
    # os dois casos e culpava o jogo por falha do canal de input: lia
    # probe_keys com o emulador pausado, nunca via o bit 0x10 do botao 1, e
    # ainda assim afirmava "B1 dado a alcance". Sem b1_chegou registrado
    # (amostra antiga), nao se pode afirmar nem uma coisa nem outra.
    # Conexao observada DENTRO de uma tentativa vence qualquer leitura global:
    # o guile_hp de antes/depois atravessa reset de round e mente.
    if punch.get("conectou"):
        return True, ("guile_hp caiu %s na tentativa a gap=%s (medido dentro "
                      "da tentativa, imune a reset de round)"
                      % (punch.get("delta"), punch.get("gap_do_hit")))
    if punch.get("b1_chegou") is False:
        return False, ("botao 1 nunca acendeu 0x10 em probe_keys: a tecla nao "
                       "chegou ao ROM — nada a concluir sobre o soco")
    b1 = after.get("guile_hp")
    if b1 is None:
        return False, "leitura do guile_hp depois do soco falhou"
    if b1 >= b0:
        if punch.get("b1_chegou") is None:
            return False, ("guile_hp %s->%s sem registro de b1_chegou: amostra "
                           "antiga, nao distingue whiff de tecla perdida"
                           % (b0, b1))
        return False, ("B1 confirmado (0x10 em probe_keys) a gap=%s e guile_hp "
                       "%s->%s: whiff de verdade" % (punch.get("gap"), b0, b1))
    return True, "guile_hp caiu %s->%s apos B1 a alcance (delta %d)" % (
        b0, b1, b0 - b1)


# --------------------------------------------------------------- injecao
def ensure_daemon():
    if not os.path.exists(YDOTOOL_SOCKET):
        subprocess.Popen(["ydotoold", "-p", YDOTOOL_SOCKET, "-P", "0660"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        time.sleep(1.0)


def ensure_focus_wayland():
    kid = None
    for _ in range(20):
        r = subprocess.run(["kdotool", "search", "--name", "Emulicious"],
                           capture_output=True, text=True, env=ENV,
                           timeout=20)
        ids = (r.stdout or "").split()
        if ids:
            kid = ids[0]
            break
        time.sleep(0.5)
    if kid is None:
        return False, None
    subprocess.run(["kdotool", "windowactivate", kid],
                   capture_output=True, text=True, env=ENV, timeout=20)
    time.sleep(0.3)
    r_act = subprocess.run(["kdotool", "getactivewindow"],
                           capture_output=True, text=True, env=ENV,
                           timeout=20)
    a = (r_act.stdout or "").strip()
    return a == kid, kid


def press_wayland(acao):
    if acao == "right":
        subprocess.run(["ydotool", "key", "106:1"], capture_output=True,
                       text=True, env=ENV, timeout=20)
    elif acao == "left":
        subprocess.run(["ydotool", "key", "105:1"], capture_output=True,
                       text=True, env=ENV, timeout=20)
    elif acao == "up":
        subprocess.run(["ydotool", "key", "103:1"], capture_output=True,
                       text=True, env=ENV, timeout=20)
    elif acao == "botao1":
        subprocess.run(["ydotool", "key", "30:1"], capture_output=True,
                       text=True, env=ENV, timeout=20)


def release_wayland(acao):
    if acao == "right":
        subprocess.run(["ydotool", "key", "106:0"], capture_output=True,
                       text=True, env=ENV, timeout=20)
    elif acao == "left":
        subprocess.run(["ydotool", "key", "105:0"], capture_output=True,
                       text=True, env=ENV, timeout=20)
    elif acao == "up":
        subprocess.run(["ydotool", "key", "103:0"], capture_output=True,
                       text=True, env=ENV, timeout=20)
    elif acao == "botao1":
        subprocess.run(["ydotool", "key", "30:0"], capture_output=True,
                       text=True, env=ENV, timeout=20)


def hold_wayland(acao, seconds):
    press_wayland(acao)
    time.sleep(seconds)
    release_wayland(acao)


def tap_reset_wayland():
    subprocess.run(["ydotool", "key", "29:1", "14:1", "14:0", "29:0"],
                   capture_output=True, text=True, env=ENV, timeout=20)


def ensure_focus_x11(wid, iid):
    for _ in range(5):
        CE._run(["xdotool", "windowactivate", "--sync", str(wid)])
        CE._run(["xdotool", "windowraise", str(wid)])
        CE._run(["xdotool", "windowfocus", "--sync", str(iid)])
        time.sleep(0.3)
        f = CE._run(["xdotool", "getwindowfocus"])
        if f and f.stdout.strip() in (str(wid), str(iid)):
            return True
    return False


def hold_x11(acao, seconds):
    nomes = {"right": "Right", "left": "Left", "up": "Up", "botao1": "a"}
    nome = nomes.get(acao)
    if nome is None:
        return
    CE._run(["xdotool", "keydown", nome])
    time.sleep(seconds)
    CE._run(["xdotool", "keyup", nome])


def tap_reset_x11():
    CE._run(["xdotool", "key", "ctrl+BackSpace"])


def select_backend():
    """wayland = kdotool+ydotool; sem eles, cai para o legado xdotool (L039
    provou que XTEST nao atravessa KWin — o fallback so vale em host X11)."""
    if shutil.which("kdotool") and shutil.which("ydotool"):
        ensure_daemon()
        return "wayland"
    if shutil.which("xdotool"):
        return "x11"
    return None


# ---------------------------------------------------------------------- prova
def run():
    if not os.path.isfile("SMS_projects/MSSF2T/out/rom/MSSF2T.sms"):
        print("[FAIL_AMBIENTE] rodar a partir da raiz do workspace "
              "(caminhos de saida sao relativos a raiz)")
        return 2, None
    backend = select_backend()
    if backend is None:
        print("[FAIL_AMBIENTE] sem kdotool/ydotool nem xdotool no PATH")
        return 2, None
    logf = open("SMS_projects/MSSF2T/out/evidence/input_memory_emu.log", "w")
    proc = subprocess.Popen(
        ["java", "-jar",
         "/mnt/sdcard/Projects/SMSForge/tools/emuladores/emulicious/Emulicious.jar",
         "-remotedebug", str(PORT),
         "/mnt/sdcard/Projects/SMSForge/SMS_projects/MSSF2T/out/rom/MSSF2T.sms"],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True, env=ENV)
    dap = None
    try:
        dap = MRP._connect_live()
        if dap is None:
            print("[FAIL] canal DAP nao ficou vivo")
            return 1, None
        dap.cont()
        time.sleep(SETTLE)
        dap.pause()
        f0 = dap.read_word(PROBE_FRAME)
        st0 = dap.read_byte(PROBE_STATE)
        print("boot: frame=%s estado=%s" % (f0, GS.get(st0, st0)))

        # ---- canario do CANAL: o reset do proprio Emulicious zera o frame.
        # Se o frame nao zerar, nenhuma outra leitura tem lastro (L039).
        focado = False
        if backend == "wayland":
            focado, _kid = ensure_focus_wayland()
            dap.cont()
            tap_reset_wayland()
        else:
            wid = CE._main_window_id()
            iid = CE._input_window_id(wid)
            if wid:
                focado = ensure_focus_x11(wid, iid)
            dap.cont()
            tap_reset_x11()
        time.sleep(1.2)
        dap.pause()
        f1 = dap.read_word(PROBE_FRAME)
        canal_vivo = f1 is not None and f0 is not None and f1 < f0
        print("reset ctrl+BackSpace: frame %s -> %s => canal %s (foco=%s)"
              % (f0, f1, "VIVO" if canal_vivo else "MORTO", focado))
        if not canal_vivo:
            metrics = _metrics(backend, canal_vivo, focado, [], False, None,
                               f0, f1)
            _dump(metrics)
            print("[FAIL] canal de teclado morto — nada a provar (L039)")
            return 1, metrics

        # ---- partida REAL: B1 no titulo (a atracao morre para sempre no
        # primeiro toque — o controle passa a ser do jogador)
        if backend == "wayland":
            ensure_focus_wayland()
            hold_wayland("botao1", 0.25)
        else:
            wid = CE._main_window_id()
            iid = CE._input_window_id(wid)
            ensure_focus_x11(wid, iid)
            hold_x11("botao1", 0.25)
        fim = time.time() + FIGHT_TIMEOUT
        estado = None
        while time.time() < fim:
            time.sleep(0.5)
            dap.pause()
            estado = dap.read_byte(PROBE_STATE)
            if estado == GS_FIGHT:
                break
            dap.cont()
        print("partida real: estado=%s" % GS.get(estado, estado))
        if estado != GS_FIGHT:
            metrics = _metrics(backend, canal_vivo, focado, [], False,
                               estado, f0, f1)
            _dump(metrics)
            print("[FAIL] B1 nao tirou a ROM do titulo")
            return 1, metrics

        # ---- deslocamento: ler COM A TECLA AINDA EM BAIXO (probe_keys so
        # vale enquanto o botao esta pressionado; ler depois do keyup
        # esconderia se a ROM registrou ou nao o comando)
        samples = []
        prev = dap.read_byte(PROBE_PX)
        for acao, tecla, expect in (("right", "Right", +1),
                                    ("left", "Left", -1)):
            if backend == "wayland":
                ensure_focus_wayland()
            else:
                wid = CE._main_window_id()
                iid = CE._input_window_id(wid)
                ensure_focus_x11(wid, iid)
            dap.cont()
            if backend == "wayland":
                press_wayland(acao)
            else:
                CE._run(["xdotool", "keydown", tecla])
            time.sleep(HOLD_S)
            dap.pause()
            x = dap.read_byte(PROBE_PX)
            k = dap.read_byte(PROBE_KEYS)
            st = dap.read_byte(PROBE_STATE)
            hp = dap.read_byte(PROBE_HP)
            bo = dap.read_byte(PROBE_BOSS)
            if backend == "wayland":
                release_wayland(acao)
            else:
                CE._run(["xdotool", "keyup", tecla])
            dx = (x - prev) if (x is not None and prev is not None) else None
            print("  %s: estado=%s hp=%s guile=%s keys_durante=0x%02X "
                  "P[0].x %s -> %s (dx=%s)"
                  % (tecla, GS.get(st, st), hp, bo, k or 0, prev, x, dx))
            dap.cont()
            samples.append({"tecla": tecla, "sentido_esperado": expect,
                            "x_antes": prev, "x_depois": x, "dx": dx,
                            "probe_keys_durante": k})
            prev = x

        # ---- soco conectando por input (handoff item 1): aproxima a
        # alcance (gap < 24) e le guile_hp cair. Nao fecha o eixo sozinho.
        soco = _punch_phase(dap, backend, canal_vivo)

        # ---- troca de lado (L053): pulo por cima e facing virando. Fase
        # separada do criterio do eixo; entra no mesmo artefato.
        sideswap = _sideswap_phase(dap, backend)

        ok, motivo = evaluate(samples, canal_vivo)
        metrics = _metrics(backend, canal_vivo, focado, samples, True,
                           estado, f0, f1)
        metrics["motivo"] = motivo
        metrics["input_provado"] = ok
        metrics["soco"] = soco
        metrics["sideswap"] = sideswap
        _dump(metrics)
        print("[%s] input->jogador %s (%s)"
              % ("PASS" if ok else "FAIL",
                 "provado" if ok else "NAO provado", motivo))
        print("[%s] soco conectando por input %s (%s)"
              % ("PASS" if soco.get("soco_provado") else "FAIL",
                 "provado" if soco.get("soco_provado") else "NAO provado",
                 soco.get("motivo")))
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


def _punch_phase(dap, backend, canal_vivo):
    """Handoff item 1: o soco CONECTANDO por input — guile_hp cai.

    Causa do whiff selado (64->64): o approach antigo parava em gap<=26 e a
    caixa do soco so alcancaca gap<24 (fight.c collide: ax=x+20..+32 contra
    bx=x+8..+24). Os corpos param a PUSH_W=20 (separate), dentro do alcance.
    CPU a dist<44 soca a cada 64 frames e guarda metade das janelas de
    ataque: hit -7, chip de guarda -2 — qualquer queda de guile_hp e
    conexao. Retry x3 com recuo, como na fase de pulo (L053).
    """
    try:
        time.sleep(0.3)
        dap.pause()
        before = {"guile_hp": dap.read_byte(PROBE_BOSS),
                  "ken_hp": dap.read_byte(PROBE_HP)}
        punch = {"canal_vivo": canal_vivo, "gap": None,
                 "gap_no_limite": False, "tentativas": []}
        if before["guile_hp"] is None:
            return {"antes": before, "punch": punch, "after": {},
                    "soco_provado": False, "motivo": "leitura falhou"}

        for n in range(3):
            # recuo: sai de hitstun/guarda e reposiciona antes do golpe
            if backend == "wayland":
                ensure_focus_wayland()
                hold_wayland("left", 0.35)
            else:
                hold_x11("left", 0.35)
            dap.cont()
            time.sleep(0.4)

            # Aproximacao ate encostar. A janela util e ESTREITA: separate()
            # para os corpos em PUSH_W=20 e a caixa do soco exige gap < 24, ou
            # seja 4 px de folga. Andar em passos curtos com o emulador pausado
            # entre eles nao chegava la — media dos runs de 07/09/2026: o laco
            # esgotava os 6 s parado em gap 42 e 24, e o `continue` da leitura
            # perdida ainda saia sem dar cont(), deixando o emulador congelado
            # pelo resto da tentativa. Passada longa com o jogo RODANDO fecha a
            # distancia de uma vez (Ken anda 2 px/frame; 1.2 s ~ 144 px).
            fim = time.time() + 12.0
            gap = None
            while time.time() < fim:
                dap.cont()
                if backend == "wayland":
                    ensure_focus_wayland()
                    hold_wayland("right", 1.2)
                else:
                    hold_x11("right", 1.2)
                dap.pause()
                px = dap.read_byte(PROBE_PX)
                p2x = dap.read_byte(PROBE_P2X)
                if None in (px, p2x):
                    continue
                gap = p2x - px
                if gap <= PUNCH_REACH - 2:
                    break
            dap.pause()
            gap = (dap.read_byte(PROBE_P2X)
                   - dap.read_byte(PROBE_PX)) if True else None
            b0 = dap.read_byte(PROBE_BOSS)
            punch["gap"] = gap
            punch["gap_no_limite"] = gap is not None and gap < PUNCH_REACH

            # B1: startup 4 + active 4 frames. O emulador precisa estar RODANDO
            # o tempo todo em que a tecla fica baixa — este era o defeito.
            #
            # O laco de aproximacao acima sai por `break` com o emulador PAUSADO
            # (o break pula o dap.cont()). A versao antiga apertava a tecla e lia
            # probe_keys ANTES de retomar, entao k_b1 era um valor velho, do
            # ultimo frame emulado — que foi durante o hold de "right". Por isso
            # as tres tentativas da amostra selada reportaram k_b1=0x08, e 0x08 e
            # PORT_A_KEY_RIGHT (SMSlib.h:299); o botao 1 e 0x10 e NUNCA apareceu.
            # A ferramenta concluia "B1 dado a alcance ... whiff" citando um
            # campo que nao continha B1 nenhum, e o soco levou a fama de
            # regressao do jogo. Medido em 07/09/2026 com o emulador rodando
            # durante a tecla: gap=20 -> guile_hp 54->47, dano 7, exatamente o
            # apply_hit(...,7) de ST_PUNCH em fight.c. O soco sempre funcionou.
            dap.cont()
            if backend == "wayland":
                ensure_focus_wayland()
                EI.ydotool_key(EI.EVDEV["a"], True)
            else:
                CE._run(["xdotool", "keydown", "a"])
            # Amostra probe_keys COM o jogo andando: 0x10 tem de aparecer de
            # fato, senao a tecla nao chegou e nao ha soco a julgar.
            k_b1, pose_b1, b1_visto = None, None, False
            fim_b1 = time.time() + 0.25          # ~15 frames > startup+active
            while time.time() < fim_b1:
                dap.pause()
                k = dap.read_byte(PROBE_KEYS)
                p = dap.read_byte(PROBE_POSE)
                dap.cont()
                if k is not None:
                    k_b1 = k if k_b1 is None else (k_b1 | k)
                    if k & 0x10:
                        b1_visto = True
                if p is not None and (p & 0x7F) == 2:
                    pose_b1 = p
                time.sleep(0.02)
            if backend == "wayland":
                EI.ydotool_key(EI.EVDEV["a"], False)
            else:
                CE._run(["xdotool", "keyup", "a"])
            punch["b1_chegou"] = b1_visto

            # janela de observacao: hitstop 6f + recovery 8f, polling rapido
            min_boss = b0
            pose_vista = None
            observacao = []
            fim = time.time() + 1.4
            while time.time() < fim:
                dap.pause()
                bo = dap.read_byte(PROBE_BOSS)
                hp = dap.read_byte(PROBE_HP)
                st = dap.read_byte(PROBE_STATE)
                pose = dap.read_byte(PROBE_POSE)
                observacao.append({"boss": bo, "ken_hp": hp,
                                   "estado": GS.get(st, st),
                                   "pose": pose})
                if pose is not None and (pose & 0x7F) == 2:
                    pose_vista = pose
                if bo is not None and bo < min_boss:
                    min_boss = bo
                dap.cont()
                time.sleep(0.08)
            dap.pause()
            ba = dap.read_byte(PROBE_BOSS)
            conectou = min_boss < b0
            punch["tentativas"].append({
                "n": n, "gap": gap, "guile_hp_antes": b0,
                "guile_hp_min": min_boss, "guile_hp_depois": ba,
                "keys_durante_b1": k_b1, "pose_no_b1": pose_b1,
                "pose_punch_vista": pose_vista,
                "observacao": observacao})
            print("  soco tentativa %d: gap=%s keys_b1=0x%02X pose_b1=%s "
                  "pose_punch=%s guile_hp %s->%s (min %s)%s"
                  % (n, gap, k_b1 or 0, pose_b1, pose_vista, b0, ba,
                     min_boss, "  CONECTOU" if conectou else ""))
            # O sinal que vale e POR TENTATIVA. Comparar o guile_hp de antes de
            # tudo com o de depois de tudo atravessa reset de round — o HP volta
            # a 64 e uma conexao real (54->47) vira "64->64, whiff". Registrado
            # aqui para o veredito nao depender de leitura global.
            if punch.get("b1_chegou"):
                punch["b1_chegou_alguma"] = True
            if conectou:
                punch["conectou"] = True
                punch["delta"] = b0 - min_boss
                punch["gap_do_hit"] = gap
                break
            time.sleep(0.2)
        punch["b1_chegou"] = bool(punch.get("b1_chegou_alguma"))

        after = {"guile_hp": dap.read_byte(PROBE_BOSS),
                 "ken_hp": dap.read_byte(PROBE_HP),
                 "estado": GS.get(dap.read_byte(PROBE_STATE) or 0, "?")}
        ok, motivo = evaluate_punch(before, punch, after)
        print("[soco] %s (%s)"
              % ("CONECTOU POR INPUT" if ok else "NAO conectou", motivo))
        return {"antes": before, "punch": punch, "after": after,
                "soco_provado": ok, "motivo": motivo}
    except (OSError, subprocess.SubprocessError):
        return {"soco_provado": False, "motivo": "falha de ambiente"}


def _read_fighter(dap):
    """Snapshot do lutador 1 e da relacao de lados, pela RAM."""
    pose = dap.read_byte(PROBE_POSE) if PROBE_POSE else None
    return {
        "px": dap.read_byte(PROBE_PX),
        "py": dap.read_byte(PROBE_PY),
        "p2x": dap.read_byte(PROBE_P2X),
        "pose": pose,
    }


def _sideswap_phase(dap, backend):
    """L053: cruzar por cima (Cima+Direcao) e observar o facing virar.

    O facing so atualiza FORA do ar (busy/airborne saltam update_facing),
    entao o flip esperado e DEPOIS de aterrissar. O espelhamento VISUAL do
    sprite continua provado por leitura do codigo (apply_pose dentro de
    update_facing, fight.c) — o probe ve a logica, nao os pixels.
    """
    try:
        time.sleep(0.4)
        dap.pause()
        before = _read_fighter(dap)
        before["facing_bit"] = bool((before["pose"] or 0) & FACE_BIT)
        before["facing"] = 1 if before["facing_bit"] else 0
        print("sideswap antes: px=%s p2x=%s pose=0x%02X (facing=%d)"
              % (before["px"], before["p2x"], before["pose"],
                 before["facing"]))

        # aproximacao: andar para a direita ate a distancia de pulo
        aprox = []
        fim = time.time() + 12.0
        while time.time() < fim:
            if backend == "wayland":
                ensure_focus_wayland()
                hold_wayland("right", 0.4)
            else:
                hold_x11("right", 0.4)
            dap.pause()
            px = dap.read_byte(PROBE_PX)
            p2x = dap.read_byte(PROBE_P2X)
            aprox.append({"px": px, "p2x": p2x})
            if None in (px, p2x):
                continue
            if p2x - px <= 28:
                break
            dap.cont()
        dap.pause()

        # pulo com retries: em contato com a CPU o Ken fica em hitstun/busy
        # e o Cima e ignorado (a 1a rodada mostrou min_py travado em 112).
        # Passo atras para sair do alcance, espera assentar, tenta ate 3x.
        flight = {"min_py": None, "amostras": [], "cruzou_no_ar": False}
        tentativas = []
        for n in range(3):
            if backend == "wayland":
                ensure_focus_wayland()
                hold_wayland("left", 0.3)
            else:
                hold_x11("left", 0.3)
            dap.cont()
            time.sleep(0.6)
            dap.pause()
            pre = _read_fighter(dap)
            tentativas.append({"n": n, "px": pre["px"], "p2x": pre["p2x"],
                               "pose": pre["pose"]})

            if backend == "wayland":
                ensure_focus_wayland()
                press_wayland("right")
            else:
                CE._run(["xdotool", "keydown", "Right"])
            dap.cont()
            time.sleep(0.05)
            if backend == "wayland":
                press_wayland("up")
                time.sleep(0.3)
                release_wayland("up")
            else:
                CE._run(["xdotool", "keydown", "Up"])
                time.sleep(0.3)
                CE._run(["xdotool", "keyup", "Up"])

            fim = time.time() + 2.5
            while time.time() < fim:
                dap.pause()
                px = dap.read_byte(PROBE_PX)
                py = dap.read_byte(PROBE_PY)
                p2x = dap.read_byte(PROBE_P2X)
                pose = dap.read_byte(PROBE_POSE)
                flight["amostras"].append({"t": n, "px": px, "py": py,
                                           "p2x": p2x, "pose": pose})
                if py is not None and (flight["min_py"] is None
                                       or py < flight["min_py"]):
                    flight["min_py"] = py
                if px is not None and p2x is not None and px > p2x:
                    flight["cruzou_no_ar"] = True
                    if py is not None and py >= GROUND_Y:
                        break
                dap.cont()
                time.sleep(0.06)
            if backend == "wayland":
                release_wayland("right")
            else:
                CE._run(["xdotool", "keyup", "Right"])
            dap.pause()
            pulou = (flight["min_py"] is not None
                     and flight["min_py"] < GROUND_Y)
            print("sideswap tentativa %d: pulou=%s cruzou=%s min_py=%s"
                  % (n, pulou, flight["cruzou_no_ar"], flight["min_py"]))
            if pulou and flight["cruzou_no_ar"]:
                break
            # proxima tentativa vale por si: zera os marcadores do voo
            flight["min_py"] = None
            flight["cruzou_no_ar"] = False
        flight["pulo"] = (flight["min_py"] is not None
                          and flight["min_py"] < GROUND_Y)
        print("sideswap voo: min_py=%s cruzou_no_ar=%s (%d amostras)"
              % (flight["min_py"], flight["cruzou_no_ar"],
                 len(flight["amostras"])))

        time.sleep(0.6)
        dap.pause()
        after = _read_fighter(dap)
        after["facing_bit"] = bool((after["pose"] or 0) & FACE_BIT)
        after["facing"] = 1 if after["facing_bit"] else 0
        print("sideswap depois: px=%s p2x=%s pose=0x%02X (facing=%d)"
              % (after["px"], after["p2x"], after["pose"], after["facing"]))

        flight["pulo"] = (flight["min_py"] is not None
                          and flight["min_py"] < GROUND_Y)
        ok, motivo = evaluate_swap(before, flight, after)
        print("[sideswap] %s (%s)"
              % ("TROCA DE LADO OBSERVADA" if ok else "nao observada", motivo))
        return {"antes": before, "voo": flight, "depois": after,
                "aproximacao": aprox, "tentativas": tentativas,
                "sideswap_provado": ok, "motivo": motivo}
    except (OSError, subprocess.SubprocessError):
        return {"sideswap_provado": False, "motivo": "falha de ambiente"}


def _dump(metrics):
    with open("SMS_projects/MSSF2T/out/evidence/input_memory.json", "w") as f:
        json.dump(metrics, f, indent=1)


def _metrics(backend, canal_vivo, focado, samples, luta_iniciada, estado,
             f0, f1, golpe=None):
    with open("SMS_projects/MSSF2T/out/rom/MSSF2T.sms", "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    m = {
        "schema": "input_memory_v2",
        "rom": ROM_REL,
        "rom_sha256": sha,
        "probe_px_addr": hex(PROBE_PX),
        "backend": backend,
        "foco_verificado": focado,
        "frames": {"antes": f0, "depois": f1},
        "amostras": samples,
        "luta_iniciada_por_input": luta_iniciada,
        "estado_final": GS.get(estado, estado),
        "input_provado": False,
        "canal_teclado_vivo": canal_vivo,
        "criterio": "dx >= 8 px NA DIRECAO COMANDADA nos dois sentidos, "
                    "com canal vivo (reset ctrl+BackSpace zera o frame)",
        "por_que_memoria": ("pixels sao ambiguos aqui: Ken e Guile dao "
                            "blobs identicos de 309 px e o gi do Ken funde "
                            "com o deck; interaction_verdict nao confere "
                            "direcao nem identidade (L038)"),
        "chain_of_custody": [
            "launch: java -jar Emulicious.jar -remotedebug " + str(PORT),
            "attach DAP; leitura com a emulacao PAUSADA",
            "input: backend " + backend
            + " (L039: XTEST nao atravessa KWin; canal real = uinput)",
            "leitura: @0xC7FA = P[0].x (main.c: probe_px)",
        ],
    }
    if golpe is not None:
        m["golpe_bonus"] = golpe
    return m


# ----------------------------------------------------------------- self-check
def self_check():
    """§19: o instrumento so e fonte com self-check passando. As fixtures sao
    as regressoes exatas que motivaram o tool (L038/L039) — nada de fixture
    generica que passa de graca."""
    falhas = []

    # 1. Regressao L039 EXATA: tecla pressionada, probe_keys 0x00, canal morto.
    s_l039 = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
               "x_depois": 40, "dx": 0, "probe_keys_durante": 0x00}]
    ok, motivo = evaluate(s_l039, canal_vivo=False)
    if ok:
        falhas.append("L039: canal morto foi aceito")
    if "canal" not in motivo:
        falhas.append("L039: motivo nao cita o canal: " + motivo)

    # 2. Armadilha L038 EXATA: "Right" e o objeto anda 32 px para a ESQUERDA;
    #    o gate antigo dava PASS por abs(dx) >= 8. Aqui tem de REPROVAR.
    s_l038 = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 104,
               "x_depois": 72, "dx": -32, "probe_keys_durante": 0x00}]
    ok, _ = evaluate(s_l038, canal_vivo=True)
    if ok:
        falhas.append("L038: dx na direcao OPOSTA foi aceito")

    # 3. Movimento curto demais: dx=+3 com Right reprovou.
    s_curto = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
                "x_depois": 43, "dx": 3, "probe_keys_durante": 0x08}]
    ok, _ = evaluate(s_curto, canal_vivo=True)
    if ok:
        falhas.append("dx=3 na direcao certa foi aceito (teto e 8)")

    # 4. Um sentido so: Right ok e Left parado reprova (criterio e simetrico).
    s_meio = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
               "x_depois": 60, "dx": 20, "probe_keys_durante": 0x08},
              {"tecla": "Left", "sentido_esperado": -1, "x_antes": 60,
               "x_depois": 60, "dx": 0, "probe_keys_durante": 0x04}]
    ok, _ = evaluate(s_meio, canal_vivo=True)
    if ok:
        falhas.append("segundo sentido parado foi aceito")

    # 5. Caminho bom: dx >= 8 na direcao comandada nos DOIS sentidos.
    s_ok = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
             "x_depois": 56, "dx": 16, "probe_keys_durante": 0x08},
            {"tecla": "Left", "sentido_esperado": -1, "x_antes": 56,
             "x_depois": 42, "dx": -14, "probe_keys_durante": 0x04}]
    ok, motivo = evaluate(s_ok, canal_vivo=True)
    if not ok:
        falhas.append("caminho bom foi reprovado: " + motivo)

    # 5b. Regressao do campo no JSON: _metrics nasce com input_provado=False;
    #     se o run esquecer de gravar o veredito, o artefato mente contra o
    #     stdout (foi exatamente o que o selo pegou nesta sessao).
    m = _metrics("wayland", True, True, s_ok, True, GS_FIGHT, 100, 200)
    if m["input_provado"] is not False:
        falhas.append("metrics default de input_provado deixou de ser False")

    # 6. Leitura perdida (None) reprova em vez de seguir.
    s_none = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
               "x_depois": None, "dx": None, "probe_keys_durante": 0x08}]
    ok, _ = evaluate(s_none, canal_vivo=True)
    if ok:
        falhas.append("leitura None foi aceita")

    # ---- fixtures da troca de lado (L053) — evaluate_swap
    b = {"px": 12, "p2x": 176, "pose": 0x81, "facing_bit": True, "facing": 1}
    v = {"min_py": 104, "pulo": True}
    a_de_cst = {"px": 190, "p2x": 176, "pose": 0x81, "facing_bit": True,
                "facing": 1}
    a_ok = {"px": 190, "p2x": 176, "pose": 0x01, "facing_bit": False,
            "facing": 0}

    # 7. Regressao L053 EXATA: cruzou mas ficou DE COSTAS (facing nao virou).
    ok, _ = evaluate_swap(b, v, a_de_cst)
    if ok:
        falhas.append("L053: cruzou e ficou de costas foi aceito")

    # 8. Facing virou mas Ken nao cruzou.
    a_meio = {"px": 150, "p2x": 176, "pose": 0x01, "facing_bit": False,
              "facing": 0}
    ok, _ = evaluate_swap(b, v, a_meio)
    if ok:
        falhas.append("sideswap: facing virou sem cruzar foi aceito")

    # 9. Cruzou 'no chao' (impossivel pela caixa de corpo) — reprova.
    v_chao = {"min_py": 112, "pulo": False}
    ok, _ = evaluate_swap(b, v_chao, a_ok)
    if ok:
        falhas.append("sideswap: troca sem pulo foi aceita")

    # 10. Estado inicial invalido: Ken ja a direita.
    b_inv = {"px": 190, "p2x": 176, "pose": 0x01, "facing_bit": False,
             "facing": 0}
    ok, _ = evaluate_swap(b_inv, v, a_ok)
    if ok:
        falhas.append("sideswap: estado inicial invertido foi aceito")

    # 11. Caminho bom: pulo, cruzou, facing virou.
    ok, motivo_swap = evaluate_swap(b, v, a_ok)
    if not ok:
        falhas.append("sideswap: caminho bom foi reprovado: " + motivo_swap)

    # 12. Leitura perdida reprova.
    b_none = {"px": None, "p2x": 176, "pose": 0x81, "facing_bit": True,
              "facing": 1}
    ok, _ = evaluate_swap(b_none, v, a_ok)
    if ok:
        falhas.append("sideswap: leitura None foi aceita")

    # ---- fixtures do soco conectando (handoff item 1 / amostra selada)
    # 13. Whiff de verdade: B1 CONFIRMADO no ROM e guile_hp 64->64.
    p_whiff = {"canal_vivo": True, "gap": 20, "gap_no_limite": True,
               "b1_chegou": True}
    ok, _ = evaluate_punch({"guile_hp": 64}, p_whiff, {"guile_hp": 64})
    if ok:
        falhas.append("soco: whiff 64->64 com B1 confirmado foi aceito")

    # 13b. Tecla que NAO chegou nao pode ser reportada como whiff — foi assim
    # que o soco levou fama de regressao do jogo por 1 dia (07/09/2026).
    p_sem_b1 = {"canal_vivo": True, "gap": 20, "gap_no_limite": True,
                "b1_chegou": False}
    ok, motivo_sem = evaluate_punch({"guile_hp": 64}, p_sem_b1,
                                    {"guile_hp": 64})
    if ok:
        falhas.append("soco: tecla perdida foi aceita como sucesso")
    elif "nao chegou" not in motivo_sem:
        falhas.append("soco: tecla perdida foi diagnosticada como whiff: "
                      + motivo_sem)

    # 13c. Amostra ANTIGA (sem o campo) nao pode afirmar whiff.
    p_antigo = {"canal_vivo": True, "gap": 20, "gap_no_limite": True}
    ok, motivo_ant = evaluate_punch({"guile_hp": 64}, p_antigo,
                                    {"guile_hp": 64})
    if ok or "amostra" not in motivo_ant:
        falhas.append("soco: amostra sem b1_chegou deveria ser inconclusiva, "
                      "veio: " + motivo_ant)

    # 14. Fora de alcance nao pode passar, nem com hp caindo.
    p_longe = {"canal_vivo": True, "gap": 30, "gap_no_limite": False}
    ok, _ = evaluate_punch({"guile_hp": 64}, p_longe, {"guile_hp": 57})
    if ok:
        falhas.append("soco: queda de hp fora de alcance foi aceita")

    # 15. Canal morto reprova.
    p_morto = {"canal_vivo": False, "gap": 20, "gap_no_limite": True}
    ok, _ = evaluate_punch({"guile_hp": 64}, p_morto, {"guile_hp": 57})
    if ok:
        falhas.append("soco: canal morto foi aceito")

    # 16. Hit (-7), chip de guarda (-2) e KO (0) sao conexoes.
    p_bom = {"canal_vivo": True, "gap": 20, "gap_no_limite": True,
             "b1_chegou": True}
    ok, motivo_soco = evaluate_punch({"guile_hp": 64}, p_bom,
                                     {"guile_hp": 57})
    if not ok:
        falhas.append("soco: hit -7 foi reprovado: " + motivo_soco)
    ok, _ = evaluate_punch({"guile_hp": 64}, p_bom, {"guile_hp": 62})
    if not ok:
        falhas.append("soco: chip de guarda -2 foi reprovado")
    ok, _ = evaluate_punch({"guile_hp": 64}, p_bom, {"guile_hp": 0})
    if not ok:
        falhas.append("soco: KO foi reprovado")

    # 17. Leitura perdida do hp reprova.
    ok, _ = evaluate_punch({"guile_hp": None}, p_bom, {"guile_hp": 57})
    if ok:
        falhas.append("soco: leitura None foi aceita")

    if falhas:
        print("[SELF-CHECK FAIL]")
        for f in falhas:
            print("  - " + f)
        return 1
    print("[SELF-CHECK PASS] 21 fixtures: L039 canal morto, L038 direcao "
          "oposta, dx curto, sentido unico, caminho bom, leitura None, "
          "L053 de costas, facing sem cruzar, sem pulo, estado invertido, "
          "sideswap caminho bom, sideswap leitura None, soco whiff com B1 "
          "confirmado, soco com tecla perdida (nao e whiff), soco de amostra "
          "antiga (inconclusivo), fora de alcance, canal morto, hit -7, "
          "chip -2, KO, leitura None")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    # whitelist literal: o instrumento so opera sobre a ROM do projeto
    if a.rom not in ("out/rom/MSSF2T.sms", "SMS_projects/MSSF2T/out/rom/MSSF2T.sms"):
        print("[FAIL_AMBIENTE] --rom fora da whitelist do projeto")
        return 2
    return run()[0]


if __name__ == "__main__":
    raise SystemExit(main())
