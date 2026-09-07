#!/usr/bin/env python3
"""Compoe o tema do cenario do Ken e emite o fluxo PSGlib nativo.

Composicao ORIGINAL (nao e transcricao de trilha comercial): groove de luta
em La menor natural com G# emprestado da menor harmonica na cadencia, no
espirito "porto japones ao entardecer" — motor ritmico constante, lead
recortado, arpejo rapido como enchimento de compasso.

O alvo e o SN76489 do Master System via PSGlib. O fluxo e literalmente a
sequencia de bytes que o PSGFrame despeja na porta 0x7F, com os comandos da
lib intercalados:

    0x00        PSGEnd  (a lib volta sozinha ao inicio -> loop infinito)
    0x01        PSGLoop (marca ponto de loop)
    0x08..0x37  substring (nao usado aqui)
    0x38..0x3F  espera 1 + (byte & 7) frames

Economia de ROM (o cartucho tem ~1 KB livre) vem de duas regras:
  1. so se escreve registrador que MUDOU no frame;
  2. esperas sempre usam o maximo de 8 frames por byte.

Uso:
  python3 tools/gen_music_ken_stage.py --emit      # grava inc/music_battle.h
  python3 tools/gen_music_ken_stage.py --wav a.wav # render local p/ audicao
  python3 tools/gen_music_ken_stage.py --self-check
"""
import argparse
import os
import sys

PSG_CLOCK = 3579545
FPS = 60
WAIT = 0x38
END = 0x00

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)

# --- grade ritmica -------------------------------------------------------
# 150 BPM, semicolcheia = 6 frames NTSC. Compasso 4/4 = 16 linhas = 96 frames.
ROW_FRAMES = 6
ROWS_PER_BAR = 16

NOTES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6,
         "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def midi(name):
    """'A4' -> numero MIDI. Aceita sustenido: 'G#3'."""
    octv = int(name[-1])
    return NOTES[name[:-1]] + (octv + 1) * 12


def period(name):
    """Numero MIDI -> divisor de 10 bits do SN76489 (f = clk / (32*div))."""
    freq = 440.0 * 2 ** ((midi(name) - 69) / 12.0)
    div = int(round(PSG_CLOCK / (32.0 * freq)))
    return max(1, min(1023, div))


# --- material musical ----------------------------------------------------
# Oito compassos; a harmonia sustenta a cadencia menor com G# no compasso 8.
CHORDS = [  # (raiz do baixo, tres notas do arpejo)
    ("A2", ("A3", "C4", "E4")),
    ("A2", ("A3", "C4", "E4")),
    ("F2", ("F3", "A3", "C4")),
    ("G2", ("G3", "B3", "D4")),
    ("A2", ("A3", "C4", "E4")),
    ("F2", ("F3", "A3", "C4")),
    ("D2", ("D3", "F3", "A3")),
    ("E2", ("E3", "G#3", "B3")),
]

# Lead (canal 0). Por compasso: lista de (linha, nota, duracao_em_linhas).
# Frases recortadas de 8 tempos, com resposta descendente nos compassos pares.
LEAD = [
    [(0, "A4", 3), (3, "C5", 1), (4, "B4", 2), (6, "A4", 2),
     (8, "E4", 3), (11, "G4", 1), (12, "A4", 4)],
    [(0, "C5", 2), (2, "B4", 2), (4, "A4", 2), (6, "G4", 2),
     (8, "A4", 3), (11, "E4", 1), (12, "D4", 4)],
    [(0, "F4", 3), (3, "A4", 1), (4, "C5", 4),
     (8, "B4", 2), (10, "A4", 2), (12, "G4", 4)],
    [(0, "G4", 2), (2, "B4", 2), (4, "D5", 4),
     (8, "C5", 2), (10, "B4", 2), (12, "A4", 4)],
    [(0, "A4", 3), (3, "C5", 1), (4, "E5", 2), (6, "D5", 2),
     (8, "C5", 3), (11, "B4", 1), (12, "A4", 4)],
    [(0, "C5", 2), (2, "A4", 2), (4, "F4", 4),
     (8, "G4", 2), (10, "A4", 2), (12, "C5", 4)],
    [(0, "D5", 4), (4, "C5", 2), (6, "A4", 2),
     (8, "F4", 3), (11, "A4", 1), (12, "D4", 4)],
    [(0, "E4", 2), (2, "G#4", 2), (4, "B4", 2), (6, "E5", 2),
     (8, "D5", 2), (10, "B4", 2), (12, "G#4", 4)],
]

# Compassos que trocam a harmonia sustentada por arpejo rapido (enchimento).
ARP_BARS = {3, 7}

# Atenuacao do SN76489: 0 = maximo, 15 = mudo. Os valores sao baixos de
# proposito. Com lead=2/baixo=3 o gate audit_audio media 89% de amostras
# ativas — nao por haver silencio (a captura tem uma unica lacuna, de 11 ms),
# mas porque a soma das quadradas saia fraca demais e os cruzamentos por zero
# caiam sob o piso de 200. A correcao e no PSG, nao no WAV.
VOL_LEAD = 1
VOL_HARM = 5
VOL_BASS = 2
VOL_PERC = 3

CH_BASE = (0x80, 0xA0, 0xC0)


def tone_bytes(ch, div):
    """Latch de tom: byte alto precisa de 0x40 para nao virar comando PSGlib."""
    return [CH_BASE[ch] | (div & 0x0F), 0x40 | ((div >> 4) & 0x3F)]


def vol_byte(ch, v):
    return (CH_BASE[ch] + 0x10) | (v & 0x0F)


def noise_bytes(mode):
    return [0xE0 | (mode & 7)]


def noise_vol(v):
    return [0xF0 | (v & 0x0F)]


def compose():
    """Devolve {frame: [bytes]} — eventos de registrador na linha do tempo."""
    ev = {}

    def put(frame, data):
        ev.setdefault(frame, []).extend(data)

    for bar, (bass_root, arp) in enumerate(CHORDS):
        bar0 = bar * ROWS_PER_BAR * ROW_FRAMES

        # canal 0: lead
        for row, note, _dur in LEAD[bar]:
            f = bar0 + row * ROW_FRAMES
            put(f, tone_bytes(0, period(note)) + [vol_byte(0, VOL_LEAD)])
            # decaimento curto: da ataque sem gastar frame extra de espera
            put(f + 3, [vol_byte(0, VOL_LEAD + 2)])

        # canal 1: arpejo rapido nos compassos de virada, terca sustentada nos demais
        if bar in ARP_BARS:
            for row in range(ROWS_PER_BAR):
                f = bar0 + row * ROW_FRAMES
                put(f, tone_bytes(1, period(arp[row % 3])) + [vol_byte(1, VOL_HARM)])
        else:
            for half in (0, 8):
                f = bar0 + half * ROW_FRAMES
                put(f, tone_bytes(1, period(arp[1])) + [vol_byte(1, VOL_HARM)])

        # canal 2: baixo motor em colcheias, com oitava no contratempo
        oct_up = bass_root[:-1] + str(int(bass_root[-1]) + 1)
        for i in range(8):
            f = bar0 + i * 2 * ROW_FRAMES
            note = oct_up if i in (3, 7) else bass_root
            put(f, tone_bytes(2, period(note)) + [vol_byte(2, VOL_BASS)])

        # canal 3: ruido — bumbo nos tempos 1 e 3, caixa em 2 e 4, chimbal nas colcheias
        for i in range(8):
            f = bar0 + i * 2 * ROW_FRAMES
            if i in (0, 4):
                put(f, noise_bytes(0x06) + noise_vol(VOL_PERC))
                put(f + 4, noise_vol(15))
            elif i in (2, 6):
                put(f, noise_bytes(0x04) + noise_vol(VOL_PERC))
                put(f + 5, noise_vol(15))
            else:
                put(f, noise_bytes(0x03) + noise_vol(VOL_PERC + 5))
                put(f + 2, noise_vol(15))

    return ev


def build_stream(ev, total_frames):
    """Serializa eventos + esperas no formato PSGlib."""
    out = bytearray()
    pending = 0

    def flush_wait():
        nonlocal pending
        while pending > 0:
            n = min(8, pending)
            out.append(WAIT | (n - 1))
            pending -= n

    for f in range(total_frames):
        if f in ev:
            flush_wait()
            out.extend(ev[f])
        pending += 1
    flush_wait()
    out.append(END)
    return bytes(out)


def make():
    ev = compose()
    total = len(CHORDS) * ROWS_PER_BAR * ROW_FRAMES
    return build_stream(ev, total), total


# --- render local (SN76489 em numpy), para audicao sem hardware ----------
def render_wav(path, data, rate=44100):
    import numpy as np
    import wave

    tone_div = [1, 1, 1]
    vol = [15, 15, 15, 15]
    noise_mode = 0
    chunks = []
    phase = [0.0, 0.0, 0.0]
    lfsr_phase = 0.0
    rng = np.random.default_rng(7)

    def amp(v):
        return 0.0 if v >= 15 else 0.25 * (10 ** (-2.0 * v / 20.0))

    i = 0
    while i < len(data):
        b = data[i]
        if b == END:
            break
        if WAIT <= b <= 0x3F:
            frames = (b & 7) + 1
            n = int(rate * frames / FPS)
            t = np.arange(n)
            buf = np.zeros(n)
            for ch in range(3):
                f = PSG_CLOCK / (32.0 * max(1, tone_div[ch]))
                ph = phase[ch] + t * f / rate
                buf += amp(vol[ch]) * np.sign(np.sin(2 * np.pi * ph))
                phase[ch] = (ph[-1] + f / rate) % 1.0 if n else phase[ch]
            if vol[3] < 15:
                shift = (0x10, 0x20, 0x40, 0x80)[noise_mode & 3]
                nf = PSG_CLOCK / (32.0 * shift)
                step = max(1, int(rate / nf))
                src = rng.choice((-1.0, 1.0), size=n // step + 1)
                buf += amp(vol[3]) * np.repeat(src, step)[:n]
            chunks.append(buf)
            i += 1
            continue
        if b & 0x80:
            ch = (b >> 5) & 3
            if b & 0x10:
                vol[ch] = b & 0x0F
                i += 1
            elif ch == 3:
                noise_mode = b & 3
                i += 1
            else:
                low = b & 0x0F
                high = data[i + 1] & 0x3F
                tone_div[ch] = (high << 4) | low
                i += 2
            continue
        i += 1

    sig = np.concatenate(chunks) if chunks else np.zeros(1)
    peak = np.max(np.abs(sig)) or 1.0
    pcm = (sig / peak * 0.85 * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return len(pcm) / rate


def write_header(path, symbol, data):
    with open(path, "w", encoding="utf-8") as f:
        f.write("/* gerado por tools/gen_music_ken_stage.py; fluxo PSGlib.\n"
                " * Tema ORIGINAL do cenario do Ken: La menor, 150 BPM, 8 compassos,\n"
                " * 4 canais (lead / harmonia-arpejo / baixo / percussao de ruido).\n"
                " * NAO editar a mao — regenerar pelo script. */\n")
        f.write(f"#define {symbol.upper()}_SIZE {len(data)}\n")
        f.write(f"static const unsigned char {symbol}[{len(data)}] = {{\n")
        for i in range(0, len(data), 16):
            f.write(",".join(f"0x{b:02X}" for b in data[i:i + 16]) + ",\n")
        f.write("};\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--wav")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    data, total = make()

    if args.self_check:
        assert data[-1] == END, "fluxo precisa terminar em PSGEnd"
        assert END not in data[:-1], "PSGEnd prematuro no meio do fluxo"
        # nenhum byte de dado pode cair na faixa de comando 0x01..0x37
        i, seen = 0, 0
        while i < len(data) - 1:
            b = data[i]
            if WAIT <= b <= 0x3F:
                seen += (b & 7) + 1
                i += 1
            elif b & 0x80 and not (b & 0x10) and ((b >> 5) & 3) != 3:
                assert data[i + 1] >= 0x40, f"byte alto sem 0x40 em {i}"
                i += 2
            else:
                assert b >= 0x80, f"byte de dado invadiu faixa de comando: 0x{b:02X}@{i}"
                i += 1
        assert seen == total, f"frames somam {seen}, esperado {total}"
        print(f"[SELF-CHECK OK] gen_music_ken_stage: {len(data)} B, "
              f"{total} frames ({total / FPS:.1f}s)")
        return 0

    print(f"stream: {len(data)} bytes, {total} frames = {total / FPS:.2f}s")
    if args.wav:
        dur = render_wav(args.wav, data)
        print(f"wav: {args.wav} ({dur:.2f}s)")
    if args.emit:
        out = os.path.join(PROJ, "inc", "music_battle.h")
        write_header(out, "music_battle", data)
        raw = os.path.join(PROJ, "res", "audio")
        os.makedirs(raw, exist_ok=True)
        with open(os.path.join(raw, "music_ken_stage.psg"), "wb") as f:
            f.write(data)
        print(f"emit: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
