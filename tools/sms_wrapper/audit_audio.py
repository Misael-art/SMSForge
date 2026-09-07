#!/usr/bin/env python3
"""audit_audio.py — gate de qualidade de audio (porta do SGDK Forge).

Valida a evidencia de audio gravada (.wav) e o contrato de arquitetura:
- energia ativa >= floor (benchmark de mix; mais de 90% => som presente quase o tempo todo).
- peak acima de um piso (nao e silencio).

A atividade e medida por RMS em janelas de 10 ms, nao amostra a amostra. A
versao antiga contava |amostra| > 200 isoladamente, e isso nao media presenca
de som: media o quanto a onda era CONTINUA. Toda onda periodica cruza o zero,
e cada cruzamento entrava na conta como amostra "inativa" — entao quanto mais
rica a polifonia, PIOR a nota. Na pratica um drone de quatro canais em
unissono (um cruzamento de zero por segundo) marcava 99,9%, enquanto um tema
de verdade em quatro vozes independentes (2062 cruzamentos por segundo, sem
nenhuma lacuna de silencio) reprovava com 88%. A janela de energia mantem o
poder de pegar mudez real — WAV silencioso continua dando 0% — sem punir
arranjo.
- ownership de canal documentado na arquitetura de audio.

Uso: audit_audio.py --wav <arquivo.wav> [--project <dir>] [--self-check]
Exit: 0 audio ok | 1 mix/silencio/falta ownership | 2 ambiente (sem wav) | 3 uso
"""
import sys, os, json, struct, argparse

WINDOW_MS = 10       # janela de energia; ~1 frame NTSC de musica
ACTIVE_RMS = 200     # mesmo piso de antes, agora aplicado ao RMS da janela


def read_wav_stats(path):
    """Retorna (n_amostras, peak, active_pct) de um WAV PCM 16-bit."""
    try:
        d = open(path, "rb").read()
    except OSError:
        return None
    if len(d) < 44:
        return None
    # parse header simples (RIFF/WAVE, PCM 16-bit)
    nch = struct.unpack("<H", d[22:24])[0] or 1
    rate = struct.unpack("<I", d[24:28])[0] or 44100
    bits = struct.unpack("<H", d[34:36])[0]
    n = struct.unpack("<I", d[40:44])[0]
    data = d[44:44 + n]
    if bits != 16:
        return None
    import array
    a = array.array("h")
    a.frombytes(data[: len(data) // 2 * 2])
    if not a:
        return None
    peak = max(abs(s) for s in a)

    # RMS por janela de WINDOW_MS. A janela cobre todos os canais juntos: para
    # o gate importa haver som, nao de qual lado ele vem.
    win = max(1, int(rate * WINDOW_MS / 1000) * nch)
    nwin = len(a) // win
    if nwin == 0:                      # wav mais curto que uma janela
        win, nwin = len(a), 1
    active = 0
    for w in range(nwin):
        block = a[w * win:(w + 1) * win]
        if (sum(s * s for s in block) / len(block)) ** 0.5 > ACTIVE_RMS:
            active += 1
    return len(a), peak, 100.0 * active / nwin

def audit(wav_path, project, active_floor=90.0):
    stats = read_wav_stats(wav_path)
    if stats is None:
        return ["wav ilegivel ou vazio (nao e PCM 16-bit mono)"], stats
    n, peak, pct = stats
    problems = []
    if peak < 200:
        problems.append(f"silencio: peak={peak} < 200")
    if pct < active_floor:
        problems.append(f"mix fraco: {pct:.0f}% ativo < {active_floor:.0f}% (revisar mix/canais)")
    # ownership documentado? (projeto ou workspace raiz)
    doc = os.path.join(project, "doc", "05_technical", "07_audio_architecture_sms.md")
    if not os.path.exists(doc):
        doc = os.path.join(os.path.dirname(__file__), "..", "..", "doc",
                           "05_technical", "07_audio_architecture_sms.md")
    if not os.path.exists(doc):
        problems.append("arquitetura de audio ausente (ownership de canal nao documentado)")
    return problems, stats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav")
    ap.add_argument("--project", default=".")
    ap.add_argument("--active-floor", type=float, default=90.0)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        import tempfile, wave, math, struct as _st
        d = tempfile.mkdtemp(prefix="smsaud_")
        RATE = 22050

        def write(name, samples):
            p = os.path.join(d, name)
            w = wave.open(p, "wb")
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
            w.writeframes(b"".join(_st.pack("<h", int(s)) for s in samples))
            w.close()
            return p

        # 1) silencio continua reprovando
        stats = read_wav_stats(write("sil.wav", [0] * RATE))
        assert stats[1] < 200, "silencio deveria dar peak abaixo do piso"
        assert stats[2] == 0.0, f"silencio deveria dar 0% ativo, deu {stats[2]}"

        # 2) o caso que motivou a correcao: onda periodica de verdade. Cruza o
        #    zero 880 vezes por segundo, entao a metrica antiga (por amostra)
        #    a reprovava; por energia ela passa, porque som HA o tempo todo.
        tone = [6000 * math.sin(2 * math.pi * 440 * i / RATE) for i in range(RATE)]
        stats = read_wav_stats(write("tom.wav", tone))
        antiga = 100.0 * sum(1 for s in tone if abs(s) > 200) / len(tone)
        assert stats[2] == 100.0, f"tom continuo deveria dar 100% ativo, deu {stats[2]}"
        assert antiga < 100.0, "o teste perde o sentido se a metrica antiga tambem desse 100%"

        # 3) metade som, metade mudo -> ~50%, o gate ainda enxerga lacuna
        stats = read_wav_stats(write("meio.wav", tone[:RATE // 2] + [0] * (RATE // 2)))
        assert 45.0 <= stats[2] <= 55.0, f"meio-a-meio deveria dar ~50%, deu {stats[2]}"

        print("[SELF-CHECK OK] audit_audio (energia em janela: silencio 0%, "
              f"tom continuo 100%, lacuna detectada; metrica antiga dava {antiga:.0f}% no tom)")
        return 0
    if not args.wav:
        print("[FAIL] --wav obrigatorio", file=sys.stderr)
        return 3
    problems, stats = audit(args.wav, args.project, args.active_floor)
    if stats:
        print(f"wav: {stats[0]} amostras, peak={stats[1]}, ativo={stats[2]:.0f}%")
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print("[PASS] audio com mix e ownership ok")
    return 0

if __name__ == "__main__":
    sys.exit(main())
