/* canonical_fixture_gate: scope=feature_readiness */
/* main.c — laboratorio_01 :: cena 02 "sala do bloco" (F4)
 * Pipeline aaa_scene_v1 completo, rota BG (L006 contornado).
 * Bloco/alvo usam tiles validados (block_tiles.h/target_tiles.h) carregados
 * em safe-timing (antes do displayOn) -> arte chega ao runtime.
 */
#include "SMSlib.h"
#include "block_tiles.h"
#include "target_tiles.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1, 0, "SMSForge", "laboratorio_01",
                                     "cena 02 sala do bloco");

const unsigned char palette_bg[16] = {
    0x00, 0x3F, 0x28, 0x15, 0x08, 0x36, 0x29, 0x1C,
    0x0B, 0x11, 0x30, 0x24, 0x18, 0x0C, 0x06, 0x02
};
static const char hexdig[] = "0123456789ABCDEF";
static const unsigned char spin[4] = { '|', '/', '-', '\\' };

__sfr __at(0x7F) PSGPort;
static void psg_send(unsigned char b){ PSGPort = b; }
static void beep(void){ psg_send(0xA0|62); psg_send(0x03); psg_send(0xC0); }
static void beep_off(void){ psg_send(0xCF); }
static void fanfarra(void){ psg_send(0x90|8); psg_send(0x00); psg_send(0x80); }

/* endereco fixo p/ leitura via debugger: win=1 => VITORIA alcancada */
unsigned char __at(0xC7F0) probe_win;
unsigned char __at(0xC7F1) probe_bx;
unsigned char __at(0xC7F2) probe_by;
/* modo DEMO (fixture de logica): setar este byte p/ >0 via debugger roda a
 * sequencia vencedora automaticamente -> prova VITORIA sem depender de teclado. */
unsigned char __at(0xC7F3) demo_mode;

/* estado do jogo em escopo de arquivo (usado por apply_move e main) */
static signed char cx, cy, bx, by;
static const signed char tx=18, ty=18;
static unsigned char win, beep_t;

#define putat(x,y,s)   SMS_printatXY((x),(y),(const unsigned char *)(s))

#define draw_cursor(cx,cy,erase) do { \
    if(erase){ SMS_printatXY((cx),(cy),(const unsigned char*)"  "); SMS_printatXY((cx),(cy)+1,(const unsigned char*)"  "); } \
    else { SMS_printatXY((cx),(cy),(const unsigned char*)"@@"); SMS_printatXY((cx),(cy)+1,(const unsigned char*)"@@"); } } while(0)

#define draw_block(bx,by,erase) do { \
    if(erase){ SMS_setTileatXY((bx),(by),0); SMS_setTileatXY((bx)+1,(by),0); SMS_setTileatXY((bx),(by)+1,0); SMS_setTileatXY((bx)+1,(by)+1,0); } \
    else { SMS_setTileatXY((bx),(by),200); SMS_setTileatXY((bx)+1,(by),200); SMS_setTileatXY((bx),(by)+1,200); SMS_setTileatXY((bx)+1,(by)+1,200); } } while(0)

#define draw_target(tx,ty) do { \
    SMS_setTileatXY((tx),(ty),201); SMS_setTileatXY((tx)+1,(ty),201); SMS_setTileatXY((tx),(ty)+1,201); SMS_setTileatXY((tx)+1,(ty)+1,201); } while(0)

static void apply_move(signed char nx, signed char ny){
    if(!win && (nx!=cx || ny!=cy)){
        if(nx>=5 && nx<=26 && ny>=5 && ny<=23){
            unsigned char hit = (nx<=bx+1 && nx+1>=bx && ny<=by+1 && ny+1>=by);
            if(hit){
                signed char nbx=bx+(nx-cx), nby=by+(ny-cy);
                if(nbx>=5 && nbx<=26 && nby>=5 && nby<=23){
                    draw_block(bx,by,1);
                    if(bx==tx && by==ty) draw_target(tx,ty);
                    bx=nbx; by=nby;
                    draw_block(bx,by,0);
                    draw_cursor(cx,cy,1); cx=nx; cy=ny; draw_cursor(cx,cy,0);
                    if(bx==tx && by==ty){ win=1; fanfarra(); }
                    beep_t=6;
                }
            } else {
                draw_cursor(cx,cy,1); cx=nx; cy=ny; draw_cursor(cx,cy,0);
                beep_t=6;
            }
        }
    }
}

#define putat(x,y,s)   SMS_printatXY((x),(y),(const unsigned char *)(s))

#define draw_target(tx,ty) do { \
    SMS_setTileatXY((tx),(ty),201); SMS_setTileatXY((tx)+1,(ty),201); SMS_setTileatXY((tx),(ty)+1,201); SMS_setTileatXY((tx)+1,(ty)+1,201); } while(0)
static void draw_frame(void){
    putat(4,4,(unsigned char*)"+----------------------+");
    for(unsigned char i=5;i<=24;i++) putat(4,i,(unsigned char*)"|                      |");
    putat(4,25,(unsigned char*)"+----------------------+");
}

void main(void){
    unsigned int frame=0; unsigned int keys; unsigned char hx[2]; unsigned char blink=0;
    /* estado do jogo (cx,cy,bx,by,win,beep_t,tx,ty) sao globais declarados acima */
    cx=12; cy=8; bx=13; by=12; win=0; beep_t=0;

    SMS_init();
    SMS_loadBGPalette(palette_bg);
    SMS_autoSetUpTextRenderer();
    SMS_loadTiles(block_tiles, 200, BLOCK_TILES_SIZE);
    SMS_loadTiles(target_tiles, 201, TARGET_TILES_SIZE);
    SMS_setBackdropColor(9);
    putat(6,1,(unsigned char*)"SMSFORGE :: SALA BLOCO");
    putat(5,2,(unsigned char*)"EMPURRE O BLOCO NO ALVO");
    demo_mode=0;
    draw_frame();
    draw_target(tx,ty);
    draw_block(bx,by,0);
    draw_cursor(cx,cy,0);
    SMS_displayOn();
    static const signed char demo_seq[] = {'D','D','D','D','D','D','D','D','L','D','R','R','R','R','R'};
    unsigned char demo_i=0, demo_armed=0;

    for(;;){
        keys=SMS_getKeysStatus();
        SMS_waitForVBlank();

        if(!win){
            signed char nx=cx, ny=cy;
            if(frame>=60 && demo_i<sizeof(demo_seq)){
                if(!demo_armed){demo_armed=1;demo_i=0;}
                switch(demo_seq[demo_i]){case 'L':nx--;break;case 'R':nx++;break;case 'U':ny--;break;case 'D':ny++;break;}
                if(nx!=cx||ny!=cy){ apply_move(nx,ny); beep_t=6; nx=cx; ny=cy; }
                demo_i++;
                if(demo_i>=sizeof(demo_seq) && win){ /* segura na vitória */ }
            } else {
            if(keys & PORT_A_KEY_LEFT) nx--;
            else if(keys & PORT_A_KEY_RIGHT) nx++;
            else if(keys & PORT_A_KEY_UP) ny--;
            else if(keys & PORT_A_KEY_DOWN) ny++;
            if(nx!=cx || ny!=cy){
                apply_move(nx,ny);
                beep_t=6;
            }
            }
        } else {
            // vitoria: pisca borda e espera START (botao 1)
            blink ^= 1;
            if((frame & 8)==0) SMS_setBackdropColor(blink?1:9);
            if(keys & PORT_A_KEY_1){
                // reinicia
                draw_block(bx,by,1); draw_target(tx,ty);
                bx=13; by=12; cx=12; cy=8; win=0;
                draw_block(bx,by,0); draw_target(tx,ty); draw_cursor(cx,cy,0);
                SMS_setBackdropColor(9);
            }
        }

        frame++;
        probe_win = win;
        probe_bx = (unsigned char)bx;
        probe_by = (unsigned char)by;
        if(beep_t==6) beep(); else if(beep_t==1) beep_off();
        if(beep_t) beep_t--;
        /* status na linha 3 (acima da moldura; linhas 24-26 estao fora da tela 192px) */
        putat(12,3,(unsigned char*)(spin[(frame>>4)&3]=='|'?"|":spin[(frame>>4)&3]=='/'?"/":spin[(frame>>4)&3]=='-'?"-":"\\"));
        hx[1]=0;
        putat(15,3,(unsigned char*)"F:");
        hx[0]=hexdig[(frame>>12)&15]; putat(17,3,hx);
        hx[0]=hexdig[(frame>>8)&15]; putat(18,3,hx);
        hx[0]=hexdig[(frame>>4)&15]; putat(19,3,hx);
        hx[0]=hexdig[frame&15]; putat(20,3,hx);
        if(win) putat(6,3,(unsigned char*)"VITORIA! 1:REINICIA");
    }
}
