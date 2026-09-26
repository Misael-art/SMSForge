/* main.c — arena sintetica do motor FSM (Plano 2, Tasks 4-5).
 *
 * A cena 01 (probe_import) mediu as leis de hardware e saiu de cena: aqui o
 * loop e 100% interpretado por fight.c. P1 comeca em ATRACAO (roteiro
 * deterministico — gate audit_deterministic_boot); a PRIMEIRA tecla fisica do
 * pad mata a atracao e o controle passa a ser do jogador (precedente MSSF2T
 * "qualquer tecla mata g_attract"). P2 permanece no roteiro — dummy da cena
 * 02 e Task 7. Animacao avanca sem qualquer tecla fisica.
 *
 * Probe de memoria (L035, mapa SMRT dos projetos-irmaos): o ESTADO mora em
 * 0xC7E0.. e o DAP do Emulicious le com a emulacao pausada — a prova de
 * input vivo (Task 5) nao depende de pixels nem de foco de janela.
 *
 * Telemetria (nao entrega visual — diretriz estetica): tres celulas de HUD
 * na linha 0 mostram nibbles de dbg_frame no contrato do
 * measure_frame_advance/hud.c:80-86 da arena_nocturna:
 *   (29,0) = bit 7 (troca a cada 128 frames — dbg e u8, o g_frame de 16 bits
 *            da arena usava >>7&0xF; aqui o nibble degenera em 0/1, o
 *            periodo medido e identico)
 *   (30,0) = dbg_frame>>3&0xF (periodo   8)
 *   (31,0) = dbg_frame&0xF    (periodo   1)
 * Glifos = quadrantes 2x2 ligados por bit do nibble (telemetria pura).
 *
 * Contratos citados (sdk/devkitSMS/SMSlib/SMSlib.h): SMS_addMetaSprite :215,
 * SMS_loadTiles :130, SMS_setTileatXY :117, useFirstHalfTiles :53 (L006),
 * SMS_getKeysHeld :290, PORT_A_KEY_* :298-303.
 */
#include "SMSlib.h"
#include "fight.h"
#include "input.h"

/* mini_art.h define (nao extern) os blobs so-rom: fight.c e o unico TU que
 * o inclui; daqui só os dois padroes de comando, por referencia. */
extern const unsigned char MINI_CMD_PUNCH[5];
extern const unsigned char MINI_CMD_HOLDF[5];

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "luta_mugen",
                                     "T5 arena FSM + pad vivo");

/* ---- tiles de fundo e HUD (2a metade: poses ocupam 0..21) ---- */
static const unsigned char tile_empty[32] = { 0 };
static const unsigned char tile_floor[32] = {
    0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF,
    0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF,
    0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF
};
/* quadrantes: TL=bit3 TR=bit2 BL=bit1 BR=bit0 -> 16 glifos distintos */
static const unsigned char hex_glyphs[512] = {
    /* 0 */ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    /* 1 */ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00,
    /* 2 */ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00,
    /* 3 */ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    /* 4 */ 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    /* 5 */ 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00,
    /* 6 */ 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00,
    /* 7 */ 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    /* 8 */ 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    /* 9 */ 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00,
    /* A */ 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00,
    /* B */ 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    /* C */ 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    /* D */ 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00,
    /* E */ 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00,
    /* F */ 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00
};

#define T_EMPTY 127
#define T_FLOOR 126               /* pal 2; p1|p3 = indice 10 -> cor 2 (CRAM 10) */
#define T_HEX   128               /* 128..143 = glifos 0..F */

/* ---- probe SMRT (mapa SNAP_ADDRS de measure_runtime_probe.py; L035) ----
 * __at() SEMPRE volatile (L009), senao o SDCC apaga a escrita. py = ALTITUDE
 * (0 = chao), nao y de tela — difere do convenio MSSF2T (chao=112). */
volatile unsigned char  __at(0xC7E0) probe_magic0;
volatile unsigned char  __at(0xC7E1) probe_magic1;
volatile unsigned char  __at(0xC7E2) probe_magic2;
volatile unsigned char  __at(0xC7E3) probe_magic3;
volatile unsigned char  __at(0xC7E4) probe_schema;
volatile unsigned int   __at(0xC7F0) probe_frame;    /* 16 bits: fps real */
volatile unsigned char  __at(0xC7F2) probe_hp;       /* vida P1 (byte) */
volatile unsigned char  __at(0xC7F3) probe_score;    /* hits conectados P1 */
volatile unsigned char  __at(0xC7F4) probe_boss;     /* vida P2 (byte) */
volatile unsigned char  __at(0xC7F5) probe_over;     /* alguem zerou a vida */
volatile unsigned char  __at(0xC7F6) probe_state;    /* estado P1 (ST_*) */
volatile unsigned char  __at(0xC7F7) probe_wave;     /* 1 = atracao ativa */
volatile unsigned char  __at(0xC7F8) probe_keys;     /* Port A crua (byte baixo) */
volatile unsigned char  __at(0xC7F9) probe_pose;     /* anim P1 (indice) */
volatile unsigned char  __at(0xC7FA) probe_px;       /* P1.x >> 8 */
volatile unsigned char  __at(0xC7FB) probe_py;       /* P1.y >> 8 = altura */
volatile unsigned char  __at(0xC7FC) probe_p2x;      /* P2.x >> 8 */
volatile unsigned char  __at(0xC7FD) probe_pattern;  /* bit0 punch, bit1 holdF */

static unsigned char hits_p1;    /* golpes conectados por P1 (telemetria) */

/* ---- roteiro deterministico: {frame_em_que_muda, teclas_P1, teclas_P2} ----
 * Geometria inicial: P1 em x=96 (facing dir), P2 em x=152 (facing esq).
 * Cada segmento tambem exercita um gate do engine:
 *  - 120: walk aproxima P1 de 96 -> 144
 *  - 180: punch1 (state 200) acerta P2: dano 5, hitstop 8, knockback 16
 *  - 300: jump (vy=2560, grav=128 -> ~40 frames no ar, terra sozinho)
 *  - 420: crouch (hurtbox baixa) · 540: guard
 *  - 660: punch2 (state 201) acerta P2: dano 8
 *  - 900: P2 avanca e CRUZA P1 — auto-facing vira nos dois
 *  - 1020: punch2 do P2 acerta P1
 *  - 1200: punch2 do P2 contra P1 em guard -> sem dano, push 8 */
typedef struct { unsigned int t; unsigned char k1, k2; } ScriptRow;
static const ScriptRow script[] = {
    {   0, 0, 0 },
    { 120, K_RIGHT, 0 },
    { 144, 0, 0 },
    { 180, K_LP, 0 },
    { 196, 0, 0 },
    { 300, K_UP, 0 },
    { 316, 0, 0 },
    { 420, K_DOWN, 0 },
    { 480, 0, 0 },
    { 540, K_GUARD, 0 },
    { 600, 0, 0 },
    { 630, K_RIGHT, 0 },
    { 646, 0, 0 },                    /* P1 em ~160 */
    { 660, K_HP, 0 },
    { 684, 0, 0 },
    { 780, K_LEFT, 0 },
    { 816, 0, 0 },                    /* P1 recua p/ ~136 */
    { 900, 0, K_LEFT },
    { 930, 0, 0 },                    /* P2 cruza: fica em ~124 */
    {1020, 0, K_HP },
    {1044, 0, 0 },
    {1100, K_GUARD, 0 },
    {1200, K_GUARD, K_HP },           /* bloqueio: P1 segura guard */
    {1220, K_GUARD, 0 },
    {1320, 0, 0 },
};

static unsigned char script_keys(unsigned int t, unsigned char who) {
    unsigned char i, k = 0;
    for (i = 0; i < sizeof(script) / sizeof(script[0]); i++)
        if (t >= script[i].t) k = who ? script[i].k2 : script[i].k1;
    return k;
}

void main(void) {
    unsigned char x, y;
    unsigned char pad, k1, k2;
    unsigned char attract = 1;
    unsigned int t = 0;
    unsigned int life2_prev = 250;

    SMS_displayOff();
    /* L006/SMSlib.h:53 — sprites leem a 1a metade (poses em 0..21). */
    SMS_useFirstHalfTilesforSprites(1);
    SMS_setSpriteMode(SPRITEMODE_TALL);

    fight_init();
    input_init();
    SMS_loadTiles(tile_empty, T_EMPTY, sizeof(tile_empty));
    SMS_loadTiles(tile_floor, T_FLOOR, sizeof(tile_floor));
    SMS_loadTiles(hex_glyphs, T_HEX, sizeof(hex_glyphs));

    /* CRAM de BG e entry = palette*4 + (indice_do_pixel & 3) (0..15), NAO o
     * numero da palette. Tile SMS = 4 bytes por linha, um por plano: chao
     * (0x00,0xFF,0x00,0xFF) -> p1|p3 = indice 10 -> cor 2; tile 126 -> pal 2
     * => entry 10. Glifos: pixel indice 1, tile 128+g -> pal g&3 => entries
     * 1,5,9,13. Errar a entry deixa a real nao-inicializada: o chao saiu
     * cinza/oliva/rosa/ciano conforme o humor do emulador entre runs — cor
     * fora da paleta mestra em dois deles (semantic gate reprovaria). */
    SMS_setBGPaletteColor(0, 0x00);    /* backdrop */
    SMS_setBGPaletteColor(1, 0x3F);
    SMS_setBGPaletteColor(5, 0x3F);
    SMS_setBGPaletteColor(9, 0x3F);
    SMS_setBGPaletteColor(13, 0x3F);   /* branco do glifo nas 4 palettes */
    SMS_setBGPaletteColor(10, 0x15);   /* cinza do chao (pal 2, cor 2) */
    for (y = 0; y < 16; y++)
        for (x = 0; x < 32; x++)
            SMS_setTileatXY(x, y, T_EMPTY);
    for (y = 16; y < 24; y++)         /* chao em y=128 — cena no viewport */
        for (x = 0; x < 32; x++)
            SMS_setTileatXY(x, y, T_FLOOR);

    fight_reset(&fighters[0], 0);
    fight_reset(&fighters[1], 1);
    dbg_frame = 0;
    probe_magic0 = 'S';
    probe_magic1 = 'M';
    probe_magic2 = 'R';
    probe_magic3 = 'T';
    probe_schema = 1;
    probe_pattern = 0;
    hits_p1 = 0;
    SMS_displayOn();

    for (;;) {
        SMS_waitForVBlank();
        SMS_initSprites();

        /* qualquer tecla fisica mata a atracao (precedente MSSF2T); P2 fica
         * no roteiro — e o dummy ate a cena 02 (Task 7). */
        pad = input_read();
        if (pad) attract = 0;
        k1 = attract ? script_keys(t, 0) : pad;
        k2 = script_keys(t, 1);

        input_tick(k1, fighters[0].facing);
        if (input_pattern_hit(MINI_CMD_PUNCH))  probe_pattern |= 0x01;
        if (input_pattern_hit(MINI_CMD_HOLDF))  probe_pattern |= 0x02;

        fight_step(&fighters[0], k1, k2);
        fight_step(&fighters[1], k2, k1);
        fight_draw();

        if (fighters[1].life < life2_prev) hits_p1++;
        life2_prev = fighters[1].life;
        probe_frame = t;
        probe_hp = (unsigned char)fighters[0].life;
        probe_score = hits_p1;
        probe_boss = (unsigned char)fighters[1].life;
        probe_over = (unsigned char)(!fighters[0].life || !fighters[1].life);
        probe_state = fighters[0].state;
        probe_wave = attract;
        probe_keys = (unsigned char)SMS_getKeysHeld();
        probe_pose = fighters[0].anim;
        probe_px = (unsigned char)(fighters[0].x >> 8);
        probe_py = (unsigned char)(fighters[0].y >> 8);
        probe_p2x = (unsigned char)(fighters[1].x >> 8);

        /* HUD de taxa: contrato measure_frame_advance (celulas 29..31,
         * linha 0; periodo 128 / 8 / 1). */
        SMS_setTileatXY(29, 0, (unsigned char)(T_HEX + ((dbg_frame >> 7) & 0xF)));
        SMS_setTileatXY(30, 0, (unsigned char)(T_HEX + ((dbg_frame >> 3) & 0xF)));
        SMS_setTileatXY(31, 0, (unsigned char)(T_HEX + (dbg_frame & 0xF)));

        SMS_copySpritestoSAT();
        dbg_frame++;
        t++;
    }
}
