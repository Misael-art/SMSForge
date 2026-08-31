/* example_proto.c — protótipo que usa a CorridorEngine (prova reutilizacao).
 *
 * Configura a engine, carrega a musica battle, e roda um mini jogo:
 * jogador (sprite) + inimigos + tiro + HP + gameOver — tudo com a API da engine.
 * Este arquivo mostra o quão pequeno fica um protótipo quando a engine existe.
 */
#include "engine.h"
#include "music_battle.h"
#include "hero_tiles.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1, 0, "SMSForge", "proto", "corridor engine");

void main(void){
    unsigned int keys;
    unsigned char hp=3, over=0;
    register unsigned char i;
    signed char spr_p;

    engine_init();
    engine_set_music(music_battle);

    /* carregar tiles de hero (jogador) na engine — engine usa tile 128+ */
    /* (o hero_tiles já foi assumido pela engine; carregar aqui se necessario) */

    spr_p = engine_sprite_add(40, 80, 128);
    engine_enemies_reset();

    for(;;){
        keys = SMS_getKeysStatus();
        engine_frame_begin();
        if(!over){
            engine_update(keys, &hp, &over);
        } else {
            if(keys & PORT_A_KEY_1){ hp=3; over=0; engine_player_reset(40,80); engine_enemies_reset(); }
        }
        engine_render(engine_frame_count(), hp, over);
    }
}
