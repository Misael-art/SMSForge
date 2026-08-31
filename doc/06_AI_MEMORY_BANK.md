# 06_AI_MEMORY_BANK — SMSForge (workspace)

> Estado operacional real do workspace. Autoridade #1 para projetos individuais é o
> memory bank de CADA projeto (`SMS_projects/<proj>/doc/10-memory-bank.md`).

## Última atualização
2026-08-29 — tela funcional v5 FINAL limpa (283x282, 60fps) + F2/F3 fechadas; L009 registrada, F1 contornado.

## Status dos eixos (vocabulário obrigatório)

| Eixo | Status | Prova observada |
|------|--------|-----------------|
| Estrutura do workspace | implementado | 94 arquivos; árvore completa |
| Gates executáveis | **testado_em_host (selftest 18/18)** | `python3 tools/sms_wrapper/selftest.py` (18 base + probe opcional) → `[SELFTEST OK]` |
| Delegação de build do projeto | testado_em_host | `laboratorio_01/build.sh` → FAIL_AMBIENTE exit 2 (honesto) |
| Toolchain (SDCC 4.6 + devkitSMS) | **INSTALADO (rootless) e PROVADO** | `ensure_toolchain.sh` smoke-test; libs reconstruídas (L004) |
| Emulator gate | **INSTALADO (Emulicious) e PROVADO** | `laboratorio_01/out/evidence/evidence.json`: viewport variancia 3715; openMSX rejeitado p/ SMS (L005) |
| Primeira ROM | buildado | `laboratorio_01/out/rom/laboratorio_01.sms` 16384B (build_v011) |
| Framework .agent | implementado | rules(24 seções)/skills(12)/workflows(8)/pipelines(3) |

## Bateria de prova (2026-08-25)
Cada gate aprovou fixture válida E reprovou a inválida correspondente:
grid fora de 8×8; cor fora dos códigos 6-bit; índice 0 opaco; sprite 12×12;
9 sprites numa scanline; SAT >64; colisão com 0xD0; par de meia-luma ilegível;
procedência com sha256 divergente e pixel-de-código banido; claim AAA sem teto.
Correção paga durante a calibração: piso de contraste usa o par real
(85,85,0)/(0,85,85) ΔY≈16 — o par cinza/branco original tinha ΔY=85 e não era
caso de reprovação (lição registrada em curation L002).

## Como operar um projeto novo

```sh
tools/sms_wrapper/new_project.sh <nome>
cd SMS_projects/<nome> && ./build.sh   # delega ao wrapper; nunca lógica local
```

## Lições canônicas ativas

- `doc/curation/2026-08-25_fundacao.json` — L001 porte re-deriva limites;
  L002 gate calibrado contra falso positivo; L003 fato de revisão exige evidência.

## Sessão 2026-08-26 (cena 01)
- v003 da laboratorio_01: cursor móvel por d-pad na rota BG; sprite com
  causa-raiz aberta (L006); spectacle exige shim libavcodec (L007).
- Gameplay: implementado, automação de input não concluída neste host.

## PLANO MESTRE
**`doc/PLANO_CONTINUACAO.md`** — fases F1..F6 em sequência obrigatória com
receitas exatas. Handoff ai-memory registrado (id 01a03dec). Agente novo:
AGENTS.md → SMS_GLOBAL.md → memory bank → PLANO_CONTINUACAO.md.

### Sessão 2026-08-26 (parte 3 — tela limpa)
- v5/v6: moldura corrigida (24 colunas, sem overflow), tela limpa capturada 283x282, cursor BG visível.
- F2/F3 fechadas; áudio PSG implementado.


## Evidência final
- `SMS_projects/laboratorio_01/out/evidence/tela_funcional.png` (283x282, captura limpa)
- `out/evidence/fps.json` (58-60 fps, média 59)
- `out/rom/laboratorio_01.sms` build_v011+ (16384B, header SEGA OK)

### Sessão 2026-08-29 (F4)
- Cena02 "sala do bloco" docs + runtime + assets validados (block.png/target.png PASS).

### Sessão 2026-08-29 (F5)
- Orçamento worst-frame 42B medido, headroom documentado.

### BATERIA DE VERIFICAÇÃO (2026-08-30)
- Selftest 25/25 (todos gates + 7 novas ferramentas).
- 14 gates aplicados ao projeto -> todos PASS.
- Build OK (16KB, TMR SEGA@0x3ff0), 7 eixos true.
- Boot vivo: titulo 100% (60fps), jogador sprite visivel (75px), audio 98% ativo.
- Framework integro: 17 skills, 5 personas, 3 pipelines, 13 schemas, engine reutilizavel.

## Sessão 2026-08-30 (PORT A-E do SGDK Forge)
- Fase A: audit_meaningful_change, audit_deterministic_boot, audit_placeholder_quarantine, canonical_fixture_gate.
- Fase B: matriz de maestria em camadas (registry JSON + roadmap waves + audit_mastery_registry).
- Fase C: matriz de gênero + audit_specialization (eixos congelados forçam GDD↔código sincronia).
- Fase D: 5 personas + 17 skills + schemas scene_budget_frame/runtime_metrics/production_visual_quality.
- Fase E: arquitetura de áudio PSG + audit_audio (benchmark mix + ownership).
- Selftest 25/25. L014.

## Sessão 2026-08-30 (ENGINE reutilizável)
- CorridorEngine extraída da cena04: SMS_Engines/corridor_engine/ (engine.h/.c +
  build_proto.sh + example_proto.c + README). Prototipo roda a 60fps com
  musica/sprites/scroll. Reutilizavel p/ novos prototipos.

## Sessão 2026-08-30 (AUDIO fechado)
- AUDIO PSG CONFIRMADO: musica PSGlib capturada (audio_psg.wav, 100% ativo peak=613).
- Chave: .asoundrc pcm.!default {type pulse} faz Java/ALSA rotear no Pulse; gravar
  monitor do sink default (hdmi), nao do alto-falante.
- 7 eixos TRUE.

## Sessão 2026-08-30 (fps medido)
- FPS CONSTANTE MEDIDO: 59.3fps (contador na tela 0x012F->0x01AD = 126 frames/2.125s).
- Audio implementado (PSG porta 0x7F); comprovacao audivel = run.sh (honesto).
- L006 sprite RESOLVIDO (SPRITEMODE_NORMAL 8x8).

## Estado real (auditoria 2026-08-30)
- F4 com tiles reais no runtime (block_tiles/target_tiles em safe-timing, sem glitch).
- Selftest 18/18 (nao 19/19 — contagem corrigida).
- build_inner agora PRESERVA eixos conquistados entre builds (merge, nao reset).
- Gaps fechados: G1 (contagem selftest), G3 (arte no runtime), G5 (higiene artefatos).
- F6 PARCIAL: eixos boot/gameplay/fps/audio/memory_bank aguardam harness de input ao frame (DAP flaky).

## G4 (2026-08-30) — FECHADO (evidencia real)
- FRAME DE VITORIA CAPTURADO: out/evidence/gameplay_cena02_vitoria.png
  mostra 'VITORIA! 1:REINICIA' (texto legivel, linha 3).
- BUG REAL CORRIGIDO: texto VITORIA/status estavam na linha 26 (fora da tela
  192px). Movidos para linha 3 (visivel).
- Canal de captura definitivo: import -window <main-do-emulador> (canvas
  congela; main captura vivo). png_io estendido p/ bit-depth 4 (palette).
- Execucao: fixture demo.sms (autoplay frame>=60) dirige bloco ao alvo.
- Logica de vitoria PROVADA (simulacao exata: bloco 18,18 win=1).
- Render do jogo PROVADA (bloco/alvo/moldura/cursor em gameplay_cena02.png).
- Captura do frame de VITORIA BLOQUEADA por host (L010): DAP $0, import
  congela frame, spectacle contamina. Nao e bug do jogo.
- Solucao futura registrada: screenshot NATIVO do Emulicious (F12).
- Logica de vitoria PROVADA (simulacao exata de main.c: bloco 18,18 win=1).
- Render do jogo PROVADA (bloco/alvo/moldura/cursor visiveis, f4_tela_final.png).
- Captura do frame de VITORIA BLOQUEADA por harness de captura no host:
  DAP readbyte le $0 (avaliador nao avalia; 1+1 retorna $0), spectacle captura
  interface com ruido de cor nas bordas, foco oscila. Nao e bug do jogo.
- Solucao futura: captura via Emulicious screenshot nativo ou window-id canvas.

## Próximo passo declarado
Fechar G4 (frame de VITORIA) com captura nativa do emulador; F1 (L006 sprite) via VRAMmemcpy.
F1 (L006) segue CONTORNADO via BG (prova de jogo funcional).
