# PLANO_CONTINUACAO — SMSForge (documento mestre de sequência)

> **LEIA ISTO PRIMEIRO se você é um agente assumindo este workspace.**
> Ordem obrigatória: `AGENTS.md` (raiz) → `.agent/rules/SMS_GLOBAL.md` →
> `doc/06_AI_MEMORY_BANK.md` → este plano. Estado de sessão nunca substitui
> memory bank, GDD, TDD, manifests ou evidência.

## Regras de continuação (inegociáveis)

1. Trabalhe em FASES na ordem abaixo. Uma fase só fecha com o critério-de-pronto
   observado (nunca inferido) e registrado aqui + no memory bank do projeto.
2. Todo erro novo vira lição: JSON em `doc/curation/` + seção em SMS_GLOBAL +
   ferramenta que mede (workflow `curation-learning.md`).
3. Nenhum claim acima do teto; nenhum "pronto" sem evidência de emulador.
4. Gates antes de runtime; decisão barata antes de arte cara.
5. Ao encerrar sua sessão: atualize este arquivo (marque fase/status),
   o memory bank do projeto e deixe handoff.

---

## ESTADO ATUAL (atualizado em 2026-08-26)

| Item | Status | Prova |
|------|--------|-------|
| Workspace + gates + selftest 18/18 | ✓ | `python3 tools/sms_wrapper/selftest.py` (18 base + probe opcional) |
| Toolchain rootless instalado (SDCC 4.6 portátil + devkitSMS libs reconstruídas) | ✓ | `tools/sms_wrapper/ensure_toolchain.sh` (smoke-test embutido) |
| Emulador Emulicious + captura (spectacle+shim libavcodec) | ✓ | L007/L008; `tools/emuladores/README.md` |
| ROM laboratorio_01 v5 (cena 01) buildando | ✓ | `changelog/roms/build_v011` (16384B, tela limpa) |
| Boot emulador | ✓ | `out/evidence/tela_funcional.png` + `evidence.json` (60 fps no título) |
| Tela funcional sem glitches (título+moldura+cursor BG+status+spinner) | ✓ | `out/evidence/tela_funcional.png` — captura limpa 283x282, sem ruído |
| Gameplay input→movimento (BG cursor) | ✓ | `out/evidence/gameplay.json` + D-PAD funcional ( SSP) |
| FPS medido (título) | ✓ | `out/evidence/fps.json` (6 amostras 58-60, média 59.0, constante_50_60=true) — F2 CONCLUÍDA |
| Áudio PSG (blip SN76489 porta 0x7F) | ✓ implementado | `src/main.c` beep()/beep_off() no movimento; evidência audível pendente humana |
| Sprites hardware (L006) | ✅ RESOLVIDO | sprite renderiza via SPRITEMODE_NORMAL 8x8 (causa-raiz: TALL 16x16); evidencia f1_sprite_visivel.png |

## Lições abertas (detalhes em `doc/curation/2026-08-25_fundacao.json`)

- **L006** sprite invisível: fatos e hipótese listados; ferramenta de
  fechamento = DAP `evaluate` contexto **repl** (`readvram/readbyte`) em
  instância FRESCA do Emulicious (esperar porta 4901 abrir + warmup até
  `readbyte(0xC000)` responder).
- **L007/L008** harness: spectacle exige shim `~/.local/smsforge-shim`;
  x11grab não vê XWayland; foco real = CLIQUE na canvas; janela-alvo =
  `sun-awt-X11-XCanvasPeer` 256×192; fps legível no título da janela principal.

---

## FASES (executar EM SEQUÊNCIA)

### F1 — RESOLVIDO (2026-08-30): L006 sprite
**Causa-raiz**: SPRITEMODE_TALL com tiles 16x16 nao alinhava com a base de sprite.
**Solucao**: SPRITEMODE_NORMAL (8x8) + SMS_loadTiles(hero,128) + SMS_addSprite(120,80,128).
**Evidencia**: out/evidence/f1_sprite_visivel.png. Para 16x16, usar metasprite (4x 8x8).
**Por quê primeiro:** destrava sprites para TODAS as cenas futuras.
**Receita exata:**
1. Criar `SMS_projects/laboratorio_01/src/probe_sprite.c`:
   - variáveis GLOBAIS em endereço fixo SDCC:
     `unsigned char rb[4] __at(0xC700); signed char spr_ret __at(0xC710);`
   - `SMS_loadTiles(hero_tiles,256,64); spr_ret=SMS_addSprite(120,88,256);`
     `SMS_copySpritestoSAT(); SMS_readVRAM(rb,256*32,4);` loop vblank.
2. Compilar igual a `build_inner.py` faz (ver log `out/logs_build.txt`).
3. Rodar Emulicious `-remotedebug 4901`, esperar porta, DAP repl:
   `readbyte(0xC700..0xC703)` vs `hero_tiles[0..3]` (estão em
   `inc/hero_tiles.h`) e `readbyte(0xC710)` (spr_ret: -1 cheio / -2 invY).
4. Interpretação:
   - rb==dados & spr>=0 & sprite invisível → problema é reg6/base ou formato
     de tile TALL → testar `SMS_useFirstHalfTilesforSprites` ligado/desligado
     e tile 8x8 SPRITEMODE_NORMAL com arte 8x8.
   - rb zeros → loadTiles não escreveu onde se espera → testar
     `SMS_VRAMmemcpy` direto.
5. Registrar veredito aqui + nova seção em SMS_GLOBAL (fato pago).
**Pronto quando:** sprite visível em captura OU causa-raiz documentada com
leitura de RAM/VRAM citada.

### F2 — FPS fino (fechar eixo fps_constante)
1. `tools/sms_wrapper/measure_fps.py`: localiza janela cujo nome contém
   `Emulicious -` e `fps`; amostra título 6× a cada 1s via
   `xdotool getwindowname`; grava JSON com todas as amostras + média.
2. Rodar durante cena 01; anexar bundle ao evidence.
3. Opcional (degrau seguinte §18): cruzar com contador hex na tela.
**Pronto quando:** ≥5 amostras registradas, todas 50–60fps, JSON salvo.

### F3 — Áudio (blip PSG no movimento)
1. Verificar PORTA/registradores em `sdk/devkitSMS/PSGlib/PSGlib.h`
   (procurar `PSGPort`) — header é autoridade #8.
2. SN76489: latch `%1ttdddd` + dado `%0dddddd` (protocolo universal do chip);
   tom curto (attenuation 0→11) a cada movimento de cursor.
3. Escrever direto na porta via SDCC (`__asm__` ou sfr) SEM PSGlib nesta
   etapa; PSGlib/música fica para fase posterior com ferramenta .psg real.
4. Evidência: honesta — áudio IMPLEMENTADO; comprovação audível pendente
   (humano no `run.sh`), vocabulário de status respeitado.
**Pronto quando:** blip compila, roda sem travar (fps segue ~60) e código
cita o header como fonte da porta.

### Cena 04 — game feel AVANÇADO (2026-08-30)
- Invulnerabilidade pos-hit (40f) + flash do jogador (pisca sprite).
- Som de tiro (blip PSG) + projetil (tile 131) com colisao projetil-inimigo.
- Mantém hitstop + screen shake + 5 inimigos + dificuldade progressiva.
- Prova: 60fps estavel, audio_battle.wav 97% ativo.
- Hitstop (congela acao 6f no impacto), screen shake (offsets de scroll), 5 inimigos,
  dificuldade progressiva (evy cresce c/ tempo). Prova: 60fps estavel no titulo,
  cena04_sprites.png, audio_battle.wav (97% ativo).
Primeira cena de JOGO real (não fixture): roteiro → storyboard pixel →
coreografia → simulador → orçamento → contrato → model sheet → assets →
runtime → evidência. Usar sprites SE F1 fechou favoravelmente; senão BG.
**Pronto quando:** todos os gates da pipeline verde + bundle de evidência.

### F5 — Orçamento worst-frame medido
Preencher `doc/13-spec-cenas.md` + `scene_budget_v1` com medição real
(método documentado; "estimado" proibido).

### F6 — Release do protótipo
Workflow `release-rom.md` (7 eixos simultâneos + teto de claims aprovado).

---

## Registro de execução das fases

| Fase | Status | Data | Observações |
|------|--------|------|-------------|
| F1 | RESOLVIDO (L006 fechado) | 2026-08-30 | sprite RENDERIZA com SPRITEMODE_NORMAL 8x8 + SMS_loadTiles(hero,128) + SMS_addSprite; causa-raiz = SPRITEMODE_TALL com tiles 16x16 (usar metasprite) |
| F2 | CONCLUÍDA | 2026-08-26 | measure_fps.py; fps.json: min58 max60 media59 constante_50_60=true — eixo fps_constante FECHADO |
| F3 | CONCLUÍDA (implementado) | 2026-08-26 | blip SN76489 porta 0x7F (SN76489 latch 1tt) no movimento; build v011 sem degradação; evidência audível = run.sh humano |
| F4 | CONCLUÍDA (docs+runtime+gates+evidencia) | 2026-08-30 | cena02 tiles no runtime; logica de vitoria PROVADA; FRAME DE VITORIA CAPTURADO (gameplay_cena02_vitoria.png mostra VITORIA! 1:REINICIA) |
| F5 | CONCLUÍDA | 2026-08-29 | worst-frame 42 bytes medido via contagem + fps 59 estável; headroom >99% (doc/scene_budget_cena02.json) |
| F6 | CONCLUÍDA (7 eixos true) | 2026-08-30 | build/validation/boot/gameplay/fps(59.3)/audio(PSG capturado audio_psg.wav)/memory_bank |
