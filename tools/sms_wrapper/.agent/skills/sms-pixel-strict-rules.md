# skill: sms-pixel-strict-rules

## Regras de pixel SMS (VDP)
- Grid 8×8 imutável; padrão tile = 16 bytes (8 linhas × 2 planos).
- Cor = código 6-bit (2 bits por canal). Paleta mestra fixa; ≤15 cores úteis por
  subpaleta (índice 0 transparente nas duas).
- Sprite 8×8/16×16 (modo global); 16×16 = 4 tiles sequenciais (ou metasprite 8×8).
- Sem flip/paleta por tile no BG (name table 1 byte). Transparência só por índice 0.

## Antes de gerar
- Paleta do asset deve estar contida na paleta mestra (audit_validate_resources)
  e o contraste medido (audit_luma_floor).
