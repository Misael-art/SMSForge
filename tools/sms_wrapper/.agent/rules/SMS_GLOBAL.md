# SMS_GLOBAL — Lei canônica do SMSForge (sempre ativa)

> Porte da SGDK_GLOBAL (MegaDrive_DEV) para Master System. Seções numeradas;
> lições novas APENDAM seção; regra vira medição, nunca só prosa.

## 1. Fonte de verdade
Hierarquia em `AGENTS.md` da raiz. Estado operacional (`10-memory-bank.md`) >
design (GDD) > processo > headers devkitSMS (API definitiva) > suposição.
Suposição nunca vira resposta; vira pergunta.

## 2. Restrições não negociáveis
Lista ❌ completa vive no AGENTS.md e é espelho desta seção. Violar qualquer
item invalida a entrega inteira — não "com exceção".

## 3. Governança e vocabulário de status
```
documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget
```
Um agente que diz "pronto" sem ROM rodando no emulador comete autoengano —
o crime fundador deste workspace. Claims têm teto aprovado (§17).

## 4. Operação do wrapper
Toda lógica de build/validação vive em `tools/sms_wrapper/`. Projetos têm shims
que delegam. Duplicar lógica = regressão estrutural.

## 5. Handoff
Fim de sessão: memory bank atualizado + handoff curto (o que mudou, próximo passo,
bloqueios). Handoff nunca substitui memory bank nem evidência.

## 6. Lei do VDP (tiles BG)
- Grid 8×8; pattern table 32 bytes/tile; **máx 256 tiles BG**.
- Name table = **1 byte por tile** (índice 0–255). Não existe flip nem paleta
  por tile no BG — variação vem de tiles distintos ou metatiles.
- Scroll global X/Y. A trava da 1ª coluna **deixa de ser opcional** quando o
  H-scroll está ao vivo: `SMS_setBGScrollX` ≠ 0 exige
  `VDPFEATURE_LEFTCOLBLANK`. Sem isso os 8 px da esquerda mostram lixo do
  tile que ainda não foi buscado (L043). Gate: `audit_hscroll_blank.py`.
- Split de scroll exige line interrupt e é técnica medida, não gratuita.
  O contador de linha dispara na linha N **depois** de recarregar no VBlank:
  armar 47 querendo a linha 64 desloca todas as bandas 16 linhas. Banda
  vazia não prova a quebra — ponha forma reconhecível nela (L046).

## 7. Lei de sprites
- SAT: máx **64 sprites**; terminador Y=0xD0 corta o processamento.
- Máx **8 sprites por scanline**. Excesso é descartado; no VDP SMS1 corrompe a
  linha. O simulador (`audit_sprite_line_sim.py`) aprova antes do runtime.
- Tamanho global **8×8 ou 8×16**. Zoom ×2 dobra o PIXEL (16×16 / 16×32 na
  tela), não a arte. Nenhum modo é mais largo que 8 px; arte 16×16 exige
  metasprite (§25, L006). "8×8 ou 16×16" como modo VDP é número do Mega Drive.
- X é armazenado **sem offset**: `SMS_addSprite(0, …)` desenha na borda
  esquerda. `VDPFEATURE_SHIFTSPRITES` desloca **8 px**, não 32.
  "X+32" / "X<32 esconde" é número do Mega Drive, refutado (L003, S05).
- Comportamento dependente de revisão (early clock, flips) não vira lei sem
  evidência de emulador/console (§23).

## 8. Lei de paleta
- CRAM 2 subpaletas ×16; índice 0 transparente nas duas → máx 30 úteis simultâneas.
- Cor = código 6-bit. Contrato de assets: canal×85. Sem gradiente suave;
  fade = recarga de paleta sincronizada ao VBlank.
- Contraste medido em degraus de luma derivada (`audit_luma_floor.py`).
  Adjetivo visual sem piso numérico não entra em spec.
- Traduzir foto/conceito: downscale NEAREST + Floyd-Steinberg **na paleta
  mestra**. Paleta NES/SNES/PICO-8/Game Boy é régua, não CRAM (L055, §32).
  MP4/GIF de partículas não é evidência. Ferramenta:
  `prepare_sms_pixel_art.py`. Skill: `sms-pixel-translate.md`.

## 9. Orçamento VRAM/VBlank (não existe DMA)
- Transferência em massa SÓ dentro do VBlank (janela ≈4.5ms NTSC).
- Orçamento worst-frame POR CENA é contrato em `13-spec-cenas.md`, medido
  ("estimado" é proibido no schema). Folga não medida é timidez (§18).
- Transição de tela que reescreve name table em massa: **desligar o display,
  redesenhar o mapa inteiro, religar**. Escritas no display ativo perdem-se
  e deixam resto na tela; limpar linha a linha não fecha a classe (L047).

## 10. Armadilhas Z80/SDCC (assumir como suspeita até provado)
- `int` = 16-bit signed; multiplicação/divisão caras; float proibido em runtime quente.
- RAM 8KB total (`--data-loc 0xC000`): sem malloc, pools estáticos.
- ISR/NMI curtos; pause = NMI.
- Locais no SDCC-Z80 recarregam via IX; ponteiros `static` no hot path.
  Espelhar tile em runtime (bitrev) troca ROM por CPU — medir o frame.
  Curva paga: STREAM_BYTES 32→59.5 fps, 64→58.3, 96→57.5, 128→55.5,
  256→40 (L045). Folga de ROM comprada com flip não é grátis.
- Física de queda/integração vale por **condição** (altura, flag airborne),
  não pelo rótulo do estado. `y` só dentro de `ST_JUMP` deixa o lutador
  pendurado quando um golpe o tira desse estado (L050).

## 11. Banking e header
- ≤48KB linear sem mapper. Mapper Sega: páginas 16KB nos slots 0x4000/0x8000;
  código não-bancado restrito aos primeiros 32KB.
- Header SEGA em 0x7FF0 exigido pela BIOS regional; `makesms` gera/checksum.

## 12. Áudio
- PSG SN76489: 3 tone + noise. PSGlib é o driver padrão. Arbitração música×SFX
  declarada no TDD. YM2413 é opcional — o jogo precisa funcionar sem FM.
- SFX toca no canal **autorado** no manifesto
  (`doc/audio_provenance_manifest.json`). `PSGSFXPlay(sfx_shot, SFX_CHANNEL3)`
  quando o asset nasceu para `SFX_CHANNEL2` derruba o mix; cooldown não
  recupera (L041). Gate: `audit_psg_channel_binding.py`.
- PSGlib volta ao início no `PSGEnd`. N cópias byte a byte do mesmo frame
  não tocam nada extra e comem ROM. Antes de sacrificar feature por espaço,
  meça a redundância do stream (L051). Gate: `audit_psg_redundancy.py`.

## 13. Timing NTSC/PAL
60 vs 50 Hz: velocidade normalizada via frame counter. Nada de delay loops.
Claim de fps constante exige medição (§17).

## 14. Anti-alucinação devkitSMS
Headers = autoridade #8. Antes de usar API: abrir `SMSlib.h`/`PSGlib.h`.
Mapa conceitual SGDK→SMSlib (NÃO é 1:1):
| Conceito MD | Equivalente SMS |
|---|---|
| DMA queue | transferências manuais dentro do VBlank |
| PAL_setPalette | SMS_loadBGPalette / SMS_loadSpritePalette |
| VDP_setTileMapXY | SMS_setTileatXY (name table 1 byte) |
| sprite flip por atributo | NÃO EXISTE no BG; sprites: revisão-dependente (§7) |
| XGM2 | PSGlib (+ PSG samples) |
Função que não estiver no header não existe.

## 15. Estética doutrinária
Dark Deco adaptado: contraste alto, luz escassa, silhueta legível a 256×192.
Pixel art autoral obrigatória. Proveniência por asset (`audit_provenance.py`);
pixel nascido de código como personagem/inimigo/boss/cenário final é bloqueado.

## 16. Ciclo de produção de cena
roteiro → storyboard (planta baixa em pixel) → coreografia → MEDIÇÃO → orçamento
→ contrato de asset → model sheet → assets → runtime → EVIDÊNCIA.
Medir depois de arte cara foi a lição mais cara da história da metodologia-mãe
(curadoria 2026-08-17): aqui isso é gate, não conselho.

## 17. Claim ceiling executável
Tokens AAA / 60fps / 50fps / pixel-perfect / release só existem com teto aprovado
(`doc/promotion_claims/<token>.json`). `audit_claims.py` reprova o resto.

## 18. Doutrina de audácia
Fechar orçamento sem medir o degrau seguinte é timidity disfarçada de prudência.
Sempre medir o próximo degrau antes de declarar folga.

## 19. Self-check obrigatório
Ferramenta de medição cujo `--self-check` falha não é fonte. Ler saída de
ferramenta sem self-check verde é violação.

## 20. Gate calibrado contra falso positivo
Todo gate precisa reprovar um caso inválido conhecido E aprovar um válido
(`selftest.py`). Gate que nunca reprovou não está calibrado.

## 21. Learning capture obrigatório
Erro → JSON canônico em `doc/curation/` + seção numerada AQUI + ferramenta que mede.
Dedup por chave canônica no ledger. Ledger sem JSON, JSON `fechada_com_ferramenta`
sem `.py` existente, ID fantasma e persona ensinando doutrina supersedida
reprovam. IDs L020–L034 nunca foram emitidos neste repo; L012 é furo
declarado (`doc/curation/id_registry.json`). Gate: `audit_learning_capture.py`
(§43).

## 22. Capacidade declarada com prova antes de promessa
Só declare capacidade que já pagou com build/evidência. "Devo conseguir" não
entra em doc de projeto; entra como risco.

## 23. Fatos pagos com evidência
Fato hardware/software só vira lei quando pago com build + emulador. Enquanto
isso: hipótese marcada, teste agendado.

**Primeiro fato pago (2026-09-01, L003):** `VDPFEATURE_SHIFTSPRITES` desloca
**8 px** (medido 114→106 em duas ROMs idênticas exceto pelo bit) e **não existe
offset +32** — X=0 e X=16 desenham visíveis. A matriz afirmava "32px" e
"X<32 esconde": números do **Mega Drive**, refutados. Probe:
`_laboratorio/early_clock`. Ainda não testado em console real nem entre
revisões SMS1/SMS2 — para isso a lei continua valendo.

**A brecha que permitia isso:** o registry mantinha as duas técnicas
honestamente em `mapped` ("provar em emulador"), mas a matriz `.md` afirmava os
números como NOTA DURA e nenhum gate lia o `.md`. Fato afirmado na leitura
humana sem entrada no registry é claim invisível.
Gate: `audit_mastery_registry.cross_check`.

## 24. Deterministic boot
Boot determinístico obrigatório: mesmo estado inicial toda execução; RNG semeado
por input/frame counter documentado. Evidência comparável exige boot estável.

## 25. Geometria de sprite: nenhum modo é mais largo que 8px
`SPRITEMODE_TALL` é **8×16**, não 16×16. `ZOOMED` dobra o PIXEL, não a arte.
Entidade com arte mais larga que 8px exige **metasprite**, em qualquer modo.
Lição L006 (laboratorio_01): a matriz de maestria S03 afirmava "8×8 ou 16×16" e
custou dias de sprite invisível — doutrina errada gera bug, não só confusão.
Corolário: fato de hardware citado na matriz é lei operante; errá-lo é defeito
de gate, não detalhe de redação.
Gate: `audit_sprite_mode.py` (cruza modo declarado no fonte com largura do asset).

## 26. Binário novo invalida evidência velha
Relinkou a ROM? Toda prova de runtime (boot/gameplay/fps/áudio) volta a `false`
até ser recapturada contra o binário novo. `build_inner.py` rebaixa sozinho:
eixo só sobrevive se a evidência for POSTERIOR à ROM.
Corolário: `--skip-pre-gates` nunca produz `validation_report: true`.
Herança de eixo entre builds vale só para eixos de runtime; `build` e
`validation_report` descrevem a execução atual e não se herdam.
Gate: `build_inner.demote_stale_axes` + `reconcile_claims.py` como pós-gate.

## 27. Base de tiles de sprite: o VDP lê na metade que VOCÊ escolher
Sprite não lê o tile que você cita, e sim o tile que a **base do reg 6** manda.
Sem `SMS_useFirstHalfTilesforSprites(1)`, `SMS_addSprite(...,128)` lê o tile
**384** — VRAM nunca escrita = ruído colorido. BG sai limpo porque usa outra base:
**"BG certo + sprite corrompido" é assinatura deste erro.**
Corolário do L006: a causa-raiz REAL era esta, provada em emulador em 2026-08-31.
As duas leis anteriores estavam certas mas eram camadas de cima:
§25 (geometria/metasprite) e o conversor 4bpp. Três defeitos empilhados sobre o
mesmo sintoma — por isso "corrigir a causa" não resolvia.
Gate: `audit_sprite_mode.py` (sprite citando tile < 256 exige a base declarada).

## 28. Tela de emulador com informação não é tela CORRETA
Variância de luma alta e conformidade de paleta **não distinguem arte de ruído**:
lixo de VRAM usa as mesmas cores da CRAM e tem variância altíssima.
`capture_evidence.py` e `screenshot_semantic_gate.py` provam **origem e
não-vacuidade**, nunca correção. Toda captura que sustente claim visual exige
inspeção do conteúdo — humana ou por comparação com referência esperada.
Fato pago: a evidência da F6 (`cena04_sprites.png`) era uma tela de ruído
aprovada por dois gates e aceita como entrega de "7 eixos true".

**Atualização 2026-09-01 (L016 fechada em parte):** o que a COR não denuncia, a
estrutura de TILE denuncia. Arte real usa poucas cores por bloco 8×8; lixo de
VRAM enche cada bloco. `screenshot_semantic_gate` mede a fração de blocos com
≥8 cores — 0,000 em toda captura limpa do acervo, 0,132–0,274 nas telas de
ruído (a evidência da F6 dá 0,149 e agora REPROVA).
**Cuidado:** esse limiar é ESPECÍFICO DE CENA ESPARSA. Arte autoral detalhada
(120 tiles de 8–15 cores) mede 1,000 na mesma métrica — usá-la como detector
universal reprovaria o jogo inteiro. Experimento registrado em L016.

**Corretude, essa sim, se prova (L016 fechada 2026-09-01):** compare a captura
com a FONTE. `audit_render_fidelity.py` extrai a ESTRUTURA da arte autoral
(quais pixels compartilham cor, independente de qual cor a paleta atribuiu) e a
procura na tela. Índice 0 é transparente e fica FORA da comparação — ali a tela
mostra o cenário, não o sprite. Medido: 100,0% nas capturas limpas, 46–57% nas
telas de ruído. Isso independe da densidade da cena.

## 29. Interação se prova pelo DESLOCAMENTO do objeto controlado
"Fração da tela que mudou" não distingue o jogador obedecendo de um inimigo
caindo, de uma morte, nem (antes do §30) do desktop do usuário. Prova de
gameplay = **o sprite controlado se deslocou na direção comandada**, medido em
pixels nativos (canvas 256×192), não em pixels da janela. Sinal fraco (luma
global) só complementa; nunca fecha o eixo sozinho.
O gate mede o que esta seção já exigia (L038–L040):
1. **Direção:** `sign(dx)` / `sign(dy)` coerente com a tecla. `Right` com
   blob andando para a esquerda é FAIL — abs(dx)≥8 sozinho mentia.
2. **Identidade:** a área do blob rastreado não salta para outro objeto
   (dois lutadores do mesmo tamanho; barril saturado sequestrando).
3. **Eco de input:** se `probe_keys` foi observado e permanece 0x00, o
   canal de teclado não chegou na ROM (L039). Fail-closed. Ausência do
   campo = não observado, não é prova de agência.
4. **Escala:** limiares de forma (6–48 × 6–80) aplicam-se em pixels
   nativos. Scale=2.25 no `.ini` do Emulicious não pode inverter o
   veredito (L040). A escala da janela entra no bundle.
5. **Canal deste host:** em KDE/Wayland, XTEST/xdotool **não** atravessa
   o KWin. O canal é kdotool (foco) + ydotool (uinput). `emulator_input.py`
   escolhe o backend. Canário: reset Ctrl+BackSpace zera `probe_frame`.
   Prova de gameplay por RAM (`input_memory.json` com SHA da ROM) é lastro
   do eixo — pixels aqui são ambíguos (L038). `reconcile_claims` aceita os
   dois lastros.
Gate: `capture_evidence.interaction_verdict` + `emulator_input.py` +
`input_memory.json` (quando a prova for por memória).
Fato pago: no laboratorio_01 o d-pad mexe ~8px/frame e a mudança global máxima
teórica da cena é ~1,2% — abaixo do limiar de 2% que existia. O eixo gameplay
ficou reprovado por meses por limiar mal calibrado, não por bug de jogo.

## 30. Captura tem que provar QUE JANELA fotografou
`spectacle -a` fotografa a janela ATIVA. Emulador sem foco (ou instância zumbi)
produz screenshot do DESKTOP — que passa no detector de vacuidade, pode conter
conteúdo pessoal do usuário e, comparado com outro screenshot de desktop, gera
"interação provada" medindo a área de trabalho mudando.
Regra: toda captura valida o tamanho contra a janela do emulador, descarta o
arquivo se for desktop e refaz com re-foco; `capture_evidence` recusa iniciar
com outra instância viva. Foram encontradas **15 capturas de desktop** no
acervo do laboratorio_01, de sessões anteriores — todas apagadas.

## 31. Evidência de áudio: isolada do usuário e datada pela ROM
Gravar o monitor do sink padrão captura TODO o áudio da máquina — música,
chamadas, notificações do usuário. Proibido. `capture_audio.py` move o fluxo do
emulador para um sink NULO dedicado, grava só esse monitor e o remove ao final.
`.wav` ANTERIOR à ROM não prova o binário atual (§26): `reconcile_claims`
passou a exigir captura posterior — existir um wav no acervo não basta.
**Falso negativo conhecido:** gravar antes de a música entrar em regime produz
WAV 100% silencioso, indistinguível de "o jogo é mudo". Isso quase levou a
"consertar" um bug inexistente. O gate repete com warmup crescente e, se
insistir em silêncio, manda confirmar contra uma ROM histórica com som antes de
tocar no código de áudio.
**Corrida de ambiente (L048):** `peak=0` depois do warmup não autoriza editar
a ROM. Matar Java zumbis do Emulicious e repetir; na mesma rodada, gravar um
controle histórico (binário congelado que já teve som). Se o congelado também
sai mudo, o canal é o host; se o congelado tem som e o atual não, aí sim a
ROM. Recorrência da L019: a mensagem sozinha não impediu a segunda ocorrência.

## 32. Grandeza do SMS se re-deriva, não se traduz
Portar metodologia de outro console é portar **método**, nunca número. Cada
grandeza — 8 sprites/scanline, SAT de 64, 2 subpaletas, 256×192, VRAM 16 KB,
RAM 8 KB, **sem DMA** — vale porque foi re-derivada do Master System.
A L001 dizia isso desde a fundação e mesmo assim recorreu duas vezes: a matriz
afirmou sprite "16×16" (L006, dias de sprite invisível) e "X+32 / early clock
32px" (L003, refutado em emulador). As duas eram números do Mega Drive.
Prosa não impediu; agora um gate lê os documentos e confere as grandezas.
Gate: `audit_hardware_constants.py`.

## 33. Instrumento quebrado inverte o diagnóstico
Antes de acusar a função sob teste, prove o INSTRUMENTO contra um caso conhecido.
L009 concluiu que `SMS_loadTiles` travava; em 2026-09-01 o probe
`_laboratorio/loadtiles_hang` mostrou que a função completa nas duas condições
(display ligado e desligado, 4 chamadas seguidas). O que falhava era a medição:
marcador `__at()` **sem `volatile`** é eliminado pelo SDCC (a escrita não é lida
em lugar nenhum do C) e a leitura DAP do Emulicious vem prefixada com `$`.
Mesmo padrão do falso negativo de áudio (§31) e do "sprite invisível" (§27).
Corolário (L035): "ler na tela" era a resposta certa quando o único canal
disponível era o depurador mal usado — não vire doutrina permanente. Quando
a medição é de estado/taxa, o canal certo é memória viva; construir o canal
vale mais que compensá-lo com heurística de pixels (§37).
Antes de teorizar estouro de VBlank, corrida de latch ou VDP "quebrado",
inspecione o **conteúdo que já está no asset/VRAM**. Alfabeto embutido no
tileset + fonte nova = "KKEN" na tela, não bug de hardware (L044). Classe
causal: `asset_content_mismatch`.
Gate: `audit_debug_markers.py`, no pré-gate do build.

## 34. Captura alveja a JANELA; foco se verifica, não se supõe
`spectacle -a` fotografa a janela **ativa** — e já fotografou o desktop do
usuário (§30/L017). `import -window <id>` alveja por ID: capturar outra coisa
deixa de ser possível, em vez de ser detectável depois. É também mais limpo
(256×217, sem barra de título) e dispensa o shim de libavcodec, que passa a
valer só para o fallback.
`xdotool windowactivate` **não garante foco**: verifique com
`getwindowfocus` antes de CADA tecla e reative até concordar; se não conseguir,
falhe alto — tecla enviada para outra janela vira "input que não mudou nada".
**Neste host (KDE/Wayland) xdotool fica cego** (`getwindowfocus` vazio) e o
XTEST não entrega evento ao cliente Xwayland (L039). Canal: kdotool +
ydotool via `emulator_input.py`. O fallback xdotool só vale em sessão X11.
**Área de jogo se deriva do hardware, não se chuta:** a canvas é 256×192,
ancorada embaixo da moldura e centrada na horizontal. A fração fixa de 28% que
existia antes cortava 60px de jogo na captura sem moldura.
Gate: `capture_evidence.game_area` + `_shoot_window` + `emulator_input.py`.

## 35. Coordenada de tile não é checada por ninguém — XYtoADDR é aritmética pura
`XYtoADDR(x,y) = SMS_PNTAddress|((((y)<<5)+(x))<<1)`. Não satura, não valida,
não avisa. Escrever fora dos limites falha de **duas** maneiras diferentes, e
tratá-las como uma só custou a L011:
- `y` em **24..27** → cai na cauda da PNT que o modo 192 linhas não renderiza.
  Nada quebra e nada aparece. Foi o `"VITORIA!"` da linha 26.
- `y >= 28` → passa de `0x3EFF` e invade `0x3F00`, a **SAT**. O "texto"
  reposiciona sprites.
- `x >= 32` → `<<5` não satura: `x=33,y=3` é o mesmo endereço que `x=1,y=4`.
As 24 linhas valem para o modo padrão; só com `VDPFEATURE_224LINES` a linha 26
passa a ser legítima. Coordenada vinda de variável **não** é aprovada em
silêncio: é reportada como não provada.
Gate: `audit_tilemap_bounds.py`, no pré-gate do build.

## 36. FPS do título prova o EMULADOR; o eixo é sobre o JOGO
`Emulicious - 100% (60 fps)` é velocidade de **emulação**: o quanto o host deu
conta. Uma ROM parada num laço vazio mantém o título em 60 fps, porque o Z80
emulado continua girando — só não desenha nada novo. Fechar `fps_constante` só
com o título é medir o instrumento, não o jogo.
Prova independente: o contador de frames que a própria ROM desenha na tela. Não
é preciso **ler** o dígito (isso exigiria a fonte, que só existe dentro do
`SMSlib.lib`); basta cronometrar quando o bloco 8×8 **muda**.
Quatro armadilhas, todas encontradas medindo e nenhuma prevista:
1. **Folga de Nyquist se confere no intervalo medido, não no pedido.** Cada
   captura leva ~1,5s se a janela for reativada a cada tiro; um `--interval
   0.3` virava 1,5s real, e a folga declarada de 7,1× era de 1,4×.
2. **Assinar RGB conta o cenário.** O backdrop piscando muda os pixels de cor 0
   do tile. Assine a **forma** (pixel ≠ cor dominante da célula): fundo trocando
   de cor inteiro continua dominante e a máscara não se mexe.
3. **`import` fotografa durante o repaint** e o dígito sai rasgado — um estado
   de 1 amostra que transforma uma troca em duas.
4. **Contar transições e dividir pela janela quantiza nas bordas** (±8 fps com
   período 128 numa janela de 16s) e um único rasgo sobrevivente contamina tudo.
   Use a **mediana das durações de estado**: robusta a outlier, e a dispersão
   em volta dela é literalmente o que o eixo se chama — constante, não médio.
Estimar o período e classificar artefato com o mesmo limiar é circular.
Gate: `measure_frame_advance.py`, ao lado (não no lugar) de `measure_fps.py`.

## 37. Escrita sem leitor não é canal — e canal condenado por instrumento só reabre com fato pago
Os probes de `0xC7F0` existiam no fonte e NENHUMA ferramenta lia: o
diagnóstico de runtime corria por pixels — foco do gerenciador de janelas
(§34), rasgo de captura e Nyquist de screenshot (§36) — enquanto o estado
completo do jogo estava a um read de distância. A L010 condenara o canal
DAP inteiro porque `evaluate` "retornava `$0` para qualquer endereço"; o
que avaliava mal era a EXPRESSÃO: `0xC7F0` avalia ao próprio número, ler
memória é `@0xC7F0` (byte) ou `word.ram@@0xC7F0` (word) — a
`Expressions.txt` do emulador documentava tudo. O §33 já tinha o nome para
isso (instrumento quebrado inverte o diagnóstico) e mesmo assim o canal
morreu condenado. Fatos operacionais pagos 2026-09-04 contra
Emulicious 2026-03-27:
1. UM pedido não-suportado MATA a thread do adaptador (`Unhandled request`
   no log) e todo pedido seguinte pende — cliente DAP com whitelist
   fechada e timeout em toda espera;
2. sessão aberta antes do boot da ROM fica stale: initialize/attach
   respondem, evaluate pende. Canário `@addr` decide; sem resposta,
   reconecta (reconectar é seguro);
3. este build NÃO TEM rota de escrita (readMemory/writeMemory/
   setVariable/setExpression ausentes; `=` é comparação, provado por
   readback) — input segue por teclado com eco em `probe_keys`; agência
   por escrita em memória é finding aberto, não promessa (§22).
Leitura de memória só com a emulação pausada; o relógio da janela de fps é
conservador (marca antes do continue e antes do pause) para nunca inflar o
fps acima do real.
Estado que dura ~20 frames não se prova por screenshot: a mesma chamada
cai na luta numa execução e no título em outra (L054). Exponha a pose/
facing no probe (custo zero de RAM) e leia a variável. Fotografar a
"pose certa" é sorteio; ler `probe_pose` é medição.
Gate: `measure_runtime_probe.py` — magic "SMRT" + schema antes de qualquer
métrica (o §26 visto pelo consumidor); fps por delta de `probe_frame`
sobre o tempo de EXECUÇÃO.

## 38. Persistência causal: relatório não é entrega
Diagnóstico, correção de ferramenta, build isolado, captura ou um único
milestone são transições, não o fim da execução. Depois de registrar o
resultado, escolha a próxima lacuna causal e continue.
Duas tentativas equivalentes sem evidência nova encerram a **rota**, não o
projeto. Documento/build com `blockers_removed=0` não é progresso.
Mismatch de representação (dimensão, indexação, grid) não é gate humano:
mude a representação ou o produtor. Escala `locked` reautoriza no grid;
probe maior é evidência, nunca substituto. GUI por ponteiro é
`interaction_channel_mismatch`. Conteúdo já presente no asset/VRAM que o
agente teorizou como bug de VDP é `asset_content_mismatch` (L044).
Afinar o roteiro da atração/demo para o próprio teste passar é
`evidence_script_tuned_to_pass` (L053): reporte o caminho como não
observado; não fabrique a evidência.
Um blocker de arte não paralisa gameplay/áudio/QA; um blocker de captura não
paralisa produção visual. Gate humano registra a pergunta e continua só os
ramos independentes — aprovação humana não se simula.
Pare somente por ação destrutiva/externa sem autorização, licença ausente,
contradição de autoridades, decisão humana irredutível sem ramo independente,
impossibilidade de hardware medida, ou rotas seguras esgotadas.
Gate: `audit_causal_persistence.py`. Workflow: `causal-persistence-loop.md`.

## 39. Época visual: boot não é qualidade
Captura que prova boot, foco de janela e rota Linux classifica no máximo
`runtime_probe_passed_visual_epoch_failed`. Não prova cena final, escala,
gameplay completo nem AAA. PNG indexado, ≤15 úteis e 6-bit são **sintaxe**;
qualidade é época `delivery` com personagens distintos, palco autoral sem
branding de engine, HUD sem overlap e escala contratada no GDD.
Blockers permanentes: `wrong_visual_epoch`,
`placeholder_or_probe_in_delivery_scene`, `duplicate_character_asset`,
`entity_scale_below_contract`, `stage_contains_branding_or_reference_screen`,
`hud_overlap_or_clipping`, `rom_asset_binding_unproven`.
Canvas da composição é 256×192 (224 só com `VDPFEATURE_224LINES`). Copiar
320×224 do Mega Drive é violação do §32, não "benchmark".
Não promover `probe`, `reference_only`, `negative_case_evidence`,
`technical_candidate`, `visual_lab_control` nem tela HAMOOPIG/splash como palco.
Não reutilizar o mesmo PNG para dois personagens. Não reduzir personagem só
para economizar tiles.
BG e HUD não podem ser o objeto mais saturado com forma de sprite — isso
sequestra o detector de gameplay e some com o jogador (L042). Lutador/
jogador é o pico de leitura. Com ROM cheia, composição (paleta, pose, fonte
já carregada) precede asset novo (L049).
Gate: `audit_visual_delivery.py`. Skill: `sms-visual-excellence.md`.

## 40. Vínculo asset → ROM é prova, não convenção
Source PNG → caminho em `res/` → símbolo gerado → SHA-256 da ROM. Boot de
uma ROM não prova que a arte autoral está naquele binário. Mapa ausente,
SHA divergente ou símbolo duplicado = `rom_asset_binding_unproven`.
Entrega (`--require` / `--delivery`) falha fechado sem o mapa.
Gate: `audit_rom_asset_binding.py`. Schema: `rom_asset_binding_v1`.

## 41. Review independente e orquestração limitada
Checkpoints `foundation` / `pre_growth` / `vertical_slice` / `release_candidate`
exigem review read-only, no máximo três domínios, hash-bound, sem autoaprovação
e sem declarar `ready_for_aaa`. Parecer stale (SHA divergente) cai.
Trabalho realmente independente pode ir em paralelo em até **três** ramos
(`visual`, `runtime`, `audio_qa`). Claim, promoção, git e memória ficam no
coordenador. Worker que promove ou eleva teto é contrato violado.
Gates: `quality_review_router.py`, `harness_orchestration.py`.
Workflows: `independent-quality-review.md`, `production-loop.md`.

## 42. Animação semântica não é rename de frame
Strip reordenado, ação clonada com outro nome, ciclo de um único frame
repetido ou pivot oscilando não são animação. Roster exigido pelo GDD
ausente reprova. Sintaxe de PNG e SAT não medem isso.
Gate: `audit_animation_semantics.py`. Skill: `sms-sprite-animation.md`.

## 43. Captura de lição é medida, não caderno
§21 exigia JSON + seção + ferramenta. O agente passou a gravar L038–L049
só no ledger: prosa com `dedup_key`. Recorrência da própria regra de
aprendizado. Relatório de lição sem JSON canônico não é captura.
IDs L020–L034 nunca foram emitidos neste repo; L012 é furo declarado.
Citar L023/L025 como lições SMSForge é número da fábrica-mãe, não ID
deste acervo (aliases reais: L007, L013/§36).
Persona/skill que ensina doutrina supersedida — X+32, TALL=16×16, DAP
"retorna $0", monitor do sink default como captura, openMSX como gate
SMS — é regressão, mesmo que a matriz/lei já tenham sido corrigidas.
Gate: `audit_learning_capture.py`. Registro: `doc/curation/id_registry.json`.

## 44. Tamanho de símbolo tem uma fonte
`#define FOO_SIZE` e `foo[N]` (e o mesmo define em dois headers) têm de
coincidir. Escrever o tamanho à mão num header-índice enquanto a folha
encolhe faz o consumidor ler além do array — sem sintoma visível, porque
o metasprite não referencia os tiles extras (L052). Header gerado a partir
da folha; `--check` no gerador. Gate: `audit_symbol_size_sync.py`.

## 45. Estado transitório se grava; screenshot dele é sorteio
O §36 (Nyquist de screenshot) e a L054 (pose no probe) dizem o mesmo defeito por
dois ângulos: um PNG não tem eixo do tempo, então transição, animação e game
feel ficam sem lastro. O canal que faltava não era outra heurística de pixel —
era **gravar**. O Emulicious grava do FRAMEBUFFER (256×192 exatos, sem moldura,
sem menu, sem desktop), o que também torna impossível vazar a tela do usuário
(§30/L017) em vez de detectá-lo depois.
Atalho instalado em `Emulicious.ini` com prefixo `Keys` (F7 inicia, F8 para);
encode por FFMPEG externo (`FFMPEGPath`). Gate: `capture_video.py`.
**Não confunda com a L055:** o que ela recusa é MP4/GIF de *mood* gerado por
ferramenta de arte apresentado como prova de ROM. Vídeo do framebuffer do
emulador rodando a ROM selada é o oposto disso — tem cadeia de custódia.
Três falhas MUDAS que o gate agora fecha (cada uma custou uma execução):
1. Instância zumbi do emulador rouba o foco **e reescreve o `.ini` ao morrer**,
   apagando o atalho recém-instalado. Abortar se já houver Emulicious vivo.
2. F10 não para a gravação: no Swing/AWT é o atalho da barra de menus. A
   gravação seguia aberta e era finalizada **ao morrer o processo** — saía um
   `.mp4` válido que parecia prova de que o atalho pegou.
3. Mover o `.mp4` quando o tamanho para de crescer o corrompe: o FFMPEG ainda
   reabre o arquivo para escrever o atom `moov`. Critério = ffprobe consegue ler.
A trilha de áudio é anexada pelo gate: o `temp.wav` do emulador declara no
chunk `data` o DOBRO dos bytes que existem, o FFMPEG batia em EOF na metade e
descartava o som. Formato lido do `fmt `, nunca constante; payload mudo não é
anexado (L048); e o remux **não pode encurtar o vídeo** — `-shortest` cortou
455 → 452 frames e o guard recusou.
Limite honesto: o vídeo prova que a ROM renderizou, que a imagem mudou e que
havia som. Não prova mecânica correta nem que a música é a certa (§28/§31).

## 46. Busca de janela por NOME exige campo livre — senão o gate mede outra ROM
`xdotool/kdotool search --name Emulicious` devolve a janela de **qualquer**
instância, e todo ponto de captura pega a primeira. Com um zumbi vivo o gate não
falha: ele mede o binário errado e emite **veredito confiante sobre o seu**.
**Demonstrado 2026-09-07:** com um Emulicious de MSSF2T rodando,
`audit_deterministic_boot --rom laboratorio_01.sms` respondeu
`[FAIL] boot NAO deterministico` — e o PNG que ele julgou mostra Ken × Guile,
"ROUND 1". Determinismo é o eixo mais exposto: zumbi PARADO dá hashes idênticos
(falso PASS), zumbi ANIMANDO dá divergentes (falso FAIL).
O perigo já tinha lei (§34/L017) e mesmo assim tinha **três tratamentos**: dois
gates abortavam, um matava, e dois não faziam nada. Lei sem enforcement uniforme
é lei só onde alguém lembrou.
Política única em `emulator_session.py`: **ABORT** por padrão (matar processo do
usuário sem pedir é pior que falhar — ele pode estar depurando); **KILL** só
onde a lição exige (L048, dentro da retentativa de áudio). A mensagem nomeia o
defeito, não só o estado.
**Detecção é por JVM, não por linha de comando:** `pgrep -f` casa também o SHELL
que invocou a ferramenta — medido, 3 PIDs onde havia 1 emulador. Confirme
`argv[0]` ser `java`, senão o gate aborta por causa de quem o chamou.

## 47. Proveniência de áudio tem gate próprio
O `audit_provenance.py` cobre só PNG — e foi por esse furo que um `.psg`
entrou na ROM sem entrada no manifest: `music_ken_stage.psg` (MSSF2T,
2026-09-07) foi parar no `res/audio/` e nenhum gate tinha o que reprovar
(L058). O `audit_psg_channel_binding.py` lê o mesmo manifest, mas só amarra
canal de SFX: arquivo coberto por UM gate não fica coberto nos outros eixos.
Manifest: `doc/audio_provenance_manifest.json`, mesma estrutura
`{"assets": [...]}` com `file` relativo (ex.: `res/audio/x.psg`) que o gate
de canal já consome — o gate novo é aditivo, não substitui ninguém.
Três eixos, todos executáveis:
1. **Cobertura:** todo `.psg` em `res/audio/` tem entrada no manifest.
   Órfão reprova — "está na ROM" não é procedência.
2. **Integridade:** `sha256` e `bytes` declarados batem com o blob em disco;
   asset que mudou sem re-declarar reprova (mesmo princípio do visual).
3. **Referência de port:** `origin` com transcrição/port/arranjo exige
   `reference` `{file, sha256}` — o arquivo referenciado existe e o hash
   bate. Jogo portado de referência comercial com trilha "autoral genérica"
   no lugar do porte é troca silenciosa de obra (L059); port sem referência
   hasheada não é port provado, é intenção. Autoral pura não deve reference.
Gate: `audit_audio_provenance.py`.


## 48. Prova de golpe contra a IA lê o estado do oponente (L060)
Whiff não é defeito de colisão enquanto o defensor não estiver na prova. O
"soco conecta às vezes" do MSSF2T virou três semanas de teoria errada
("janela de 4 px" entre `PUSH_W` e a caixa) porque a leitura de código não
era instrumentada. Os probes dataram a causa real: a IA recua ANDANDO com
guarda quando o jogador ataca e `(g_frame & 8)` (ST_WALK_B, gap 20->28
dentro da janela ativa), contra-ataca antes do nosso ativo e acerta chute em
quem agacha. Regra executável:
1. Prova de golpe carrega `P[1].state`/`P[1].guard` (byte do oponente) junto
   com o resultado — whiff sem estado do defensor não tem causa.
2. Cronometragem contra IA é por TEMPO DE RELÓGIO com o emulador rodando
   contínuo; polling DAP pausado tem granularidade de 2-4 frames e janela
   fixa de frames erra por ±8 px (medido).
3. Atribuição de dano a golpe exige dano compatível (soco 7, chute 10,
   projétil 12, chip 2) — queda de 10 com "pose de soco por perto" é chute,
   não soco.
Gate: `prove_input_memory.py` (punch_window, linha_tempo_b1, P1_STATES).

## 49. Orçamento de frame se mede com instrumento na ROM (L061)
Orçamento "declarado" em spec não fecha eixo nenhum — e o degrau seguinte é
um instrumento que mora na ROM, não na bancada. Padrão do probe SMRT:
`probe_vline` (VCounter lido NO FIM do trabalho do frame, antes do wait de
VBlank) + `probe_vovf` (contador saturante de frames com vline >= limiar de
VBlank). O contador é a evidência dura (imune a amostragem); o vline é o
contexto. Derrame não derruba fps — espreme o streaming de VRAM, então
"fps 60" não absolve orçamento estourado: mediu-se 247 frames derramados em
~2700 com fps 60 (MSSF2T v085, modo atração). Pior caso declarado é o que a
medição usa (troca de pose + HUD + projéteis), não o caminho vazio.
Gate: `measure_worst_frame.py` (por projeto; molde com `--self-check`).

## 50. Estado raro de UI se captura com roteiro que o força (L062)
Banner de 120 frames não cai em keyframe uniforme — três gravações de 100s
perderam o "K.O." com 8/12 frames. Roteiro executável: (1) input que tira a
ROM do modo atração e FORÇA o estado (pressão contínua em direção ao
oponente esvazia hp antes do TIME UP); (2) gravação com folga (o round é
mais longo que o palpite); (3) extração densa (fps=1) para localizar o
frame; (4) frame extraído vira artefato nomeado, o vídeo selado prova a
cadeia. Sorte de keyframe não é método; roteiro é.
Gate: `capture_video.py` (--press com roteiro de força).

## 51. Falha total de canal DAP: suspeitar de diálogo modal e de vão de sessão (L063, L064)
Dois modos de falha total, ambos com cara de "ambiente instável":
1. **Diálogo modal bloqueia o carregamento da ROM** (L063): o Emulicious
   abriu "Update Behaviour" no boot; a ROM da linha de comando nunca carrega,
   o debugger interno nasce null e TODO `evaluate` NPE-ia
   ("DAPDebugger.debugger is null") com a porta TCP VIVA — as ferramentas
   diziam "canal DAP não ficou vivo" e a culpa caía no jogo/medição.
   Diagnóstico executável: título da janela sem o nome da ROM + janela de
   diálogo via `kdotool search`. Correção persistente no ini (`Update=0`);
   config do emulador é suspeita padrão quando o canário NPE-ia com porta
   respondendo.
2. **Evidência fresca morre em vão entre turnos** (L064): a janela de frescor
   do selo (120 min) atravessa vãos de horas entre turnos do agente — a
   cadeia completa (capturas -> selo) roda em UM único comando, sem depender
   de turno. E `rom_asset_binding.json` é escrito à mão: atualizar no mesmo
   ciclo do rebuild — defasou duas gerações (09ed345a -> 1800c79c ->
   0f4963c0) antes de alguém reparar.
Gate: `emulator_session.py` + `seal_fresh_evidence_bundle.py`.

## 52. Gesto de comando nao paga delay de harness (L065, L066, L067)
Um buffer de 8 ticks a 60 Hz é ~133 ms. `press_spec()` que chama
`focus_wayland()` (~300 ms) **antes de cada tecla** espalha Down→Right→A
por ~18 frames e o Down sai do hist antes do A. Isso nao prova que o QCF
da ROM esta quebrado.

Regras executaveis:
1. Gestos encadeados usam **um unico foco** e `press_spec(..., refocus=False)`.
   Default `refocus=True` permanece para teclas isoladas (andar, soco).
2. Prova de QCF le hist/qcf/SP/estado no maximo alguns frames apos o botao,
   nao 0,9 s depois (a janela de 8 ticks ja e so neutro).
3. Se `qcf==1` e o especial nao entra, suspeitar da **borda** de B1
   (KEY_PRESSED) atrasada 1-3 frames — aceitar HOLD na mesma janela de 8.
   Nao alargar `hist[]` para caber o harness.
Gate: `emulator_input.py` (`refocus`, `qcf_fits` no `--self-check`).
HAMOOPIG: `tools/prove_special.py` + probe `0xC7D0`.

## 53. build_record nao e memory bank (L068)
`out/build_record.json` grava eixos no compile. Runtime nasce `false` e so
sobe no **proximo** build se `axis_support()` achar artefato no contrato da
fabrica (`evidence.json` informative, `fps.json`, `input_memory.json`).
Editar `axes` a mao e proibido (release-rom). Divergencia "memory bank diz
testado / build_record diz false" e esperada ate o rebuild com evidencias
mais novas que a ROM — autoridade #1 continua o memory bank.
Gate: `reconcile_claims.py` (reprova `true` sem lastro; nao promove a mao).
