/* engine.h — CorridorEngine: base reutilizável p/ shoot-em-up SMS (devkitSMS).
 *
 * Encapsula o que a cena04 provou: sprites (L006), PSG audio (musica+SFX),
 * scroll BG com estrelas, jogador (input+invuln+flash), inimigos, projetil,
 * HUD e game over. Prototipos novos usam esta API em vez de reescrever.
 *
 * Layout de VRAM (fixo):
 *   tiles 128..131  hero (jogador) / inimigo / projetil
 *   tile  132       estrela (BG)
 *   tile  201       estrela grande / decor
 * Cores: paleta mestra fixa (SMSForge).
 */
#ifndef ENGINE_H
#define ENGINE_H

#include "SMSlib.h"

/* ---- configuração do protótipo ---- */
#define ENG_MAX_ENEMIES  5

/* ---- setup único ---- */
void engine_init(void);                 /* VDP, paletas, text renderer, estrelas, sprites */
void engine_set_music(const unsigned char *song);   /* PSGlib em loop; NULL p/ mudo */

/* ---- entidades (sprites 8x8) ---- */
signed char engine_sprite_add(unsigned char x, unsigned char y, unsigned char tile);
void engine_sprite_set(signed char spr, unsigned char x, unsigned char y, unsigned char tile);
void engine_sprite_hide(signed char spr);
void engine_sprites_flush(void);        /* copySpritestoSAT */

/* ---- jogador ---- */
void engine_player_reset(unsigned char x, unsigned char y);
void engine_player_update(unsigned int keys, unsigned char *hp, unsigned char *over);
unsigned char engine_player_x(void);
unsigned char engine_player_y(void);

/* ---- inimigos ---- */
void engine_enemies_reset(void);
void engine_enemies_update(unsigned int frame);     /* cair + respawn + dificuldade */

/* ---- projetil ---- */
void engine_bullet_fire(unsigned char x, unsigned char y);
void engine_bullet_update(void);
unsigned char engine_bullet_active(void);

/* ---- loop / frame ---- */
void engine_frame_begin(void);          /* SMS_waitForVBlank + PSGFrame + input */
void engine_update(unsigned int keys, unsigned char *hp, unsigned char *over);
void engine_render(unsigned int frame, unsigned char hp, unsigned char over);

/* ---- audio (SFX) ---- */
void engine_sfx_hit(void);
void engine_sfx_shot(void);
void engine_sfx_destroy(void);

/* ---- HUD / estado ---- */
unsigned int engine_frame_count(void);
extern unsigned char engine_over;

#endif
