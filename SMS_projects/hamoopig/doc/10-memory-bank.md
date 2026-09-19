# 10-memory-bank — hamoopig

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-09-19 — **v006: QCF + projétil OBSERVADOS.** Protótipo técnico parcial, não porte completo.

ROM `out/rom/hamoopig.sms` 32768 B, SHA-256
`4d6bfa4005b27412551fa3f8a041db813c69e163ce3dd2e7c8cf422cdb707964`
(changelog `build_v006`). Origem HAMOOPIG **não modificada**. MSSF2T **não modificado**.

## Eixos de entrega (7)
| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | 32768 B, SHA `4d6bfa40…` |
| validation_report | buildado | pre_gates pass |
| boot no emulador | testado_em_emulador | `title.png` / `fight.png`; probe SMRT |
| gameplay | testado_em_emulador (andar, soco, especial) | `special_probe.json`: hist 2,2,6,6; qcf=1; SP 32→4; fire=2; HP dummy 8→0 |
| 60/50 fps | testado_em_emulador | `runtime_probe.json` 59.42 / 59.42 |
| áudio | não iniciado | — |
| memory bank atualizado | documentado | este arquivo |

`out/build_record.json` continua com eixos de runtime `false` porque é gerado no **compile** e a fábrica só promove `gameplay` via `input_memory.json` / `interaction_proven`. **Não editar à mão.** Autoridade #1 é este memory bank.

## QCF — o que a instrumentação mostrou
1. `press_spec` com refoco por tecla (~300 ms) estoura o hist de 8 ticks. Corrigido: `refocus=False` no gesto.
2. Amostra 0,9 s depois do gesto só via 5 (neutro). Amostra ≤50 ms depois ainda contém 2 e 6.
3. Na v005, `qcf=1` com hist `[5,2,5,6,…]` mas especial não entrava: B1 só na **borda**. Recuo SMS: B1 **hold** enquanto o QCF ainda está na janela de 8 ticks. Hist **não** foi alargado.
4. v006 `at_qcf`: hist `[2,2,6,6,5,5,5,5]`, `qcf=1`, `fire=2` (projétil consumido no hit), SP 32→4 (custo 32 + ganho 4 do hit), HP 8→0, estado 99 = `ST_WIN` (611 & 0xFF).

## Observado
- Título / select / luta técnica 16×32
- Soco dano 7; especial/projétil dano que zerou o dummy
- Probe hist em `0xC7D0` (temporário de diagnóstico, útil manter)

## Ainda não é porte
Arte final, animações, golpes próprios, guarda/throw/multihit **provados**, HUD completo, palcos, áudio, worst-frame, PAL, Kensaiden, revanche filmada.

## Blocker dominante
Guarda e throw observáveis; depois partida/revanche completa; áudio; worst-frame; arte.

## Handoff
1. Provar guarda (recuar + chip 2) e throw se couber no 2 botões
2. PSG de hit/especial
3. Worst-frame + scanline
4. Reautoria 32×64; Ken sem pixels Capcom; Kensaiden depois do contrato
