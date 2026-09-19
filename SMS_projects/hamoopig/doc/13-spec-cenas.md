# 13-spec-cenas — hamoopig

> Autoridade #3. "estimado" é proibido. Números abaixo sem método = **não medidos**.

## Contrato de hardware (fixo)
| Recurso | Limite físico | Fonte |
|---------|---------------|-------|
| Tela | 256×192 | SMS_GLOBAL §6 / VDP |
| VRAM | 16 KB | SMS_GLOBAL |
| RAM | 8 KB | `--data-loc 0xC000` |
| Sprites/scanline | 8 | SMS_GLOBAL §7 |
| SAT | 64 | SMS_GLOBAL §7 |
| Subpaletas | 2×16, índice 0 transparente | §8 |
| VBlank | ~4.5 ms NTSC, sem DMA | §9 |
| ROM linear | 48 KB | B01 |

## Cena TITLE / OPENING
### Layout de VRAM declarado
| Região | Faixa | Uso |
|--------|-------|-----|
| BG | 1–41 | fonte |
| SAT | vazia | sem sprites |

### Orçamento worst-frame
Ainda **não medido**. Método previsto: `measure_worst_frame.py` + probe `vline`.

## Cena FIGHT (arena técnica)
### Layout de VRAM
| Região | Faixa | Uso |
|--------|-------|-----|
| BG fonte/HUD | 1–51 | texto, chão, barras |
| sprites | 128–191 | 2 lutadores × 2 poses × 2 direções |
| SAT | 8 sprites | 4+4 TALL |

### Sprites por scanline (pico declarado, não simulado ainda)
8 quando os dois lutadores compartilham linhas. Manifesto de simulação pendente.

### fps / worst-frame
fps do loop (probe, SHA `7a8951ee…`): janela 1 = 58.2; janela 2 = 28.12 (não constante).
Worst-frame (`worst_frame.json`, 20 s): **derramou**, vovf_delta=597, vline_max=255. Folga zero.
