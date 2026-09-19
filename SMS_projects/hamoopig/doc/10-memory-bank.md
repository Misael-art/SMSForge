# 10-memory-bank — hamoopig

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-09-19 — **v009: guarda chip-2 observada. Throw implementado, não observado (B2 no teclado). PSG com sinal, mix 49%. Worst-frame derramou.**

ROM `out/rom/hamoopig.sms` 32768 B, SHA-256
`7a8951eef4c886e03631bffcefec55e45ae94fd1aedbb16f566f618679f361bd`
(changelog `build_v009`). Origem HAMOOPIG não modificada.

## Eixos
| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | 32768 B, SHA `7a8951ee…` |
| validation_report | buildado | pre_gates pass |
| boot | testado_em_emulador | probe SMRT |
| gameplay | testado_em_emulador (soco, especial, **guarda**) | `guard_probe.json` HP 64→62, p2g=1, ctrl=4 |
| fps | parcial | probe janela 58.2 / 28.12 (segunda contaminada); worst-frame derramou |
| áudio | implementado, mix abaixo do piso | `audio.wav` peak=7470, 49% ativo (<90%: BGM só na luta) |
| memory bank | documentado | este arquivo |

## Guarda
Select **Down** = P2 `CONTROL_BLOCK` (dummy parado segurando trás). Soco → chip **2**. `guard_probe.json`.

## Throw
Contrato 2 botões: **B1+B2** a gap≤24, dano 10, ignora guarda. `prove_throw.py` com A+S e A+Z deu delta 7 (soco): o Emulicious deste host mapeia B1=A; B2 não foi encontrado no teclado. Código presente, **não observado**.

## QCF/projétil
Continua o resultado da v006 (SHA anterior): hist 2-2-6-6, fire=2. Não re-provado nesta SHA.

## Worst-frame
`worst_frame.json`: veredito **derramou**, vovf_delta=597 em 20 s, vline_max=255. Folga zero. Degrau: reduzir trabalho pré-VBlank (PSGFrame+HUD+SAT).

## Lições de fábrica
L065–L068 em `doc/curation/2026-09-19_l065_l068_qcf_harness.json`, SMS_GLOBAL §52–§53.

## Blocker
Throw observado (achar B2 ou comando só com D-pad+B1); pior-quadro; mix de áudio na abertura; arte.

## Handoff
1. Mapear B2 no Emulicious ou throw em comando D-pad conhecido
2. Cortar trabalho de frame (vovf)
3. BGM desde o título para o piso 90%
4. Arte 32×64; Kensaiden depois
