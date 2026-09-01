#!/usr/bin/env python3
"""capture_audio.py — grava o audio DO EMULADOR, isolado do resto da maquina.

Antes deste gate o acervo tinha .wav sem procedencia: alguem gravou de algum
jeito, em algum momento, de alguma ROM. Nao dava para saber se o som era da
build citada — nem se era do emulador.

PRIVACIDADE (licao L017, agora no dominio do audio): gravar o *monitor* do sink
padrao capturaria TODO o audio da maquina — musica, chamadas, notificacoes.
Aqui o fluxo do emulador e movido para um sink NULO dedicado e so o monitor
desse sink e gravado. Nenhum outro aplicativo entra na captura. O sink e
removido no final, sempre (o audio do usuario volta ao normal).

Limite honesto (§28): o gate prova que HA som e que ele veio do emulador.
NAO prova que e a musica certa nas notas certas — isso exige ouvido humano ou
comparacao com referencia.

Uso:
  capture_audio.py --project <dir> --rom <rom.sms> [--seconds 6] [--out audio]
  capture_audio.py --self-check
Exit: 0 gravado | 1 falha/silencio | 2 ambiente ausente | 3 uso
"""
import sys, os, time, wave, shutil, argparse, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SINK = "smsforge_capture"
RATE = 44100

def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def _emulator_sink_inputs():
    """Indices dos fluxos de audio pertencentes ao emulador (java)."""
    r = _run(["pactl", "list", "sink-inputs"])
    out, idx, is_emu = [], None, False
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("Sink Input #"):
            if idx is not None and is_emu:
                out.append(idx)
            idx, is_emu = line.split("#")[1].strip(), False
        low = line.lower()
        if "java" in low or "emulicious" in low:
            is_emu = True
    if idx is not None and is_emu:
        out.append(idx)
    return out

def _peak(pcm_bytes):
    import array
    a = array.array("h")
    a.frombytes(pcm_bytes[: len(pcm_bytes) // 2 * 2])
    return max((abs(x) for x in a), default=0)

def write_wav(path, pcm_bytes, rate=RATE):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm_bytes)

def capture(project, rom, seconds=6, out_name="audio"):
    import capture_evidence as ce
    for t in ("pactl", "parec", "java"):
        if not shutil.which(t):
            print(f"[FAIL_AMBIENTE] ferramenta ausente: {t}")
            return 2
    jar = ce.resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado")
        return 2
    stale = _run(["pgrep", "-f", "Emulicious[.]jar"])
    if stale.returncode == 0 and stale.stdout.strip():
        print("[FAIL_AMBIENTE] ja existe Emulicious rodando; encerre antes "
              "(pkill -f 'Emulicious[.]jar')")
        return 2

    out_dir = os.path.join(project, "out", "evidence")
    os.makedirs(out_dir, exist_ok=True)
    wav_path = os.path.join(out_dir, f"{out_name}.wav")

    mod = _run(["pactl", "load-module", "module-null-sink",
                f"sink_name={SINK}", "sink_properties=device.description=SMSForge"])
    if mod.returncode != 0:
        print(f"[FAIL_AMBIENTE] nao foi possivel criar sink isolado: {mod.stderr[:120]}")
        return 2
    mod_id = mod.stdout.strip()
    proc = None
    try:
        proc = subprocess.Popen(["java", "-jar", jar, os.path.abspath(rom)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                                start_new_session=True)
        moved = []
        for _ in range(30):                       # espera o fluxo de audio nascer
            time.sleep(0.5)
            for si in _emulator_sink_inputs():
                if si not in moved and _run(["pactl", "move-sink-input", si,
                                             SINK]).returncode == 0:
                    moved.append(si)
            if moved:
                break
        if not moved:
            print("[FAIL] emulador nao produziu fluxo de audio para isolar")
            return 1
        # FALSO NEGATIVO CONHECIDO: gravar cedo demais (fluxo movido antes de a
        # musica entrar em regime) produz WAV 100% silencioso, indistinguivel de
        # "o jogo nao tem som". Isso quase levou a "consertar" um bug inexistente:
        # a ROM tinha audio e a captura e que estava adiantada. Por isso: warmup
        # crescente + repeticao enquanto o peak for zero.
        pcm = b""
        for attempt in range(3):
            time.sleep(1.5 + 2.0 * attempt)
            try:
                rec = subprocess.run(
                    ["parec", "-d", f"{SINK}.monitor", "--format=s16le",
                     f"--rate={RATE}", "--channels=1"],
                    capture_output=True, timeout=seconds + 5)
                pcm = rec.stdout
            except subprocess.TimeoutExpired as e:
                pcm = e.stdout or b""
            if len(pcm) >= RATE and _peak(pcm) > 0:
                break
            print(f"[retry] captura {attempt+1} veio silenciosa; "
                  "aumentando warmup (pode ser adiantamento, nao mudez)")
        if len(pcm) < RATE:                        # < 0.5s de audio
            print(f"[FAIL] captura vazia ({len(pcm)}B)")
            return 1
        if _peak(pcm) == 0:
            write_wav(wav_path, pcm)
            print(f"[FAIL] 3 capturas silenciosas: {wav_path}. Pode ser ROM muda "
                  "OU captura adiantada — confirme com uma ROM historica que "
                  "tenha som antes de mexer no codigo de audio.")
            return 1
        write_wav(wav_path, pcm)
        print(f"[OK] audio do EMULADOR gravado (isolado): {wav_path} "
              f"({len(pcm)//2} amostras, {len(pcm)/2/RATE:.1f}s)")
        return 0
    finally:
        if proc:
            proc.terminate()
        _run(["pactl", "unload-module", mod_id])   # devolve o audio do usuario

def _self_check():
    import tempfile, struct, math
    d = tempfile.mkdtemp(prefix="smsaud_")
    try:
        # WAV escrito por esta ferramenta e legivel pelo gate audit_audio
        import audit_audio
        pcm = b"".join(struct.pack("<h", int(12000 * math.sin(i / 8.0)))
                       for i in range(RATE))
        p = os.path.join(d, "t.wav")
        write_wav(p, pcm)
        st = audit_audio.read_wav_stats(p)
        assert st is not None, "audit_audio nao conseguiu ler o WAV gerado"
        n, peak, active = st
        assert n == RATE, f"amostras erradas: {n}"
        assert peak > 10000, f"peak inesperado: {peak}"
        assert active > 90, f"tom continuo deveria ser ~100% ativo: {active}"
        # silencio tem que ser detectavel como tal
        ps = os.path.join(d, "s.wav")
        write_wav(ps, b"\x00\x00" * RATE)
        n2, peak2, active2 = audit_audio.read_wav_stats(ps)
        assert peak2 == 0 and active2 == 0, "silencio deveria dar peak/active 0"
        # deteccao de fluxo do emulador nao inventa resultado sem emulador
        assert isinstance(_emulator_sink_inputs(), list)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] capture_audio (WAV gerado e legivel pelo audit_audio; "
          "tom ativo e silencio distinguidos)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--rom")
    ap.add_argument("--seconds", type=int, default=6)
    ap.add_argument("--out", default="audio")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    if not (a.project and a.rom):
        print("[FAIL] --project e --rom obrigatorios", file=sys.stderr)
        return 3
    return capture(a.project, a.rom, a.seconds, a.out)

if __name__ == "__main__":
    sys.exit(main())
