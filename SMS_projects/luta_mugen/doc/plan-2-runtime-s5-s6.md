# Plano 2 — Runtime S5–S6 + contrato de escala no conversor (luta_mugen)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fechar o furo medido do S4 (gate `audit_sprite_line_sim` = FAIL, pico 32/linha,
SAT 256) aplicando o contrato de escala travado no GDD, e então construir o runtime Z80
que interpreta as tabelas geradas até a golden slice (cena 03) com evidência no emulador.

**Architecture:** O motor (Python, `tools/sms_wrapper/mugen2sms/`) ganha uma etapa S4.5:
downscale 1:4 fixo + emissão de arte no formato de runtime provado pelo MSSF2T (metasprite
de 3 bytes `{dx, dy, tile}` + `METASPRITE_END`; espelhamento horneteado como tile extra,
porque **o SAT do SMS não tem flip de sprite** — precedente: MSSF2T `src/fight.c:1108-1129`
usa `TILE_FB1L`, um tile espelhado separado). O consumidor (`SMS_projects/luta_mugen/src/`)
é um interpretador de tabelas compiladas: FSM por dados, física Q8.8, colisão clsn em
software, streaming de VRAM só no VBlank, banking Sega mapper.

**Tech stack:** Python 3 (conversor, testes pytest), SDCC + devkitSMS (`sdk/devkitSMS`,
headers = autoridade #8), gates do harness `tools/sms_wrapper/` (mesmo harness que deu
FAIL — ele é o veredito, não opinião minha).

**Spec:** `SMS_projects/luta_mugen/doc/11-gdd.md` §"Escala do lutador — TRAVADA" +
`doc/15-tdd.md` §"Corte jogável" + `doc/10-memory-bank.md` (estado real).

## Global Constraints

- Escala travada (GDD 2026-09-25, decisão humana): `SPRITEMODE_TALL` 8×16; lutador
  **≤4 sprites TALL por scanline** (~32 px) × **≤3 de altura** (~48 px); downscale
  **1:4 fixo** no conversor; pose que ainda estourar vira `manual` e **não entra no
  build**; flicker/rotação de prioridade para mascarar overflow é proibido.
- Cena versus: 2 lutadores = pico 8/scanline **exato** (teto físico), SAT ≤ 64.
- ❌ float/double em runtime; ❌ malloc/free; ❌ API inventada — só o que está citado
  em `sdk/devkitSMS/SMSlib/SMSlib.h` / `PSGlib/PSGlib.h` (linhas citadas por tarefa);
  ❌ VRAM fora do VBlank; ❌ lógica de build fora de `tools/sms_wrapper/`.
- Ken/arte real **nunca** no Git: derivativos só em `out/local_study/` (gitignored);
  o repo comita apenas fixtures sintéticos e o runtime.
- Paridade de doação: todo arquivo novo do fork é registrado em
  `doc/doacao_md_mugen2sms.json` como `origin: "local_original"` com
  `local_sha256_after_deviation`; editar arquivo pinado exige **re-pin** no mesmo commit.
- Gate final = ROM vista rodando no emulador com evidência selada ao SHA da ROM
  (`seal_fresh_evidence_bundle.py`). `documentado ≠ implementado ≠ buildado ≠
  testado_em_emulador`.
- APIs verificadas (usar EXATAMENTE estas; header é a fonte):
  - `SMS_setSpriteMode(SPRITEMODE_TALL)` — SMSlib.h:54-57
  - `SMS_addMetaSprite(x, y, metasprite)` / `METASPRITE_END 0x80` — SMSlib.h:214-216
  - `SMS_initSprites()` SMSlib.h:188 · `SMS_copySpritestoSAT()` SMSlib.h:211
  - `SMS_loadTiles(src, tilefrom, size)` = 4bpp/32B por tile — SMSlib.h:130
  - `SMS_setBGPaletteColor/SMS_setSpritePaletteColor(entry,color6bit)` — SMSlib.h:249-250
  - `SMS_getKeysHeld()/SMS_getKeysPressed()` + `PORT_A_KEY_*` (UP 0x0001, DOWN 0x0002,
    LEFT 0x0004, RIGHT 0x0008, **1** 0x0010, **2** 0x0020, START=1) — SMSlib.h:287-303
  - `SMS_setTileatXY(x,y,tile)` — SMSlib.h:117 · `SMS_useFirstHalfTilesforSprites(1)`
    (lei L006; já em uso no esqueleto `src/main.c`)
  - `SMS_mapROMBank(n)` / `SMS_saveROMBank()` / `SMS_restoreROMBank()` — SMSlib.h:70-83
  - `PSGPlay(song)` / `PSGFrame()` por VBlank / `PSGSFXPlay(sfx, SFX_CHANNELS2AND3)` —
    PSGlib.h:37-43, 56-57, 8-11 (SFX só nos canais 2+3; música nos 0+1)

**Blocker herdado (documentado no memory bank):** o round Ken do S4 gerou cena com pico
32/scanline e SAT 256 → `veredito: FAIL`. As Tasks 1–2 invertem esse número com o MESMO
gate.

---

### Task 1: S4.5a — downscale 1:4 e reclassificação no conversor

**Files:**
- Create: `tools/sms_wrapper/mugen2sms/converters/sms_scale.py`
- Modify: `tools/sms_wrapper/mugen2sms/analysis/fidelity.py` (poses usam escala de runtime p/ classe)
- Modify: `tools/sms_wrapper/mugen2sms/generators/smsdev.py:77` (`generate` aplica escala antes de `to_sms_pose`)
- Test: `tools/sms_wrapper/mugen2sms/tests/test_sms_scale.py`
- Modify: `SMS_projects/luta_mugen/doc/doacao_md_mugen2sms.json` (registrar novo + re-pin dos editados)

**Interfaces:**
- Consumes: `Pose/placements` de `converters/sms_tiles.to_sms_pose`; `classify_character(ch, limits)` de `analysis/fidelity`.
- Produz: `sms_scale.MAX_COLS = 4`, `sms_scale.MAX_TALL_ROWS = 3`, `sms_scale.SCALE = 4`,
  `sms_scale.downscale_indexed(sp, k=4) -> SimpleNamespace(width,height,pixels,palette,group,image)`
  (nearest topo-esquerda, mesmo método de `prepare_sms_pixel_art.py`; o input é o sprite
  IR — `.width/.height/.pixels flat/.palette RGB tuples),
  `sms_scale.pose_runtime_size(w_px, h_px) -> tuple[int,int]` (pós-1:4, por excesso),
  `sms_scale.needs_scale(w,h) -> bool` (não cabe 4 col × 3 TALL em 1:1),
  `sms_scale.exceeds_budget(w,h) -> bool` (nem 1:4 salva → `manual`).

- [x] **Step 1: Teste falho** — `tests/test_sms_scale.py`:

```python
from converters import sms_scale as sc

def test_downscale_nearest_mantem_indices():
    img = {"w": 16, "h": 16, "palette": [(0,0,0),(255,0,0),(0,255,0)],
           "pixels": [bytes([1]*16) if y < 8 else bytes([2]*16) for y in range(16)]}
    out = sc.downscale_indexed(img, 4)
    assert (out["w"], out["h"]) == (4, 4)
    assert all(row == bytes([1,1,1,1]) for row in out["pixels"][:1])
    assert all(row == bytes([2,2,2,2]) for row in out["pixels"][1:])

def test_orcamento_pose_poca_escala():
    # 128x112 nativo -> 32x28 -> 4 colunas de 8px; 28px = 2 linhas TALL + sobra p/ 3a
    assert sc.pose_runtime_size(128, 112) == (4, 2)   # (colunas, linhas TALL) ceil
    assert not sc.exceeds_budget(128, 112)
    # 48 px de largura pós-escala = 192 nativo -> 6 colunas > 4 -> manual
    assert sc.exceeds_budget(192, 48)
```

- [x] **Step 2:** `pytest tests/test_sms_scale.py -v` → FAIL (`No module named ... sms_scale`).

- [x] **Step 3: Implementar `sms_scale.py`** — `downscale_indexed` amostra nearest
  (`px[y*k//h][x*k//w]`), preserva `palette` intacta (cores já são do contrato — a
  paleta não muda ao reduzir; só a contagem de pixels). `pose_runtime_size`:
  `cols = -(-w8 // 8)` com `w8 = -(-w_px // SCALE)`; idem linhas TALL (16 px).
  `exceeds_budget = cols > MAX_COLS or rows > MAX_TALL_ROWS`. Sem dependências novas.

- [x] **Step 4: Ligar no fluxo.** Em `generators/smsdev.generate`, antes de
  `to_sms_pose(sp)`, aplicar `downscale_indexed(sp_img, sc.SCALE)`; se
  `sc.exceeds_budget(w,h)` da pose resultante → adicionar `Element("pose:<n>.<i>",
  "manual", "estourou-apos-escala")` ao relatório e **pular** a arte (linha no
  `s4_generation_report.json` `excluded_by_classe.manual`). Em
  `analysis/fidelity.classify_character`, a regra `scanline>8` passa a usar o
  orçamento **pós-escala** (`pose_runtime_size` da bounding box da pose × 2 lutadores).

- [x] **Step 5: Testes verdes + round Ken local** (arte fora do Git):

```bash
cd tools/sms_wrapper/mugen2sms && python3 -m pytest tests/ -q           # esperado: tudo verde
python3 -m generators.smsdev "/mnt/sdcard/Projects/Mugenesis/Base de Estudo/chars/street-fighter/ken_masters_adv.zip" \
    --out ../../SMS_projects/luta_mugen/out/local_study/generated
```
  (o CLI real é `smsdev <pacote> --out <dir>` — generators/smsdev.py:169-170; rodada
  local a partir de `tools/sms_wrapper/mugen2sms`, ~3 min em background)
  Esperado: `s4_generation_report.json` sem traceback e com `estourou-apos-escala`
  em `excluded_by_classe.manual`. O `gate_scanline` pode **virar PASS já aqui**
  (worst-scene agora conta a pose pós-escala) — reportar o número medido, sem
  assumir veredito.

- [x] **Step 6: Re-pin do manifest + commit** (rode o script que recalcula
  `local_sha256_after_deviation` dos 3 arquivos editados + registra `sms_scale.py`):

```bash
git add tools/sms_wrapper/mugen2sms/converters/sms_scale.py \
        tools/sms_wrapper/mugen2sms/analysis/fidelity.py \
        tools/sms_wrapper/mugen2sms/generators/smsdev.py \
        tools/sms_wrapper/mugen2sms/tests/test_sms_scale.py \
        SMS_projects/luta_mugen/doc/doacao_md_mugen2sms.json
git commit -m "feat(mugen2sms): S4.5a downscale 1:4 travado pelo GDD no conversor"
```

---

### Task 2: S4.5b — formato de runtime (metasprite 3B, tiles TALL pareados, flip horneteado, P2 por shift de índice)

**Files:**
- Create: `tools/sms_wrapper/mugen2sms/generators/runtime_format.py`
- Modify: `tools/sms_wrapper/mugen2sms/generators/smsdev.py` (gera também `<slug>_runtime.h/.c` no formato do runtime)
- Test: `tools/sms_wrapper/mugen2sms/tests/test_runtime_format.py`
- Modify: manifest (registro + re-pin)

**Interfaces:**
- Consumes: `Pose(width,height,tiles,placements,...)` de `converters/sms_tiles`.
- Produz:
  - `runtime_format.build_frames(pose, tile_base: int) -> bytes` — sequências de
    3 bytes **`dx, dy, tile`** terminadas por `dx=0x80` (`METASPRITE_END`), formato
    provado em ROM por MSSF2T (`SMS_projects/MSSF2T/src/fight.c:1095-1129`).
  - `runtime_format.pack_tiles_tall(pose) -> (blob, map_flip)` — blob = concatenção de
    pares verticais (topo 8×8, base 8×8) **por construção da fonte**: o conversor já
    sabe que uma pose tem alturas 16; índice local sempre par. `map_flip[(tx,ty)]` →
    índice do tile espelhado horizontalmente (bytes invertidos pixel a pixel; SMS não
    tem flip de sprite — espelho é outro padrão, custo medido de VRAM).
  - `runtime_format.shift_palette_indices(blob, offset)` — cópia com `idx+offset`
    (P2 = mesmos padrões em faixa de índices distinta do MESMO sprite palette; a
    restrição medida é `|pal(P1) ∪ pal(P2)| ≤ 15` — sprite palette única do SMS,
    SMSlib.h:249-250).

- [x] **Step 1: Teste falho** — `tests/test_runtime_format.py`:

```python
from generators import runtime_format as rf
from converters.sms_tiles import Pose, Placement

def _mini_pose():
    tiles = [bytes(32), bytes(range(32))]                      # 2 tiles 4bpp
    return Pose(width=8, height=16, tiles=tiles,
                placements=[[Placement(0, False, False, 0, 0),
                             Placement(1, True,  False, 0, 8)]],
                palette=(), unique_tiles=2, flips_used={1})

def test_metasprite_triples_e_fim():
    b = rf.build_frames(_mini_pose(), tile_base=0x20)
    assert b[0:3] == bytes([0, 0, 0x20])                  # dx,dy,tile
    assert b[3:6] == bytes([0, -8 & 0xFF, 0x21])          # segundo sprite
    assert b[6] == 0x80 and len(b) == 7

def test_flip_vira_tile_espelhado_distinto():
    pose = _mini_pose()
    blob, mirrors = rf.pack_tiles_tall(pose)
    mirrored = mirrors[1]                      # tile 1 tinha hflip
    # linha 0 da fonte = planos (0x00,0x01,0x02,0x03): espelhar inverte bits de cada plano
    assert blob[mirrored*32 : mirrored*32 + 4] == bytes([0x00, 0x80, 0x40, 0xC0])
    assert blob[mirrored*32 : (mirrored+1)*32] != pose.tiles[1]  # espelho é OUTRO padrão
```

- [x] **Step 2:** `pytest tests/test_runtime_format.py -v` → FAIL (`No module named`).

- [x] **Step 3: Implementar `runtime_format.py`** conforme interfaces acima. Regras
  duras: `dx = tx*8`, `dy = -(altura - (ty*16+16))` (origem do metasprite = pés,
  como MSSF2T espera); tile espelhado é alocado depois dos normais (dedup por
  conteúdo do blob). `shift_palette_indices` soma `offset` só a índices `!=0`.

- [x] **Step 4: Emitir runtime no `smsdev.generate`** — por personagem:
  `<slug>_runtime.c` com tabelas nomeadas:

```c
const unsigned char pose_meta_<anim>_<frame>[] = { /* rf.build_frames */ 0x80 };
const struct { unsigned char dur_frames; const unsigned char *meta; } frames_<slug>[] = {...};
const unsigned char tiles_<slug>[];  unsigned int tiles_<slug>_len;  /* base 0 = tile par */
const unsigned char pal_<slug>_bg[16], pal_<slug>_spr[16];           /* bytes 6-bit */
const signed int clsn_<slug>[];                                      /* int16, já do S4 */
const unsigned char patt_<slug>[];                                   /* StepCodes do sms_cmd */
```

- [x] **Step 5: Gate do harness tem que virar verde.** Rodar o round Ken local; o
  worst-scene do `s4_generation_report.json` agora conta **por formato de runtime**:
  2 lutadores × ≤4 sprites/linha + entradas de espelho não contam na scanline.

```bash
python3 -m generators.smsdev "/mnt/sdcard/Projects/Mugenesis/Base de Estudo/chars/street-fighter/ken_masters_adv.zip" \
    --out ../../SMS_projects/luta_mugen/out/local_study/generated
python3 -c 'import json;g=json.load(open("../../SMS_projects/luta_mugen/out/local_study/generated/s4_generation_report.json"))["gate_scanline"];print(g["veredito"],g["peak_per_line"],g["sat_entries"])'
```
  Esperado: `PASS 8 ≤64` (pico ≤8, SAT ≤64). **Se não virar PASS, parar e reportar o
  número — não há terceiro caminho** (a escala é contrato do GDD).

- [x] **Step 6:** suíte completa + re-pin + commit
  `feat(mugen2sms): S4.5b formato de runtime SMS; gate worst-scene do Ken vira <veredito>`.

---

### Task 3: Cena 01 `probe_import` — runtime esqueleto lê tabela gerada e ROM boot

**Files:**
- Create: `SMS_projects/luta_mugen/inc/luta.h` (contrato das tabelas)
- Modify: `SMS_projects/luta_mugen/src/main.c` (substitui esqueleto)
- Create: `SMS_projects/luta_mugen/tests_c/scene01.c` — NÃO: o teste da cena 01 é a
  ROM no emulador (harness). Fixtures sintéticos committáveis vivem em
  `SMS_projects/luta_mugen/inc/gen/` (gerados do char sintético dos testes, sem Ken).
- Modify: `doc/13-spec-cenas.md` (preencher cena 01 com números MEDIDOS)

**Interfaces:**
- Consumes: `<slug>_runtime.c` da Task 2 compilado ao projeto (`inc/gen/` para o
  sintético; `out/local_study/gen/` para Ken, via flag de build local).
- Produz: `luta.h` com os structs que as Tasks 4–7 compartilham:

```c
typedef struct { unsigned char dur; const unsigned char *meta; } Frame;
typedef struct { signed char x, y; unsigned short w, h; } Box;   /* clsn flat */
typedef struct {
    unsigned char id;             /* pose id (estados referenciam por id) */
    unsigned char n_frames; const Frame *frames;
} Anim;
typedef struct { unsigned char facing; signed int x; signed int y; /* Q8.8 */
                 unsigned char anim, frame, tick; unsigned short life; } Fighter;
#define FIGHTER_TILE_BASE 0x00    /* sprites no 1º half (SMSlib.h:53, L006) */
```

- [x] **Step 1:** Escrever `main.c` da cena 01: `SMS_displayOff();
  SMS_useFirstHalfTilesforSprites(1); SMS_setSpriteMode(SPRITEMODE_TALL);` carregar
  `tiles_`, paletas (`SMS_setBGPaletteColor`/`SMS_setSpritePaletteColor` por entrada),
  nome table com rodapé de tiles sólidos (`SMS_setTileatXY`), desenhar a frame 0 de
  cada anim em pose estática alternando a cada 30 frames (`SMS_addMetaSprite`),
  `SMS_initSprites(); ... SMS_copySpritestoSAT(); SMS_displayOn();` dentro do loop
  `SMS_waitForVBlank()`. **Verificação de hardware (não assumir):** pares TALL
  topo/base — renderizar um tile-teste 0=branco/1=preto na cena 01 e conferir na
  captura; se o VDP inverter o par, corrigir `pack_tiles_tall` (ordem topo↔base) com
  teste novo na Task 2 — não remendar no runtime.
- [x] **Step 2: Build gate:** `bash SMS_projects/luta_mugen/build.sh` → ROM; erro de
  link >48 KB já antecipa a Task 6 (banco) — neste ponto o sintético cabe linear.
- [x] **Step 3:** `python3 tools/sms_wrapper/emulator_session.py --project SMS_projects/luta_mugen --rom <rom>`
  e `capture_evidence.py` → screenshot não-branca; `audit_deterministic_boot.py --rom`
  → PASS; `audit_render_fidelity.py` (estrutura da fonte vs captura — sprite presente).
- [x] **Step 4: Preencher `doc/13-spec-cenas.md` cena 01** com VRAM/picos da MEDIDA
  (não estimativa). Commit: `feat(luta_mugen): cena 01 probe — tabela gerada vira ROM no emulador`.

---

### Task 4: Interpretador FSM + física Q8.8 + colisão clsn (motor `fight.c`)

**Files:**
- Create: `SMS_projects/luta_mugen/src/fight.c`, `inc/fight.h`
- Test: evidência = cena 02 (não existe unit-test de Z80 aqui); cada decisão de
  frame budget vira linha no memory bank.

**Interfaces:**
- Consumes: `Anim/Frame/Box/Fighter` (Task 3) + tabelas do runtime (Task 2).
- Produz:

```c
void fight_reset(Fighter *p, unsigned char slot);
void fight_step(Fighter *p, unsigned int keys, unsigned int opp_keys); /* 1 frame */
void fight_draw(void);              /* precedentes MSSF2T: projéteis antes, SAT */
extern volatile unsigned char dbg_frame;  /* __at() só com volatile (L009) */
```

- [ ] **Step 1:** Máquina por dados: `states_<slug>[]` destilados no S2/S4 (anim,
  flags `physics|hitcheck|blockable`, janela startup/active/recovery vinda de
  `clsn` por frame). Tick: `if (++p->tick >= frames[...].dur) {p->tick=0; próxima
  frame;}`. Física: `vx, vy` em Q8.8 (tabelas `const signed int grav_tbl[]`;
  NUNCA `int16 * 8.5`). Colisão: AABB em colunas inteiras (`box_overlap`), hit →
  `hitstop=8`, knockback da tabela do estado, dano constante por golpe (sem
  multiplicador — fora do corte, TDD).
- [ ] **Step 2:** Idle/walk/jump/crouch/punch1/punch2/block para o sintético;
  animação avança sem input (ver Task 5 para input vivo).
- [ ] **Step 3:** Build + boot; `measure_frame_advance.py` (contador `dbg_frame`)
  → 50–60; commit `feat(luta_mugen): FSM interpretado por tabelas + clsn em software`.

---

### Task 5: Input vivo (o eixo que reprovou MSSF2T) — gate primeiro, código depois

**Files:**
- Create: `SMS_projects/luta_mugen/src/input.c`, `inc/input.h`
- Consumes: `patt_<slug>[]` (StepCode de `converters/sms_cmd`: byte de dir/keys +
  janela), `SMS_getKeysHeld()/Pressed()`.

**Interfaces:**
- Produz: `unsigned int input_read(void);` → bits já na convenção
  `{U,D,B,F}=DIR_BITS, {A,S}=KEY_BITS do sms_cmd;`
  `input_pattern_hit(const unsigned char *steps) -> unsigned char;`

- [ ] **Step 1: Provar o canal ANTES da ROM reagir:**
  `python3 tools/sms_wrapper/emulator_input.py --self-check` (canal = uinput
  kdotool/ydotool; NUNCA XTEST em Wayland/KWin — L039), depois enviar uma tecla e
  ver `dbg_keys` no probe de memória (`measure_runtime_probe.py` lê RAM via DAP sem
  depender de pixels — precedentes L035/§37).
- [ ] **Step 2:** Buffer de 16 amostras + match de padrão (janela de frames vinda do
  StepCode `rel_time`); botões: 1=fraco, 2=forte (remape QCB+1 etc. do GDD);
  start = pause (NMI existente do crt0).
- [ ] **Step 3:** Cena de teste: pad → Ken anda/salta/socor **ao vivo**; evidência
  com `capture_video.py` (transição não vive em screenshot — §45). Commit:
  `feat(luta_mugen): input vivo provado no emulador via canal uinput`.

---

### Task 6: Banking + streaming de VRAM (paga a dívida medida do S3: 1,16 MB de tiles/lutador)

**Files:**
- Modify: `SMS_projects/luta_mugen/src/stream.c` (novo), `inc/luta.h`
- Consumes: `SMS_loadTiles` (SMSlib.h:130), `SMS_mapROMBank`/`save/restore`
  (SMSlib.h:70-83), arte > 48 KB só com header SDSC/mapper correto (padrão
  MSSF2T spec-banking; verificar `sdk/README.md` antes).

- [ ] **Step 1:** Layout: slot 2 (16 KB) bancado para dados; código fixo nos 32 KB
  iniciais. Troca de bank **somente dentro do callback de VBlank**
  (`SMS_saveROMBank(); SMS_mapROMBank(b); SMS_loadTiles(...); SMS_restoreROMBank();`).
- [ ] **Step 2:** Streaming por pose: só os tiles da pose ativa (≤2 KB/slot de
  lutador no corte TALL; +espelhos +P2 — medir e declarar no spec-cenas). Fila:
  pose pedida no frame N é carregada no VBlank N+1 e aplicada no N+2 (latência é
  design, não bug: documentar no TDD).
- [ ] **Step 3:** `measure_worst_frame.py --project ... --rom ...` dentro do
  orçamento; gate FAIL no derrame → voltar ao humano (lição MSSF2T: derramou lá).
  Commit: `feat(luta_mugen): banking Sega mapper + streaming por pose medidos no VBlank`.

---

### Task 7: Cena 02 `ken_vs_dummy` — 2 lutadores por dados, HUD de tiles, áudio PSG

**Files:**
- Create: `SMS_projects/luta_mugen/src/hud.c`, `src/sfx.c` + reautoría de áudio em
  `SMS_projects/luta_mugen/res/audio/*.psg` (6 SFX + 1 BGM — zero PCM; manifest de
  áudio com sha256 → `audit_audio_provenance.py`)
- Modify: `main.c` (loop da cena 02)

- [ ] **Step 1:** P2 = shift de índices (Task 2) com ACT alternativos do acervo
  local; dummy = mesmo `states_` com IA espeIHO simples (idle, recua, soca a cada
  60 frames) — sem IA avançada (GDD).
- [ ] **Step 2:** Vida = barra de tiles na BG (24×2, `SMS_setTileatXY` no VBlank);
  KO por vida 0 → pose KO (hitstop final), round reinicia; `PSGPlay(bgm)` +
  `PSGFrame()` no loop, `PSGSFXPlay(sfx, SFX_CHANNELS2AND3)` nos golpes.
- [ ] **Step 3:** Gates da cena: boot determinístico, input, fps (`measure_fps.py`
  ≥5 amostras 50–60) E frame advance, `audit_psg_channel_binding`, `audit_psg_quality`,
  evidência selada (`seal_fresh_evidence_bundle.py`). Commit + memory bank atualizado.

---

### Task 8: Cena 03 `golden_slice` + PROVA DO CONTRATO + fechamento de claims

- [ ] **Step 1:** Melhor-de-3 com timer em tiles, 1 especial por lutador
  (QCB+1 remapeado, Task 5); segundo lutador trocado **apenas por `.def`** no build
  local (prova do contrato do GDD: nenhum `.c` do núcleo muda — documentar os dois
  builds e os SHAs).
- [ ] **Step 2:** Rodar TODOS os gates do AGENTS.md aplicáveis na cena pesada COM
  áudio; `reconcile_claims.py`, `audit_claims.py`, `audit_rom_asset_binding.py`;
  teto de claims: `protótipo jogável de engine de luta MUGEN→SMS dirigida por dados`.
- [ ] **Step 3:** `doc/10-memory-bank.md` com os 7 eixos e provas; `doc/13-spec-cenas.md`
  fechado; então superpowers:finishing-a-development-branch (perguntar antes de push).

---

## Requisitos de honestidade deste plano

1. Tasks 1–2 **não podem** declarar sucesso sem o `s4_generation_report.json` com
   `veredito: PASS` medido pelo gate do harness — o mesmo artefato que deu FAIL.
2. Nenhum claim de qualidade visual acima de `probe` até a Task 7; Ken só existe em
   round local gitignored.
3. Cada número novo em doc vem com o comando que o mediu (regra do spec-cenas).
4. Se a escala travada (~32×48 px) produzir silhueta ruim na cena 01 (Lição aberta 2
   do memory bank), isso é **achado medido reportado ao humano**, não ajuste
   silencioso de escala.
