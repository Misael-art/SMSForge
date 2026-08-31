
/* canonical_fixture_gate: scope=hardware_state — fixture de validacao,
   NAO infere claim de jogo (apenas prova um comportamento). */
#include "SMSlib.h"
SMS_EMBED_SEGA_ROM_HEADER_16KB(0,0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1,0,"probe","f1v2","sprite");
const unsigned char pal[16]={0x00,0x3F,0x03,0x15,0x08,0x36,0x29,0x1C,0x0B,0x11,0x30,0x24,0x18,0x0C,0x06,0x02};
static const unsigned char tileX[16]={0x81,0x81,0x42,0x42,0x24,0x24,0x18,0x18,0x18,0x18,0x24,0x24,0x42,0x42,0x81,0x81};
int main(void){
    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_loadTiles(tileX,256,16);          /* tiles de sprite em 0x2000 (reg6 base) */
    SMS_loadBGPalette(pal);
    SMS_loadSpritePalette(pal);
    SMS_setBackdropColor(9);
    SMS_initSprites();
    SMS_addSprite(64,64,256);             /* 16x16 tall na posicao (64,64) */
    SMS_copySpritestoSAT();
    SMS_displayOn();
    for(;;)SMS_waitForVBlank();
}
