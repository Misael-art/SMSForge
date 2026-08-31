/* canonical_fixture_gate: scope=hardware_state */
/* probe_f1_sprite.c — F1/L006: sprite VISIVEL com caminho alternativo.
 *
 * Hipoteses L006 a testar:
 *   (a) SMS_loadTiles usa base de sprite (reg6) que pode divergir;
 *   (b) SPRITEMODE_NORMAL (8x8, nao TALL) + SMS_VRAMmemcpy explicito.
 *
 * Observacao: captura de frame vivo = import -window <main> (canvas congela).
 * Este probe desenha o sprite em posicao FIXA e espera ser visivel.
 */
#include "SMSlib.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1, 0, "probe", "f1", "sprite");

const unsigned char palette_bg[16] = {
    0x00, 0x3F, 0x03, 0x15, 0x08, 0x36, 0x29, 0x1C,
    0x0B, 0x11, 0x30, 0x24, 0x18, 0x0C, 0x06, 0x02
};
const unsigned char palette_sp[16] = {
    0x00, 0x3F, 0x03, 0x15, 0x08, 0x36, 0x29, 0x1C,
    0x0B, 0x11, 0x30, 0x24, 0x18, 0x0C, 0x06, 0x02
};
/* tile 8x8 "X" vermelho sobre fundo branco. Cores: 1=branco(0x3F), 2=vermelho(0x03) */
static const unsigned char tileX[16] = {
    0x81, 0x81, 0x42, 0x42, 0x24, 0x24, 0x18, 0x18,
    0x18, 0x18, 0x24, 0x24, 0x42, 0x42, 0x81, 0x81
};

int main(void){
    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_NORMAL);           /* 8x8 */
    /* tiles de sprite no primeiro endereco via VRAMmemcpy explícito.
     * VDP reg6 (sprite pattern base) default do devkitSMS = 0x0000? testar ambos. */
    SMS_VRAMmemcpy(0x0000, tileX, 16);              /* tiles 0-7 no base 0 */
    SMS_loadBGPalette(palette_bg);
    SMS_loadSpritePalette(palette_sp);
    SMS_setBackdropColor(9);

    SMS_initSprites();
    SMS_addSprite(64, 64, 0);                        /* tile 0, 8x8 no 0x0000 */
    SMS_copySpritestoSAT();

    SMS_displayOn();
    for(;;){ SMS_waitForVBlank(); }
}
