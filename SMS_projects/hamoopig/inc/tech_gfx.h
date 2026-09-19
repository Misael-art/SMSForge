/* Autoral SMSForge: glifos 1bpp + silhueta tecnica. NAO e personagem final. */
#ifndef TECH_GFX_H
#define TECH_GFX_H

#define FONT_GLYPHS 41
#define FONT_1BPP_SIZE 328
#define FIGHTER_TILES 8
#define FIGHTER_TILE_BYTES 256
#define CHARSET_STR " 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.!:-"

extern const unsigned char font_1bpp[FONT_1BPP_SIZE];
extern const unsigned char fighter_idle_p1[FIGHTER_TILE_BYTES];
extern const unsigned char fighter_punch_p1[FIGHTER_TILE_BYTES];
extern const unsigned char fighter_idle_p2[FIGHTER_TILE_BYTES];
extern const unsigned char fighter_punch_p2[FIGHTER_TILE_BYTES];
extern const unsigned char tile_floor[32];
extern const unsigned char tile_bar_hp[32];
extern const unsigned char tile_bar_sp[32];
extern const unsigned char tile_bar_empty[32];
extern const unsigned char tile_fb[64];

#endif
