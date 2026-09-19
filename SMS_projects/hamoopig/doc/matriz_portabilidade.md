# Matriz de portabilidade HAMOOPIG → SMS

Origem lida, não modificada. Status honestos: arquivo ≠ portado.

| Módulo origem | Comportamento | Dep. MD/SGDK | Adaptação SMS | Dados reutilizáveis | Converter | Reimplementar | Orçamento | Teste | Status | Evidência |
|---|---|---|---|---|---|---|---|---|---|---|
| main/scene | opening/title/select/fight/after | SPR/VDP SGDK | scene_request/commit SMSlib | IDs gRoom | — | scene.c | 1 tick extra na troca | ciclo de cenas | executado em emulador | title/fight.png SHA 4d6bfa40 |
| input | pressed/hold/released 6 botões | JOY SGDK | 2 botões+D-pad, 16-bit | semântica | mapa 6→2 | input.c | 1 leitura/tick | held/pressed | implementado | código |
| player/FSM | estados 100/410/101… | Sprite* SGDK | Fighter + tabela | números de estado | timing 60Hz | fighter.c | 2 atores estáticos | soco/guarda | executado em emulador | punch_probe.json HP 64→57 |
| combat_event | hit/guard/throw 1× instância | — | Contact[4] | regra | — | combat.c | 4 eventos | overlap persistente | implementado | código |
| physics | gravidade, piso, push | s16 MD | int16, GROUND_Y 112 | ideia | impulso | fighter.c | — | pulo/limites | implementado | código |
| collision | HBox/BBox/MBox | sprites debug | Box pixel | layout | escala 16×32 | fighter.c | — | simetria | implementado | código |
| hud | vida/SP/clock/HITS/KO | WINDOW/sprites MD | tiles BG | textos | atlas 16×16→8×8 | hud.c | ~20 tiles/frame | leitura | implementado (subset) | código |
| title/opening | fade, OPTIONS | pal 64 | texto técnico | créditos | arte logo | title.c | — | B1 | implementado (provisório) | código |
| select | roster 3, paleta, stage | sprites grandes | IDs Ryo/Musgo | IDs | retratos | title.c | — | confirm | implementado (stub) | código |
| stage/camera | 512×256, DMA | VDP MD | chão tile 8×8 | — | palco 256×192 | fight_enter | SAT vs BG | seams | implementado (técnico) | código |
| audio | XGM1+PCM | YM2612 | PSGlib hurt ch3 / shot ch2 / battle | — | streams autorais | audio.c | 4 canais | mix ≥90% | implementado, mix 49% | audio.wav peak 7470 |
| player_ken | sheet arcade | IP Capcom | ID reservado | frame data só se reautorado | pixels **não** | — | — | — | bloqueado (IP) | decisão GDD |
| player_musgo / ryo | estados próprios | sprites MD | FighterDef | tabelas de estado | arte | fighter_def | 16×32 agora | vs todos | adaptado com recuo | silhueta técnica |
| projéteis | fball sprite | DMA | 1 por lutador, tile 192 | regra | tile 8×16 técnico | fighter fire_* | +2 SAT | persistência | executado em emulador (hit; bola no ar não fotografada) | special_probe.json fire=2 HP 8→0 |
| throw | frente+A perto | 6 botões | B1+B2 gap≤24, dano 10 | regra | — | fighter ST_THROW | SAT | delta 10 | implementado, não observado | prove_throw delta 7 (só soco; B2 teclado) |
| Kensaiden | — | — | personagem novo por contrato | — | arte autoral | Etapa 9 | — | vs roster | não iniciado | núcleo primeiro |
