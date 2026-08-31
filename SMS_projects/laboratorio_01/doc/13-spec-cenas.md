# 13-spec-cenas — laboratorio_01

| Cena | Tiles BG únicos | Sprites simultâneos (pico/linha) | VRAM/frame VBlank (medido) | Áudio ativo | Status |
|------|-----------------|-----------------------------------|----------------------------|-------------|--------|
| boot_interativo | fonte do text renderer (~64 tiles) | 0 (BG) | ~32 bytes name table + paleta | blip ch2 | validado |
| sala do bloco | fonte + 1 tile bloco + 1 tile alvo (~66) | 0 (BG) | 42 bytes/frame (medido: 24 escritas VRAM) | blip ch2 + fanfarra | validado |
| cacador de sprites | fonte + hero sprite (8x8) | 2 sprites (jogador+alvo) | ~50 bytes/frame (2 sprites SAT+audio) | blip + fanfarra | implementado |

## Orçamento cena 02 (scene_budget_v1 — medição real pendente F5)
- bg_tiles_unique: 66 < 256 ✓
- sprite_peak_per_line: 0 ≤ 8 ✓
- vblank: ~40 bytes < 6KB janela NTSC ✓ (método: contagem de SMS_setTileatXY ×2 bytes, a medir com contador de ciclos F5)

| corredor estelar | fonte + estrelas + hero sprite | 4 sprites (1 jogador+3 inimigos) | ~60 bytes/frame | musica battle (PSGlib) | implementado |
