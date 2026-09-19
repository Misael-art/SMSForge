# 13 - Especificacao Tecnica por Cena - HAMOOPIG [VER.001] [SGDK 211] [GEN] [ENGINE] [FIGHTING]

> Documento canonico para budgets por cena, contrato de evidencia e papel formal de cada surface.
> Menu, title screen e outras telas de front-end contam como cenas formais.

## Contexto de escala

Contexto do projeto: `technical_demo` (porta direta da engine HAMOOPIG). Teto de claim: `prototype`.
Os budgets abaixo sao os observados na engine upstream, NAO metas de producao AAA deste workspace.
Porta estendida: inclui seletor, HUD de atlas, Musgo e novo ciclo de round.

## scene_roadmap

### Cena 0 - `room_tela_hamoopig` (abertura/logo)

- origem: engine upstream (FSM de salas em `src/fsm.c`)
- conteudo observado: fundo em grade azul com onda/logo HAMOOPI, transicao por fade de paleta
- evidencia: `out/emulator_evidence/blastem-linux-20260910T192043Z-1434440/screenshot.png`

Contrato de round (2026-09-11):

- formato: melhor de tres (`ROUNDS_TO_WIN=2`)
- KO: vida chega e permanece em zero; vencedor recebe uma vitoria
- time over: maior vida vence; empate nao concede vitoria
- reset: `FUNCAO_ROUND_RESTART` reinicializa estado transitorio simetricamente e preserva IDs, paletas e placar
- relogio: `ROUND_CLOCK_TICKS=38` preserva o tick arcade legado; nao e declarado como segundo real
- evidencia exigida: KO de P1 e P2, empate/time over, round seguinte restaurado e especial/projetil apos transicao
- estado da arte 2026-09-15: Showdown usa o candidato de referência `rascunho/showdown_native_crop_preview.png`, convertido para 512x256 com 14 cores opacas nos indices 1..14, 864 tiles representantes e quatro iterações de medoid, sem ampliacao 4x4. Indice zero reservado ao transparente. A fonte tem hash 1b9bc2e6bb96f0f27218cacc189477c5689dca687ef557bc91ca3d3ed5f4715f e continua fixture tecnico, nao arte final aprovada; o candidato 1024 foi rejeitado pelo guard real de VRAM. A captura nova deve ser comparada visualmente com a referência. HUD de energia usa 16 colunas e zera integralmente; vida positiva conserva uma coluna.

### Cena 1 - `room_title_menu` (tela de titulo)

- owner: `src/title.c` via `gRoom==1`
- entrada: boot deterministico, composição `res/gfx/title_scene.png` e fonte atlas 16x16
- abertura: splash HAMOOPIG é uma cena separada (`SCENE_OPENING`); após fade-out,
  `SCENE_TITLE` carrega composição própria. O primeiro botão é consumido pela
  abertura e nunca confirma `START` por acidente.
- menu principal: `START` e `OPTION`; a tela permanece ativa até confirmação.
- `START`: inicia um fade-out de 8 ticks; somente após `PAL_isDoingFade()`
  terminar a composição é desmontada e o pedido transacional
  `SCENE_SELECT` é emitido, com `gFrames` zerado pelo gerenciador de cenas.
- `OPTION`: páginas de cinco itens derivadas de `cursor / 5`: `SFX`, `MUSIC`,
  `LIFE`, `CLOCK`, `TIME`, `DEBUG`, `DEFAULTS` e `BACK`.
- `DEBUG`: duas páginas com `BOX`, `HIT`, `TEXT`, `PERF`, `FRM`, `STEP`, `TICK`,
  `240` e `BACK`; `B` retorna para OPTIONS preservando o cursor em DEBUG.
- controles: P1 D-pad navega, A/START confirma, B retorna; P2 ignorado
- composição: fundo azul pixel-art com logo/pig em `title_scene`, painel estreito
  no plano A (sem faixa preta de tela inteira) e cursor de um tile; a abertura
  não compartilha mais `room_0_bga`, evitando créditos/sprites residuais.
- budget: `title_scene` usa 151 tiles residentes a partir do tile 1; fonte,
  cursor e painel seguem em tiles altos. DMA somente ao entrar ou redesenhar o
  menu. A revisão visual independente permanece pendente.
- evidência: `doc/engine/p03_config_report.json`, `out/emulator_evidence/p03_menu_final`,
  `p03_options2` e `p03_efeito`.

### Cena 2 - `room_character_select` (seletor)

- owner: `src/select.c`
- entrada: LEFT/RIGHT alterna Ryo, Ken e Musgo; A/START confirma
- saida: `CLEAR_VDP` entrega a cena a `gRoom=10`
- evidencia exigida: selecao visivel e retorno a partir da tela pos-partida

### Cena 3 - `room_after_match` (pos-partida)

- owner: ramo `gRoom==11` de `src/main.c`
- entrada: duas vitorias, tempo minimo de resultado e derrotado em 570; a duracao da animacao vencedora nao pode antecipar o pouso
- opcoes: A = revanche com mesmos lutadores; START = seletor
- proibicao: nenhum FSM/fisica da luta anterior roda depois da troca de owner
- evidencia exigida: tela do vencedor + uma captura de cada rota de saida
- tipografia: celulas 16x16 extraidas do atlas solicitado, PAL1/prioridade alta, painel BG_A nas linhas 5..10. Mapa em RAM enviado por DMA_QUEUE_COPY; PAL2/PAL3 pertencem aos lutadores.

### Cena 1 - `room_fight_arena` (combate 1v1)

- origem: engine upstream (`src/fsm.c`, `src/player.c`, `src/physics.c`, `src/collision.c`, `src/hud.c`)
- conteudo: arena Showdown com Ryo/Ken/Musgo selecionaveis, HUD de vida/relógio,
  barra de especial em oito células BG_A, mensagens BG_A e lógica FSM de golpes
- combo: cada acerto válido emite um evento para o atacante; `N HITS` permanece
  por 60 ticks lógicos após o último acerto e expira mesmo que o lutador volte
  a idle. Colisão simultânea soma uma vez para cada atacante.
- sprites por scanline: governados pelo sprite engine do SGDK 2.11 (SPR_initEx); medicao dedicada de scanline NAO foi feita nesta porta (fora do escopo; `validado_budget: nao`)
- evidencia: `out/emulator_evidence/blastem-linux-20260910T192043Z-1434440/screenshot.png`

## Contrato de evidencia desta porta

- build: `out/logs/linux_wine_build_report.json` (wine_bridge_status=buildado)
- boot: sessoes BlastEm em `out/emulator_evidence/` com screenshot + save.sram + log
- audio: SFX GPL importados e `FUNCAO_PLAY_SND` ligado; prova de captura/escuta permanece separada
- hud: barras P1/P2 e relógio usam sprites compactos; especial usa BG_A com
  escala `0..32`; combo `N HITS` usa BG_A na linha 21; KO e sombra permanecem
  sprites. Células vazias são tile 0.

## Residencia estatica da revisao visual

- Stage 864 + atlas de mensagens 72 + tile inicial 1 = primeiro livre 937.
- Regiao automatica de sprites: 420 tiles, inicio 1020 no layout observado.
- Sobra entre recursos estaticos e sprites: 83 tiles no layout observado. Nao e folga de DMA/SAT.
- Degrau seguinte: stage 1024 + atlas 72 leva a 1097, sobrepoe o limite 1020 e foi rejeitado.
- `FUNCAO_INIT` consulta `TILE_SPRITE_INDEX` antes da carga e falha explicitamente se houver sobreposicao.
- Queda Musgo 120x120 (2 frames), derrota 128x64 (1), vitoria 88x128 (1); poses de estado, nao ciclo de vitoria multiframes.
- Proximos testes obrigatorios: pior DMA, uso dinamico/fragmentacao de sprites, SAT/scanline e PAL. Build/contagem nao os substituem.

## Provas adicionais — 2026-09-13

PAL basico exercitado na mesma ROM 532d4453: P2 vencedor e START, em
`visual_ko_20260913T114702Z`. NTSC simetrico em `visual_ko_20260913T114321Z`.
DRAW e vencedor por tempo com vida desigual vistos, com reset; contrato C
coberto por 9.216 pares. Referencia `doc/curation/2026_09_13/qa_continuation_closeout.md`.
Isto nao promove residencia estatica a pior budget nem titulo do emulador a FPS do loop.

## Pool de cenários — revisão 2026-09-14

- `gBG_Choice==1`: Showdown Park, recurso `gfx_showdown`, mundo 512×256,
  864 tiles residentes, câmera horizontal/vertical já existente.
- `gBG_Choice==2`: Stage 2 — pântano no cais, recurso `gfx_bgb2`, mundo 512×256,
  864 tiles após conversão. A fonte RGB original, prompt, hashes e relatório
  estão em `data/source_art/stage2_swamp/`; o PNG indexado é uma candidata
  autoral e permanece sujeito à revisão visual no emulador.
- `STAGE2 ON/OFF` é uma preferência de sessão. P1 C alterna o palco no
  seletor; quando desligado, o seletor força Showdown. P2 não altera o palco.
- O contrato estático `tests/test_stage2_palette.py` garante índice BG_B zero
  reservado, grade de cor 9-bit e teto de 864 tiles; isso não substitui prova
  de câmera, DMA, áudio ou qualidade visual em NTSC/PAL.
