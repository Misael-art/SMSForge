# 10-memory-bank — laboratorio_01

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-08-31 — jogador promovido a METASPRITE 16x16 (§25/L006) + correção da raiz
profunda do L006 no conversor de tiles. Eixos de runtime REBAIXADOS pelo próprio
build (§26: ROM relinkada invalida evidência anterior) — recaptura pendente.

## Eixos de entrega (7)
| Eixo | Status | Prova |
|------|--------|-------|
| build | **buildado** | `out/rom/laboratorio_01.sms` 16.384B; `TMR SEGA` @espelho 0x7FF0, checksum 0x5ABB |
| validation_report | validado (pre-gates) | recursos+procedência pass; record em out/build_record.json |
| boot no emulador | **testado_em_emulador** | `out/evidence/evidence.json` PASS (viewport var 3715); Emulicious 2026-03-27 |
| gameplay | testado_em_emulador (VITORIA capturada) | frame de VITORIA em gameplay_cena02_vitoria.png (texto legivel); logica provada por simulacao + execucao real |
| 60/50 fps | testado_em_emulador | fps.json: 6 amostras 58-60 (media 59.0), constante_50_60=true — eixo FECHADO |
| áudio | implementado (evidência audível pendente) | blip SN76489 porta 0x7F no movimento (v6); confirmação humana via ./run.sh |
| memory bank atualizado | sim | este arquivo (auditoria 2026-08-30) |

## Decisões registradas
- Header SEGA embutido via macros oficiais (`SMS_EMBED_SEGA_ROM_HEADER_16KB` +
  SDSC auto-date), confirmadas em SMSlib.h:429–485.
- Toolchain instalado rootless via `tools/sms_wrapper/ensure_toolchain.sh`
  (SDCC 4.6 portátil; SMSlib/PSGlib RECONSTRUÍDAS do fonte — lição L004).

## Cena 01 "boot_interativo" (2026-08-26)
- v003 buildada com pre-gates verdes (recursos+procedência no próprio build).
- Rota BG para o cursor (desvio documentado — L006: sprite com pixels índice-0,
  causa-raiz aberta; readvram/repl do Emulicious é a ferramenta de fechamento).
- Evidência de boot v1 segue válida; gameplay parcial (ver eixos acima).

## Sessão 2026-08-26 (parte 2)
- F2 fechada: fps.json 58-60fps constante.
- F3 implementada: blip PSG no movimento (sem degradação de fps).
- L006 avançou: travamento isolado DENTRO de SMS_loadTiles (L009).

## F4 cena02 (2026-08-29)
- GDD cena02, spec, storyboard, contrato criados (pipeline aaa_scene_v1 S0-S4).
- Runtime: bloco 2x2 empurrável, alvo, vitória + reinício, colisão AABB, beep/fanfarra.
- Build v012 OK, tela limpa capturada.

## FPS FECHADO (2026-08-30)
- 59.3fps MEDIDO via contador de frames na tela (0x012F->0x01AD = 126f/2.125s). Eixo fps_constante=true.
- Audio: IMPLEMENTADO (PSG porta 0x7F); comprovacao audivel limitada pelo host (L012: Java do Emulicious nao roteia no Pulse). Eixo audio=false, honesto.

## Cena 04 "corredor estelar" (2026-08-30)
- Combina sprites (L006) + musica battle rica (PSGlib 4 canais) + scroll + HUD + HP/gameover.
- Prova: cena04_sprites.png (jogador sprite visivel, 60fps) + audio_battle.wav (96% ativo, peak 9936).
- Musica gerada por probes/gen_music.py (formato .psg do PSGlib); inc/music_battle.h.

## Próximo passo declarado
- Fechar fps/audio medidos no emulador (F2/F3 ja implementados; medicao no emulador).
- F1: L006 sprite (probe; VRAMmemcpy + SPRITEMODE_NORMAL 8x8).
- Atualizar build_record com eixos provados.
- F1: resolver L006 sprite (probe em probes/).
- Reconstruir build_record com eixos provados (nao por edicao).
- F1: resolver L006 sprite via VRAMmemcpy (probe em probes/).
- Reconstruir build_record com eixos de runtime provados (não por edição).


## Sessão 2026-08-31 — metasprite 16x16 e a raiz profunda do L006

**RAIZ PROFUNDA ENCONTRADA (mais funda que o modo de sprite):**
`png_to_sms_tiles.py` emitia **2 planos de bits (16 B/tile)** enquanto
`SMS_loadTiles` copia para `tilefrom*32` — caminho **4bpp, 32 B/tile**
(SMSlib.h:130 é a autoridade; para 2 planos existe `SMS_load2bppTiles`).
Cada par de "tiles" de 16 B era lido como UM tile de 32 B: quadrantes e planos
embaralhados. **A arte 16x16 nunca chegou íntegra à VRAM.** O sintoma foi
atribuído por semanas ao modo de sprite; o modo era só a camada de cima.

Consequência concreta: `hero_tiles` tinha 64 B (2 tiles) em vez de 128 B (4).
O jogador desenhava o tile 128 e os "inimigos"/projétil desenhavam os tiles
129..131 — que eram **fragmentos da arte do herói**.

**Feito nesta sessão:**
- `png_to_sms_tiles.py` corrigido para 4bpp real (32 B/tile, 4 planos, cores 0..15);
  self-check com regressão: cor 15 precisa acender os 4 planos.
- `inc/hero_tiles.h` regenerado: 128 B = 4 tiles (128..131 = TL,TR,BL,BR).
- Jogador = `SMS_addMetaSprite` com formato autoritativo lido em
  `devkitSMS/SMSlib/src/SMSlib_metasprite.c`: triplas (dx, dy, tile) + `METASPRITE_END`.
- Declaração de sprites passou a ser **por frame** (`SMS_initSprites` → adds →
  `SMS_copySpritestoSAT`): `SMS_addMetaSprite_f` não devolve handle.
- Inimigo e projétil ganharam tiles próprios (132, 133) com assets declarados
  em `res/sprites/` — saíram dos quadrantes do herói.
- `star_tile` corrigido de 16 B para 32 B (mesmo bug do conversor).
- Física ajustada a 16x16: colisão AABB e limites de tela.

**Orçamento SAT:** 4 (metasprite) + 5 inimigos + 1 projétil = **10 de 64**.
Pico por scanline continua sob o teto de 8, mas o jogador agora ocupa **2**
sprites por linha nas suas 16 linhas — margem menor que antes.

**Verificado estaticamente:** round-trip `hero.png → 4 tiles → arte` idêntico,
e o header casa byte a byte com o conversor. Build OK (16384 B).

**VISTO RODANDO (2026-08-31)** — a sessão tinha emulador; minha afirmação
anterior de que não tinha estava errada. Ao rodar, apareceram MAIS DUAS causas:

**Quarentena:** `enemy.png` e `shot.png` são PLACEHOLDERS (`role: outro`), assim
como `block.png` e `target.png`. Nenhum pode ir para entrega sem arte autoral ou
aprovação estruturada — `audit_placeholder_quarantine.py --check-release` bloqueia.


## L006 FECHADO COM EVIDÊNCIA — três defeitos empilhados

Rodar no emulador revelou que a arte 16x16 correta **ainda** saía como ruído.
Duas causas adicionais, achadas nesta ordem:

1. **Name table nunca limpa.** O runtime só preenchia `4..27 x 4..24`; o resto
   exibia lixo de VRAM. É a moldura de ruído presente em TODA captura desde a
   cena 04 — inclusive na evidência que sustentou a F6.
2. **Base de tiles de sprite (§27) — A CAUSA-RAIZ REAL.** Sem
   `SMS_useFirstHalfTilesforSprites(1)`, o VDP lê os padrões de sprite na
   SEGUNDA metade da VRAM: `SMS_addSprite(...,128)` lê o tile **384**, nunca
   escrito. Assinatura do erro: **BG limpo + sprite corrompido**.

Somadas às duas já corrigidas (conversor 2bpp→4bpp e a geometria §25), eram
**quatro** defeitos sobre o mesmo sintoma. Por isso "corrigir a causa" nunca
limpava a tela, e por isso o L006 foi declarado RESOLVIDO em 2026-08-30 com a
tela ainda em ruído.

### Estado dos eixos (contra a ROM atual, bundle selado)
| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | 16384 B |
| validation_report | pass | pre-gates verdes |
| boot_emulador | **testado_em_emulador** | `out/evidence/evidence.png` — tela limpa, HUD legível, campo de estrelas, metasprite 16x16 com cruz atravessando os 4 quadrantes; `bundle.json` selado |
| fps_constante | **testado_em_emulador** | `out/evidence/fps.json` — 6 amostras, 60/60/60, `constante_50_60=true` |
| gameplay | **testado_em_emulador** | `evidence.json`: `sprite_dx=+89px` após `Right` — bloco de 96px rastreado entre capturas; `sprite_displacement_proven=true` |
| audio | **NÃO provado** | `.wav` existente é de build anterior |
| memory_bank_atualizado | este arquivo | — |

### Gameplay FECHADO (2026-08-31) — e o que foi preciso
As duas razões do fracasso anterior eram reais e foram resolvidas:
- **Game over antes da captura**: settle reduzido (`--frames 5`) captura com o
  jogo vivo. Botão 1 = tecla **`z`** (descoberto empiricamente: mudou 53,9% da
  tela ao sair do game over).
- **Limiar global mal calibrado**: substituído por rastreamento do sprite (§29).
  `largest_sprite_block` acha o maior aglomerado com FORMA de sprite (6..40 px
  por lado, razão < 3 — sem isso, colunas de estrela sequestravam a medição) e
  compara com a última posição conhecida (o jogador some em frames de flash de
  invulnerabilidade).

**Prova:** `sprite_dx=+89px` após `Right`. Medição independente anterior no par
`mv.png → mv_step1.png`: mesmo bloco de 96px indo de x[54..67] para x[191..204].

### Aviso de harness (L012)
Uma captura pegou a **janela errada** (área de trabalho 2560x1080, conteúdo
pessoal) e passou no detector de vacuidade — variância 401 > 40. Foi apagada.
`screenshot_semantic_gate.py` reprovou corretamente pela regra de desktop.
Causa: instância anterior do emulador viva (`--keep`) confundiu a busca de
janela. Encerrar o emulador entre capturas é obrigatório.


## L012 — 15 capturas de desktop no acervo (privacidade + evidência falsa)

`spectacle -a` fotografa a janela ATIVA. Com o emulador sem foco (ou instância
zumbi), a "evidência" virava um screenshot da área de trabalho — que passa no
detector de vacuidade. Duas dessas comparadas entre si produziram
**"interação provada" medindo o desktop mudando**, não o jogo.

Encontradas **15** capturas 2560x1080 em `out/evidence/`, várias de sessões
anteriores (`boot_v002.png`, `gameplay_A.png`, `tela_base_final2.png`…).
Todas apagadas — podiam conter conteúdo pessoal do usuário.

`capture_evidence.py` agora: (a) recusa iniciar com outra instância viva;
(b) valida o tamanho de CADA captura (principal e de passo), descarta o arquivo
se for desktop e refaz com re-foco. Regra: SMS_GLOBAL §30.

## Estado final dos eixos
6 de 7 fechados. **áudio segue `false`** — o `.wav` do acervo é de build
anterior e não foi recapturado contra esta ROM. É o único eixo em aberto.
