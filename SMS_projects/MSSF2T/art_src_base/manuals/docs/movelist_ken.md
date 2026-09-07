# Movelist de referência — KEN (SSF2T, arcade)

> Referência de design para o GDD futuro. Frame data e hits exatos se
> validam contra `sprites/ken_arcade_st_v1.png` na conversão.
> Super (Shoryureppa): confirmar comando/frames na strip.

## Especiais

| Golpe | Comando | Notas p/ SMS |
|---|---|---|
| Hadouken | QCF + soco | Projétil (ver `effects_projectiles_arcade_v1.png`); velocidade em px/frame, sem float |
| Shoryuken | DP + soco | Invencibilidade inicial; arco vertical discretizado |
| Tatsumaki Senpuukyaku | QCB + chute | Deslocamento horizontal + hitbox giratória simplificada |

## Base (normais + agarrões, a detalhar no GDD)

Socos/chutes (close/far/crouch/jump), 2 agarrões, knockdown, dizzy, block
stun, chip damage. Elenco mínimo do teste: idle, walk, jump, crouch, 3
socos, 3 chutes, 3 especiais, hit, block, KO.
