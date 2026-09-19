# 15 - Technical Design Document - HAMOOPIG [VER.001] [SGDK 211] [GEN] [ENGINE] [FIGHTING]

O TDD descreve como o jogo sera construido. Ele nao substitui o GDD; traduz as escolhas de design em arquitetura, memoria, VDP, audio, input e validacao.

## 1. Contexto Tecnico

- Contexto do projeto: ver `doc/project_context_manifest.json`
- Teto de entrega tecnica: prototype
- Hardware alvo: Mega Drive
- SDK: SGDK 2.11
- Regiao alvo: NTSC e PAL com probes HPRB; PAL-240 foi observado, mas a
  sensação de velocidade e o áudio ainda não têm revisão sensorial final

## 2. Arquitetura

- Modelo de cenas: `scene.c` agenda/commita transições; OPENING, TITLE, SELECT,
  FIGHT, AFTER_MATCH e ROUND_RESET usam owners explícitos. `gRoom==9` permanece
  ponto de extensão sem produtor.
- Estrutura de módulos: `main.c` orquestra; `opening.c` e `title.c` cuidam do
  front-end; `init.c` possui reset; `select.c` possui roster/cenário; `stage.c`
  centraliza definições; `hud.c` desenha vida/especial/clock/HITS; `player.c`
  consome `CombatEvent`; `timing.c` é autoridade de ticks.
- Estado global permitido: `P`, `GE`, `Spark`, clock, round/wins e camera em `globals.h`; cada cena limpa ou preserva explicitamente seus campos
- Buffers estaticos: `palette[64]`, scroll tables e arrays dentro de `PlayerDEF`; sem heap no gameplay
- Proibicoes: sem `float`, sem `malloc/free`, sem API SGDK inventada

## 3. Sistemas

### Input

- Latencia alvo: uma leitura por frame antes da FSM/animacao
- Mapeamento: dois pads de seis botoes; A confirma/revanche, START confirma/retorna ao seletor no pos-partida
- Estados que consomem input: seletor, luta e pos-partida

### Gameplay

- Sistemas core: luta 1v1, dano/KO, melhor de tres, time over, projetil, hit pause, HUD e camera
- Sistemas secundarios:
- Pool de atores/projeteis/particulas:

### Render e VDP

- Planos usados: BG_B palco; BG_A mensagens, especial e combo; sprites para
  lutadores, vida compacta, relógio e efeitos; WINDOW somente quando declarado.
- Técnicas: preload de cena, tiles compartilhados, back-pressure de upload,
  câmera por `StageDefinition` e transição com owner único de CRAM. IDs do
  registry canônico ainda precisam ser sincronizados; esta lista não inventa
  identificadores de técnica.
- Budget observado: HPRB schema 7 registra 224/240 linhas, DMA, SAT, links e
  sprites por linha; os relatórios vinculados à ROM atual são a autoridade.
- Fallbacks: HUD ocultável, cenário flat sem parallax, debug separado e PAL-224
  quando H240 não cabe.

### Audio

- Driver: XGM1
- Canais e prioridade: XGM1/PSG conforme manifesto; `FUNCAO_PLAY_SND` respeita
  `gConfig.audioSfx` e a BGM respeita a borda de `audioMusic`.
- SFX críticos: confirmação/navegação, impacto, especial e KO, sujeitos à
  auditoria de proveniência e revisão auditiva.
- Política de mascaramento: OFF bloqueia novos SFX e para/retoma BGM sem alterar
  regras de combate.

### Save / Persistencia

- Escopo: preferências apenas em RAM durante a sessão; SRAM posterior.
- Checksum/duplicacao: não aplicável nesta fase; ROM/evidência usam SHA-256.

## 4. Contratos de Cena

Cada cena deve aparecer em `doc/13-spec-cenas.md` e declarar:

- `scene_id`
- tecnicas usadas com registry ID/tag
- owner skill
- budget
- fallback
- evidencia esperada

## 5. Riscos Tecnicos

| Risco | Impacto | Mitigacao | Evidencia |
|---|---|---|---|
| Sprite Safe retornar NULL | travamento ao posicionar/flipar | guards antes de APIs de Sprite | build + BlastEm |
| Sprites grandes | drop/flicker/VRAM | manter ceiling prototype e medir separadamente | ResComp + evidencia visual |
| Reset parcial | estado vaza entre rounds | reset integral, preservando somente ID/paleta/wins | prova de round |
| Tick de clock dependente da regiao | duracao divergente | constante arcade explicita; PAL nao qualificado | QA NTSC/PAL futura |

## 6. Validacao

- Build canonico: `tools/sgdk_wrapper/build_sgdk_wine_bridge.sh`
- BlastEm: captura deve usar `out/rom.bin` fresco e registrar hash/sessao
- Freshness audit:
- Scene closeout:
- QA:

## 7. Atualizacao

Mudanca de arquitetura, tecnica, cena, budget ou pipeline exige atualizar:

- `doc/10-memory-bank.md`
- `doc/changelog/changelog.md`
- `doc/13-spec-cenas.md`
- `doc/technique_usage_manifest.json`
