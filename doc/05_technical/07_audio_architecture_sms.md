# Arquitetura de áudio — Master System (PSG + YM2413 opcional)

> Adaptada de `99_aaa_audio_architecture_guide.md` do SGDK Forge (Mega Drive) para
> o chip de som do Master System. PSG SN76489 (3 tone + noise) é o único obrigatório;
> YM2413 (FM) é opcional (JP/SMS com unidade FM) — o jogo SEMPRE roda sem FM.

## 1. Ownership de canal (não-negociável)

| Canal | Função padrão | Conflito permitido? |
|-------|---------------|---------------------|
| ch0 (tone) | melodia principal | SFX só se a música ceder |
| ch1 (tone) | contraponto / harmonia | — |
| ch2 (tone) | baixo / ostinato | — |
| ch3 (noise) | percussão | SFX de impacto |

- **BGM** usa os canais conforme tabela; **SFX** tem canal reservado (por projeto)
  ou arbitração explícita no TDD. Nunca dois sons disputam o mesmo canal sem regra.

## 2. Composição e formato
- Música é um **stream .psg** (PSGlib): byte `>=0x80`=latch, `0x40-0x7F`=dado sem
  latch, `0x38`=fim de frame, `0x00`=loop, `0x01`=loopPoint.
- Gerador: `probes/gen_music.py` → `inc/music_*.h`. Tocar com `PSGPlay` + `PSGFrame()`
  por VBlank.
- Benchmark de mix: cada canal em `default_senior` quando o .psg tem melodia+baixo+
  percussão e a gravação atinge ≥90% de amostras ativas.

## 3. Orçamento no frame
- `PSGFrame()` é barato, mas áudio concorre com VRAM no worst-frame de VBlank.
  Medir junto (runtime_metrics.audio) — nunca assumir que áudio é grátis.

## 4. Evidência audível (obrigatória antes do claim)
- Gravar o monitor do Pulse (sink default, ver L013: `.asoundrc` ALSA→Pulse).
- `audio_*.wav` → benchmark: `audio_active_pct` e `peak`. Se <90% ativo → revisar mix.

## 5. Proibições
- Depender de YM2413 para funcionalidade (controles de gameplay).
- Volume 100% constante em todos os canais (confusão de mix).
- SFX no canal da melodia sem cessão explícita.
