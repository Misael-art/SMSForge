
/* canonical_fixture_gate: scope=static_contract — fixture de validacao,
   NAO infere claim de jogo (apenas prova um comportamento). */
#include "SMSlib.h"
SMS_EMBED_SEGA_ROM_HEADER_16KB(0,0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1,0,"probe","hello","minimal");
const unsigned char pal[16]={0x00,0x3F,0x03,0x15,0x08,0x36,0x29,0x1C,0x0B,0x11,0x30,0x24,0x18,0x0C,0x06,0x02};
void main(void){
    SMS_init();
    SMS_loadBGPalette(pal);
    SMS_autoSetUpTextRenderer();
    SMS_setBackdropColor(9);
    SMS_printatXY(1,1,(unsigned char*)"HELLO PROBE");
    SMS_displayOn();
    for(;;)SMS_waitForVBlank();
}
