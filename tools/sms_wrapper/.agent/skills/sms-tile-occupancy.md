# skill: sms-tile-occupancy

## Conceito
Quantos tiles 8×8 únicos uma cena ocupa na VRAM (sem deduplicação H/V flip, que
não existe no SMS — a dedup é só por valor igual).

## Método
- Contar tiles únicos de todos os assets de BG da cena.
- Alocar 1 slot por tile único; index ≤255 no name table.
- Degradar a cena se estourar (nunca estourar o orçamento).

## Gate
- audit_validate_resources (grid 8×8) + contagem manual no spec de cenas.
