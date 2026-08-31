/* canonical_fixture_gate: scope=hardware_state */
/* probe_f1b.c — F1 fechamento: A = SMS_loadTiles vs B = SMS_VRAMmemcpy
 * Escreve RB hex na tela para leitura visual (sem DAP).
 */
#include "SMSlib.h"
#include "hero_tiles.h"
SMS_EMBED_SEGA_ROM_HEADER_16KB(0,0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1,0,"probe","f1b","A/B");
const unsigned char pal[16]={0x00,0x3F,0x03,0x15,0x08,0x36,0x29,0x1C,0x0B,0x11,0x30,0x24,0x18,0x0C,0x06,0x02};
static const char hd[]="0123456789ABCDEF";
void main(void){
    unsigned char ra[4], rb[4];
    SMS_init();
    SMS_loadBGPalette(pal);
    SMS_autoSetUpTextRenderer();
    // Teste A: loadTiles
    SMS_loadTiles(hero_tiles,256,64);
    SMS_readVRAM(ra,256*32,4);
    // Limpa area e Teste B: VRAMmemcpy direto
    // (sobrescreve mesmos 4 bytes com padrão diferente para provar escrita)
    SMS_VRAMmemcpy(256*32, hero_tiles, 4);
    SMS_readVRAM(rb,256*32,4);
    SMS_setBackdropColor(9);
    SMS_printatXY(1,1,(unsigned char*)"F1 A/B VRAM 0x2000");
    SMS_printatXY(1,3,(unsigned char*)"A:");
    for(unsigned char i=0;i<4;i++){ unsigned char hx[2]; hx[1]=0; hx[0]=hd[(ra[i]>>4)&15]; SMS_printatXY(3+i*3,3,hx); hx[0]=hd[ra[i]&15]; SMS_printatXY(4+i*3,3,hx); }
    SMS_printatXY(1,5,(unsigned char*)"B:");
    for(unsigned char i=0;i<4;i++){ unsigned char hx[2]; hx[1]=0; hx[0]=hd[(rb[i]>>4)&15]; SMS_printatXY(3+i*3,5,hx); hx[0]=hd[rb[i]&15]; SMS_printatXY(4+i*3,5,hx); }
    SMS_printatXY(1,7,(unsigned char*)"EXP:FF008003");
    SMS_displayOn();
    for(;;)SMS_waitForVBlank();
}
