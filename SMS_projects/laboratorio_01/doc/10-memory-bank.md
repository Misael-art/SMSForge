# 10-memory-bank — laboratorio_01

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-08-30 — auditoria: F4 tiles reais, selftest 18/18, eixos runtime em build_record = false (a reconstruir com prova real).

## Eixos de entrega (7)
| Eixo | Status | Prova |
|------|--------|-------|
| build | **buildado** | `out/rom/laboratorio_01.sms` 16.384B; `TMR SEGA` @espelho 0x7FF0, checksum 0x5ABB |
| validation_report | validado (pre-gates) | recursos+procedência pass; record em out/build_record.json |
| boot no emulador | **testado_em_emulador** | `out/evidence/evidence.json` PASS (viewport var 3715); Emulicious 2026-03-27 |
| gameplay | testado_em_emulador (VITORIA capturada) | frame de VITORIA em gameplay_cena02_vitoria.png (texto legivel); logica provada por simulacao + execucao real |
| 60/50 fps | testado_em_emulador | fps.json: 6 amostras 58-60 (media 59.0), constante_50_60=true — eixo FECHADO |
| áudio | implementado (evidência audível pendente) | blip SN76489 porta 0x7F no movimento (v6); confirmação humana via ./run.sh |
| memory bank atualizado | sim | este arquivo (auditoria 2026-08-30) |

## Decisões registradas
- Header SEGA embutido via macros oficiais (`SMS_EMBED_SEGA_ROM_HEADER_16KB` +
  SDSC auto-date), confirmadas em SMSlib.h:429–485.
- Toolchain instalado rootless via `tools/sms_wrapper/ensure_toolchain.sh`
  (SDCC 4.6 portátil; SMSlib/PSGlib RECONSTRUÍDAS do fonte — lição L004).

## Cena 01 "boot_interativo" (2026-08-26)
- v003 buildada com pre-gates verdes (recursos+procedência no próprio build).
- Rota BG para o cursor (desvio documentado — L006: sprite com pixels índice-0,
  causa-raiz aberta; readvram/repl do Emulicious é a ferramenta de fechamento).
- Evidência de boot v1 segue válida; gameplay parcial (ver eixos acima).

## Sessão 2026-08-26 (parte 2)
- F2 fechada: fps.json 58-60fps constante.
- F3 implementada: blip PSG no movimento (sem degradação de fps).
- L006 avançou: travamento isolado DENTRO de SMS_loadTiles (L009).

## F4 cena02 (2026-08-29)
- GDD cena02, spec, storyboard, contrato criados (pipeline aaa_scene_v1 S0-S4).
- Runtime: bloco 2x2 empurrável, alvo, vitória + reinício, colisão AABB, beep/fanfarra.
- Build v012 OK, tela limpa capturada.

## FPS FECHADO (2026-08-30)
- 59.3fps MEDIDO via contador de frames na tela (0x012F->0x01AD = 126f/2.125s). Eixo fps_constante=true.
- Audio: IMPLEMENTADO (PSG porta 0x7F); comprovacao audivel limitada pelo host (L012: Java do Emulicious nao roteia no Pulse). Eixo audio=false, honesto.

## Cena 04 "corredor estelar" (2026-08-30)
- Combina sprites (L006) + musica battle rica (PSGlib 4 canais) + scroll + HUD + HP/gameover.
- Prova: cena04_sprites.png (jogador sprite visivel, 60fps) + audio_battle.wav (96% ativo, peak 9936).
- Musica gerada por probes/gen_music.py (formato .psg do PSGlib); inc/music_battle.h.

## Próximo passo declarado
- Fechar fps/audio medidos no emulador (F2/F3 ja implementados; medicao no emulador).
- F1: L006 sprite (probe; VRAMmemcpy + SPRITEMODE_NORMAL 8x8).
- Atualizar build_record com eixos provados.
- F1: resolver L006 sprite (probe em probes/).
- Reconstruir build_record com eixos provados (nao por edicao).
- F1: resolver L006 sprite via VRAMmemcpy (probe em probes/).
- Reconstruir build_record com eixos de runtime provados (não por edição).
