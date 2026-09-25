/* main.c — cena 01 `probe_import` do luta_mugen.
 *
 * Proposito unico desta cena: provar no hardware que a tabela gerada pelo
 * mugen2sms (S4.5b) vira ROM que boot e mostra o pose no VDP do Master System,
 * e MEDIR a ordem do par TALL (topo, base) em vez de assumir.
 *
 * Timeline deterministica (mesma em todo boot — audit_deterministic_boot):
 *   frames 0..179  : PROBE de contrato — um sprite 8x16 com metade branca
 *                    (indice 1) e metade preta (indice 2) centrado na tela.
 *                    Captura: topo branco == pack_tiles_tall correto.
 *   frames 180..   : poses do fixture sintetico (mini) em pose estatica,
 *                    alternando a cada 30 frames: A0 idle, A200 soco f0,
 *                    A200 soco f1 (esta usa o METAL = espelho-h como OUTRO
 *                    padrao, pois o SMS nao tem flip de sprite).
 *
 * Contratos de hardware citados (sdk/devkitSMS/SMSlib/SMSlib.h):
 *   SPRITEMODE_TALL :54-57 · useFirstHalfTilesforSprites :53 (L006)
 *   SMS_addMetaSprite/METASPRITE_END :214-216 · SMS_loadTiles :130
 *   paletas por entrada :249-250. Sem float, sem malloc, sem API inventada.
 */
#include "SMSlib.h"
#include "luta.h"
#include "gen/mini_art.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "luta_mugen",
                                     "cena 01 probe_import");

/* ---- probe do par TALL ----------------------------------------------------
 * Telemetria de contrato de hardware, nao entrega visual (diretriz estetica):
 * tile A = todos pixels no indice 1 (branco), tile B = indice 2 (preto).
 * Carregado em patterns 12/13: em TALL o VDP le (par, par+1) — se a captura
 * mostrar preto em cima, a ordem topo/base do conversor esta invertida e o
 * conserto e em runtime_format.pack_tiles_tall, nunca aqui. */
static const unsigned char probe_tall[64] = {
    0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00,
    0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00,
    0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00
};
/* tile de vazio (indice 0 = transparente -> backdrop) para o resto da PNT */
static const unsigned char tile_empty[32] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

/* precedente MSSF2T fight.c:rebuild_meta — rebase de tile na copia, porque a
 * base de carga do pose so existe em runtime (streaming pagara Task 6). */
unsigned char meta_rebase(const unsigned char *meta, unsigned char base,
                          signed char *dst) {
    unsigned char n = 0;
    /* MSSF2T fight.c:1082/1089: o terminador 0x80 so casa lido ASSINADO.
     * Comparar unsigned char (128) com (signed char)METASPRITE_END (-128)
     * promove a int e nunca iguala -> loop infinito comestendo a RAM. */
    while ((signed char)meta[n] != (signed char)METASPRITE_END) {
        dst[n] = (signed char)meta[n];            /* dx (ja refletido no METAL) */
        dst[n + 1] = (signed char)meta[n + 1];    /* dy */
        dst[n + 2] = (signed char)(base + meta[n + 2]);
        n += 3;
    }
    dst[n] = (signed char)METASPRITE_END;
    return n / 3;
}

/* pool de cada pose = 64 B = 2 pares TALL (normal + espelho) */
#define POSE_BYTES  64
static const unsigned char *const pose_tiles[3] = {
    MINI_A0F0_TILES,   MINI_A200F0_TILES,   MINI_A200F1_TILES
};
static const unsigned char *const pose_meta[3] = {
    MINI_A0F0_META,    MINI_A200F0_META,    MINI_A200F1_META
};
static const unsigned char *const pose_metal[3] = {
    MINI_A0F0_METAL,   MINI_A200F0_METAL,   MINI_A200F1_METAL
};
static const unsigned char *const pose_pal[3] = {
    MINI_A0F0_PAL,     MINI_A200F0_PAL,     MINI_A200F1_PAL
};

static signed char meta_ram[2][16];     /* 5 entradas + fim = 16 B */
static unsigned int g_frame;

static void load_pose_pal(unsigned char i) {
    unsigned char k;
    for (k = 0; k < 16; k++)
        SMS_setSpritePaletteColor(k, pose_pal[i][k]);
}

void main(void) {
    unsigned char x, y;

    SMS_displayOff();
    /* L006/SMSlib.h:53 — sprites leem a 1a metade; sem isto vira ruido. */
    SMS_useFirstHalfTilesforSprites(1);
    SMS_setSpriteMode(SPRITEMODE_TALL);

    /* VRAM patterns: poses nos tiles 0,4,8; probe em 12; vazio em 14. */
    for (y = 0; y < 3; y++)
        SMS_loadTiles(pose_tiles[y], (unsigned int)y * 4, POSE_BYTES);
    SMS_loadTiles(probe_tall, 12, sizeof(probe_tall));
    SMS_loadTiles(tile_empty, 14, sizeof(tile_empty));

    /* BG: 0 = backdrop preto, 1 = cinza do rodape (codigo 6-bit canais 0-3).
     * Chao na linha 16 (y=128) para manter a cena dentro da metade central
     * que o capture_evidence amostra (viewport box = canvas x64..191, y29..137). */
    SMS_setBGPaletteColor(0, 0x00);
    SMS_setBGPaletteColor(1, 0x15);
    for (y = 0; y < 16; y++)
        for (x = 0; x < 32; x++)
            SMS_setTileatXY(x, y, 14);
    for (y = 16; y < 24; y++)
        for (x = 0; x < 32; x++)
            SMS_setTileatXY(x, y, 12);

    /* fase probe: cores fixas 1=branco, 2=preto na sprite palette */
    SMS_setSpritePaletteColor(1, 0x3F);
    SMS_setSpritePaletteColor(2, 0x00);

    g_frame = 0;
    SMS_displayOn();

    for (;;) {
        SMS_waitForVBlank();
        SMS_initSprites();

        if (g_frame < 180) {
            /* probe: 1 entrada TALL explicita — origem = topo do par */
            SMS_addSprite(120, 96, 12);
        } else {
            unsigned char pose = (unsigned char)((g_frame / 30) % 3);
            unsigned char base = (unsigned char)(pose * 4);
            if ((g_frame % 30) == 0)
                load_pose_pal(pose);
            /* origem dy do gerador = topo da pose (convencao MSSF2T);
             * pes no chao y=128 => topo em 128 - 16 (pose do fixture 16 px). */
            meta_rebase(pose_meta[pose], base, meta_ram[0]);
            meta_rebase(pose_metal[pose], base, meta_ram[1]);
            SMS_addMetaSprite(96, 112, meta_ram[0]);
            SMS_addMetaSprite(152, 112, meta_ram[1]);
        }

        SMS_copySpritestoSAT();
        g_frame++;
    }
}
