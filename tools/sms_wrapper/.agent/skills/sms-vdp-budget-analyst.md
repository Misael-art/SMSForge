# skill: sms-vdp-budget-analyst

## Verdades
- VRAM 16KB (0x0000-0x3FFF). Layout fixo: BG patterns, name table (32×28=896B),
  SAT (64 sprites ×4B=256B), sprite patterns.
- Sem DMA: transferências em massa SÓ no VBlank (~4.5ms NTSC).
- Orçamento por cena = contrato (13-spec-cenas.md), medido não estimado.

## Tétas
- Tiles BG únicos ≤256 (name table 1 byte → index 0-255).
- Sprites ≤64 na SAT; ≤8 por scanline.
- Worst-frame: contabilizar cada transferência; folga não medida = timidez (§18).
