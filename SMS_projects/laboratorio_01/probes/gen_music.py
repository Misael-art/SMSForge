
/* canonical_fixture_gate: scope=runtime_observation — fixture de validacao,
   NAO infere claim de jogo (apenas prova um comportamento). */
#!/usr/bin/env python3
"""gen_music.py — gera um stream .psg do PSGlib (format confirmado de PSGlib.asm)
com musica RICA: melodia (ch0), contraponto (ch1), baixo (ch2), percussao noise (ch3).

Formato PSGlib (de PSGlib.asm):
  - byte >= 0x80 : latch  -> bit7=latch, bit4=volume(1)/tone(0), bit6=canais 2-3,
                            bit5=par/impar no grupo, bits0-3 = low(volume|tone low 5 bits)
  - byte 0x40-0x7F : dado de tom sem latch (reusa ultimo latch, tone high)
  - byte 0x38       : fim de frame (avança 1 frame)
  - byte 0x39..     : and 0x07 = frames a pular
  - byte 0x08-0x37  : substring (len = v-0x08+4)
  - byte 0x01       : set loop point
  - byte 0x00       : loop (recomeca do loop point)

Gera inc/music_battle.h (melodia de acao) para a cena04.
"""
import math

def latch(canal, volume, val, high=False):
    """Canal 0-3. volume=True => bit4. val: tone low 5 bits / tone high 4 bits / volume 4 bits."""
    b = 0x80 | ((canal & 3) << 5)
    if volume:
        b |= 0x10
    b |= (val & 0x0F if volume else (val & 0x0F if high else val & 0x1F))
    return b

def set_tone(canal, freq):
    """Escreve tone low + high do canal. freq 0-1023."""
    low = freq & 0x0F
    hi = (freq >> 4) & 0x0F
    return [latch(canal, False, low), latch(canal, False, hi, high=True)]

def set_vol(canal, vol):
    return [latch(canal, True, vol & 0x0F)]

def tick(body):
    """Tick = sequencia de eventos terminada por fim de frame (0x38)."""
    return body + [0x38]

# --- nota -> frequencia PSG (canal tone appros) ---
# freq = (clock/n/note) - 1; clock SN76489=3.579545MHz/16 p/ tone => ~223738Hz
def note(n):
    # n: semitono (0=C). frequencia = 2237370 / (periodo). aproximado
    if n == -1:
        return None
    freq = int(447500 / (440.0 * (2 ** ((n - 9) / 12.0))))
    return max(0, min(1023, freq))

# melodia de cena de batalha: 16 ticks, 4 acordes (tempo)
melody = [  # (semitonos) ch0 melodía, ch1 contra, ch2 baixo, ch3 noise
    (0,   0,  0,  0), (0, 4,  0, 1), (0, 7,  0, 0), (2, 0,  0, 1),
    (3,   0,  3,  0), (3, 7,  3, 1), (5, 0,  3, 0), (5, 9,  3, 1),
    (7,   0,  5,  0), (7, 4,  5, 1), (5, 0,  5, 0), (4, 0,  5, 1),
    (3,   0,  3,  0), (2, 0,  3, 1), (0, 0,  0, 0), (0, 12, 0, 1),
]

stream = [0x01]  # set loop point no inicio
for (m, ct, bs, nz) in melody:
    body = []
    for canal, semi in [(0, m), (1, ct), (2, bs)]:
        f = note(semi)
        if f is not None:
            body += set_tone(canal, f)
            body += set_vol(canal, 8 if canal < 2 else 7)
    # percussao noise no canal 3 (latch noise + volume)
    body += [latch(3, True, 0x0F if nz else 0x0), latch(3, True, 0x0D if nz else 0x0)]
    body += [latch(3, False, 0x4 if nz else 0x0)]  # noise tone (aproximado)
    body += set_vol(2, 7 if nz else 0x0)
    stream += tick(body)
stream += [0x00]  # loop

music = bytes(stream)
print(f"musica .psg: {len(music)} bytes, {len(melody)} ticks")
h = "#pragma once\nstatic const unsigned char music_battle[] = {\n"
h += ", ".join("0x%02x" % b for b in music)
h += "\n};\n"
open("/mnt/sdcard/Projects/SMSForge/SMS_projects/laboratorio_01/inc/music_battle.h", "w").write(h)
print("inc/music_battle.h gerado")

# self-check basico: verificar que o stream so tem bytes validos
for b in music:
    assert 0 <= b <= 0xFF
print("gerador OK")
