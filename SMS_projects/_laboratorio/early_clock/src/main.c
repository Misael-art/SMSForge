/* early_clock — probe de laboratorio (SMSForge)
 *
 * PERGUNTA: VDPFEATURE_SHIFTSPRITES (reg 0, bit 3 — SMSlib.h:29) desloca o
 * sprite quantos pixels? E SMS_addSprite armazena X+32 (matriz S05)?
 *
 * Duas ROMs identicas exceto por SHIFT_ON. A diferenca de posicao entre as
 * capturas E a resposta. Boot deterministico (§24): nada anima.
 */
#include "SMSlib.h"

#ifndef SHIFT_ON
#define SHIFT_ON 0
#endif

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "early_clock",
                                     "probe: deslocamento de sprite");

/* Tile solido 8x8 (4bpp, 32 bytes): cor 1 em todos os pixels.
 * Marcador de posicao, nao arte de jogo — probe nao produz asset. */
static const unsigned char marker[32] = {
    0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00,
    0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00,
    0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00,
    0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00
};

const unsigned char pal[16] = {
    0x00, 0x3F, 0x30, 0x0C, 0x03, 0x2A, 0x15, 0x38,
    0x07, 0x38, 0x1C, 0x23, 0x2F, 0x11, 0x26, 0x19
};

void main(void) {
    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
    SMS_loadBGPalette(pal);
    SMS_loadSpritePalette(pal);
    SMS_displayOff();
    /* §27: sprites leem padroes da PRIMEIRA metade da VRAM */
    SMS_useFirstHalfTilesforSprites(1);
    SMS_loadTiles(marker, 100, 32);          /* tile 100 */
    /* name table limpa (§: VRAM nao nasce zerada) */
    for (unsigned char row = 0; row < 24; row++)
        for (unsigned char col = 0; col < 32; col++)
            SMS_setTileatXY(col, row, 0);
#if SHIFT_ON
    SMS_VDPturnOnFeature(VDPFEATURE_SHIFTSPRITES);
#else
    SMS_VDPturnOffFeature(VDPFEATURE_SHIFTSPRITES);
#endif
    SMS_displayOn();

    SMS_initSprites();
    SMS_addSprite(100, 60, 100);   /* referencia: mede o deslocamento */
    SMS_addSprite(0, 100, 100);    /* ancora em X=0: testa o suposto offset +32 */
    SMS_addSprite(16, 140, 100);   /* X<32: a matriz diz que sumiria */
    SMS_copySpritestoSAT();

    for (;;) {
        SMS_waitForVBlank();
    }
}
