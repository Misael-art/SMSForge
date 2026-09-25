# 13-spec-cenas — luta_mugen

> Budget REAL por cena. **Autoridade #3.**
> Regra: **"estimado" é proibido neste arquivo.** Todo número aqui é medido,
> com o método da medição citado. Folga não medida é timidez (§18).

## Contrato de hardware (fixo, não negociável)
| Recurso | Limite físico |
|---------|---------------|
| Tela | 256×192 |
| VRAM | 16 KB |
| RAM | 8 KB |
| Sprites por scanline | 8 |
| Sprites na SAT | 64 |
| Subpaletas | 2 × 16 (índice 0 transparente nas duas) |
| Cores úteis simultâneas | 30 |
| Janela VBlank | ~4.5 ms (NTSC) — **não existe DMA** |
| ROM sem mapper | 48 KB |

## Cena 01 — `probe_import` (fixture sintético `mini`; ROM 16 KB)

Estado operacional: **testado_em_emulador** — evidência `out/evidence/cena01_probe.png`
(variancia janela 5347.5 / viewport 818.2, `capture_evidence.py` PASS), boot
determinístico 2 execuções idênticas (`audit_deterministic_boot.py` PASS), arte
confirmada 100% (`audit_render_fidelity.py` PASS em [90,131]).

### Leis de hardware MEDIDAS nesta cena (não assumidas)
| Contratos | Medição |
|-----------|---------|
| Par TALL `(pattern, pattern+1)` = (topo, base) | probe 8×16 metade branca(idx1)/preta(idx2): captura do phase 0..3 s mostrou **branco em cima** — `pack_tiles_tall` confirmado, sem inversão |
| `SMS_addMetaSprite` origem y = 1ª linha visível do topo | ego passado y=112 ocupa linhas 112..127 na captura |
| `SMS_useFirstHalfTilesforSprites(1)` + `SPRITEMODE_TALL` | poses renderizam limpas (sem ruido) — L006 não disparou |
| espelho-h como OUTRO padrão (sem flip no SMS) | METAL carregado e renderizado no oponente (x=152..167) |

### Layout de VRAM declarado
| Região | Faixa | Tiles | Uso |
|--------|-------|-------|-----|
| patterns BG | 12 (64 B) + 14 (32 B) | 3 | rodapé cinza + vazio |
| patterns sprite | 0..11 e 12..13 (3 pools de 64 B + probe) | 9 tiles = 288 B | 3 poses com espelho |
| name table | 32×24 = 768 B escritos no boot | — | céu vazio + chão linha 16 |
| SAT | 8 entradas de 64 | — | 4 colunas TALL × 2 meias-linhas |

### Orçamento worst-frame (MEDIDO)
| Item | Bytes/frame | Método da medição |
|------|-------------|-------------------|
| cópia SAT (8 entradas × 2 B) | 16 B | contagem estática do loop de frame (`SMS_copySpritestoSAT`), confirmada por capture |
| name table por frame | 0 B | NT escrita só no boot (código lido) |
| tiles por frame | 0 B | streaming é Task 6; carga única no boot |
| CRAM (amortizado) | 16 palavras a cada 30 frames | `load_pose_pal` no switch de pose |

- **Total worst-frame**: 16 B de VRAM/VBlank (nada de tile streaming ainda)
- **Headroom**: >98% da janela de VBlank — mas NUNCA medido em ciclo de CPU;
  o contrato real de worst-frame chega com Ken (Task 6/`measure_worst_frame.py`)
- **Método**: contagem instrumentada do código de frame + captura de evidência
- **Degrau seguinte medido**: banco + streaming dos pools de Ken (Task 6) —
  376 KB de arte gerada contra 16 KB de VRAM é o débito que paga o teste

### Sprites por scanline (pico)
`audit_sprite_line_sim.py` sobre `out/evidence/cena01_line_sim_scene.json`
(4 colunas TALL 8×16 modeladas como 8 entradas 8×8): **pico 4/linha, SAT 8/64,
zero violações** — dentro do contrato GDD de lutador (≤4/linha).

### fps observado
`measure_fps.py` — 6 amostras, todas **60 fps** (`constante_50_60: true`),
janela `Emulicious - 100% (60 fps)`: `out/evidence/cena01_fps.json`.
