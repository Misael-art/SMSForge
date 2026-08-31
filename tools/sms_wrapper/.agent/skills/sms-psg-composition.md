# skill: sms-psg-composition

## Canais SN76489 (PSGlib)
- 3 tone (ch0,1,2) + 1 noise (ch3).
- Música: melodia (ch0), contraponto (ch1), baixo (ch2), percussão noise (ch3).
- SFX: arbitração explícita por canal no TDD (nunca competir com música no mesmo canal).

## Formato .psg (PSGlib)
- latches `>=0x80` (bit7=latch, bit4=volume, bit6=canais2-3, bit5=par/impar).
- dados `0x40-0x7F` (sem latch); `0x38`=fim de frame; `0x00`=loop; `0x01`=loopPoint.
- Gerar com probes/gen_music.py (formato confirmado), adicionar ao projeto como .h.

## Prova audível
- Gravar o monitor do Pulse (sink default) → audio_*.wav → benchmark de amostras ativas.
- Frameciche apenas via PSGFrame() por VBlank.
