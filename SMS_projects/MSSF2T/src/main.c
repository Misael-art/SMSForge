/* MSSF2T — Master Street Fighter 2 Turbo
 * Engine HAMOOPIG-like (FSM numerica, hitboxes, rounds) no VDP do SMS.
 * Autoridade API: SMSlib.h / PSGlib.h.
 */
#include "SMSlib.h"
#include "fight.h"

SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "MSSF2T",
                                "Master Street Fighter 2 Turbo");

/* Canal de runtime L035: header SMRT + schema 1, sempre volatile. */
volatile unsigned char __at(0xC7E0) probe_magic0;
volatile unsigned char __at(0xC7E1) probe_magic1;
volatile unsigned char __at(0xC7E2) probe_magic2;
volatile unsigned char __at(0xC7E3) probe_magic3;
volatile unsigned char __at(0xC7E4) probe_schema;
volatile unsigned int  __at(0xC7F0) probe_frame;
volatile unsigned char __at(0xC7F2) probe_hp;
volatile unsigned char __at(0xC7F3) probe_score;
volatile unsigned char __at(0xC7F4) probe_boss;
volatile unsigned char __at(0xC7F5) probe_over;
volatile unsigned char __at(0xC7F6) probe_state;
volatile unsigned char __at(0xC7F7) probe_wave;
volatile unsigned char __at(0xC7F8) probe_keys;
/* 0xC7F9 estava livre no mapa do probe. Expor a POSE do jogador 1 e o que
 * permite provar agachar/pular por memoria: por pixel a janela e curta
 * (~20 frames) e a contagem de frames do capture_evidence nao e exata, entao
 * fotografar a pose certa vira sorteio. Aditivo: o schema v1 le enderecos
 * fixos e nao inclui este. */
volatile unsigned char __at(0xC7F9) probe_pose;
volatile unsigned char __at(0xC7FA) probe_px;
volatile unsigned char __at(0xC7FB) probe_py;
/* x do oponente: sem ele nao da para saber se o pulo ULTRAPASSOU (a troca de
 * lado depende da posicao relativa, nao da absoluta). */
volatile unsigned char __at(0xC7FC) probe_p2x;

void main(void) {
    unsigned int ka;

    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_displayOff();
    SMS_useFirstHalfTilesforSprites(1);
    /* Trava o H-scroll das duas primeiras linhas: o parallax move o ceu, e
     * sem isto o placar (nomes, barras, timer) andaria junto com as nuvens.
     *
     * LEFTCOLBLANK apaga os 8 px da esquerda. Nao e enfeite: com H-scroll
     * ligado o VDP mostra lixo nessa coluna (o tile que esta entrando ainda
     * nao foi buscado), e na captura do KO aparecia um talho vertical com
     * pedaco das barras de vida e um bloco cinza cortando ceu, mar e deck.
     * STAGE_X_MIN e 8, entao nem o lutador encurralado entra na faixa. */
    SMS_VDPturnOnFeature(VDPFEATURE_LOCKHSCROLL | VDPFEATURE_LEFTCOLBLANK);
    fight_init();
    SMS_setLineInterruptHandler(&stage_raster);
    SMS_enableLineInterrupt();
    SMS_displayOn();
    fight_go_live();

    probe_magic0 = 'S'; probe_magic1 = 'M';
    probe_magic2 = 'R'; probe_magic3 = 'T';
    probe_schema = 1;

    for (;;) {
        /* Uma leitura cobre os dois portes: PORT_B_KEY_* sao os bits altos.
         * Passar 0 para o jogador 2 tornava o modo 2P impossivel. */
        ka = SMS_getKeysStatus();
        fight_update(ka);        /* logica FORA do VBlank; VRAM so depois */
        fight_prepare_stream();  /* espelha para a RAM tambem fora do VBlank */
        SMS_waitForVBlank();
        g_frame++;
        stage_scroll_frame();   /* arma o parallax antes de gastar o VBlank */
        fight_stream();
        hud_draw();
        hud_banner();
        fight_draw();

        probe_frame = g_frame;
        probe_hp = P[0].hp;
        probe_score = P[0].rounds;
        probe_boss = P[1].hp;
        probe_over = (unsigned char)(g_gs == GS_RESULT);
        probe_state = (unsigned char)g_gs;
        probe_wave = g_timer;
        probe_keys = (unsigned char)ka;
        /* pose em 0..7 deixa o bit 7 livre: leva o facing de carona, para o
         * gate poder provar a troca de lado sem gastar outro byte do probe. */
        probe_pose = (unsigned char)(P[0].pose | (P[0].facing ? 0x80 : 0));
        probe_px = (unsigned char)P[0].x;
        probe_py = (unsigned char)P[0].y;
        probe_p2x = (unsigned char)P[1].x;
    }
}
