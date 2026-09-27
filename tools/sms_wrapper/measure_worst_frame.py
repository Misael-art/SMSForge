#!/usr/bin/env python3
"""measure_worst_frame.py — mede o worst-frame de VBlank NA ROM (L061).

Orçamento de cena "declarado" (ex.: doc/13-spec-cenas.md) não fecha eixo
nenhum até existir instrumento NA ROM. Padrão do probe SMRT (aditivo,
schema 1):
  - probe_vline (0xC7EA): VCounter lido após os uploads, CRAM, HUD e SAT do
    trecho de VBlank. VBlank começa em 0xC0 (linha 192 NTSC) e segue até
    o contador dar a volta; valor <0xC0 significa que o trabalho passou da
    janela segura e invadiu o próximo display ativo.
  - probe_vovf (0xC7EB, word): contador não saturante de frames com vline <
    0xC0. Delta de leituras = evidência dura, imune a amostragem e ao antigo
    falso teto em 255.
  - probe_phase (0xC7ED): última fase observada (1 CPU/input, 2 trabalho de
    VBlank, 3 amostra final de VDP, 4 preparação de metasprites em RAM).
Um segundo contador "missed" chegou a existir no WIP de 2026-09-15: incrementado
na MESMA condição de vovf, era redundante por construção e comeu 16 B do banco
(makesms "Bank 1 overflow"); removido do ROM e daqui. vovf é o único contador.
A ROM mede 3000 frames contínuos de MODO ATRAÇÃO (CPU x CPU: especiais,
projéteis, trocas de pose com stream, HUD e banners), depois sela vovf e o
menor vline em RAM. O DAP só conecta DEPOIS do selo: pause()/cont() durante a
janela fazia o Z80 perder tempo de frame e contaminava a própria grandeza.
3000 frames cobrem pelo menos 50 s a 60 Hz e 60 s a 50 Hz. Derrame não derruba
fps: espreme o streaming de VRAM, então "fps 60" não absolve orçamento estourado.

Pré-requisito do projeto: probe SMRT com probe_vline/probe_vovf nos
endereços acima, probe_worst_done/probe_vline_min em 0xC7EE/0xC7EF e modo
atração que exercite o pior caminho.

Uso:
  measure_worst_frame.py --project SMS_projects/MSSF2T \
      --rom SMS_projects/MSSF2T/out/rom/MSSF2T.sms [--seconds 45]

`--seconds` é a janela mínima solicitada (1–50 s); a ROM mede sempre 3000
frames. O runner deixa a emulação seguir sem DAP por 90 s por padrão; use
`--wait-seconds` (90–1800) para ROMs de diagnóstico abaixo de 50 FPS. O DAP
conecta uma vez após o prazo e lê o snapshot imutável.

Exit:
  0  pass — nenhum frame derramou no VBlank (vovf não avançou)
  1  reprova — vovf avançou (derramou), leitura sem lastro, ou ROM sem
     contrato de probe (sem_contrato: nada medido é evidência)
  2  ambiente ausente (java/emulador/DAP)
  3  uso (argumentos)
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import capture_evidence as CE                                    # noqa: E402
import measure_runtime_probe as MRP                              # noqa: E402
from emulicious_dap import PORT, magic_ok                         # noqa: E402

PROBE_HEADER = 0xC7E0         # magic 'SMRT' + byte de schema (L071/§56)
PROBE_VLINE = 0xC7EA
PROBE_VOVF = 0xC7EB
PROBE_PHASE = 0xC7ED
PROBE_WORST_DONE = 0xC7EE
PROBE_VLINE_MIN = 0xC7EF
PROBE_FRAME = 0xC7F0
PROBE_STATE = 0xC7F6
PROFILE_ADDRS = {
    "wait": 0xC7D0,
    "stream": 0xC7D1,
    "palette": 0xC7D2,
    "hud": 0xC7D3,
    "sat": 0xC7D4,
}
PROFILE_SPILL_MAX = 0xC7D6
PROBE_WINDOW_FRAMES = 3000
PROBE_DEFAULT_WAIT_SECONDS = int(PROBE_WINDOW_FRAMES / 50.0 + 30.0)
PROBE_MAX_WAIT_SECONDS = 1800
PROBE_MAX_SECONDS = PROBE_WINDOW_FRAMES / 60.0
VLIMIAR = 0xC0            # abaixo disso, o VDP ja voltou ao display ativo
GS = {0: "ROUND", 1: "FIGHT", 2: "KO", 3: "RESULT", 4: "TITLE"}


# ---------------------------------------------------------------- contrato
DECL_RX = {
    "probe_vline em 0xC7EA": re.compile(r"__at\(0xC7EA\)"),
    "probe_vovf WORD em 0xC7EB": re.compile(r"unsigned\s+int[^;]*__at\(0xC7EB\)"),
    "probe_phase em 0xC7ED": re.compile(r"__at\(0xC7ED\)"),
    "probe_worst_done em 0xC7EE": re.compile(r"__at\(0xC7EE\)"),
    "probe_vline_min em 0xC7EF": re.compile(r"__at\(0xC7EF\)"),
    "janela de 3000 frames": re.compile(
        r"#define\s+WORST_FRAME_WINDOW\s+3000u"),
}
PROFILE_RX = {
    name: re.compile(r"__at\(0x%04X\)\s+probe_profile_%s\b"
                     % (addr, name))
    for name, addr in PROFILE_ADDRS.items()
}
PROFILE_SPILL_RX = re.compile(
    r"__at\(0xC7D6\)\s+probe_vline_spill_max\b")


def probe_contract(project):
    """A fonte declara o mapa e selo canônicos? (L071/§56/L082)

    O header SMRT na RAM autentica a identidade do probe, mas NÃO prova que
    a ROM instrumenta o worst-frame: arena_nocturna tem magic+schema e nenhum
    vline/vovf/phase — o 'pass' de lixo estático em 0xEA era falso verde
    (L077). vovf precisa ser WORD; done/min precisam selar uma janela
    contínua antes de qualquer pausa do DAP (L082)."""
    src = os.path.join(project, "src")
    text = ""
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.endswith((".c", ".h")):
                with open(os.path.join(src, f), errors="replace") as fh:
                    text += fh.read()
    missing = [k for k, rx in DECL_RX.items() if not rx.search(text)]
    return (not missing), missing


def profile_contract(project):
    """Perfil opcional por checkpoints; não faz parte do contrato SMRT comum."""
    src = os.path.join(project, "src")
    text = ""
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if f.endswith((".c", ".h")):
                with open(os.path.join(src, f), errors="replace") as fh:
                    text += fh.read()
    return (all(rx.search(text) for rx in PROFILE_RX.values())
            and PROFILE_SPILL_RX.search(text) is not None)


def state_label(project, state):
    """Use enum ST_* when the project declares one; otherwise retain GS map."""
    if state is None:
        return None
    src = os.path.join(project, "src")
    if os.path.isdir(src):
        for f in sorted(os.listdir(src)):
            if not f.endswith((".c", ".h")):
                continue
            with open(os.path.join(src, f), errors="replace") as fh:
                m = re.search(r"enum\s*\{([^}]+)\}", fh.read())
            if not m:
                continue
            names = re.findall(r"\bST_[A-Z0-9_]+\b", m.group(1))
            names = [n for n in names if n != "ST_N_STATES"]
            if names:
                return names[state][3:] if state < len(names) else str(state)
    return str(GS.get(state, state))


def profile_lines(raw):
    """Converte checkpoints VCounter em linhas desde o primeiro checkpoint.

    NTSC tem a descontinuidade documentada DA→D5 e volta FF→00. D5–DA pode
    ocorrer dos dois lados da primeira descontinuidade, então a ordem temporal
    dos checkpoints resolve a ocorrência mais cedo compatível.
    """
    def candidates(v):
        if v is None:
            return []
        if v < 0xC0:
            return [70 + v]
        if v <= 0xD4:
            return [v - 0xC0]
        if v <= 0xDA:
            return [v - 0xC0, 27 + v - 0xD5]
        return [27 + v - 0xD5]

    if not raw or any(v is None for v in raw):
        return None
    first = min(candidates(raw[0]))
    elapsed = [0]
    prev = first
    for v in raw[1:]:
        choices = [n for n in candidates(v) if n >= prev]
        if not choices:
            return None
        prev = min(choices)
        elapsed.append(prev - first)
    return elapsed


# ---------------------------------------------------------------- logica pura
def analyze(samples, vovf_inicio, vovf_fim, limiar=VLIMIAR):
    """Veredito do worst-frame a partir de amostras + delta do contador.

    - vovf_delta > 0: REPROVA — frames com trabalho dentro do VBlank,
      contados pela própria ROM (imune a amostragem).
    - vovf_delta == 0 e vline_min < limiar: contradição por construção
      (vovf conta exatamente esses frames fora do blank) — leitura sem lastro.
    - leitura None não conta como amostra; sem amostra nenhuma, sem
      veredito.
    """
    vline_min = None
    validos = [s for s in samples if s.get("vline") is not None]
    for s in validos:
        if vline_min is None or s["vline"] < vline_min:
            vline_min = s["vline"]
    if vovf_inicio is None or vovf_fim is None:
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": None, "amostras": len(validos)}
    if not validos:
        return {"verdicto": "sem_lastro", "vline_min": None,
                "vovf_delta": vovf_fim - vovf_inicio, "amostras": 0}
    delta = vovf_fim - vovf_inicio
    if delta > 0:
        return {"verdicto": "derramou", "vline_min": vline_min,
                "vovf_delta": delta, "amostras": len(validos)}
    if vline_min < limiar:
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": delta, "amostras": len(validos)}
    return {"verdicto": "pass", "vline_min": vline_min,
            "vovf_delta": 0, "amostras": len(validos)}


def analyze_snapshot(vline_min, vovf_total, done, frame, seconds=45.0):
    """Julga o snapshot selado pela ROM depois de 3000 frames sem DAP."""
    if not (0 < seconds <= PROBE_MAX_SECONDS):
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": None, "amostras": 0,
                "motivo": "janela solicitada fora do limite 1..50 s"}
    if done != 1 or frame is None or frame < PROBE_WINDOW_FRAMES:
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": None, "amostras": 0,
                "motivo": "janela worst-frame incompleta ou sem selo"}
    if vline_min is None or vovf_total is None:
        return {"verdicto": "sem_lastro", "vline_min": vline_min,
                "vovf_delta": None, "amostras": 0,
                "motivo": "snapshot de worst-frame ilegivel"}
    r = analyze([{"vline": vline_min}], 0, vovf_total, VLIMIAR)
    r["frames_medidos"] = PROBE_WINDOW_FRAMES
    r["frames_rom_final"] = frame
    r["janela_s_min"] = PROBE_MAX_SECONDS
    r["janela_selada"] = bool(done)
    return r


# ---------------------------------------------------------------- ambiente
def effective_wait_seconds(requested=None):
    if requested is None:
        return PROBE_DEFAULT_WAIT_SECONDS
    if not (PROBE_DEFAULT_WAIT_SECONDS <= requested <= PROBE_MAX_WAIT_SECONDS):
        raise ValueError("--wait-seconds deve estar entre %d e %d" %
                         (PROBE_DEFAULT_WAIT_SECONDS, PROBE_MAX_WAIT_SECONDS))
    return float(requested)


def measure(rom, project, seconds=45.0, out_name="worst_frame",
            wait_seconds=None):
    if not (0 < seconds <= PROBE_MAX_SECONDS):
        print("[FAIL_USO] --seconds deve estar entre 1 e %.0f; "
              "a ROM sela 3000 frames" % PROBE_MAX_SECONDS)
        return 3, None
    try:
        wait_s = effective_wait_seconds(wait_seconds)
    except ValueError as e:
        print("[FAIL_USO] %s" % e)
        return 3, None
    okc, missing = probe_contract(project)
    if not okc:
        out_dir = os.path.join(project, "out", "evidence")
        os.makedirs(out_dir, exist_ok=True)
        res = {"verdicto": "sem_contrato", "vline_min": None,
               "vovf_delta": None, "amostras": 0, "janela_s": seconds,
               "runner_wait_s": wait_s,
               "motivo": "fonte da ROM nao declara: " + "; ".join(missing),
               "rom": os.path.abspath(rom),
               "rom_sha256": hashlib.sha256(open(rom, "rb").read()).hexdigest(),
               "estados_vistos": [], "amostras_brutas": []}
        with open(os.path.join(out_dir, out_name + ".json"), "w") as f:
            json.dump(res, f, indent=1)
        print("[worst-frame] veredito=sem_contrato — %s" % "; ".join(missing))
        print("               nada medido neste endereco e evidencia; "
              "instrumente o mapa e o selo canonicos antes de claimar budget")
        return 1, res
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
        # 3000 frames levam no máximo 60 s a 50 Hz; 30 s cobrem boot/carga
        # lentos observados no host. Nenhum pause()/cont() ocorre na janela.
        print("[worst-frame] DAP desconectado por %.0f s; aguardando selo "
              "de %d frames" % (wait_s, PROBE_WINDOW_FRAMES))
        time.sleep(wait_s)
        dap = MRP._connect_live()
        if dap is None:
            print("[FAIL] canal DAP nao ficou vivo (porta %s)" % PORT)
            return 1, None
        try:
            return _session(dap, out_dir, out_name, seconds, rom, project,
                            wait_s)
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


def _session(dap, out_dir, out_name, seconds, rom, project, wait_seconds):
    # _connect_live retorna pausado, mas só DEPOIS dos 3000 frames autônomos.
    # A ROM congela vovf/vline_min em done=1, logo o attach não altera a amostra.
    header = dap.read_block(PROBE_HEADER, 5)
    sha = hashlib.sha256(open(rom, "rb").read()).hexdigest()
    if not magic_ok(header):
        res = {"verdicto": "sem_contrato", "vline_min": None,
               "vovf_delta": None, "amostras": 0, "janela_s": seconds,
               "runner_wait_s": wait_seconds,
               "motivo": "probe SMRT/schema 1 ausente em 0xC7E0 "
                         "(lido=%s) — ROM sem instrumento válido" % header,
               "rom": os.path.abspath(rom), "rom_sha256": sha,
               "estados_vistos": [], "amostras_brutas": []}
        with open(os.path.join(out_dir, out_name + ".json"), "w") as f:
            json.dump(res, f, indent=1)
        print("[worst-frame] veredito=sem_contrato — header SMRT ausente")
        return 1, res

    vl = dap.read_byte(PROBE_VLINE)
    vmin = dap.read_byte(PROBE_VLINE_MIN)
    vf = dap.read_word(PROBE_VOVF)
    ph = dap.read_byte(PROBE_PHASE)
    st = dap.read_byte(PROBE_STATE)
    done = dap.read_byte(PROBE_WORST_DONE)
    frame = dap.read_word(PROBE_FRAME)
    res = analyze_snapshot(vmin, vf, done, frame, seconds)
    res["janela_s"] = seconds
    res["runner_wait_s"] = wait_seconds
    res["vovf_inicio"] = 0
    res["vovf_fim"] = vf
    res["rom"] = os.path.abspath(rom)
    res["rom_sha256"] = sha
    snapshot_state = state_label(project, st)
    res["estado_snapshot"] = snapshot_state
    res["estados_vistos"] = []  # janela selada não manteve série de estados
    res["amostras_brutas"] = [{"t": "snapshot", "vline": vl,
                               "vline_min": vmin, "vovf": vf,
                               "phase": ph,
                               "estado_snapshot": snapshot_state,
                               "frame": frame, "done": done}]
    project = os.path.dirname(os.path.dirname(os.path.dirname(rom)))
    if profile_contract(project):
        raw_profile = {name: dap.read_byte(addr)
                       for name, addr in PROFILE_ADDRS.items()}
        raw_profile["spill_max"] = dap.read_byte(PROFILE_SPILL_MAX)
        order = ["wait", "stream", "palette", "hud", "sat", "spill_max"]
        profile_valid = (vf > 0 and raw_profile["spill_max"] < VLIMIAR)
        cumulative = (profile_lines([raw_profile[name] for name in order])
                      if profile_valid else None)
        res["perfil_vcounter"] = {
            "raw": raw_profile,
            "profile_valido": profile_valid,
            "linhas_desde_wait": dict(zip(order, cumulative or [])),
            "linhas_por_etapa": (dict(zip(
                order, [cumulative[0]] + [cumulative[i] - cumulative[i - 1]
                                          for i in range(1, len(cumulative))]))
                if cumulative else None),
        }
    with open(os.path.join(out_dir, out_name + ".json"), "w") as f:
        json.dump(res, f, indent=1)
    print("[worst-frame] veredito=%s vovf_delta=%s vline_min=%s "
          "amostras=%d estados=%s"
          % (res["verdicto"], res["vovf_delta"], res["vline_min"],
             res["amostras"], res["estados_vistos"]))
    return (0 if res["verdicto"] == "pass" else 1), res


# ---------------------------------------------------------------- self-check
def self_check():
    ok = []

    r = analyze([{"vline": 0xFF}, {"vline": 0xD5}], 7, 7)
    ok.append(("pass sem derrame", r["verdicto"] == "pass"
               and r["vovf_delta"] == 0 and r["vline_min"] == 0xD5))
    r = analyze([{"vline": 0xD0}, {"vline": 0x72}], 7, 9)
    ok.append(("derrame reprovado pelo contador", r["verdicto"] == "derramou"
               and r["vovf_delta"] == 2))
    r = analyze([{"vline": None}], None, None)
    ok.append(("leitura perdida = sem lastro", r["verdicto"] == "sem_lastro"))
    r = analyze([], 3, 3)
    ok.append(("zero amostras = sem lastro", r["verdicto"] == "sem_lastro"))
    # vline dentro do display com contador parado é contradição.
    r = analyze([{"vline": 0x70}], 5, 5)
    ok.append(("vline baixo sem contador = sem lastro",
               r["verdicto"] == "sem_lastro"))
    r = analyze([{"vline": 0xFF}], 255, 255)
    ok.append(("contador WORD sem delta passa",
               r["verdicto"] == "pass"))
    r = analyze_snapshot(0xD5, 0, 1, PROBE_WINDOW_FRAMES + 300, 45)
    ok.append(("snapshot completo sem derrame passa",
               r["verdicto"] == "pass" and r["frames_medidos"] == 3000))
    r = analyze_snapshot(0x50, 2, 1, PROBE_WINDOW_FRAMES + 300, 45)
    ok.append(("snapshot completo com derrame reprova",
               r["verdicto"] == "derramou" and r["vovf_delta"] == 2))
    ok.append(("espera padrao preserva 90 s",
               effective_wait_seconds() == 90))
    ok.append(("espera longa aceita ROM lenta",
               effective_wait_seconds(150) == 150.0))
    try:
        effective_wait_seconds(89)
        short_wait_rejected = False
    except ValueError:
        short_wait_rejected = True
    ok.append(("espera curta nao reduz janela selada", short_wait_rejected))
    try:
        effective_wait_seconds(1801)
        long_wait_rejected = False
    except ValueError:
        long_wait_rejected = True
    ok.append(("espera tem limite superior", long_wait_rejected))
    r = analyze_snapshot(0xD5, 0, 0, PROBE_WINDOW_FRAMES + 300, 45)
    ok.append(("snapshot sem selo nao fecha janela",
               r["verdicto"] == "sem_lastro"))
    r = analyze_snapshot(0xD5, 0, 1, PROBE_WINDOW_FRAMES - 1, 45)
    ok.append(("snapshot curto nao fecha janela",
               r["verdicto"] == "sem_lastro"))
    r = analyze_snapshot(0xD5, 0, 1, PROBE_WINDOW_FRAMES + 300, 51)
    ok.append(("janela acima do probe nao e suportada",
               r["verdicto"] == "sem_lastro"))
    prof = profile_lines([0xC3, 0xD9, 0x20, 0x40])
    ok.append(("checkpoints VCounter atravessam retorno FF->00",
               prof == [0, 22, 99, 131]))
    ok.append(("checkpoints VCounter sem dados rejeitam",
               profile_lines([0xC0, None]) is None))
    # contrato do probe: sem header SMRT+schema, nenhuma leitura e evidencia
    ok.append(("lixo sem magic nao autentica",
               magic_ok([0, 0, 0, 0, 0]) is False))
    ok.append(("SMRT+schema1 autentica",
               magic_ok(list(b"SMRT") + [1]) is True))
    ok.append(("magic certo com schema errado rejeita",
               magic_ok(list(b"SMRT") + [2]) is False))
    ok.append(("header ausente (None) rejeita", magic_ok(None) is False))
    # contrato de fonte: a triade precisa estar DECLARADA no fonte da ROM
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        sd = os.path.join(td, "src")
        os.makedirs(sd)
        mc = os.path.join(sd, "m.c")

        def _src(body):
            with open(mc, "w") as f:
                f.write(body)
            return probe_contract(td)

        okc, miss = _src(
            "volatile unsigned char __at(0xC7EA) probe_vline;\n"
            "volatile unsigned int  __at(0xC7EB) probe_vovf;\n"
            "volatile unsigned char __at(0xC7ED) probe_phase;\n"
            "volatile unsigned char __at(0xC7EE) probe_worst_done;\n"
            "volatile unsigned char __at(0xC7EF) probe_vline_min;\n"
            "#define WORST_FRAME_WINDOW 3000u\n")
        ok.append(("triade completa autentica", okc and not miss))
        okc, miss = _src(
            "volatile unsigned char __at(0xC7EA) probe_vline;\n"
            "volatile unsigned char __at(0xC7EB) probe_vovf;\n"
            "volatile unsigned char __at(0xC7ED) probe_phase;\n"
            "volatile unsigned char __at(0xC7EE) probe_worst_done;\n"
            "volatile unsigned char __at(0xC7EF) probe_vline_min;\n"
            "#define WORST_FRAME_WINDOW 3000u\n")
        ok.append(("vovf como BYTE rejeita (saturacao)", not okc))
        okc, miss = _src(
            "volatile unsigned char __at(0xC7EA) probe_vline;\n"
            "volatile unsigned int  __at(0xC7EB) probe_vovf;\n"
            "volatile unsigned char __at(0xC7ED) probe_phase;\n"
            "volatile unsigned char __at(0xC7EE) probe_worst_done;\n"
            "volatile unsigned char __at(0xC7EF) probe_vline_min;\n"
            "#define WORST_FRAME_WINDOW 2999u\n")
        ok.append(("janela diferente de 3000 rejeita", not okc))
        okc, miss = _src(
            "volatile unsigned char __at(0xC7EA) probe_vline;\n")
        ok.append(("so vline rejeita (faltam campos do contrato)",
                   not okc and len(miss) == 5))
        okc, miss = _src("int main(void){return 0;}\n")
        ok.append(("ROM sem probe algum rejeita (arena/laboratorio)",
                   not okc and len(miss) == 6))
        with open(mc, "a") as f:
            f.write("volatile unsigned char __at(0xC7D0) probe_profile_wait;\n"
                    "volatile unsigned char __at(0xC7D1) probe_profile_stream;\n"
                    "volatile unsigned char __at(0xC7D2) probe_profile_palette;\n"
                    "volatile unsigned char __at(0xC7D3) probe_profile_hud;\n"
                    "volatile unsigned char __at(0xC7D4) probe_profile_sat;\n"
                    "volatile unsigned char __at(0xC7D6) probe_vline_spill_max;\n")
        ok.append(("perfil opcional exige snapshot do maior derrame",
                   profile_contract(td)))
        with open(mc, "w") as f:
            f.write("enum { ST_IDLE, ST_WALK_F, ST_N_STATES };\n")
        ok.append(("enum de estado do projeto rotula snapshot corretamente",
                   state_label(td, 0) == "IDLE"
                   and state_label(td, 1) == "WALK_F"))
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
    ap.add_argument("--seconds", type=float, default=45.0,
                    help="janela minima solicitada, 1..50 s (ROM sela 3000 frames)")
    ap.add_argument("--wait-seconds", type=float,
                    help="espera DAP, 90..1800 s (default 90; diagnostico de ROM lenta)")
    ap.add_argument("--out", default="worst_frame")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return self_check()
    if not args.rom or not os.path.isfile(args.rom):
        print("[FAIL_AMBIENTE] ROM obrigatoria e inexistente: %s" % args.rom)
        return 3
    code, _ = measure(args.rom, args.project, args.seconds, args.out,
                      args.wait_seconds)
    return code


if __name__ == "__main__":
    sys.exit(main())
