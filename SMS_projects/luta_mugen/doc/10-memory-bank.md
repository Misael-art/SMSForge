# 10-memory-bank — luta_mugen

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
2026-09-25 (noite) — Plano 2 Task 4 executada: interpretador FSM por tabelas
(`src/fight.c`) com física Q8.8, colisão clsn hit/hurt em software, hitstop,
knockback e pushback bloqueado; cena 01 rodando com sequência determinística
de 13 inputs scriptados. ROM `145a0433…fb16` reverificada nos gates de boot,
frame advance e boot determinístico. Tests Python: 79/79.

## Eixos de entrega (7) — gate final exige os 7 simultâneos
| Eixo | Status | Prova |
|------|--------|-------|
| build | testado_em_emulador (cena 01 FSM) | `build.sh` → `out/rom/luta_mugen.sms` 16 KB, SHA `145a0433…fb16` (anterior cena 01 probe: `274d3109…d7b8`) |
| validation_report | parcial | `t4_boot.json` capture PASS, `audit_deterministic_boot` PASS (2 runs idênticos, esta ROM), `t4_frame_advance_128.json` 59.6 fps constante |
| boot no emulador | testado_em_emulador | `out/evidence/t4_boot.png` — dois lutadores no chão pós-knockback + HUD de dígitos; viewport variancia 2423.3 |
| gameplay | parcial | FSM completo (idle/walk/jump/crouch/guard/punch1/punch2, hitstop, bloqueio) dirigido por `script[]` determinístico; input VIVO ainda zero (Task 5) |
| 60/50 fps | testado_em_emulador | `out/evidence/t4_frame_advance_128.json` — contador `dbg_frame` da própria ROM, célula 29 (período 128), 23× sobreamostragem, 28 trocas, constante True |
| áudio | não iniciado | PCM classificado unsupported; reautoria PSG (6 SFX + 1 BGM) ainda não escrita |
| memory bank atualizado | implementado | esta seção, nesta data |

> Vocabulário: `documentado ≠ implementado ≠ buildado ≠ testado_em_emulador`.
> O motor (ferramentas) está em `implementado com testes Python` — 79/79 verdes
> (`tools/sms_wrapper/mugen2sms/tests/`, executado 2026-09-25). Isso NÃO é
> eixo de entrega do jogo.

## O que FOI OBSERVADO (Plano 1)
- S0–S4 commitados: `4166868` (S0), `6b181f2` (S1), `f773b05` (S2),
  `db70051` (S3), `2d3a326` (S4). Cópia doada sob contrato de paridade
  (`doc/doacao_md_mugen2sms.json`, 34 arquivos, pino por SHA).
- Ken `ken_masters_adv` parseia inteiro: 463 sprites / 161 animações / 934
  frames / 1.526 clsn / 91 comandos / 126 estados / 33 sons, 0 erros de parse
  (medido por `ken_full_parse.py` contra o acervo local, fora do Git).
- Fidelidade medida (S3): 2.273 direct / 317 approximate / 93 manual / 297
  unsupported. VRAM: 36.401 tiles únicos dedup = 1,16 MB vs 16 KB → streaming
  por pose obrigatório.
- **Gate do harness REPROVA o corte nativo**: pior pose × 2 lutadores =
  pico 32/scanline (teto 8), SAT 256 (teto 64)
  (`out/local_study/generated/s4_generation_report.json`, gitignored).
  Veredito `FAIL` registrado, não contornado.
- Resposta à reprovação é decisão HUMANA, tomada em 2026-09-25: escala
  travada TALL 8×16, lutador ≤4 sprites/linha × ≤3 colunas (≈32×48 px em
  tela), downscale 1:4 fixo no conversor, pose que estourar vira `manual`,
  flicker proibido. Está no GDD §"Escala do lutador" e no TDD §"Corte
  jogável". O conversor AINDA NÃO aplica o contrato — é a primeira tarefa
  do Plano 2, com gate (o mesmo `audit_sprite_line_sim` que deu FAIL deve
  dar PASS com a escala aplicada).

## O que FOI OBSERVADO (Plano 2 até Task 3)
- Leis de hardware MEDIDAS na cena 01 (não assumidas): par TALL
  `(pattern, pattern+1)` = (topo, base) — probe branco/preto mostrou branco em
  cima; origem de `SMS_addMetaSprite` = 1ª linha visível do topo da pose;
  espelho-h renderiza como OUTRO padrão (METAL no oponente); fixture com
  trailer de paleta PCX + `same=0` no subheader produz PAL visível (0x25).
- O harness `capture_evidence.py` reprova cena cujo conteúdo fica FORA da
  metade central da imagem (viewport box = canvas x64..191, y29..137) — a cena
  01 foi recentrada (chão na linha 16, lutadores x=96/152) em vez de maquiar o
  gate.
- `-set Update=0` do Emulicious só pinta depois do primeiro redraw (~2 s de
  Java): burst de capturas precisa aguardar a janela existir E o floor aparecer.
- Ken redondo S4.5b: 3.921 artefatos / 376.226 B (+199.396 B de espelhos — o
  custo real da ausência de flip), gate worst-scene PASS peak 8 / SAT 32.

## O que FOI OBSERVADO (Plano 2 Task 4 — FSM + física + clsn)
- `src/fight.c` interpreta tabelas compiladas do fixture `mini`: 7 animações
  (0/20/40/100/120/200/201), 8 estados, física Q8.8 inteira (vx 512 fwd /
  −384 back, JUMP_VY 2560, GRAV 128 ≈ 40 frames de ar), hitbox AABB em
  software com janela = frame de startup, hitstop 8 nos dois lutadores,
  pushback 16 (8 se bloqueado), knockback posicional, auto-facing no chão.
- **Formato CLSN mudou (desvio consciente, re-pinnado no contrato de doação
  `ccb56ad9…`)**: duas seções com sentinela `-32767` cada —
  `<hit i16×4…> -32767 <hurt i16×4…> -32767`. Motivo: o runtime precisa
  distinguir hitbox de hurtbox por frame; o formato antigo (lista única) não
  permite. Fixture sintético expandido: 9 imagens / 7 animações com sprite e
  clsn DISTINTOS por ação (anti-clonagem virou contrato de teste).
- Telemetria de frame na BG: `dbg_frame` (`__at` com volatile, L009) exportado
  em 3 dígitos hexadecimais por glifos de quadrante 2×2 (células 29/30/31);
  pixels procedurais de telemetria são a exceção declarada da diretriz
  estética. Célula de período 8 (dígito 2) é INSAMPLÁVEL neste host
  (Nyquist 1,2 < 3,0 — `t4_frame_advance.json` FAIL honesto); a medição
  canonica usa a célula de período 128 com janela de 60 s.
- Compromisso de paleta PAGÁVEL na Task 7: o SMS tem uma paleta de sprite; P1
  carrega o `_PAL` do frame atual e P2 em pose diferente herda a cor de P1.
- Blocker do gate de boot determinístico era um zumbi `capture_evidence --keep`
  (L057): o gate mediu a janela ERRADA e deu FAIL falso; morto o zumbi, PASS
  com 2 execuções de estado idêntico.

## Decisões registradas
- Motor = ferramentas em `tools/sms_wrapper/mugen2sms/`; runtime interpreta
  tabelas compiladas; CNS-em-runtime recusado (2026-09-25).
- Banking Sega mapper decidido (ROM ≈150 KB/lutador medido no round S4).
- P2/dummy = shift de faixa de índice no MESMO sprite palette (o SMS tem uma única
  paleta de sprite; custo de padrões duplicados medido no Plano 2, não "zero").
- Áudio: zero PCM portado; 6 SFX + 1 BGM reautorizados em PSGlib.
- Licença: arte real do Ken nunca entra no Git; derivativos só em
  `out/local_study/` (gitignored); fixtures sintéticos são os únicos dados
  MUGEN-like no repo.
- Escala do lutador travada (ver acima) — decisão do usuário, não do agente.

## Blocker dominante atual
O contrato de escala FOI aplicado e medido (S4.5a/S4.5b: gate worst-scene do
Ken PASS, pico 8/linha, SAT 32 — `out/local_study/generated/s4_generation_report.json`,
gitignored). O FSM da Task 4 roda, avança frame e colide em software com boot
determinístico comprovado. Blocker dominante agora: **input vivo** — o eixo que
reprovou MSSF2T. A ROM só reage a `script[]` interno; nada foi provado do
teclado do host até a janela do emulador (Task 5, gate primeiro:
`emulator_input.py --self-check` ANTES de a ROM reagir).

## Lições abertas
- L-aberta-1: `validate_measurement_tools.py` descobre ferramentas por prefixo
  `audit_`/`measure_` na raiz do wrapper; as ferramentas do mugen2sms não são
  alcançadas. Curadoria pendente (registrar no discovery ou criar wrapper) —
  só com aprovação humana explícita.
- L-aberta-2: downscale 1:4 em arte de 69×83 px mediana produz ~17×21 px —
  silhueta de lutador pode definhar. A prova é visual, no emulador (S5), não
  na planilha. Hipótese: recorte por boneco (remake de pose) pode substituir
  downscale bruto em poses-chave. Ferramenta que fecha: `audit_render_fidelity`
  + evidência capturada na cena 01.

## Handoff
Executar `doc/plan-2-runtime-s5-s6.md` — Tasks 0–4 fechadas; próximo ramo é a
**Task 5 (input vivo)**. Primeiro comando do próximo agente:
`python3 tools/sms_wrapper/emulator_input.py --self-check` (canal uinput
kdotool/ydotool; NUNCA XTEST em Wayland/KWin — L039) e baseline verde de
`tools/sms_wrapper/mugen2sms/tests/` (79 testes).
