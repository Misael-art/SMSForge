# 15-tdd — HAMOOPIG SMS

> Autoridade #7. API = `SMSlib.h` / `PSGlib.h`.

## Restrições
Sem float, sem malloc, sem DMA, ≤8 sprites/scanline, SAT 64, 8 KB RAM.
Números de Mega Drive (320×224, DMA, XGM2, 6 botões) não entram.

## Arquitetura
Fronteiras: `main` (loop/VBlank/probe), `scene`, `input`, `fighter`+`FighterDef`,
`combat` (eventos), `hud`, `gfx`/`title`, `probe`.
Dois `Fighter` estáticos 0-based. FSM numérica do subset HAMOOPIG.
Dispatch de personagem por tabela `fighter_def(id)`, não por `switch` de regras.

## Input
Uma leitura `SMS_getKeysStatus()` por tick. PORT_A = P1, PORT_B = P2.
Pressed/hold/released por comparação em 16 bits. Dummy não herda CPU.
Pause = `SMS_queryPauseRequested` (NMI).

## Pools
| Pool | Máx | Notas |
|------|-----|-------|
| Fighter | 2 | ~40 B cada |
| Contact | 4 | snapshot do tick |
| Input hist | 2×8 | QCF |
| scratch VRAM | 256 B | espelho de tiles no boot |

## VRAM
| Tiles | Uso |
|-------|-----|
| 1–41 | fonte 1bpp autoral |
| 48–51 | chão + barras |
| 128–191 | silhuetas técnicas P1/P2 idle/punch e espelhos |

`SMS_useFirstHalfTilesforSprites(1)`, `SPRITEMODE_TALL`, metasprite 16×32
(4 sprites/lutador, 8 na scanline quando alinhados). HUD é tile, nunca sprite.

## Timing
NTSC 60 Hz: relógio 99 s, 1 tick de segundo = 60 frames. Não copiar
`ROUND_CLOCK_TICKS=38` da origem sem unidade.

## Áudio
PSGlib previsto. Esta ROM ainda não toca BGM. Beeps diretos não fecham o eixo.

## Banking
Alvo inicial: 32–48 KB linear. Mapper Sega só com spec + curadoria do wrapper.

## Probe SMRT schema 1
Mesmo mapa MSSF2T (0xC7E0..) para reusar `measure_runtime_probe.py`.
`volatile` obrigatório (L009).
