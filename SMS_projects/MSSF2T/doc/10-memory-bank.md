# 10-memory-bank — MSSF2T

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-09-07 (manhã) — **O SOCO CONECTA POR INPUT.** O micro-gap 5 fechou:
aproximação até o contato real (gap=20, `PUSH_W`), Botão 1 (tecla A, bit
0x10 = PORT_A_KEY_1 confirmado em `probe_keys`), e o `probe_boss`
(Guile hp) caiu **64→57 = dano 7, hit cheio sem guarda**, com a pose
`POSE_PUNCH` (0x82) observada no `probe_pose` — o golpe SAIU pela RAM,
não por pixel. A causa do whiff da sessão anterior era o instrumento:
o approach antigo parava em gap ≤ 26 e a caixa do soco só alcança
gap < 24 (`fight.c collide`: ax=x+20..+32 contra bx=x+8..+24).
ROM `out/rom/MSSF2T.sms` 32768 B — **SHA inalterada**:
`2990757fb67990c427733114ae676bb5ea38e23d465b5f7b6cbf8d7070a8b6e0`
(nenhum rebuild nesta passada; o instrumento é que mudou).
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
| **gameplay** | **testado_em_emulador** | `input_memory.json` v2: `input_provado=true`, canal VIVO, dx=+85/−67 na direção comandada, `probe_keys`=0x08/0x04 durante o hold; **soco conecta** (`soco_provado=true`, hit −7 com pose 0x82); troca de lado re-observada na mesma run |
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
- Direita: `probe_keys=0x08` **durante** o hold, P[0].x 24→98 (dx=+74).
- Esquerda: `probe_keys=0x04`, P[0].x 98→8 (dx=−90).
- Critério intacto: dx ≥ 8 px NA DIREÇÃO COMANDADA nos dois sentidos, com
  canal vivo. `--self-check` com 12 fixtures, incluindo as regressões exatas
  L039 (canal morto) e L038 (blob andou para o lado oposto e o gate antigo
  dava PASS por abs(dx)).
- Bônus honesto no mesmo artefato: o soco não conectou (guile_hp 64→64),
  mas a **CPU acertou o Ken** no meio da amostragem (hp 64→57) — jogo vivo
  dos dois lados.

### O soco conecta por input (2026-09-07)
Mesmo instrumento, fase nova (`_punch_phase` + `evaluate_punch`, 19
fixtures no `--self-check`): aproxima até encostar (corpos param a
`PUSH_W`=20, dentro do alcance <24), B1 de 9 frames, polling do
`probe_boss` por 1,4 s, retry ×3 com recuo. Run selada
(`input_memory.json`, mesma SHA):
- tentativa 0: **whiff honesto** — B1 não chegou no 1º toque
  (`pose_no_b1`=0x81 WALK, hp 64→64); o retry é do instrumento.
- tentativa 1: `pose_punch_vista`=0x82 (POSE_PUNCH|facing) e
  **guile_hp 64→57 (delta 7 = hit cheio, sem guarda)** — CONECTOU.
- Critério: canal vivo + gap < 24 lido antes do golpe + queda de
  `guile_hp`. Hit (−7), chip de guarda (−2) e KO (0) são conexões;
  64→64 é whiff — fixture da regressão selada no self-check.
- Nota honesta: `probe_keys` no instante pausado mostrava 0x08 (Right
  do approach se cruzando com o keydown do A na mesma leitura); a
  agência do soco está na pose 0x82 + queda de hp, não nesse sample.
- Ken levou 64→54 da CPU durante as amostras (hp no Left) — jogo vivo
  dos dois lados.

### L053: de "correto por leitura" para OBSERVADO
Mesma fase do instrumento: aproximação até gap ≤ 30, passo atrás para sair
do hitstun, pulo com Cima+Direção. Artefato selado (`input_memory.json`):
`min_py=57`, `cruzou_no_ar=true`, aterrissou px=89 > p2x=67, `probe_pose`
0x81 → 0x01 — **o facing virou para o novo lado**, exatamente o que o
conserto (`apply_pose` dentro de `update_facing`) deveria fazer.
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
  diagnóstico descartável `tools/diag_input.py` removidos. Rebuild **não**
  saiu byte-idêntico (SDCC); SHA desta evidência = `2990757f…`.
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
- Input de prova neste host: **kdotool + ydotool** (`emulator_input.py`).
  xdotool/XTEST não atravessa o KWin (L039).

## Blockers
1. ~~Input não chega ao emulador~~ **RESOLVIDO** — era Wayland/KWin (L039).
   Canal vivo por kdotool+ydotool; eixo gameplay fechado.
2. ROM apertada: **1091 B livres**.
3. Espelhar em runtime custa CPU: contador interno ~57 fps durante o probe
   (título do emulador: 59.8). Diferença é overhead de pausa/attach do DAP —
   remedir sem attach antes de culpar o flip.
4. Silhueta ainda é downsample+quantize da sheet.
5. ~~Soco não conecta~~ **RESOLVIDO (2026-09-07)** — era o instrumento
   (approach parava em gap ≤ 26, fora do alcance < 24). A distância real,
   hit cheio −7 observado por RAM. Ficou registrado que a CPU ora guarda
   (chip −2) ora não; K.O. por soco seguido é o teste natural seguinte.

## Quais evidências valem para esta SHA
**Atuais (2026-09-07, manhã, binário `2990757f…`, seladas juntas):**
`input_memory.json` (v2: input + soco −7 + sideswap), `fps.json`,
`runtime_probe.json`, `evidence.png` (boot/abertura), `laco2.png`
(KEN WINS), `audio.wav` (92%), `evidence_bundle.json` (**selado com 7
artefatos frescos**). `poses.json` reprovou 3× no re-run de manhã (a
janela de observação da atração desalinha com o ciclo do roteiro — cada
falha perdeu uma pose diferente); o artefato da noite continua valendo
para CROUCH (mesma SHA), e JUMP/PUNCH aparecem dentro do
`input_memory.json` fresco (0x87 no voo, 0x82 no soco).

**De sessões anteriores, mesma SHA (referência, não selo fresco):**
`laco.png`, `title.png`, `rounds.png`/`resultado.png`/
`volta_ao_titulo.png`, `poses.json`.

**De binários anteriores (não usar como prova):** `gameplay*`, `ko1110*`,
`ko1130*`, `ko1145*`, `special*`, `final.png*`, `stage_final*`,
`runtime_probe_diag*`, `audio_ref.wav` (controle de ambiente),
`audio_pre.wav` (controle), `input_memory_old.json` e tudo o que foi
produzido contra o binário `e42c4887…`.

## Handoff
O golden slice do GDD está fechado em todos os eixos exceto os que a própria
GDD marca fora do `ready_for_aaa`. Degraus seguintes, em ordem causal:
1. ~~Soco conectando por input~~ **FECHADO (2026-09-07)** — hit −7 por RAM,
   `soco_provado=true` em `input_memory.json`. Extensão natural, não
   blocker: sequência de socos até o K.O. com a CPU devolvendo (fecha o
   laço "golpe→dano→round decidido" com input nos dois lados).
2. **Worst-frame de VBlank medido em ROM** (`doc/13-spec-cenas.md` segue
   "documentado", nunca medido) — ATENÇÃO: medir exige instrumentar a ROM
   (contador de overrun/atraso no probe) e portanto **rebuild = SHA nova =
   re-medir TODA a evidência** (input/fps/áudio/probe/boot/laço/poses/selo)
   contra o binário novo. Planejar a janela para isso.
3. Só então, nova arte autoral (silhueta própria, blocker 4).

Curadoria L039/L053 (Wayland/uinput + troca observada) **fechada na fábrica**
em 2026-09-07: `emulator_input.py`, `reconcile_claims` aceita
`input_memory.json` com SHA da ROM.

### Nota de ambiente (2026-09-07, manhã)
Uma **segunda sessão de agente** rodava a suíte `laboratorio_01` no MESMO
Emulicious/host durante esta passada. Colisões reais: handoff
single-instance (meu boot nasceu no estado DELA, frame=1159), higiene
`pkill` mútua derrubando o DAP no meio do run, e disputa de foco de teclado
(kdotool `ids[0]` não distingue duas janelas "Emulicious"). Solução da
vez: arbitragem humana — a irmã foi pausada e o host ficou livre. Rotina
futura: conferir `pgrep -f "Emulicious[.]jar"` antes de rodar e nunca
disputar foco; `pkill` sempre com padrão `Emulicious[.]jar` (o padrão sem
colchetes mata o próprio shell que o executa).

## Ciclo 2026-09-07 (tarde) — trilha do cenário do Ken + dois defeitos de gate

### O que entrou na ROM
`music_battle` era uma sirene de 6 notas em uníssono nos três osciladores
(49 B, 12 frames repetidos 240×). Entrou no lugar um tema autoral: Lá menor
com G# emprestado da menor harmônica na cadência, 150 BPM, 8 compassos,
loop de 12,8 s, quatro canais com papéis separados (lead / harmonia que
vira arpejo nas viradas / baixo motor em colcheias / percussão de ruído).
Gerador: `tools/gen_music_ken_stage.py`, que serializa direto no formato
PSGlib. 945 B — `_CODE` vai a 0x7F2D e **sobram 211 bytes** no cartucho de
32 KB. Qualquer asset novo daqui pra frente exige banking.

Verificado no emulador, não só no papel: as viradas de acorde F3/G3/D3/E3
aparecem na captura de áudio real nas mesmas posições de tempo do render de
referência, dentro de 0,2 s.

### Defeito 1 — `audit_audio` media continuidade, não presença de som
O gate contava `|amostra| > 200` uma a uma. Toda onda periódica cruza o
zero, e cada cruzamento entrava como amostra "inativa": **quanto mais rica
a polifonia, pior a nota**. A sirene antiga (1 cruzamento de zero por
segundo) marcava 99,9%; o tema novo, sem nenhuma lacuna de silêncio além de
11 ms no boot, reprovava com 88%. Subir as atenuações do PSG elevou o peak
e ainda assim baixou o índice — prova de que o eixo medido não era nível.
Agora mede RMS em janelas de 10 ms. Silêncio continua dando 0%.

### Defeito 2 — nenhuma ferramenta promovia eixo para `true`
`build_inner.py` inicializava os 7 eixos em `false` e só **herdava** os
`true` do registro anterior; `reconcile_claims.py` apenas conferia. Logo o
primeiro `true` de qualquer projeto só podia ter vindo de edição à mão do
`build_record.json` — o que `release-rom.md` proíbe. Os eixos não tinham
como fechar pelo caminho legítimo.

Correção: os predicados viraram `reconcile_claims.axis_support()`, fonte
única, e `build_inner` **deriva** dali em vez de herdar. Quem grava e quem
confere não podem mais divergir.

### Defeito 3 (descoberto pela correção anterior)
Com a derivação ligada, `boot_emulador`, `fps_constante` e
`memory_bank_atualizado` ficaram `true` sustentados por artefatos **8h mais
velhos** que a ROM. Causa: `demote_stale_axes` tinha um atalho que, quando
o sha não mudava entre dois builds, retornava `PRESERVADO` e **pulava a
demoção inteira**. O atalho existia porque recompilar renovava o mtime da
ROM — causa já corrigida na raiz por `rom_birth_mtime`. Era remendo sobre
problema morto, e deixava passar evidência genuinamente velha. Removido: a
comparação por data já acerta sozinha com o mtime de nascimento restaurado.

`selftest.py`: 57/57 verdes depois das três mudanças.

### REGRESSÃO ABERTA — o soco voltou a não conectar
Este mesmo documento registra, na seção de handoff, "Soco conectando por
input **FECHADO (2026-09-07)** — hit −7 por RAM, `soco_provado=true`".
**Não reproduz.** `prove_input_memory.py` nesta ROM, 3 tentativas:

    soco tentativa 0: gap=20 keys_b1=0x08 pose_b1=129 guile_hp 64->64
    soco tentativa 1: gap=22 keys_b1=0x08 pose_b1=129 pose_punch=130 guile_hp 64->64
    soco tentativa 2: gap=20 keys_b1=0x08 pose_b1=133 guile_hp 64->64
    [soco] NAO conectou — whiff, a regressao exata da amostra selada

O B1 chega (`keys_b1=0x08`), a pose de soco troca (130), a distância está
em 20–22 px, e o HP do Guile não move. A mudança desta sessão foi só de
áudio, então **não é candidata plausível a causa** — o mais provável é que
o fechamento da manhã tenha sido observação de uma amostra favorável, não
propriedade estável. O eixo `gameplay` fecha pelo predicado de
deslocamento (`input_provado` + canal vivo + SHA), que é o que
`reconcile_claims` exige; o soco **não** está provado e não deve ser
reivindicado em release.

Próximo degrau, antes de qualquer arte nova: reproduzir o whiff de forma
determinística (frame de ativo do hitbox vs. gap) e decidir se o defeito é
de alcance, de janela de ativo ou de detecção de colisão.
