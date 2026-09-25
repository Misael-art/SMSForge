/* luta.h — contrato das tabelas geradas (mugen2sms S4.5b) para o runtime.
 *
 * Formato byte-a-byte provado em ROM por MSSF2T (inc/ken_idle_tiles.h:58 e
 * src/fight.c rebuild_meta/draw_fb): metasprite = triplas assinadas
 * (dx, dy, tile) com dx=0x80 no terminador; tile de runtime =
 * (pool_idx*2) + base_de_carga_do_pose, por isso o draw soma `base` ao ler.
 * Espelho horizontal E outro padrao no pool (SMS nao tem flip de sprite);
 * o blob METAL ja traz base+idx do espelho e dx refletido (dx' = lo+hi-dx).
 *
 * API verificada em sdk/devkitSMS/SMSlib/SMSlib.h:
 *   SMS_setSpriteMode/SPRITEMODE_TALL :54-57 (par TALL = tileEven, tileEven+1)
 *   SMS_useFirstHalfTilesforSprites   :53   (L006 — sprites leem 1a metade)
 *   SMS_addMetaSprite / METASPRITE_END:214-216
 *   SMS_loadTiles                     :130  (4bpp, 32 B/tile, tamanho em bytes)
 *   SMS_setBGPaletteColor/_Sprite     :249-250 (palavra 6-bit r|g<<2|b<<4)
 */
#ifndef LUTA_H
#define LUTA_H

#include "SMSlib.h"

/* Uma frame de animacao: duracao em frames de 60/50 Hz + ponteiro p/ triplas.
 * O tile base de cada pose e decidido em runtime (streaming, Task 6); aqui so
 * existe um carregamento estatico linear. */
typedef struct { unsigned char dur; const unsigned char *meta; } Frame;

/* Caixa de colisao (clsn do AIR): cantos em px MUGEN (y para cima), achatar
 * para AABB de tela acontece no runtime (Task 4). */
typedef struct { signed char x, y; unsigned short w, h; } Box;

typedef struct {
    unsigned char id;                       /* pose id (estados referenciam por id) */
    unsigned char n_frames; const Frame *frames;
} Anim;

typedef struct { unsigned char facing; signed int x; signed int y; /* Q8.8 */
                 unsigned char anim, frame, tick; unsigned short life; } Fighter;

/* Sprites leem a primeira metade da VRAM: base 0 (SMSlib.h:53, L006). */
#define FIGHTER_TILE_BASE 0x00

/* Copia as triplas de `meta` para `dst` somando `base` ao byte de tile e
 * devolve o numero de entradas (precedente: rebuild_meta do MSSF2T).
 * dst precisa de espaco para 3*(n+1) bytes. */
extern unsigned char meta_rebase(const unsigned char *meta, unsigned char base,
                                 signed char *dst);

#endif /* LUTA_H */
