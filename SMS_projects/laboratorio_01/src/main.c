/* main.c — laboratorio_01 :: cena 04 "corredor estelar" (combina tudo)
 *
 * Combina: sprites (L006 resolvido), musica PSG rica (PSGlib battle), scroll
 * BG horizontal, sistema de pontos/HP, game over. Prova o pipeline completo.
 *
 * Jogador = METASPRITE 16x16 (tiles 128..131, quadrantes TL/TR/BL/BR) movido
 * por d-pad (8px). Inimigos = sprites 8x8 (tile 132) caindo; projetil = tile 133.
 * Scroll = deslocamento do name table (BG).
 * Pontua por tempo sobrevivido; HP 3; game over ao chegar a 0; START reinicia.
 *
 * 2026-08-31 — promocao a metasprite 16x16 (§25/L006). Antes: jogador era um
 * unico tile 8x8 e os inimigos/projetil desenhavam os OUTROS quadrantes da arte
 * do heroi (tiles 129..131), porque a arte 16x16 nunca chegou inteira a VRAM.
 * Raiz profunda corrigida em png_to_sms_tiles.py (emitia 2 planos/16B por tile
 * onde SMS_loadTiles espera 4bpp/32B — SMSlib.h:130).
 *
 * Declaracao de sprites e POR FRAME (SMS_initSprites -> adds -> copySpritestoSAT):
 * SMS_addMetaSprite_f nao devolve handle, entao nao ha SMS_updateSpritePosition.
 */
#include "SMSlib.h"
#include "PSGlib.h"
#include "hero_tiles.h"
#include "enemy_tiles.h"
#include "shot_tiles.h"
#include "music_battle.h"

/* Metasprite do jogador: triplas (delta_x, delta_y, tile) + METASPRITE_END.
 * Formato conforme devkitSMS/SMSlib/src/SMSlib_metasprite.c (autoridade). */
#define TILE_HERO   128            /* 128..131 = TL,TR,BL,BR (4 tiles) */
#define TILE_ENEMY  132
#define TILE_SHOT   133
#define TILE_STAR   134
#define HERO_W      16
#define HERO_H      16

static const signed char hero_meta[] = {
    0, 0, TILE_HERO,       /* TL */
    8, 0, TILE_HERO + 1,   /* TR */
    0, 8, TILE_HERO + 2,   /* BL */
    8, 8, TILE_HERO + 3,   /* BR */
    METASPRITE_END
};

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(1, 0, "SMSForge", "laboratorio_01",
                                     "cena 04 corredor estelar");

const unsigned char palette_bg[16] = {
    0x00, 0x3F, 0x28, 0x15, 0x08, 0x36, 0x29, 0x1C,
    0x0B, 0x11, 0x30, 0x24, 0x18, 0x0C, 0x06, 0x02
};
static const char hexdig[] = "0123456789ABCDEF";
/* Tile de estrela (padrao pontilhado) para o campo de fundo.
 * 4bpp: 4 bytes por linha (plano0..plano3) => 32 bytes. Estava em 16 bytes
 * (meio tile) pelo mesmo bug do conversor; so o plano0 acende (cor 1). */
static const unsigned char star_tile[32] = {
    0x08,0x00,0x00,0x00,  0x20,0x00,0x00,0x00,
    0x02,0x00,0x00,0x00,  0x80,0x00,0x00,0x00,
    0x10,0x00,0x00,0x00,  0x40,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,  0x01,0x00,0x00,0x00
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
    register unsigned char i;
    unsigned char scrollx=0;
    unsigned char hitstop=0;             /* frames de congelamento ao colidir */
    unsigned char shake=0;               /* frames de screen shake */
    signed char shake_dir=1;
    unsigned char invuln=0;              /* frames de invulnerabilidade pos-hit (flash) */
    signed int bx2=-32, by2=0;           /* projetil (TILE_SHOT) */
    signed char bvx=5;
    unsigned char sfx_shot=0;            /* timer do som de tiro */

    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
    SMS_loadBGPalette(palette_bg);
    SMS_loadSpritePalette(palette_bg);
    SMS_autoSetUpTextRenderer();
    SMS_loadTiles(hero_tiles, TILE_HERO, HERO_TILES_SIZE);    /* 128..131 (128B) */
    SMS_loadTiles(enemy_tiles, TILE_ENEMY, ENEMY_TILES_SIZE); /* 132 (32B) */
    SMS_loadTiles(shot_tiles, TILE_SHOT, SHOT_TILES_SIZE);    /* 133 (32B) */
    SMS_loadTiles(star_tile, TILE_STAR, 32);                  /* 134 (32B) */
    SMS_setBackdropColor(9);
    /* preenche name table com estrelas (TILE_STAR) em posicoes pseudo-aleatorias */
    for(register unsigned char row=4;row<25;row++)
        for(register unsigned char col=4;col<28;col++)
            SMS_setTileatXY(col,row, ((row*12+col*7)&3)==0 ? TILE_STAR : 0);
    SMS_displayOn();

    /* Sprites sao declarados POR FRAME (ver bloco de desenho no loop):
     * SMS_addMetaSprite_f nao devolve handle, logo nao ha update por handle. */

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
                else if(keys & PORT_A_KEY_RIGHT){ if(px<256-HERO_W-8)px+=8; }
                else if(keys & PORT_A_KEY_UP) { if(py>8)py-=8; }
                else if(keys & PORT_A_KEY_DOWN){ if(py<192-HERO_H-8)py+=8; }
                /* Tiro (botao 2): dispara projétil para a direita c/ som */
                if((keys & PORT_A_KEY_2) && bx2<-10){ bx2=px+HERO_W; by2=py+(HERO_H/2)-4; sfx_shot=4; }

                /* projétil avança (somente um ativo) */
                if(bx2>=-10){ bx2+=bvx; if(bx2>256){ bx2=-32; } }

                /* inimigos caem; velocidade cresce com o tempo (dificuldade) */
                for(i=0;i<5;i++){
                    ey[i] += evy[i];
                    if(i<3) evy[i] = 2 + ((g_frame>>8) & 0x3);   /* progressivo ate 5 */
                    if(ey[i] > 196){ ey[i] = -24; ex[i] = 40 + ((g_frame*17 + i*43) & 0x3F) * 3; }
                }

                /* colisao jogador(16x16) x inimigo(8x8) — so se nao invulneravel */
                if(invuln==0){
                    for(i=0;i<5;i++){
                        if((px<ex[i]+8 && px+HERO_W>ex[i]) && (py<ey[i]+8 && py+HERO_H>ey[i])){
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
            /* DESENHO (declaracao por frame, front-to-back).
             * Orcamento SAT: 4 (metasprite do jogador) + 5 inimigos + 1 projetil
             * = 10 de 64. Pico por scanline: 2 (jogador e 2 tiles de largura)
             * + inimigos alinhados + projetil — limite de 8 vale sempre. */
            SMS_initSprites();
            /* flash de invulnerabilidade: omite o jogador em frames alternados */
            if(!invuln || (g_frame & 1))
                SMS_addMetaSprite(px, py, (void *)hero_meta);
            for(i=0;i<5;i++)
                if(ey[i] > -16) SMS_addSprite(ex[i], ey[i], TILE_ENEMY);
            if(bx2 >= -10) SMS_addSprite(bx2, by2, TILE_SHOT);
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
