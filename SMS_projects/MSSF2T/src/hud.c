#include "fight.h"
#include "fight_gfx.h"
#include "font_tiles.h"

/* Fonte 8x8 em BG. O GDD pedia "HUD em tiles: nomes, barras, timer, rounds"
 * e so as barras existiam — nao havia glifo nenhum na ROM. */

static const char charset[] = FONT_CHARSET;

static unsigned int glyph(char c) {
    unsigned char i;
    for (i = 0; i < FONT_TILES_COUNT; i++)
        if (charset[i] == c)
            return (unsigned int)(TILE_FONT + i);
    return (unsigned int)(TILE_FONT + FONT_TILES_COUNT - 1);  /* espaco */
}

void text_init(void) {
    SMS_loadTiles(font_tiles, TILE_FONT, FONT_TILES_SIZE);
}

/* Trava o endereco UMA vez e usa o auto-incremento do VDP, em vez de um
 * SMS_setAddr por caractere. Os tiles sao unsigned int, nao byte: o palco
 * mora em 256+ e o bit 8 do indice vai no byte de flags do name table. */
static void put_run(unsigned char col, unsigned char row,
                    const unsigned int *tiles, unsigned char n) {
    unsigned char i;
    if (col >= 32) return;
    if ((unsigned char)(col + n) > 32) n = (unsigned char)(32 - col);
    SMS_setNextTileatXY(col, row);
    for (i = 0; i < n; i++)
        SMS_setTile(tiles[i]);
}

void text_at(unsigned char col, unsigned char row, const char *s) {
    unsigned int buf[32];
    unsigned char n = 0;
    while (s[n] && n < 32) {
        buf[n] = glyph(s[n]);
        n++;
    }
    put_run(col, row, buf, n);
}

/* Apagar = devolver o tile do palco. O texto vive por cima do cenario, entao
 * limpar com tile 0 deixava um retangulo preto no lugar do ceu. */
void text_clear(unsigned char col, unsigned char row, unsigned char n) {
    unsigned int buf[32];
    unsigned char i;
    if (n > 32) n = 32;
    for (i = 0; i < n && (unsigned char)(col + i) < 32; i++)
        buf[i] = (unsigned int)(TILE_STAGE + stage_ken_map[row][col + i]);
    put_run(col, row, buf, i);
}

void text_num(unsigned char col, unsigned char row, unsigned char v,
              unsigned char digits) {
    unsigned char buf[4];
    unsigned char i = digits;
    if (digits > 3) digits = 3, i = 3;
    while (i--) {
        buf[i] = (unsigned char)('0' + (v % 10));
        v /= 10;
    }
    buf[digits] = 0;
    text_at(col, row, (const char *)buf);
}

#define TILE_BAR_FULL  (TILE_FONT + BAR_FULL_OFFSET)
#define TILE_BAR_EMPTY (TILE_FONT + BAR_EMPTY_OFFSET)

/* A barra do 1P esvazia da direita para a esquerda (em direcao ao centro),
 * a do 2P da esquerda para a direita — como no arcade. */
static void bar(unsigned char col, unsigned char hp, unsigned char mirror) {
    unsigned int buf[8];
    unsigned char i, k, n = (unsigned char)((hp + 7) >> 3);
    if (n > 8) n = 8;
    for (i = 0; i < 8; i++) {
        k = mirror ? (unsigned char)(7 - i) : i;
        buf[k] = (unsigned int)(i < n ? TILE_BAR_FULL : TILE_BAR_EMPTY);
    }
    put_run(col, 1, buf, 8);
}

/* Nomes e barras nao mudam de lugar: escritos uma vez, em fight_init.
 *
 * O palco antigo trazia um alfabeto embutido (tiles 1..7 = K,E,N,G,U,I,L) e
 * ja desenhava "KEN"/"GUILE" pelo mapa — escrever a fonte ao lado produzia
 * "KKEN"/"GGUILE". O cais autoral novo deixa as duas primeiras linhas pretas
 * e os nomes sao só da fonte. */
void hud_static(void) {
    text_at(1, 0, "KEN");
    text_at(25, 0, "GUILE");
    bar(2, HP_MAX, 1);
    bar(22, HP_MAX, 0);
}

/* Os "ultimos valores" do HUD sao static: sem zerar, ao voltar do titulo o
 * placar acreditava que ja estava desenhado e ficava em branco. */
static unsigned char last_hp0 = 0xFF, last_hp1 = 0xFF;
static unsigned char last_timer = 0xFF, last_rounds = 0xFF;

void hud_reset(void) {
    last_hp0 = last_hp1 = last_timer = last_rounds = 0xFF;
}

void hud_draw(void) {
    unsigned char rounds;

    /* Na abertura o placar nao existe: sem esta guarda o hud_draw redesenhava
     * barras e timer por cima do titulo todo frame. */
    if (g_gs == GS_TITLE || g_hitstop)
        return;

    if (P[0].hp != last_hp0) { bar(2, P[0].hp, 1); last_hp0 = P[0].hp; }
    if (P[1].hp != last_hp1) { bar(22, P[1].hp, 0); last_hp1 = P[1].hp; }
    if (g_timer != last_timer) {
        text_num(15, 0, g_timer, 2);
        last_timer = g_timer;
    }
    rounds = (unsigned char)(P[0].rounds | (P[1].rounds << 2));
    if (rounds != last_rounds) {
        unsigned int pip[2];
        pip[0] = (unsigned int)(P[0].rounds > 1 ? TILE_BAR_FULL : TILE_BAR_EMPTY);
        pip[1] = (unsigned int)(P[0].rounds ? TILE_BAR_FULL : TILE_BAR_EMPTY);
        put_run(11, 1, pip, 2);
        pip[0] = (unsigned int)(P[1].rounds ? TILE_BAR_FULL : TILE_BAR_EMPTY);
        pip[1] = (unsigned int)(P[1].rounds > 1 ? TILE_BAR_FULL : TILE_BAR_EMPTY);
        put_run(19, 1, pip, 2);
        last_rounds = rounds;
    }
}

static unsigned char slen(const char *s) {
    unsigned char n = 0;
    while (s[n]) n++;
    return n;
}

/* --- tela de abertura --------------------------------------------------
 *
 * Sem arte nova: o cais, a fonte e os dois lutadores JA estao na ROM, que
 * tem 1553 B livres. O titulo e composicao, nao asset — cena escurecida por
 * troca de paleta (16 bytes), texto na fonte existente e os lutadores em
 * pose de guarda. As nuvens e o mar continuam rolando por baixo, porque o
 * parallax nao sabe que mudou de tela.
 */
#define TL_ROW1 4
#define TL_ROW2 6
#define TL_ROW3 8
#define TL_PRESS 12
#define TL_CRED 23

static void centro(unsigned char row, const char *s) {
    unsigned char n = slen(s);
    text_at((unsigned char)((32 - n) >> 1), row, s);
}

void title_draw(void) {
    /* As duas primeiras linhas sao do placar; na abertura viram cenario. */
    text_clear(0, 0, 32);
    text_clear(0, 1, 32);
    centro(TL_ROW1, "MASTER SUPER");
    centro(TL_ROW2, "STREET FIGHTER II");
    centro(TL_ROW3, "TURBO");
    centro(TL_CRED, "SMSFORGE 2026");
}

void title_press(unsigned char visivel) {
    if (visivel)
        centro(TL_PRESS, "PRESS BUTTON 1");
    else
        text_clear(9, TL_PRESS, 14);
}

void title_clear(void) {
    text_clear(0, TL_ROW1, 32);
    text_clear(0, TL_ROW2, 32);
    text_clear(0, TL_ROW3, 32);
    text_clear(0, TL_PRESS, 32);
    text_clear(0, TL_CRED, 32);
}

/* Texto central de estado (ROUND / FIGHT / K.O. / vencedor). */
#define BANNER_ROW 10

static const char *banner_text(unsigned char id) {
    switch (id) {
    case BN_ROUND1: return "ROUND 1";
    case BN_ROUND2: return "ROUND 2";
    case BN_ROUND3: return "FINAL ROUND";
    case BN_FIGHT:  return "FIGHT!";
    case BN_KO:     return "K.O.";
    case BN_TIMEUP: return "TIME UP";
    case BN_P1WINS: return "KEN WINS";
    case BN_P2WINS: return "GUILE WINS";
    case BN_DRAW:   return "DRAW GAME";
    default:        return 0;
    }
}

void hud_banner(void) {
    static unsigned char shown = 0xFF;
    static unsigned char shown_col = 0, shown_len = 0;
    const char *s;
    unsigned char id = g_banner ? g_banner_id : BN_NONE;

    if (id == shown)
        return;
    if (shown_len)
        text_clear(shown_col, BANNER_ROW, shown_len);
    shown_len = 0;
    s = banner_text(id);
    if (s) {
        shown_len = slen(s);
        shown_col = (unsigned char)((32 - shown_len) >> 1);
        text_at(shown_col, BANNER_ROW, s);
    }
    shown = id;
}
