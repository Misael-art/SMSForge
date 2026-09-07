# skill: sms-psg-audio

## Verdades
- SN76489: 3 canais de tone + 1 de noise. PSGlib = driver padrão
  (`PSGPlay`, `PSGSetBackgroundVolume`… — CONFIRMAR no header antes de usar).
- Arbitração música × SFX declarada no TDD (4 canais só).
- SFX toca no canal **autorado** no manifesto
  (`doc/audio_provenance_manifest.json`). Canal errado derruba o mix;
  cooldown não recupera (L041). Gate: `audit_psg_channel_binding.py`.
- Samples PSG comprimidos custam ROM e timing — medir.
- PSGlib faz loop no `PSGEnd`. N cópias do mesmo frame não tocam nada
  extra. Meça redundância antes de cortar feature (L051).
  Gate: `audit_psg_redundancy.py`.
- YM2413 (FM unit/JP): opcional. Jogo precisa funcionar sem FM, sempre.
- Atualização de áudio entra no orçamento do frame junto com VRAM.
