# SMSForge — Fábrica metodológica de jogos para Sega Master System

Porte da filosofia do MegaDrive_DEV (SGDKForge) para o hardware de 1985.

> **"Se não foi visto rodando no emulador, não existe."**

## Síntese

Compilador de disciplina: transforma restrições físicas do Master System
(Z80 3.58MHz, VDP sem DMA, paleta mestra fixa de 64 códigos, 8 sprites por
scanline, RAM de 8KB) em gates medidos, e erros cometidos por modelos
anteriores em seções de lei + ferramentas. O elo fraco nunca foi o hardware:
era o agente prometendo o que não tinha provado.

## Diferenças estruturais vs MegaDrive (por que não foi copy-paste)

| Eixo | Mega Drive (SGDKForge) | Master System (SMSForge) |
|------|------------------------|--------------------------|
| CPU | 68000 @7.6MHz, int 32-bit | Z80 @3.58MHz, int 16-bit (SDCC), sem mul/div |
| Toolchain | GCC m68k + SGDK 2.11 | SDCC ≥4.2 + devkitSMS (SMSlib, PSGlib, makesms) |
| VDP | Genesis VDP, DMA, shadow/highlight, 9-bit palette | VDP TMS-derivado, **sem DMA**, paleta mestra fixa 64 códigos |
| Sprites/scanline | H40: 20 sprites E 320px | **8 sprites por linha** (excesso descartado/corrompe SMS1) |
| Tiles BG | atributos por tile (flip/palette) | name table de **1 byte/tile**: sem flip nem paleta por tile |
| Áudio | YM2612 FM + PSG + DAC (XGM2) | SN76489 PSG (4 canais); YM2413 opcional |
| RAM | 64KB+ | **8KB** (data-loc 0xC000) |
| ROM | até 4MB+ linear-ish | 48KB linear; mapper Sega 16KB pages acima |
| Emulator gate | BlastEm | Emulicious / openMSX headless |

A espinha dorsal metodológica (hierarquia de verdade, ciclo decisão-barata-primeiro,
gates executáveis, vocabulário de status, learning loop) é idêntica — porque essa parte
é geral de engenharia, não de console.

## Estrutura

Veja `AGENTS.md` (contrato de entrada obrigatório).

```
SMSForge/
├── AGENTS.md                 ← contrato de entrada p/ qualquer IA
├── doc/                      ← verdade do workspace
├── sdk/devkitSMS/            ← toolchain (headers = autoridade final de API)
├── tools/sms_wrapper/        ← FONTE ÚNICA de build + framework .agent + gates
├── tools/emuladores/         ← Emulicious (gate), MEKA, openMSX, Gearsystem
├── SMS_projects/             ← os jogos (cada um autocontido)
└── SMS_Engines/              ← engines reutilizáveis
```

## Status honesto deste workspace

Ver `doc/06_AI_MEMORY_BANK.md`. Resumo: estrutura implementada; gates provados
por self-test; toolchain/emuladores precisam ser instalados na máquina host
(siga `sdk/README.md`). Nenhuma ROM existe ainda — e isso está dito aqui.
