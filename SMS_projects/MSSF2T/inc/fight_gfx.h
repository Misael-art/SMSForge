/* gerado por tools/gen_fight_gfx.py — NAO editar a mao.
 * Os tamanhos saem das proprias folhas: escrever de novo aqui foi o
 * que deixou fight_gfx.h dizendo 1024 para uma folha de 832 B. */
#ifndef FIGHT_GFX_H
#define FIGHT_GFX_H
#include "stage_ken_tiles.h"

/* Apenas as folhas que olham para a ESQUERDA: o facing direito e
 * espelhado em runtime (bitrev + dx-mirror). Ver doc/15-tdd.md. */
extern const unsigned char ken_idle_tiles[];
extern const signed char ken_idle_meta[];
extern const unsigned char ken_walk_tiles[];
extern const signed char ken_walk_meta[];
extern const unsigned char ken_punch_tiles[];
extern const signed char ken_punch_meta[];
extern const unsigned char ken_special_tiles[];
extern const signed char ken_special_meta[];
extern const unsigned char ken_hit_tiles[];
extern const signed char ken_hit_meta[];
extern const unsigned char ken_ko_tiles[];
extern const signed char ken_ko_meta[];
extern const unsigned char ken_crouch_tiles[];
extern const signed char ken_crouch_meta[];
extern const unsigned char ken_jump_tiles[];
extern const signed char ken_jump_meta[];
extern const unsigned char guile_idle_tiles[];
extern const signed char guile_idle_meta[];
extern const unsigned char guile_walk_tiles[];
extern const signed char guile_walk_meta[];
extern const unsigned char guile_punch_tiles[];
extern const signed char guile_punch_meta[];
extern const unsigned char guile_special_tiles[];
extern const signed char guile_special_meta[];
extern const unsigned char guile_hit_tiles[];
extern const signed char guile_hit_meta[];
extern const unsigned char guile_ko_tiles[];
extern const signed char guile_ko_meta[];
extern const unsigned char guile_crouch_tiles[];
extern const signed char guile_crouch_meta[];
extern const unsigned char guile_jump_tiles[];
extern const signed char guile_jump_meta[];
extern const unsigned char hadouken_tiles[];
extern const signed char hadouken_meta[];
extern const unsigned char sonicboom_tiles[];
extern const signed char sonicboom_meta[];
extern const unsigned char stage_ken_map[24][32];

#define KEN_IDLE_TILES_SIZE 832
#define KEN_WALK_TILES_SIZE 896
#define KEN_PUNCH_TILES_SIZE 896
#define KEN_SPECIAL_TILES_SIZE 832
#define KEN_HIT_TILES_SIZE 896
#define KEN_KO_TILES_SIZE 320
#define KEN_CROUCH_TILES_SIZE 640
#define KEN_JUMP_TILES_SIZE 512
#define GUILE_IDLE_TILES_SIZE 960
#define GUILE_WALK_TILES_SIZE 768
#define GUILE_PUNCH_TILES_SIZE 896
#define GUILE_SPECIAL_TILES_SIZE 960
#define GUILE_HIT_TILES_SIZE 704
#define GUILE_KO_TILES_SIZE 448
#define GUILE_CROUCH_TILES_SIZE 768
#define GUILE_JUMP_TILES_SIZE 640
#define HADOUKEN_TILES_SIZE 128
#define SONICBOOM_TILES_SIZE 128

#endif
