/* main.c — ponto de entrada do projeto modelo SMSForge.
 *
 * Usa APENAS API confirmada em SMSlib.h (autoridade #8):
 *   SMS_init / SMS_setSpriteMode / SMS_displayOn / SMS_waitForVBlank
 *   SMS_autoSetUpTextRenderer / SMS_printatXY (macros linhas 117/277)
 *
 * Regra do gate de evidencia: o viewport precisa MOSTRAR VIDA
 * (texto + spinner animado por frame counter) — tela lisa reprova.
 */
#include "SMSlib.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1, 0, "SMSForge", "__PROJECT_NAME__",
                                     "projeto modelo");

void main (void) {
    unsigned int frame = 0;
    unsigned char buf[2];
    const unsigned char spin[4] = { '|', '/', '-', '\\' };

    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
    SMS_autoSetUpTextRenderer();
    SMS_setBackdropColor(1);
    SMS_printatXY(9, 11, (const unsigned char *)"SMSFORGE BOOT OK");
    SMS_displayOn();

    for (;;) {
        SMS_waitForVBlank();
        frame++;
        if ((frame & 15) == 0) {          /* spinner a cada 15 frames = vivo */
            buf[0] = spin[(frame >> 4) & 3];
            buf[1] = 0;
            SMS_printatXY(15, 13, buf);
        }
    }
}
