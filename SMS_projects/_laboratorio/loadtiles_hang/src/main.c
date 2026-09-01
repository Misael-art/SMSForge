/* loadtiles_hang — probe de laboratorio (SMSForge)
 *
 * L009(3) afirma travamento DENTRO de SMS_loadTiles. Mede-se com marcadores
 * VOLATILE (L009 item 2: sem volatile o SDCC elimina a atribuicao e o marcador
 * mente) impressos NA TELA — sem DAP, evitando a armadilha do prefixo '$'
 * (L009 item 1).
 *
 * DISPLAY_ON_DURING_LOAD reproduz a condicao historica: os loads vinham depois
 * de SMS_autoSetUpTextRenderer, que LIGA o display.
 */
#include "SMSlib.h"

#ifndef DISPLAY_ON_DURING_LOAD
#define DISPLAY_ON_DURING_LOAD 0
#endif

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "loadtiles_hang",
                                     "probe: SMS_loadTiles trava?");

volatile unsigned char __at(0xC900) m1;   /* antes do load  */
volatile unsigned char __at(0xC901) m2;   /* depois do load */
volatile unsigned char __at(0xC902) m3;   /* depois de 4 loads seguidos */

static const unsigned char tile_a[32] = {
    0xFF,0,0,0, 0xFF,0,0,0, 0xFF,0,0,0, 0xFF,0,0,0,
    0xFF,0,0,0, 0xFF,0,0,0, 0xFF,0,0,0, 0xFF,0,0,0
};
const unsigned char pal[16] = {0x00,0x3F,0x30,0x0C,0x03,0x2A,0x15,0x38,
                               0x07,0x38,0x1C,0x23,0x2F,0x11,0x26,0x19};
static const char hexd[] = "0123456789ABCDEF";

static void put_hex(unsigned char x, unsigned char y, unsigned char v) {
    unsigned char b[3];
    b[0] = hexd[(v >> 4) & 15]; b[1] = hexd[v & 15]; b[2] = 0;
    SMS_printatXY(x, y, (const unsigned char *)b);
}

void main(void) {
    m1 = 0; m2 = 0; m3 = 0;
    SMS_init();
    SMS_loadBGPalette(pal);
    SMS_loadSpritePalette(pal);
    SMS_autoSetUpTextRenderer();      /* LIGA o display (SMSlib README) */
#if !DISPLAY_ON_DURING_LOAD
    SMS_displayOff();
#endif
    m1 = 0xA1;
    SMS_loadTiles(tile_a, 100, 32);   /* o load sob suspeita */
    m2 = 0xB2;
    /* quatro loads seguidos, como faz o laboratorio_01 hoje */
    SMS_loadTiles(tile_a, 101, 32);
    SMS_loadTiles(tile_a, 102, 32);
    SMS_loadTiles(tile_a, 103, 32);
    SMS_loadTiles(tile_a, 104, 32);
    m3 = 0xC3;
    SMS_displayOn();

    SMS_printatXY(2, 8,  (const unsigned char *)"M1:");
    put_hex(6, 8, m1);
    SMS_printatXY(2, 10, (const unsigned char *)"M2:");
    put_hex(6, 10, m2);
    SMS_printatXY(2, 12, (const unsigned char *)"M3:");
    put_hex(6, 12, m3);
    SMS_printatXY(2, 15, (const unsigned char *)"LOADTILES OK");

    for (;;) SMS_waitForVBlank();
}
