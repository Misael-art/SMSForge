# skill: sms-pixel-strict-rules

## Regras de pixel SMS (VDP)
- Grid 8×8 imutável; padrão tile = 32 bytes (8 linhas × 4 bytes, 4bpp).
- Cor = código 6-bit (2 bits por canal). Paleta mestra fixa; ≤15 cores úteis por
  subpaleta (índice 0 transparente nas duas).
- Sprite 8×8/8×16 (modo global). 16×16 na tela = zoom (pixel dobrado) ou
  metasprite (4 tiles 8×8). Nenhum modo VDP é mais largo que 8 px (L006).
- Flip e subpaleta por tile EXISTEM no BG (entrada de name table 16-bit; §6,
  L069, probe `pnt_16bit`). Transparência só por índice 0.

## Antes de gerar
- Paleta do asset deve estar contida na paleta mestra (audit_validate_resources)
  e o contraste medido (audit_luma_floor).
- Foto/truecolor: `prepare_sms_pixel_art.py` (skill `sms-pixel-translate.md`).
  Sem preset NES/SNES/PICO-8 (L055).
