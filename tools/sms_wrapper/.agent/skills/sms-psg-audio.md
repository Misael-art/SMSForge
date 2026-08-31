# skill: sms-psg-audio

## Verdades
- SN76489: 3 canais de tone + 1 de noise. PSGlib = driver padrão
  (`PSGPlay`, `PSGSetBackgroundVolume`… — CONFIRMAR no header antes de usar).
- Arbitração música × SFX declarada no TDD (4 canais só).
- Samples PSG comprimidos custam ROM e timing — medir.
- YM2413 (FM unit/JP): opcional. Jogo precisa funcionar sem FM, sempre.
- Atualização de áudio entra no orçamento do frame junto com VRAM.
