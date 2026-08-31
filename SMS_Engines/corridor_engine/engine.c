/* engine.c — implementação da CorridorEngine (ver engine.h).
 * Portada da cena04 do laboratorio_01; base p/ prototipos SMS.
 */
#include "engine.h"
#include "PSGlib.h"

/* assets internos (tiles) */
static const unsigned char star_tile[16] = {
    0x08,0x00, 0x20,0x00, 0x02,0x00, 0x80,0x00,
    0x10,0x00, 0x40,0x00, 0x00,0x00, 0x01,0x00
};
/* paleta mestra SMSForge (idx0 transp, 1 branco, 2 ambar, 9 azul) */
static const unsigned char eng_pal[16] = {
    0x00, 0x3F, 0x28, 0x15, 0x08, 0x36, 0x29, 0x1C,
    0x0B, 0x11, 0x30, 0x24, 0x18, 0x0C, 0x06, 0x02
};

static const char hexdig[] = "0123456789ABCDEF";

unsigned char engine_over = 0;
static unsigned int g_frame = 0;

/* estado do jogador */
static signed int px=40, py=80;
static unsigned char invuln=0, hitstop=0, shake=0;
static signed char shake_dir=1;

/* inimigos */
static signed int ex[ENG_MAX_ENEMIES], ey[ENG_MAX_ENEMIES];
static signed char evy[ENG_MAX_ENEMIES];
static signed char spr_e[ENG_MAX_ENEMIES];

/* projetil */
static signed int bx2=-32, by2=0;
static signed char bvx=5, spr_b=0;
static unsigned char sfx_shot=0;

/* sprites (jogador + inimigos + projetil) */
static signed char spr_p=0;

/* PSG direto */
__sfr __at(0x7F) PSGPort;
static void psg_send(unsigned char b){ PSGPort = b; }

#define putat(x,y,s)  SMS_printatXY((x),(y),(const unsigned char *)(s))

/* ---- setup ---- */
void engine_init(void){
    register unsigned char row, col;
    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_NORMAL);            /* 8x8 (L006) */
    SMS_loadBGPalette(eng_pal);
    SMS_loadSpritePalette(eng_pal);
    SMS_autoSetUpTextRenderer();
    SMS_loadTiles(star_tile, 132, 16);
    SMS_setBackdropColor(9);
    /* campo de estrelas */
    for(row=4;row<25;row++)
        for(col=4;col<28;col++)
            SMS_setTileatXY(col,row, ((row*12+col*7)&3)==0 ? 132 : 0);
    SMS_displayOn();
    SMS_initSprites();
}

void engine_set_music(const unsigned char *song){
    if(song) PSGPlay((void*)song);
    else     PSGStop();
}

/* ---- sprites ---- */
signed char engine_sprite_add(unsigned char x, unsigned char y, unsigned char tile){
    return SMS_addSprite(x,y,tile);
}
void engine_sprite_set(signed char spr, unsigned char x, unsigned char y, unsigned char tile){
    if(spr>=0){ SMS_updateSpritePosition(spr,x,y); SMS_updateSpriteImage(spr,tile); }
}
void engine_sprite_hide(signed char spr){ if(spr>=0) SMS_hideSprite(spr); }
void engine_sprites_flush(void){ SMS_copySpritestoSAT(); }

/* ---- jogador ---- */
void engine_player_reset(unsigned char x, unsigned char y){
    px=x; py=y; invuln=0; hitstop=0; shake=0;
    if(spr_p>=0) SMS_updateSpritePosition(spr_p,px,py);
}
void engine_player_update(unsigned int keys, unsigned char *hp, unsigned char *over){
    if(keys & PORT_A_KEY_LEFT)  { if(px>8)  px-=8; }
    else if(keys & PORT_A_KEY_RIGHT){ if(px<240)px+=8; }
    else if(keys & PORT_A_KEY_UP) { if(py>8)py-=8; }
    else if(keys & PORT_A_KEY_DOWN){ if(py<184)py+=8; }
    if(keys & PORT_A_KEY_2) engine_bullet_fire(px+8, py+4);
    engine_bullet_update();
    if(spr_p>=0) SMS_updateSpritePosition(spr_p,px,py);

    /* colisao jogador-inimigo */
    if(invuln==0){
        register unsigned char i;
        for(i=0;i<ENG_MAX_ENEMIES;i++){
            if((px<ex[i]+8 && px+8>ex[i]) && (py<ey[i]+8 && py+8>ey[i])){
                if(*hp>0){ (*hp)--; engine_sfx_hit(); hitstop=6; invuln=40; ey[i]=-24; if(*hp==0){*over=1; engine_over=1;} }
            }
        }
    } else {
        invuln--;
    }
    /* flash durante invulnerabilidade */
    if(invuln && spr_p>=0){ SMS_hideSprite(spr_p); if(g_frame&1) SMS_updateSpriteImage(spr_p,128); }
    else if(spr_p>=0){ SMS_updateSpriteImage(spr_p,128); }
}
unsigned char engine_player_x(void){ return (unsigned char)px; }
unsigned char engine_player_y(void){ return (unsigned char)py; }

/* ---- inimigos ---- */
void engine_enemies_reset(void){
    register unsigned char i;
    for(i=0;i<ENG_MAX_ENEMIES;i++){ ey[i]=-20-i*40; ex[i]=60+i*40; evy[i]=2+(i&1); }
}
void engine_enemies_update(unsigned int frame){
    register unsigned char i;
    for(i=0;i<ENG_MAX_ENEMIES;i++){
        ey[i]+=evy[i];
        if(i<3) evy[i]=2+((frame>>8)&0x3);
        if(ey[i]>196){ ey[i]=-24; ex[i]=40+((frame*17+i*43)&0x3F)*3; }
        if(spr_e[i]>=0) SMS_updateSpritePosition(spr_e[i],ex[i],ey[i]);
    }
}

/* ---- projetil ---- */
void engine_bullet_fire(unsigned char x, unsigned char y){
    if(bx2<-10){ bx2=x; by2=y; sfx_shot=4; engine_sfx_shot(); }
}
void engine_bullet_update(void){
    register unsigned char i;
    if(bx2>=-10){ bx2+=bvx; if(bx2>256) bx2=-32; }
    if(spr_b>=0) SMS_updateSpritePosition(spr_b,bx2,by2);
    if(bx2>=-10){
        for(i=0;i<ENG_MAX_ENEMIES;i++){
            if((bx2<ex[i]+8 && bx2+8>ex[i]) && (by2<ey[i]+8 && by2+8>ey[i])){
                ex[i]=-32; ey[i]=-24; bx2=-32; engine_sfx_destroy();
            }
        }
    }
}
unsigned char engine_bullet_active(void){ return (unsigned char)(bx2>=-10); }

/* ---- SFX ---- */
void engine_sfx_hit(void){ psg_send(0xC0|5); }
void engine_sfx_shot(void){ psg_send(0x90|7); }
void engine_sfx_destroy(void){ psg_send(0x90|6); }

/* ---- frame ---- */
void engine_frame_begin(void){
    SMS_waitForVBlank();
    PSGFrame();
}
void engine_update(unsigned int keys, unsigned char *hp, unsigned char *over){
    /* enemies + jogador; hitstop congela a ação */
    if(hitstop){ hitstop--; if(hitstop==0){ shake=4; shake_dir=1; } }
    else {
        engine_enemies_update(g_frame);
        engine_player_update(keys, hp, over);
        /* som de tiro */
        if(sfx_shot){ sfx_shot--; psg_send(0x90|(sfx_shot&0x7)); if(sfx_shot==1) psg_send(0x9F); }
        g_frame++;
    }
}
void engine_render(unsigned int frame, unsigned char hp, unsigned char over){
    unsigned char buf[2];
    /* scroll/shake */
    if(shake){ SMS_setBGScrollX((shake_dir>0)?(frame&1):0); shake--; if((frame&1)==0) shake_dir=-shake_dir; }
    else      { SMS_setBGScrollX(0); }
    engine_sprites_flush();
    /* HUD */
    putat(4,1,(unsigned char*)"HP:300 SCORE:0000");
    buf[1]=0;
    buf[0]=hexdig[((frame>>7)&0x0F)]; putat(24,1,buf);
    buf[0]=hexdig[((frame>>3)&0x0F)]; putat(25,1,buf);
    buf[0]=hexdig[(frame&0x0F)]; putat(26,1,buf);
    if(over){ if((frame&8)==0) SMS_setBackdropColor(((frame>>3)&1)?1:9); putat(8,3,(unsigned char*)"GAME OVER! 1:REINICIA"); }
}
unsigned int engine_frame_count(void){ return g_frame; }
