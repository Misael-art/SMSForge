# skill: sms-vdp-tiles

## Verdades duras
- Grid 8×8; pattern table 32 bytes/tile; **máx 256 tiles BG** (name table é 1 byte/tile).
- Sem flip/paleta por tile no BG. Variação visual = tiles distintos, metatiles, ou paleta trocada.
- Name table 32 colunas; linhas visíveis por modo (192/224/240).
- Scroll global X/Y; split exige line interrupt (técnica medida).

## Checklist de cena
1. Storyboard em grid 8×8 ANTES de arte.
2. Contagem de tiles únicos ≤256 (metatile 16×16 quando passar).
3. Layout VRAM fixo declarado no TDD antes do primeiro asset.

## Ferramentas
- `audit_validate_resources.py --kind bg` (grid/cor/índice0)
