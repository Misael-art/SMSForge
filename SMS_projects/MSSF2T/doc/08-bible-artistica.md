# 08-bible-artistica — MSSF2T

Dark Deco não se aplica: a linguagem é **arcade Street Fighter** traduzida ao VDP
do Master System (silhueta dura, 1px outline, sem AA).

## Paleta sprite (compartilhada Ken+Guile+FX)
Índice 0 transparente. Outline preto, pele, cabelo amarelo, gi laranja (Ken),
verde camo (Guile), projétil azul, spark amarelo. ≤15 úteis.

## Paleta BG
Céu, mar, madeira, casco branco, HUD. Sem wordmark CAPCOM.

## Escala locked
32×64 por lutador, **56 px visíveis** (medido no PNG indexado). Olhos 1+1 px.
Must-preserve: gi laranja vs camo verde, cabelo loiro vs flattop.

## Model sheets
Guias em `rascunho/*_guide.png` (autoria nativa no grid). `res/fighters/` é
a incumbente. `art_src_base/` permanece `reference_only`.

## Época
`delivery` no golden slice. Gate: `audit_visual_delivery.py --delivery`.
