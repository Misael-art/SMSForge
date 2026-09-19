# HAMOOPIG — engine de luta SGDK 2.11

Porta da engine **HAMOOPIG** (HAMOOPI no Mega Drive) para o pipeline canónico SGDK 2.11 deste workspace.

HAMOOPIG é a implementação Mega Drive da engine **HAMOOPI** de **GameDevBoss (Daniel Moura), 2015–2022**. Créditos obrigatórios ao autor. HAMOOPI é GPL v2 (`rascunho/upstream_reference/HAMOOPI_GPL_v2.txt`). O código SGDK desta pasta veio de `SGDK_Engines/HAMOOPIG-SGDK` (port `humbertodias/sgdk-HAMOOPIG`).

## O que esta porta é

- Engine de luta 1v1 com FSM, hitboxes, física, IA e input 6 botões
- Build pelo wrapper canónico (`tools/sgdk_wrapper/build.sh`), não pelo Makefile Docker do upstream
- Teto de claim: `prototype` / `technical_demo`
- **Não** é jogo AAA autoral. Roster e arte de Ryo são do upstream e não passam da barra viva deste workspace

## O que foi completado nesta pasta

O `res.zip` do sgdk-HAMOOPIG vinha sem PCM e sem sprites de HUD. A porta 2.11 agora inclui:

| Peça | Origem | Runtime |
|---|---|---|
| 17 SFX `snd_*` | WAV GPL do HAMOOPI, 16 kHz PCM XGM | `FUNCAO_PLAY_SND` ligado |
| Relógio `spr_n0..n9` | `system/spr_num_*.pcx` do HAMOOPI, remapeados à PAL1 | `FUNCAO_RELOGIO` ligado |
| Sombra `spr_sombra` | silhueta do frame de Ryo, no chão, PAL1 | spawn + follow ligados |

Documentação da engine original: `doc/engine/`.

## Build e run

```bash
../../tools/sgdk_wrapper/build.sh "$PWD"
```

No Linux a rota canónica é Wine/flatpak (`build_sgdk_wine_bridge.sh`). Não chamar `build.bat` neste host.

## Estado

Ver `doc/10-memory-bank.md`. Pronto = ROM em `out/rom.bin` **e** evidência BlastEm. Áudio e HUD passam a existir nesta revisão; prova em emulador só depois do rebuild.
