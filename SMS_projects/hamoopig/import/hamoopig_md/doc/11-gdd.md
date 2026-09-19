# 11 - Game Design Document — HAMOOPIG [VER.001] [SGDK 211] [GEN] [ENGINE] [FIGHTING]

## Contrato vigente (2026-09-15)

HAMOOPIG é um modelo de engine de luta 1v1 para Mega Drive: o jogador passa
por abertura, título, seleção de lutadores/cenário e uma luta melhor de três.
O loop é movimentar, atacar/defender, confirmar dano, carregar/usar especial,
ler vida/tempo/combos e resolver o round. Ryo, Ken e Musgo são o roster atual;
Showdown Park e BGB2 são os dois cenários carregados por `StageDefinition`.

O front-end tem `START` e `OPTION`; P2 é ignorado no front-end. As opções
controlam apresentação e regras de sessão (SFX, MUSIC, LIFE, CLOCK, TIMER BG,
TIME, SPECIAL, HITS, RULES, STG2 e DEBUG). Abertura e título são cenas distintas
com fade protegido. SRAM, netplay, campanha, novos lutadores e balanceamento
competitivo profundo estão fora desta versão.

Estado de entrega: `prototype`. Código, build e testes host estão ativos; a
revisão visual independente dos cenários/transições e a revisão auditiva do mix
ainda são pendências explícitas. Ver `doc/engine/fighting_engine_roadmap.json`.

## Project Brief

- promessa: uma base extensível para jogos de luta 1v1 com regras observáveis;
- ação: escolher lutadores/cenário, lutar, vencer rounds e repetir/rematch;
- diferencial técnico: HUD compacto por tiles compartilhados, eventos de combate
  centralizados, cenas transacionais e orçamento medido para o VDP;
- não é: uma entrega AAA, netplay, campanha narrativa ou pacote de arte final.

## Visao

Um arcade de luta legível e substituível por dados, com abertura HAMOOPIG,
menu persistente, roster curto e dois palcos largos. A identidade visual usa o
logo/personagem existentes e a fonte do HUD, sem esconder a origem de fixtures
de estudo. Cada eixo (regra, visual, áudio e budget) recebe um status próprio.

## Core Loop

- ação → colisão/evento → dano, hitstop, medidor, combo e SFX → risco de KO →
  recompensa de round/vitória;
- nos primeiros 30 segundos o jogador escolhe roster, seleciona PARK/DOCK,
  movimenta, desfere golpes e observa vida, especial, relógio e HITS.

## Feature Scope Map

### Entra no slice

- abertura separada, fade, título START/OPTION e seleção de lutadores;
- luta 1v1, melhor de três, vida/clock, KO/time-over, especial e HITS;
- Showdown Park e BGB2 selecionáveis por P1;
- opções de sessão com efeitos observáveis e debug isolado.

### Entra depois

- modo treino com dummy, input display e refill;
- replay determinístico de QA e SRAM de preferências;
- novos lutadores, golpes e balanceamento competitivo.

### Fora de escopo

- netplay/rollback, campanha narrativa longa, plataformas físicas no cenário e
  promoção AAA de fixtures de estudo.

## Identidade de Front-End

- comunica uma engine arcade própria: logo HAMOOPIG, personagem preservado e
  menu legível sem cobrir créditos da abertura;
- linguagem híbrida de dojo/cartoon com cenários naturais de alto contraste;
- idle atual é estático no título; fade e cursor fornecem feedback controlado;
- seleção confirma lutador e mostra PARK/BGB2 antes de entrar na luta;
- faixa preta de tela inteira, texto ilegível, cenário repetido sem intenção e
  sprite fora da paleta são fora de tom.

## Ambicao Tecnica, Visual e Sonora

- `quality_promise`: prototype executável, legível e mensurado; não usar boot ou
  ausência de erro como aprovação artística;
- `visual_direction`: pixels autorados/identificados, paleta 9-bit, lutadores
  legíveis, HUD transparente e separação de planos;
- `sound_direction`: BGM por cena, SFX de confirmação/impacto/especial/KO,
  flags independentes e revisão auditiva posterior;
- `gameplay_quality_bar`: input por borda, ticks coerentes, eventos únicos,
  reset simétrico e feedback de dano/medidor/combo;
- `hardware_strategy`: pools estáticos, tiles compartilhados, back-pressure de
  DMA, StageDefinition e fallback flat sem inventar capacidades do VDP.

## Tecnicas Escolhidas

Toda tecnica precisa existir no registry canonico e servir a gameplay, narrativa, leitura, direcao visual ou sonora. Quantidade de efeitos nao substitui coerencia.

| Cena/sistema | Registry id | Tags | Funcao no jogo | Papel visual/sonoro | Owner skills | Budget/evidencia esperada | Fallback |
|---|---|---|---|---|---|---|---|
| opening/title | `null (registry sync pending)` | SCENE/UI | separar splash e menu sem input duplicado | fade protegido e logo legível | scene architecture | `tests/test_scene_contract.py` + captura | corte protegido |
| fight HUD | `null (registry sync pending)` | HUD/VRAM | vida, especial, clock e HITS | leitura compacta sem faixa preta | hud/runtime | `tests/test_hud_segment_contract.py` + ROM | ocultar HUD |
| stage loader | `null (registry sync pending)` | CAMERA/BUDGET | trocar PARK/DOCK por dados | scroll amplo e limites coerentes | stage/runtime | `tests/test_stage_definition_contract.py` + HPRB | BG_B flat |

### Tecnicas rejeitadas ou adiadas

| Registry id | Decisao | Motivo | Condicao para reconsiderar |
|---|---|---|---|
| `null (parallax multi-plane)` | adiada | BG_A é compartilhado pelo HUD e o budget ainda não fecha | registrar ID no registry e provar budget VDP |

## Mecanicas core

- movimento, salto, defesa, golpes e projéteis dos três lutadores;
- vida 0..96, medidor 0..32, combo por atacante e melhor de três;
- relógio 99/60/OFF, time-over, pausa/free-step apenas no debug e reset de round.

## Progressao

- a progressão atual é por rounds e seleção/rematch, não campanha;
- cada partida escolhe um dos dois estágios e preserva o palco no rematch.

## Regras e limites

- dano e medidor passam pelo ledger de eventos;
- evento confirmado é consumido uma vez; overlap persistente não duplica hit;
- especial é cobrado na aceitação do estado e resetado por round nesta fase;
- arte final, mix aprovado e hardware físico permanecem fora do aceite atual.

## First Playable Slice

- ROM com abertura→título→seleção→luta e retorno pós-round;
- prova vida, clock, HITS, especial, KO/time-over, dois palcos e opções ON/OFF;
- loop existe quando a luta chega ao round, um evento causa dano sem duplicação,
  o KO resolve e o reset inicia nova luta com HUD/recursos íntegros.

## Route Decision Record

- `context_type`: projeto_existente;
- `dominant_route`: runtime + validation, com tradução de arte candidata;
- `first_skill`: scene architecture / timing / art conversion;
- `first_tool`: wrapper SGDK/Wine e conversores em `data/source_art`;
- `resource_loading_model`: scene_local_preload;
- `asset_strategy`: mixed (IMAGE + spritesheet + tiles compartilhados);
- `evidence_required`: build, testes host, HPRB, captura ROM vinculada e revisão;
- `forbidden_shortcuts_until_evidence`: inventar pixels, medir ROM antiga ou
  chamar screenshot isolada de aprovação sensorial.

## Escopo atual

- evolução P00–P11 em teto `prototype`, com P10/P11 ainda parciais;
- matriz completa, ciclos prolongados, revisão sensorial e aprovação final de
  arte/áudio ainda não encerrados.

## Cenas de Front-End

- `SCENE_OPENING`: splash e créditos com fade;
- `SCENE_TITLE`: START/OPTION e páginas de configuração/debug;
- `SCENE_SELECT`: roster P1/P2 e alternância de cenário por C;
- `SCENE_AFTER_MATCH`: rematch ou retorno à seleção.

## Vibe Playable Birth Route

Projetos novos nascem com rota Vibe Playable preparada, mas bloqueada.

Pedido natural de jogo/fase/personagem/FX deve acionar roteador visual antes de runtime definitivo.

Nenhum asset, aprovacao humana ou evidencia BlastEm existe no template.
