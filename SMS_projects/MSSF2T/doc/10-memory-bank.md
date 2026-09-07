# 10-memory-bank — MSSF2T

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-09-06 (noite) — **O EIXO GAMEPLAY FECHOU.** O canal de teclado estava
morto por causa do Wayland (L039): o xdotool/XTEST nunca atravessa o KWin.
Canal reaberto com **kdotool** (foco via KWin/DBus) + **ydotool** (uinput,
nível kernel) — o evento nasce dentro do kernel e o KWin entrega a quem
estiver focado. Com input real: Ken anda nos dois sentidos (registrado em
`probe_keys`), e a **troca de lado da L053 foi observada** por pulo por cima.
ROM `out/rom/MSSF2T.sms` 32768 B
SHA-256 `2990757fb67990c427733114ae676bb5ea38e23d465b5f7b6cbf8d7070a8b6e0`
(este é o binário DO REBUILD desta sessão, após a limpeza das folhas `_l`.
O rebuild **não** saiu idêntico ao anterior `e42c4887…` — o não-determinismo
de binário do SDCC, já registrado no projeto, vale aqui: mesmo fonte, SHA
diferente. Por isso TODA a evidência abaixo foi re-medida DEPOIS do rebuild,
contra o binário novo; o selo `evidence_bundle.json` atesta a frescor.)
Espaço livre de ROM: **1091 B**.

## Eixos — todos medidos NESTA SHA
| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | 32768 B, 1091 B livres, rebuild idempotente |
| validation_report | buildado | `out/build_record.json` |
| boot_emulador | testado_em_emulador | `evidence.png` (luma 6337/5100) |
| fps_constante | testado_em_emulador | título do emulador: 59.8 médio (59–60, 6 amostras); contador da ROM via DAP: 56.5–57.7 (overhead de pausa do probe) |
| audio | testado_em_emulador | `audio.wav` peak=7329, **92% ativo** — PASS |
| abertura | testado_em_emulador | `evidence.png` (boot, abertura; luma 6337/5100) |
| laço de arcade | testado_em_emulador | `laco2.png` (**KEN WINS**, 90 s) + `laco.png` (atração viva, 70 s) — nesta SHA |
| KO | testado_em_emulador (indireto) | não se chega a KEN WINS (melhor de três) sem round decidido; banner K.O. segue sem frame capturado |
| **gameplay** | **testado_em_emulador** | `input_memory.json` v2: `input_provado=true`, canal VIVO, dx=+85/−63 na direção comandada, `probe_keys`=0x08/0x04 durante o hold |
| memory_bank_atualizado | documentado | este arquivo |

`reconcile_claims.py` e `seal_fresh_evidence_bundle.py` rodam DEPOIS deste
arquivo (ordem de frescor: evidência → memory bank → conciliação → selo).

### Nota sobre o eixo KO
O frame do banner "K.O." **segue sem captura exata**: dura 120 frames e cair
no timing é loteria (nesta sessão, 70 s e 90 s caíram na luta da atração e
no KEN WINS). O KO segue provado **indiretamente e sem ambiguidade**: não se
chega a "KEN WINS" (melhor de três) sem round decidido — e `laco2.png`
mostra exatamente isso, fresco, nesta SHA.

## O canal de teclado: causa raiz encontrada (L039 → resolvida)
Fatos medidos nesta sessão:
1. A sessão do host é **KDE Plasma sobre Wayland** (`XDG_SESSION_TYPE=wayland`,
   `kwin_wayland` ativo, Emulicious é cliente Xwayland). Nesse arranjo o
   `xdotool` fica cego (`getwindowfocus` vazio) e o XTEST não entrega evento
   — exatamente os sintomas da L039. **Não era maldade do Java nem da ROM.**
2. O canal real é **kdotool** (ativa a janela via script do KWin por DBus) +
   **ydotool** (injeção via `/dev/uinput`, nível kernel; daemon `ydotoold`
   com socket dedicado `/tmp/.ydotool_socket_smsforge`).
3. Canário de canal: o reset do próprio Emulicious (Ctrl+BackSpace) zera
   `probe_frame` (ex.: 469 → 40). Sem isso, nenhuma leitura tem lastro.
4. Mapeamento físico descoberto por leitura de `probe_state`: **Botão 1 =
   tecla A** (título → luta na primeira amostra: Z e X não, A sim).
   Direcionais são as setas; pulo = Cima.

## O eixo gameplay fechou — e a troca de lado foi observada
`tools/prove_input_memory.py` (v2, mesma ROM):
- Partida REAL: B1 no título (a atração morre no primeiro toque).
- Direita: `probe_keys=0x08` **durante** o hold, P[0].x 20→105 (dx=+85).
- Esquerda: `probe_keys=0x04`, P[0].x 105→42 (dx=−63).
- Critério intacto: dx ≥ 8 px NA DIREÇÃO COMANDADA nos dois sentidos, com
  canal vivo. `--self-check` com 12 fixtures, incluindo as regressões exatas
  L039 (canal morto) e L038 (blob andou para o lado oposto e o gate antigo
  dava PASS por abs(dx)).
- Bônus honesto no mesmo artefato: o soco não conectou (guile_hp 64→64),
  mas a **CPU acertou o Ken** no meio da amostragem (hp 64→57) — jogo vivo
  dos dois lados.

### L053: de "correto por leitura" para OBSERVADO
Mesma fase do instrumento: aproximação até gap ≤ 30, passo atrás para sair
do hitstun, pulo com Cima+Direção. Na primeira tentativa: `min_py=58` (subiu
54 px), `cruzou_no_ar=true`, aterrissou com px=116 > p2x=96, e
`probe_pose` 0x84 → 0x01 — **o facing virou para o novo lado**, exatamente o
que o conserto (`apply_pose` dentro de `update_facing`) deveria fazer.
Limite honesto mantido: o espelhamento **visual** do sprite na tela segue
provado por leitura do código; o probe enxerga a lógica, não os pixels.
Detalhe de método: a 1ª tentativa da sessão falhou honestamente
(min_py=112) porque em contato com a CPU o lutador está busy e o Cima é
ignorado — o instrumento ganhou retry com recuo; a falha ficou no log.

## Poses: agachar e pular deixaram de mentir
`ST_JUMP` desenhava a folha de ANDAR e `ST_CROUCH` a de PARADO. Agora são 8
poses distintas (idle, walk, punch, special, hit, KO, crouch, jump).
`poses.json` re-medido nesta sessão: agachar/pular provados por memória;
JUMP com menor y=67. A arte nova não saiu de `art_src_base/` (ver seção
anterior no git — `author_pose_variants.py` remodela a silhueta a partir das
folhas próprias). Custo: 2560 B.

### Gravidade valia só dentro de ST_JUMP (L050)
`apply_gravity()` agora roda em qualquer estado; `airborne()` é altura, não
estado. Depois do conserto toda pose de chão tem y mínimo = 112.

### Empurrão no ar
`separate()` ignora quem está no ar — por isso o pulo por cima agora cruza.

## Recuperação de ROM: a música era 240 cópias do mesmo frame
`music_battle` tinha 2881 B — 240 repetições byte a byte do mesmo frame de
12 B (L051). Cortado para 49 B (`tools/shrink_music_loop.py`): 3264 B
recuperados com áudio medido igual. Gate: `audit_psg_redundancy.py`.

## fight_gfx.h dizia 1024 para folha de 832 (L052)
O tamanho vivia em dois lugares e divergiu: leitura de 192 B além do array.
Agora `tools/gen_fight_gfx.py` gera o header a partir das folhas (fonte
única) e há `audit_symbol_size_sync.py`.

## Tela de abertura e laço de arcade
Composição com o que já havia (paleta escurecida, índice 1 branco para o
texto). Laço: **abertura → (Botão 1) luta · (9 s parado) atração → rounds →
KO → resultado → (7 s) abertura**. `music_title` fora do orçamento; a
abertura reusa `music_battle`.

## O que mudou nesta sessão (noite)
- **Instrumento:** `prove_input_memory.py` v2 — backend Wayland (kdotool +
  ydotool) com fallback X11 legado; leitura de `probe_keys` COM a tecla em
  baixo; partida real a partir do título; fase de troca de lado com retry;
  `--self-check` de 12 fixtures. A prova de input NÃO usa pixels.
- **Limpeza:** as 14 folhas `inc/*_l_tiles.h` (defasadas, fora do build) e o
  diagnóstico descartável `tools/diag_input.py` removidos. Rebuild saiu
  byte a byte idêntico (`e42c4887…`).
- **Evidência:** toda a cadeia re-medida contra o binário do rebuild:
  `input_memory.json` (v2, com sideswap), `fps.json` (59.8),
  `runtime_probe.json` (57.69/56.51), `evidence.png` (boot/abertura),
  `laco.png`/`laco2.png` (atração viva e KEN WINS), `audio.wav` (92%),
  `poses.json`. A captura de áudio falhou 3× silenciosa e passou no
  retry — transitório de ambiente (L048/L019), sem mexer na ROM.
- **Bug pego pelo selo:** a 1ª versão do instrumento v2 gravava
  `input_provado=false` no JSON enquanto o stdout imprimia PASS —
  `evidence_bundle` reprovou a contradição claim↔artefato; corrigido
  (o veredito agora é gravado no campo) e a fixture da regressão entrou no
  `--self-check`.
- **Git:** projeto versionado (baseline `b63eef0` antes das mudanças).

## Decisões
- Flip: **runtime** (bitrev + dx-mirror). Reverte a decisão anterior; custo
  em `doc/15-tdd.md`.
- `STREAM_BYTES` = 96 B/frame, um lutador por vez. **Não mexer sem remedir o
  fps.**
- Palco autoral em VRAM 256+ (região só de BG). `reference_only` é régua,
  nunca fonte.
- Canvas 32×64 locked. `ready_for_aaa` false.
- Input de prova: **memória, nunca pixels** neste host (L035/L038/L054).
- Curadoria da lição de input (JSON canônico + seção em SMS_GLOBAL + gate no
  wrapper) ficou **proposta pendente de aprovação humana** — o memory bank
  do projeto registra o fato; a fábrica formaliza depois.

## Blockers
1. ~~Input não chega ao emulador~~ **RESOLVIDO** — era Wayland/KWin (L039).
   Canal vivo por kdotool+ydotool; eixo gameplay fechado.
2. ROM apertada: **1091 B livres**.
3. Espelhar em runtime custa CPU: contador interno ~57 fps durante o probe
   (título do emulador: 59.8). Diferença é overhead de pausa/attach do DAP —
   remedir sem attach antes de culpar o flip.
4. Silhueta ainda é downsample+quantize da sheet.
5. Soco ainda não provado CONECTANDO por input (guile_hp 64→64 na amostra;
   a CPU acertou o Ken, o Ken não acertou de volta) — micro-gap aberto.

## Quais evidências valem para esta SHA
**Atuais (desta sessão, noite, binário `2990757f…`):** `input_memory.json`
(v2 + sideswap), `poses.json`, `evidence.png` (boot/abertura), `laco.png`,
`laco2.png` (KEN WINS), `fps.json`, `runtime_probe.json`, `audio.wav`,
`evidence_bundle.json` (selado, 8 artefatos).

**De binários anteriores (não usar como prova):** `gameplay*`, `ko1110*`,
`ko1130*`, `ko1145*`, `special*`, `final.png*`, `stage_final*`,
`runtime_probe_diag*`, `audio_ref.wav` (controle de ambiente),
`audio_pre.wav` (controle), `input_memory_old.json`, e **toda a evidência
produzida contra o binário `e42c4887…`** — inclusive `title.png`,
`rounds.png`/`resultado.png`/`volta_ao_titulo.png` da tarde: mesmos bytes de
fonte, binário diferente; servem de referência visual, não de prova.

## Handoff
O golden slice do GDD está fechado em todos os eixos exceto os que a própria
GDD marca fora do `ready_for_aaa`. Degraus seguintes, em ordem causal:
1. **Soco conectando por input** (fechar o micro-gap 5: aproximar, socar,
   ler `probe_boss` cair) — mesmo instrumento, meia hora.
2. **Curadoria da lição de input** (Wayland/XTEST → uinput): JSON canônico
   em `doc/curation/` + seção em SMS_GLOBAL + gate no wrapper — exige
   aprovação humana explícita (modo curadoria).
3. **Worst-frame de VBlank medido em ROM** (`doc/13-spec-cenas.md` segue
   "documentado", nunca medido) — orçamento de cena fecha de verdade.
4. Só então, nova arte autoral (silhueta própria, blocker 4).
