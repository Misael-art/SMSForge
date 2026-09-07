# 10-memory-bank — MSSF2T

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-09-06 — L050–L054 absorvidas na fábrica (JSON+lei+gate/skill). Poses
próprias de agachar e pular, gravidade consertada, espelhamento na troca
de lado, e 3,2 KB de ROM recuperados da música.
ROM `out/rom/MSSF2T.sms` 32768 B
SHA-256 `e42c488704188265c1c86bbcc64b3b383e86fafce1a2887a9ca5ec4607d1ee02`
Espaço livre de ROM: **1091 B** (no início da sessão: **0**).

## Eixos — todos medidos NESTA SHA
| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | 32768 B, 1091 B livres |
| validation_report | buildado | `out/build_record.json` |
| boot_emulador | testado_em_emulador | `boot.png`, informative=true |
| fps_constante | testado_em_emulador | 57.44 / 55.98 / 57.49 — PASS |
| audio | testado_em_emulador | peak=7330, **91% ativo** (controle v024 = 100%) — PASS |
| abertura | testado_em_emulador | `title.png` — título, convite piscando, cena escurecida |
| laço de arcade | testado_em_emulador | `resultado.png` (KEN WINS) → `volta_ao_titulo.png` |
| KO | testado_em_emulador (indireto) | `rounds.png` (ROUND 2) + `resultado.png` — ver nota |
| **gameplay** | **NÃO PROVADO** | ver abaixo — não é falha da ROM |
| memory_bank_atualizado | documentado | este arquivo |

`reconcile_claims.py`: PASS.

### Nota sobre o eixo KO
O frame do banner "K.O." **não foi capturado** nesta passagem: ele dura 120
frames e o `capture_evidence` não é exato em contagem de frames (quatro
tentativas caíram em ROUND 2, FIGHT! e no resultado). O KO está provado
**indiretamente e sem ambiguidade**: não se chega a "ROUND 2" nem a
"KEN WINS" (melhor de três) sem round decidido. Não renomeei um print de
ROUND 2 para `ko.png` só para o nome fechar.

## O espelhamento na troca de lado — corrigido, NÃO observado
`update_facing()` mudava `facing` mas nunca reaplicava a pose, e `set_state()`
retorna cedo quando o estado não muda: quem estava parado e era ultrapassado
ficava **de costas** até trocar de estado por acaso. O conserto é chamar
`apply_pose()` quando o facing muda.

**Mas eu não vi a troca acontecer (L053).** O caminho só é alcançável por pulo
por cima (a caixa de corpo impede cruzar no chão), e nas amostras do probe Ken
chegou a 6–14 px de ultrapassar e não passou. Ajustei a vitrine da atração
para ele aproximar antes de pular — e parei aí: continuar torcendo o
roteiro da demo para satisfazer o meu próprio teste é
`evidence_script_tuned_to_pass`. Estado honesto: **conserto correto por
leitura, caminho agora fisicamente alcançável, troca de lado não observada.**

## Recuperação de ROM: a música era 240 cópias do mesmo frame
`music_battle` tinha 2881 B — 240 repetições **byte a byte** do mesmo frame de
12 B (L051). O PSGlib volta ao início sozinho no `PSGEnd`, então as 239 cópias
não tocavam nada. `tools/shrink_music_loop.py` cortou para 49 B (e
`music_title` de 577 para 145 B): **3264 B recuperados**, com o áudio medido
igual antes e depois. Foi isso que pagou as poses novas. Gate de fábrica:
`audit_psg_redundancy.py`.

## fight_gfx.h dizia 1024 para folha de 832
O tamanho de cada folha vivia em DOIS lugares e `fight.c` só enxergava o
segundo (L052). O `repack_sheets.py` encolheu as folhas do Ken e só o primeiro
foi atualizado: `pose_size()` devolvia mais do que existe e o streamer lia até
**192 bytes além do fim do array**. Agora `tools/gen_fight_gfx.py` gera o
header a partir das folhas — a folha é a única fonte da verdade, e há
`--check`. Gate de fábrica: `audit_symbol_size_sync.py`.

## O eixo gameplay NÃO fecha — e o motivo não é o jogo
O `evidence.json` pode ainda trazer `interaction_proven` de bundle velho.
**Não trate captura de pixels como prova de input neste host.** Fatos:

1. A fábrica (L038–L040) já exige **direção**, identidade e escala nativa em
   `interaction_verdict`. Bundles anteriores a essa curadoria mentiam com
   `abs(dx)>=8` sozinho — um "Right" com blob à esquerda dava PASS.
2. Ken e Guile ainda podem produzir blobs **idênticos** (309 px, 22×42); de
   pé no deck o gi do Ken funde com as tábuas. Identidade do detector de
   pixels continua frágil aqui; o canal certo é memória (`probe_px`).
3. **O canal de teclado está morto neste ambiente (L039).** `probe_keys =
   0x00` com a tecla pressionada (XSendEvent e XTEST); `getwindowfocus`
   vazio; o reset do Emulicious não reseta. Vale para esta ROM **e para a
   `build_v024`**. Nenhum claim histórico de "gameplay provado por input"
   nesta linha tem lastro.

Instrumento novo: `tools/prove_input_memory.py` responde a pergunta na
memória (`probe_px` = P[0].x), exigindo deslocamento **na direção comandada**
nos dois sentidos. Hoje ele reprova — corretamente, porque o input não chega.
Quando o canal voltar, é ele que fecha o eixo, não o detector de pixels.

## Poses: agachar e pular deixaram de mentir
`ST_JUMP` desenhava a folha de ANDAR e `ST_CROUCH` desenhava a de PARADO — os
estados existiam na FSM sem arte própria. Agora são 8 poses distintas
(idle, walk, punch, special, hit, KO, **crouch**, **jump**).

A arte nova **não** saiu de `art_src_base/`: `author_native_fighters.py` usa
`_fill_from_sheet`, que recorta do rip da Capcom. `tools/author_pose_variants.py`
lê `inc/*_tiles.h` — a arte que o projeto já autora e já entrega — e remodela
a silhueta por faixa (tronco e pernas com fatores diferentes; esmagar tudo por
igual vira chibi). No pulo as pernas também comprimem na horizontal, senão o
lutador fica de pernas abertas e plantadas, com cara de idle esticado.
Custo: 2560 B.

### Gravidade valia só dentro de ST_JUMP (L050)
Levar golpe no ar tirava o lutador de `ST_JUMP`; como só o ramo `airborne` do
`control()` integrava `y`, a queda **parava e ele ficava pendurado no ar** —
e de lá andava, agachava e socava. Quem flagrou foi o probe (L054):
`IDLE/WALK/CROUCH a y=93` com o chão em 112. Agora `apply_gravity()` roda em
qualquer estado e `airborne()` é altura, não estado. Depois do conserto toda
pose de chão tem y mínimo = 112.

### Empurrão no ar
`separate()` empurrava os corpos mesmo a meia altura: ninguém pulava por cima
de ninguém. Passa a ignorar quem está no ar.

## Tela de abertura
Composição, não asset novo: o cais, a fonte e os dois lutadores já estavam na
ROM (que tinha 1553 B livres). A cena é o próprio palco com a **paleta
escurecida** (16 bytes) — menos o índice 1, que fica branco inteiro para o
texto não afundar junto. Título, convite piscando e crédito saem da fonte.

Laço de arcade: **abertura → (Botão 1) luta · (9 s parado) atração → rounds →
KO → resultado → (7 s) abertura**. Antes a ROM nascia no meio de um round e o
resultado era beco sem saída.

`music_title` (577 B) **não** entrou: seria 37% do orçamento livre. A abertura
reusa `music_battle`, que é ostinato e serve de tema.

## O que mudou nesta sessão
**Espaço.** ROM estava em 100% de 32 KB (código até 0x7F70, header em 0x7FF0).
As dez folhas `*_l` eram byte a byte o bit-reverse das base: trocadas por
espelhamento em runtime, equivalência verificada pixel a pixel nas 12 poses.
Mais `repack_sheets.py` (sprites vazios + pares duplicados): 10368 → 9408 B.

**Arte.** `fix_sprite_transparency.py` removeu o placeholder desenhado por
baixo das folhas do Ken (retângulo cor 12 + moldura cor 1) que o VDP mostrava
como caixa azul opaca — defeito visível na `gameplay.png` da sessão anterior.

**Mecânica.** 2P estava morto (`fight_update(ka, 0)`); o roteiro de demo
morava dentro de `control()` disputando o controle com o jogador; um golpe
acertava uma vez por frame ativo; os corpos se atravessavam; a guarda valia
pelas costas; `qcf()` varria o histórico do mais novo para o mais velho,
reconhecendo frente→baixo e dando especial de graça na diagonal. Novos: pulo,
agachar que encolhe a hurtbox, soco alto vs chute baixo, empurrão de corpo,
duplo KO/empate, reinício no resultado.

**Vídeo.** Banco duplo de tiles por lutador: a pose só aparece inteira, fim do
sprite meio velho / meio novo em todo golpe.

**Fonte e HUD.** Não havia glifo nenhum na ROM. 41 glifos + tiles de barra:
nomes, timer, ROUND/FIGHT/K.O./TIME UP/vencedor, barras de verdade.

**Palco.** Cais autoral de 93 tiles (céu em camadas, nuvens, mar com
perspectiva, iate atracado, deck de tábuas, barris) com parallax por
interrupção de linha. **Nenhum pixel de `art_src_base/`** — a sheet da Capcom
é `reference_only` e serviu de régua. O `make_stage()` do
`translate_ssf2t.py`, que jogava o rip direto na ROM contra o §15/§39, foi
desativado.

**Áudio.** SFX tocavam em canal diferente do autorado (`sfx_shot` é de
CHANNEL2, `sfx_hit` de CHANNELS2AND3, ambos iam no CHANNEL3): mix caiu para
86%. Passaram a usar `sfx_hurt`/`sfx_down`, que já eram de canal 3 e estavam
sem uso na ROM. 86% → **94%**, acima até do baseline (92%).

## Decisões
- Flip: **runtime** (bitrev + dx-mirror). Reverte a decisão anterior; custo em `doc/15-tdd.md`.
- `STREAM_BYTES` = 96 B/frame, um lutador por vez. **Não mexer sem remedir o fps.**
- Palco autoral em VRAM 256+ (região só de BG). `reference_only` é régua, nunca fonte.
- Nada de BG ou HUD pode ser o objeto mais saturado com forma de sprite.
- Canvas 32×64 locked. `ready_for_aaa` false.

## Blockers
1. **Input não chega ao emulador** — bloqueia o eixo gameplay e qualquer teste
   de jogabilidade real. É ambiente, não ROM.
2. ROM apertada de novo: 1553 B livres depois do palco.
3. Espelhar em runtime custa CPU: ~57 fps, não os 59,6 do baseline.
4. Silhueta ainda é downsample+quantize da sheet.

## Quais evidências valem para esta SHA
**Atuais:** `poses.json` (agachar/pular por memória), `title.png`, `boot.png`, `evidence.png/json`, `rounds.png`,
`resultado.png`, `volta_ao_titulo.png`, `audio.wav`, `fps.json`,
`runtime_probe.json`, `input_memory.json`.

**De binários anteriores (não usar como prova):** `gameplay*`, `ko1110*`,
`ko1130*`, `ko1145*`, `special*`, `final.png*`, `stage_final*`,
`runtime_probe_diag*`, `audio_ref.wav` (é da build_v024, controle de
ambiente), `audio_pre.wav` (build_v056, mesma finalidade).

## Handoff
Resolver o canal de input (foco de janela / WM) e então fechar o eixo gameplay
com `tools/prove_input_memory.py`. Folhas `inc/*_l_tiles.h` seguem no disco,
fora do build e defasadas — candidatas a remoção.
