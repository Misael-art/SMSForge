# 13-spec-cenas — MSSF2T

> Autoridade #3. "estimado" é proibido depois da primeira ROM. Até lá, números
> abaixo são **declarados** (não `validado_budget`) e o degrau seguinte é medir.

## Contrato de hardware
| Recurso | Limite |
|---------|--------|
| Tela | 256×192 |
| Sprites/scanline | 8 |
| SAT | 64 |
| Subpaletas | 2×16 |
| VBlank | ~4.5 ms, sem DMA |
| ROM linear | 48 KB |

## Cena 01 — golden_fight (Ken vs Guile, cais)
### Layout de VRAM declarado
| Região | Faixa | Uso |
|--------|-------|-----|
| BG 0–95 | palco + HUD |
| SPR 128–199 | lutadores + projéteis |
| name table | 32×24 |
| SAT | ≤48 entradas típicas (tiles vazios omitidos) |

### Orçamento worst-frame (DECLARADO — a medir na ROM)
| Item | Bytes/frame | Método |
|------|-------------|--------|
| Stream de frame (só na troca) | ≤1024 | 32 tiles × 32 B, um lutador |
| SAT copy | 256 | SMSlib |
| Name table HUD (3 linhas) | 192 | SMS_setTileatXY |

- **Total worst-frame**: não medido em ROM (status: documentado)
- **Degrau seguinte**: `measure_runtime_probe.py` + contagem de `SMS_loadTiles` na troca de pose

### Sprites por scanline
Contrato: ≤4 por lutador na mesma linha; no clash descarta coluna de trás.
Manifest: `doc/sprite_scene_golden.json`. Gate: `audit_sprite_line_sim.py`.

### fps
A medir com `measure_frame_advance.py` após a primeira ROM.
