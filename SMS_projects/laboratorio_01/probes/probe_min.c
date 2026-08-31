
/* canonical_fixture_gate: scope=static_contract — fixture de validacao,
   NAO infere claim de jogo (apenas prova um comportamento). */
#include "SMSlib.h"
SMS_EMBED_SEGA_ROM_HEADER_16KB(0,0);
void main(void){
  SMS_init();
  SMS_setBackdropColor(1);
  SMS_displayOn();
  for(;;)SMS_waitForVBlank();
}
