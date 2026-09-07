# 11-gdd — Master Street Fighter 2 Turbo (MSSF2T)

> Autoridade #2. Se não está aqui, não entra.

## Pitch (1 frase)
Dois lutadores distintos (Ken vs Guile) num palco de cais SMS-nativo, melhor de três, com soco, chute, especial, guarda, hitstop e KO — demake jogável de Super Street Fighter II Turbo no Master System.

## Gênero declarado
fighting
(eixos congelados: hitboxes, startup_active_recovery, hitstop, rounds, specials, guard)

## Loop central
Aproximar / afastar → escolher normal ou especial → o oponente guarda ou leva hitstop/knockback → barra cai → KO → próximo round.

## 5 Leis
- **Agência**: d-pad move, B1/B2 atacam, recuar guarda; o sprite controlado desloca na direção comandada.
- **Feedback**: hitstop (4–8 frames), spark, PSG de hit, barra diminui no mesmo round.
- **Fluxo**: CPU dummy no MVP; 2P no mesmo slice.
- **Consistência**: mesmo comando no mesmo estado = mesmo startup/active/recovery.
- **Recompensa**: round ganho, melhor de 3, pose de vitória.

## MVP (golden slice) — escopo travado
- Ken (1P, gi laranja, cabelo loiro) vs Guile (2P/CPU, camo, flattop).
- Palco: cais / porto (tradução do stage do Ken, **sem** wordmark CAPCOM).
- HUD em tiles: nomes, barras, timer, rounds.
- Round start → luta → impacto → KO → resultado.
- Estados HAMOOPIG-like (subset): 100 idle, 410/420 walk, 200 crouch, 300 jump, 101 punch, 104 kick, 107 guard, 700 special, 501 hit, 570 KO, 611 win.
- Especiais MVP: Ken Hadouken (QCF+B1), Guile Sonic Boom (QCF+B1). Shoryuken / Flash Kick / Tatsumaki = pós-MVP.
- Input SMS: B1=soco, B2=chute. Sem 6 botões.

## Contrato de escala (locked)
- Canvas lutador: **32×64** px (4×8 tiles 8×8), modo `SPRITEMODE_TALL` (8×16) + metasprite.
- Altura visível mínima: **48 px** (medida 56 px opacos no canvas 32×64 após
  reautoria nativa que preenche o grid travado).
- Largura máxima ocupada numa scanline: 4 sprites/lutador; no clash, descarta a coluna de trás do lutador mais longe para caber ≤8/linha + projétil.
- HUD é tile, nunca sprite.
- Não reduzir abaixo de 32×64 para economizar tiles. Probe maior não substitui.

## Fora de escopo (MVP)
- Roster de 16, Super Combos, dizzy, throws, stages extras, Sagat, select completo, SRAM, ending, FM/YM2413, 6 botões.
- Pixels de `art_src_base/` na ROM.
- Números de Mega Drive (320×224, DMA, XGM2).

## Teto de claims aprovado
`protótipo jogável de luta 1v1` com **época visual delivery** no golden slice
(Ken vs Guile, cais, HUD). Não é entrega final nem cópia 1:1 do arcade.
`ready_for_aaa` continua false.

## Benchmark (régua, não fonte)
HAMOOPIG-SGDK / TaiketsuUltraHeroGenesis: FSM, hitboxes, rounds, feedback.
SSF2T arcade: densidade, silhueta, timing. Pixels só com tradução nativa.
