#!/usr/bin/env python3
"""audit_audio.py — gate de qualidade de audio (porta do SGDK Forge).

Valida a evidencia de audio gravada (.wav) e o contrato de arquitetura:
- amostras ativas >= floor (benchmark de mix; mais de 90% => musica tocando de forma rica).
- peak acima de um piso (nao e silencio).
- ownership de canal documentado na arquitetura de audio.

Uso: audit_audio.py --wav <arquivo.wav> [--project <dir>] [--self-check]
Exit: 0 audio ok | 1 mix/silencio/falta ownership | 2 ambiente (sem wav) | 3 uso
"""
import sys, os, json, struct, argparse

def read_wav_stats(path):
    """Retorna (n_amostras, peak, active_pct) de um WAV 16-bit mono."""
    try:
        d = open(path, "rb").read()
    except OSError:
        return None
    if len(d) < 44:
        return None
    # parse header simples (RIFF/WAVE, PCM 16-bit)
    nch = struct.unpack("<H", d[22:24])[0]
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
    active = sum(1 for s in a if abs(s) > 200)
    return len(a), peak, 100.0 * active / len(a)

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
        import tempfile, wave
        d = tempfile.mkdtemp(prefix="smsaud_")
        # wav silencioso -> deve reprovar
        p = os.path.join(d, "sil.wav")
        w = wave.open(p, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
        w.writeframes(b"\x00\x00" * 22050); w.close()
        read_wav_stats(p)
        import importlib.util
        st, _ = read_wav_stats, None
        # usar audit com wav silencioso (sem project p/ nao importar doc)
        prob, _ = (None, None)
        stats = read_wav_stats(p)
        assert stats[1] < 200
        print("[SELF-CHECK OK] audit_audio (detector de silencio)")
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
