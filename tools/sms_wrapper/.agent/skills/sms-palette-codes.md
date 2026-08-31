# skill: sms-palette-codes

## Contrato
- Cor = código 6-bit (canais 0..3). Assets usam canal×85 = {0,85,170,255}.
- 2 subpaletas ×16; índice 0 transparente nas duas; ≤15 úteis cada.
- Fade = recarga de paleta no VBlank (`SMS_loadBGPaletteHalfBrightness` etc. — ver header).

## Regras
1. Nenhuma cor fora dos códigos (gate reprova).
2. Par fg/bg precisa Δluma ≥ piso (`audit_luma_floor.py`).
3. RGB físico exato varia por revisão — contratos usam CÓDIGOS, nunca adjetivos.
