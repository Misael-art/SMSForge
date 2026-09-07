# Movelist de referência — GUILE (SSF2T, arcade)

> Referência de design para o GDD futuro. Frame data e hits exatos se
> validam contra `sprites/guile_arcade_st_v1.png` na conversão.
> Super: confirmar comando/frames na strip (não afirmar de memória).

## Especiais (charge — segurar direção ~2s)

| Golpe | Comando | Notas p/ SMS |
|---|---|---|
| Sonic Boom | charge trás → frente + soco | Projétil (ver `effects_projectiles_arcade_v1.png`); charge cabe em contador de frames |
| Flash Kick | charge baixo → cima + chute | Antiaéreo; arco vertical discretizado |

## Base (normais + agarrões, a detalhar no GDD)

Socos/chutes (close/far/crouch/jump), agarrões (incl. air throw a confirmar),
knockdown, dizzy, block stun, chip damage. Elenco mínimo do teste: idle
(pose icônica parada), walk, jump, crouch, 3 socos, 3 chutes, 2 especiais,
hit, block, KO.
