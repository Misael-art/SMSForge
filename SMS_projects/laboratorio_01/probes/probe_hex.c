
/* canonical_fixture_gate: scope=visual_semantic — fixture de validacao,
   NAO infere claim de jogo (apenas prova um comportamento). */
#include "SMSlib.h"
SMS_EMBED_SEGA_ROM_HEADER_16KB(0,0);
void main(void){
  SMS_init();
  SMS_loadBGPalette((const unsigned char[]){0x00,0x3F,0x03,0x15,0x08,0x36,0x29,0x1C,0x0B,0x11,0x30,0x24,0x18,0x0C,0x06,0x02});
  SMS_autoSetUpTextRenderer();
  SMS_setBackdropColor(9);
  SMS_printatXY(4,3,(const unsigned char*)"0123456789ABCDEF");
  SMS_displayOn();
  for(;;)SMS_waitForVBlank();
}
