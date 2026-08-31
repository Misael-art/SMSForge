/* canonical_fixture_gate: scope=hardware_state */
/* probe_sprite.c v4 — TIMING SEGURO: todas as escritas ANTES do displayOn.
 * Se o sprite aparece aqui, o pipeline esta OK e o problema original era
 * outro. Tela esperada: fundo azul, texto OK, cursor branco/vermelho no centro.
 */
#include "SMSlib.h"
#include "hero_tiles.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1, 0, "probe", "sprite", "v4");

const unsigned char palette_bg[16] = {
    0x00, 0x3F, 0x03, 0x15, 0x08, 0x36, 0x29, 0x1C,
    0x0B, 0x11, 0x30, 0x24, 0x18, 0x0C, 0x06, 0x02
};
static const char hd[] = "0123456789ABCDEF";

const unsigned char palette_sp[16] = {
    0x00, 0x3F, 0x03, 0x15, 0x08, 0x36, 0x29, 0x1C,
    0x0B, 0x11, 0x30, 0x24, 0x18, 0x0C, 0x06, 0x02
};

volatile unsigned char rb[4];
volatile signed char spr_ret;

void main (void) {
    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_loadTiles(hero_tiles, 256, HERO_TILES_SIZE);
    SMS_loadBGPalette(palette_bg);
    SMS_loadSpritePalette(palette_sp);
    SMS_autoSetUpTextRenderer();
    SMS_setBackdropColor(9);

    SMS_printatXY(1, 0, (const unsigned char *)"PROBE V4 SAFE-TIMING");
    SMS_initSprites();
    spr_ret = SMS_addSprite(112, 88, 256);
    SMS_copySpritestoSAT();
    SMS_readVRAM((unsigned char *)rb, 256 * 32, 4);

    /* resultado textual (fonte provada) */
    SMS_printatXY(1, 2, (const unsigned char *)"RB:");
    for (unsigned char n = 0; n < 4; n++) {
        unsigned char hx[2]; hx[1] = 0;
        hx[0] = hd[(rb[n] >> 4) & 15]; SMS_printatXY(4 + n * 2, 2, hx);
        hx[0] = hd[rb[n] & 15];        SMS_printatXY(5 + n * 2, 2, hx);
    }
    SMS_printatXY(1, 4, (const unsigned char *)
        (spr_ret >= 0 ? "SPR:OK" : "SPR:ERR"));

    SMS_displayOn();
    for (;;) { SMS_waitForVBlank(); }
}
