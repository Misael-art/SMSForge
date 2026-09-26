# 10-memory-bank — luta_mugen

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
2026-09-25 (madrugada) — Plano 2 Task 5 executada: input VIVO provado na RAM
(`src/input.c` + `tools/prove_input.py`, canal uinput kdotool/ydotool), mapa de
probes SMRT com 14 células, e um BUG REAL caçado pela evidência: o BG palette
escrevia em CRAM `2` achando ser "palette 2" enquanto o chão lê entry `10` — a
entry real nunca era inicializada e o chão saía cinza/oliva/rosa/ciano conforme
o estado do emulador entre runs. ROM `fe66394c…dc9` em todos os gates.
Tests Python: 79/79.

## Eixos de entrega (7) — gate final exige os 7 simultâneos
| Eixo | Status | Prova |
|------|--------|-------|
| build | testado_em_emulador (cena 01 FSM + input vivo) | `build.sh` → `out/rom/luta_mugen.sms` 16 KB, SHA `fe66394c…dc9` (T4 FSM: `145a0433…fb16`; cena 01 probe: `274d3109…d7b8`) |
| validation_report | parcial | `t5_probe.json` (SMRT magic/schema, fps DAP 59.19/58.79), `t5_boot.json` capture PASS, `audit_deterministic_boot` PASS (2 runs idênticos, esta ROM), `t5_live.json` vídeo PASS movimento 1.1% |
| boot no emulador | testado_em_emulador | `out/evidence/t5_boot.png` — dois lutadores no chão + HUD; chão cinza DETERMINÍSTICO (85,85,85 = 0x15) após correção da entry CRAM 10 |
| gameplay | testado_em_emulador (parcial: 1 jogador) | `t5_input_memory.json` — 5 eixos por INPUT real na RAM: Right dx=+70 / Left dx=−88 (keys 0x08/0x04 vistos com tecla em baixo), pulo pico 94 px + estado JUMP, soco B1 0x10 a gap −9 → boss 237→232 (dano 5 do CNS) + score 3, agachar estado 4; latch de padrão 0x03 (QCF-simplificado e hold-F batem no matcher). Guard vivo ainda não mapeado (2 botões) — cena 02 |
| 60/50 fps | testado_em_emulador | `t5_probe.json` — `probe_frame` lido via DAP na RAM (imune a foco/zumbi), 2 janelas de 8 s: 59.19 e 58.79 |
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

## O que FOI OBSERVADO (Plano 2 Task 5 — input vivo + mapa SMRT)
- `src/input.c`: ring buffer de amostras facing-relative (16, máscara
  power-of-2), matcher de passos no formato do CMD blob gerado
  (`[dir|keys<<4, flags]`, hold/release), janela = idade máxima − mínima dos
  passos casados. `K_GUARD` NÃO é alcançável no pad de 2 botões — bit
  sintético de teste; o bloqueio vivo é o crouch (S_BLOCKABLE). Remap
  "recuar = guard" do GDD fica para a cena 02 (documentado em `inc/input.h`).
- Mapa SMRT da ROM (magic `SMRT`+schema 1 em 0xC7E0..E4; frame u16 0xC7F0;
  snapshot 0xC7F2..0xC7FD: hp/score/boss/over/state/wave(atracao)/keys/pose/
  px/py/p2x/pattern-latch) — `measure_runtime_probe.py` PASS e fps medido na
  RAM via DAP, sem depender de pixels nem de foco de janela.
- `tools/prove_input.py` (criterio próprio com `--self-check`, 11 fixtures):
  canario = reset Ctrl+BackSpace zerando `probe_frame`; leitura de `keys`
  DURANTE a tecla em baixo; tecla que não chegou ≠ whiff; veredito só na RAM.
  Na ROM final: 5/5 eixos PASS (números na tabela de eixos).
- **Bug caçado pela evidência — BG CRAM entry errada**: `SMS_setBGPaletteColor
  (entry, cor)` recebe entry ABSOLUTA 0..15 = `palette*4 + (indice&3)`; o
  código escrevia em `2` querendo dizer "palette 2". O chão (tile 126 → pal 2;
  bytes 0x00,0xFF por linha no formato 4-bytes-por-linha-do-gerador →
  p1|p3 = índice 10 → cor 2) lê a entry **10**, nunca inicializada — entre
  runs o chão saiu cinza, oliva, ROSA (254,170,255) e CIANO (170,255,255),
  cores FORA da paleta mestra que `screenshot_semantic_gate` reprovaria. Os
  glifos (tile 128+g → pal g&3, índice 1) só tinham branco na palette 0;
  agora entries 1/5/9/13 = 0x3F. Lição: cor que MUDA entre runs é entrada não
  inicializada, não capricho do emulador.
- Armadilha do `capture_video.py --press`: a rajada inteira roda no INÍCIO da
  gravação e o gate compara primeiro×último frame (piso 1%). Um script que
  volta ao ponto de partida (Right depois Left) reprova com 0.83% mesmo com a
  cena toda em movimento. Script que termina LONGE (`Up=250,Right=1800`) passa
  com 1.1%.
- Foco Wayland é compartilhado: logo após `prove_input.py` fechar, o F7 do
  `capture_video` não chegou à janela (FAIL honesto "gravação não começou");
  um retry com o palco limpo passou. Zumbi morto antes de CADA gate (L057).
- `mini_art.h` DEFINE os blobs (não extern) — só `fight.c` o inclui; demais
  TUs declaram `extern const unsigned char MINI_CMD_*[5]` (senão
  ASlink multiple-definition).

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
Input vivo PROVADO na RAM (5/5 eixos, `t5_input_memory.json`) e vídeo de cena
viva com deslocamento sustained PASS. Blocker dominante agora: **dívida de
VRAM do Ken real** — 376.226 B gerados vs 16 KB de ROM: sem banking +
streaming por pose (Task 6, `measure_worst_frame.py` no gate) a prova do
contrato (Task 8, golden slice) não existe. A cena 02 (Task 7: identidade P2
por shift de índice, HUD de vida, PSG, guard vivo) é o ramo paralelo seguro.

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
Executar `doc/plan-2-runtime-s5-s6.md` — Tasks 0–5 fechadas; próximo ramo é a
**Task 6 (banking + streaming de VRAM por pose)**, gate `measure_worst_frame.py`
e teto 16 KB → ROM bancada ~150 KB/lutador. Antes de qualquer gate de janela:
matar zumbi (`pkill -f '[E]mulicious.jar'` em chamada separada — L057) e
`emulator_input.py --self-check`. Baseline: 79 testes Python +
`tools/prove_input.py --self-check` + `measure_runtime_probe.py` na ROM atual.
