# skill: sms-vdp-budget-analyst

## Verdades
- VRAM 16KB (0x0000-0x3FFF). Layout fixo: BG patterns (14KB = 448 tiles),
  name table (32×28 entradas × 2B = 1792B, 0x3800+), SAT (64 sprites ×4B=256B),
  sprite patterns.
- Sem DMA: transferências em massa SÓ no VBlank (~4.5ms NTSC).
- Orçamento por cena = contrato (13-spec-cenas.md), medido não estimado.

## Tétas
- Tiles BG únicos ≤448 (entrada de name table é 16-bit; índices 0–447 — §6, L069).
- Sprites ≤64 na SAT; ≤8 por scanline.
- Worst-frame: contabilizar cada transferência; folga não medida = timidez (§18).
