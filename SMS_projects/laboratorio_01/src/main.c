/* main.c — laboratorio_01 :: cena 04 "corredor estelar" (combina tudo)
 *
 * Combina: sprites (L006 resolvido), musica PSG rica (PSGlib battle), scroll
 * BG horizontal, sistema de pontos/HP, game over. Prova o pipeline completo.
 *
 * Jogador = sprite 8x8 (hero tile 128) movido por d-pad (8px). Inimigos =
 * sprites 8x8 (tile 129/130) caindo. Scroll = deslocamento do name table (BG).
 * Pontua por tempo sobrevivido; HP 3; game over ao chegar a 0; START reinicia.
 */
#include "SMSlib.h"
#include "PSGlib.h"
#include "hero_tiles.h"
#include "music_battle.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1, 0, "SMSForge", "laboratorio_01",
                                     "cena 04 corredor estelar");

const unsigned char palette_bg[16] = {
    0x00, 0x3F, 0x28, 0x15, 0x08, 0x36, 0x29, 0x1C,
    0x0B, 0x11, 0x30, 0x24, 0x18, 0x0C, 0x06, 0x02
};
static const char hexdig[] = "0123456789ABCDEF";
/* tile de estrela (padrao pontilhado) para o campo de fundo */
static const unsigned char star_tile[16] = {
    0x08,0x00, 0x20,0x00, 0x02,0x00, 0x80,0x00,
    0x10,0x00, 0x40,0x00, 0x00,0x00, 0x01,0x00
};

/* PSG blip */
__sfr __at(0x7F) PSGPort;
static void psg_send(unsigned char b){ PSGPort = b; }

unsigned char __at(0xC7F0) probe_hp;
unsigned char __at(0xC7F1) probe_score;
unsigned char __at(0xC7F2) probe_over;
unsigned int g_frame = 0;      /* g_frame em escopo de arquivo (p/ HUD) */

#define putat(x,y,s)  SMS_printatXY((x),(y),(const unsigned char *)(s))

static void draw_hud(void){
    unsigned char buf[2];
    putat(4,1,(unsigned char*)"HP:300 SCORE:0000");
    buf[1]=0;
    buf[0]=hexdig[((g_frame>>7)&0x0F)]; putat(24,1,buf);
    buf[0]=hexdig[((g_frame>>3)&0x0F)]; putat(25,1,buf);
    buf[0]=hexdig[(g_frame&0x0F)]; putat(26,1,buf);
}

int main(void){
    unsigned int keys; unsigned char hx[2];
    signed int px=40, py=80;             /* jogador (pixels) */
    unsigned char hp=3, over=0;
    /* 5 inimigos (sprite 8x8) caindo de cima */
    signed int ex[5]={60,100,150,190,225}, ey[5]={-20,-60,-100,-140,-180};
    signed char evy[5]={2,2,3,2,3};
    signed char spr_p, spr_e[5];
    register unsigned char i;
    unsigned char scrollx=0;
    unsigned char hitstop=0;             /* frames de congelamento ao colidir */
    unsigned char shake=0;               /* frames de screen shake */
    signed char shake_dir=1;
    unsigned char invuln=0;              /* frames de invulnerabilidade pos-hit (flash) */
    signed int bx2=-32, by2=0;           /* projétil (tile 131) */
    signed char bvx=5, spr_b=0;
    unsigned char sfx_shot=0;            /* timer do som de tiro */

    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
    SMS_loadBGPalette(palette_bg);
    SMS_loadSpritePalette(palette_bg);
    SMS_autoSetUpTextRenderer();
    SMS_loadTiles(hero_tiles, 128, HERO_TILES_SIZE);   /* tiles 128..131 */
    /* tile de estrelas (132): padrao pontilhado p/ o campo de fundo */
    SMS_loadTiles(star_tile, 132, 16);
    SMS_setBackdropColor(9);
    /* preenche name table com estrelas (tile 132) em posicoes pseudo-aleatorias */
    for(register unsigned char row=4;row<25;row++)
        for(register unsigned char col=4;col<28;col++)
            SMS_setTileatXY(col,row, ((row*12+col*7)&3)==0 ? 132 : 0);
    SMS_displayOn();

    SMS_initSprites();
    spr_p = SMS_addSprite(px, py, 128);
    for(i=0;i<5;i++) spr_e[i] = SMS_addSprite(ex[i], ey[i], 129+(i&1));
    spr_b = SMS_addSprite(bx2, by2, 131);    /* projétil (tile 131) inicialmente fora */

    PSGPlay(music_battle);              /* musica de acao em loop */

    draw_hud();
    for(;;){
        keys=SMS_getKeysStatus();
        SMS_waitForVBlank();
        PSGFrame();

        if(!over){
            if(hitstop){
                /* HITSTOP: congela a acao brevemente para game feel (feeble melodia continua) */
                hitstop--;
                if(hitstop==0){ shake=4; shake_dir=1; }
            } else {
                /* input jogador */
                if(keys & PORT_A_KEY_LEFT)  { if(px>8)  px-=8; }
                else if(keys & PORT_A_KEY_RIGHT){ if(px<240)px+=8; }
                else if(keys & PORT_A_KEY_UP) { if(py>8)py-=8; }
                else if(keys & PORT_A_KEY_DOWN){ if(py<184)py+=8; }
                /* Tiro (botao 2): dispara projétil para a direita c/ som */
                if((keys & PORT_A_KEY_2) && bx2<-10){ bx2=px+8; by2=py+4; sfx_shot=4; }

                /* projétil avança (somente um ativo) */
                if(bx2>=-10){ bx2+=bvx; if(bx2>256){ bx2=-32; } }

                /* inimigos caem; velocidade cresce com o tempo (dificuldade) */
                for(i=0;i<5;i++){
                    ey[i] += evy[i];
                    if(i<3) evy[i] = 2 + ((g_frame>>8) & 0x3);   /* progressivo ate 5 */
                    if(ey[i] > 196){ ey[i] = -24; ex[i] = 40 + ((g_frame*17 + i*43) & 0x3F) * 3; }
                }
                if(spr_p>=0) SMS_updateSpritePosition(spr_p, px, py);
                for(i=0;i<5;i++) if(spr_e[i]>=0) SMS_updateSpritePosition(spr_e[i], ex[i], ey[i]);
                if(spr_b>=0) SMS_updateSpritePosition(spr_b, bx2, by2);

                /* colisao jogador-inimigo (8x8) — só se nao invulneravel */
                if(invuln==0){
                    for(i=0;i<5;i++){
                        if((px<ex[i]+8 && px+8>ex[i]) && (py<ey[i]+8 && py+8>ey[i])){
                            if(hp>0){
                                hp--; psg_send(0xC0|5); hitstop=6; invuln=40;  /* invulnerabilidade pos-hit */
                                ey[i]=-24;
                                if(hp==0) over=1;
                            }
                        }
                    }
                } else {
                    invuln--;
                }
                /* colisao projétil-inimigo (destroi inimigo + pontos) */
                if(bx2>=-10){
                    for(i=0;i<5;i++){
                        if((bx2<ex[i]+8 && bx2+8>ex[i]) && (by2<ey[i]+8 && by2+8>ey[i])){
                            ex[i]=-32; ey[i]=-24;    /* inimigo destruído (respawn no topo) */
                            bx2=-32; psg_send(0x90|6);
                        }
                    }
                }
                /* som de tiro (blip curto no PSG) */
                if(sfx_shot){ sfx_shot--; psg_send(0x90|(sfx_shot&0x7)); }
                if(sfx_shot==1) psg_send(0x9F);
            }
            /* flash do jogador durante invulnerabilidade (pisca sprite) */
            if(invuln && spr_p>=0){
                SMS_hideSprite(spr_p);  if((g_frame&1)) SMS_updateSpriteImage(spr_p,128);
            } else if(spr_p>=0){
                SMS_updateSpriteImage(spr_p,128);
            }
            /* screen shake: desloca scroll por offset breve (effetemos bocal) */
            if(shake){
                scrollx = (unsigned char)(shake_dir>0 ? (g_frame&1) : 0);
                shake--; if((g_frame&1)==0) shake_dir=-shake_dir;
            }
            SMS_setBGScrollX(scrollx);
            SMS_copySpritestoSAT();
        } else {
            SMS_setBGScrollX(0);
            if((g_frame&8)==0) SMS_setBackdropColor(((g_frame>>3)&1)?1:9);
            if(keys & PORT_A_KEY_1){
                px=40; py=80; hp=3; over=0; hitstop=0; shake=0; invuln=0; bx2=-32; sfx_shot=0;
                for(i=0;i<5;i++){ ey[i]=-20-i*40; ex[i]=60+i*40; evy[i]=2+(i&1); }
                SMS_setBackdropColor(9);
            }
        }

        g_frame++;
        probe_hp=hp; probe_score=(unsigned char)(g_frame>>3); probe_over=over;
        draw_hud();
        if(over) putat(8,3,(unsigned char*)"GAME OVER! 1:REINICIA");
    }
}
