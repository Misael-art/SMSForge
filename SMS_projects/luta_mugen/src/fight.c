/* fight.c — motor de luta interpretado por tabelas (Plano 2, Task 4).
 *
 * TABELAS DESTILADAS a mao do fixture sintetico (mini.air / mini.cns dos
 * testes mugen2sms) — o gerador ainda nao emite estados (S4 gera arte/cmd);
 * quando passar a emitir, e ESTA estrutura que ele preenche, nao o codigo.
 * Arte/pads de colisao vem dos blobs gerados (inc/gen/mini_art.h).
 *
 * Leis do plano 2 implementadas aqui:
 *  - Tick de anim: if (++tick >= frames[frame].dur) avanca; sem anim =
 *    "dur" gerado, entao dur vem do AIR destilado (255 = segura).
 *  - Fisica Q8.8 SEM float: walk.fwd=2 -> 512; walk.back=-1.5 -> -384;
 *    jump.vy=-10 -> +2560 (y = altura, positivo p/ cima); yaccel=0.5 -> 128.
 *  - Colisao: AABB de colunas inteiras lidas do blob CLSN (secao hit,
 *    sentinela -32767, secao hurt, sentinela). Frame sem CLSN herda o CLSN
 *    do frame 0 da anim (precedente: clsn2default do AIR).
 *  - Hit: hitstop=8 nos dois, knockback 16 px (8 se bloqueado), dano da
 *    tabela por golpe (200 -> 5, 201 -> 8, do CNS). Sem multiplicador.
 *  - Sem pressao de VDP: tudo roda no loop; nada aloca (RAM estatica).
 *
 * Compromisso declarado (pago na Task 7/cena 02): paleta de sprite e unica
 * e carrega o PAL do frame corrente do P1 — P2 em pose diferente herda a
 * cor do P1. Identidade P2 (shift de indice) e da cena 02.
 */
#include "SMSlib.h"
#include "luta.h"
#include "fight.h"
#include "gen/mini_art.h"

#define FLOOR_PX   128                    /* mesmo chao medido da cena 01 */
#define POSE_W     16                     /* largura da pose do fixture */
#define X_MIN      (16u * 256u)           /* Q8.8 — borda util da arena */
#define X_MAX      (240u * 256u)
#define JUMP_VY    2560                   /* |jump.vy| = 10 px/frame */
#define GRAV       128                    /* yaccel = 0.5 px/frame^2 */

/* ---- poses: um slot de VRAM (64 B = 1 par TALL apos dedup) por frame ---- */
/* base = slot*2 (tile par do par TALL); dur destilado de mini.air. */
#define FR(dur, base, sfx, clsn) \
    { (dur), (base), MINI_##sfx##_META, MINI_##sfx##_METAL, clsn, \
      MINI_##sfx##_AXIS }
#define NOCL 0

static const Frame frames_all[] = {
    FR(255,  0, A0F0,    MINI_A0F0_CLSN   ),
    FR(  8,  2, A20F0,   MINI_A20F0_CLSN  ),
    FR(  8,  4, A20F1,   MINI_A20F1_CLSN  ),
    FR(255,  6, A40F0,   MINI_A40F0_CLSN  ),
    FR(255,  8, A100F0,  MINI_A100F0_CLSN ),
    FR(255, 10, A120F0,  MINI_A120F0_CLSN ),
    FR(  3, 12, A200F0,  MINI_A200F0_CLSN ),
    FR(  5, 14, A200F1,  NOCL             ),
    FR(  3, 16, A201F0,  MINI_A201F0_CLSN ),
    FR(  4, 18, A201F1,  NOCL             ),
    FR(  5, 20, A201F2,  NOCL             ),
};
#define FR_OF(i) (frames_all + (i))

/* ---- animacoes (id AIR, frames, loop) ---- */
static const Anim anims[] = {
    {  0, 1, 1, FR_OF(0) },   /* idle    */
    { 20, 2, 1, FR_OF(1) },   /* walk    */
    { 40, 1, 1, FR_OF(3) },   /* jump    */
    {100, 1, 1, FR_OF(4) },   /* crouch  */
    {120, 1, 1, FR_OF(5) },   /* guard   */
    {200, 2, 0, FR_OF(6) },   /* punch1  */
    {201, 3, 0, FR_OF(8) },   /* punch2  */
};

/* ---- estados destilados de mini.cns [Statedef *] ---- */
#define S_CONTROL   0x01
#define S_AIR       0x02
#define S_HIT       0x04
#define S_BLOCKABLE 0x08

typedef struct { unsigned char id, anim, flags;
                 signed int vel;          /* Q8.8 relativo ao facing */
                 unsigned char dmg; } StateDef;

enum { ST_IDLE, ST_WALK_F, ST_WALK_B, ST_JUMP, ST_CROUCH, ST_GUARD,
       ST_PUNCH1, ST_PUNCH2, ST_N_STATES };

static const StateDef states[ST_N_STATES] = {
    {   0, 0, S_CONTROL,                    0, 0 },
    {  20, 1, S_CONTROL,    (signed int)512,  0 },  /* walk.fwd = 2   */
    {  21, 1, S_CONTROL,   (signed int)-384,  0 },  /* walk.back = -1.5 */
    {  40, 2, S_AIR,                          0, 0 },
    { 100, 3, S_CONTROL | S_BLOCKABLE,        0, 0 },
    { 120, 4, S_CONTROL | S_BLOCKABLE,        0, 0 },
    { 200, 5, S_HIT,                          0, 5 },  /* CNS damage = 5 */
    { 201, 6, S_HIT,                          0, 8 },  /* CNS damage = 8 */
};

Fighter fighters[2];
volatile unsigned char dbg_frame;

static signed char meta_ram[2][16];       /* 5 entradas + fim = 16 B */

/* ---- utilitarios ---- */

/* precedente MSSF2T fight.c:rebuild_meta — o terminador 0x80 so casa lido
 * ASSINADO (unsigned 128 != (signed)-128 promote a int). */
unsigned char meta_rebase(const unsigned char *meta, unsigned char base,
                          signed char *dst) {
    unsigned char n = 0;
    while ((signed char)meta[n] != (signed char)METASPRITE_END) {
        dst[n] = (signed char)meta[n];
        dst[n + 1] = (signed char)meta[n + 1];
        dst[n + 2] = (signed char)(base + meta[n + 2]);
        n += 3;
    }
    dst[n] = (signed char)METASPRITE_END;
    return n / 3;
}

static signed int rd16(const unsigned char *b) {
    return (signed int)((unsigned int)b[0] | ((unsigned int)b[1] << 8));
}

#define CLSN_END (-32767)

/* primeira caixa da secao hit; 0 se secao vazia (sentinela imediata). */
static unsigned char clsn_hit(const unsigned char *b, Box *o) {
    if (!b || rd16(b) == CLSN_END) return 0;
    o->x1 = (signed char)rd16(b);     o->y1 = (signed char)rd16(b + 2);
    o->x2 = (signed char)rd16(b + 4); o->y2 = (signed char)rd16(b + 6);
    return 1;
}

/* primeira caixa da secao hurt (pula hit + sentinela). */
static unsigned char clsn_hurt(const unsigned char *b, Box *o) {
    if (!b) return 0;
    if (rd16(b) != CLSN_END) b += 8;  /* caixa de 1 hit (fixtures tem <=1) */
    b += 2;                           /* sentinela fim-hit */
    if (rd16(b) == CLSN_END) return 0;
    o->x1 = (signed char)rd16(b);     o->y1 = (signed char)rd16(b + 2);
    o->x2 = (signed char)rd16(b + 4); o->y2 = (signed char)rd16(b + 6);
    return 1;
}

typedef struct { signed int l, t, r, b; } Rect;   /* px de tela */

/* caixa MUGEN (x relativo ao eixo, y<=0 acima do chao) -> AABB de tela. */
static void box_rect(const Fighter *p, const Box *b, Rect *r) {
    signed int xp = (signed int)(p->x >> 8);
    signed int alt = (signed int)(p->y >> 8);
    if (!p->facing) { r->l = xp + b->x1; r->r = xp + b->x2; }
    else            { r->l = xp - b->x2; r->r = xp - b->x1; }
    r->t = FLOOR_PX + b->y1 - alt;
    r->b = FLOOR_PX + b->y2 - alt;
}

static const Frame *cur_frame(const Fighter *p) {
    return &anims[p->anim].frames[p->frame];
}

/* hurtbox vigente: frame atual, senao heranca do frame 0 da anim. */
static const unsigned char *hurt_clsn(const Fighter *p) {
    const Frame *f = cur_frame(p);
    if (f->clsn) return f->clsn;
    return anims[p->anim].frames[0].clsn;
}

static void enter_state(Fighter *p, unsigned char s) {
    p->state = s;
    p->anim = states[s].anim;
    p->frame = 0;
    p->tick = 0;
    p->hit_done = 0;
    if (s == ST_JUMP) p->vy = JUMP_VY;   /* impulso unico na saida do chao */
}

static void clamp_x(Fighter *p) {
    if (p->x < X_MIN) p->x = X_MIN;
    if (p->x > X_MAX) p->x = X_MAX;
}

/* ---- API ---- */

/* blobs por slot de pose (mesma ordem de frames_all): tiles p/ init,
 * paleta p/ troca no frame do P1. */
static const unsigned char *const frames_tiles[11] = {
    MINI_A0F0_TILES,   MINI_A20F0_TILES,  MINI_A20F1_TILES,
    MINI_A40F0_TILES,  MINI_A100F0_TILES, MINI_A120F0_TILES,
    MINI_A200F0_TILES, MINI_A200F1_TILES, MINI_A201F0_TILES,
    MINI_A201F1_TILES, MINI_A201F2_TILES
};
static const unsigned char *const frames_pal[11] = {
    MINI_A0F0_PAL,   MINI_A20F0_PAL,  MINI_A20F1_PAL,
    MINI_A40F0_PAL,  MINI_A100F0_PAL, MINI_A120F0_PAL,
    MINI_A200F0_PAL, MINI_A200F1_PAL, MINI_A201F0_PAL,
    MINI_A201F1_PAL, MINI_A201F2_PAL
};

void fight_init(void) {
    unsigned char i;
    /* pool linear: frames_all[i] carregado no tile base i*2 (64 B c/ pose). */
    for (i = 0; i < 11; i++)
        SMS_loadTiles(frames_tiles[i], (unsigned int)i * 2, 64);
}

void fight_reset(Fighter *p, unsigned char slot) {
    p->facing = slot ? 1 : 0;
    p->x = slot ? (152u * 256u) : (96u * 256u);
    p->y = 0;
    p->vx = 0;
    p->vy = 0;
    p->life = 250;                        /* CNS [Data] life = 250 */
    p->hitstop = 0;
    p->keys_prev = 0;
    enter_state(p, ST_IDLE);
}

void fight_step(Fighter *p, unsigned int keys, unsigned int opp_keys) {
    const StateDef *sd;
    Fighter *o;
    unsigned int pressed;
    unsigned int fwdk, backk;
    unsigned char ns;

    (void)opp_keys;   /* resumo p/ Task 5 (clash); hit reciproco usa fighters[] */

    if (p->hitstop) { p->hitstop--; return; }   /* congela anim+fisica (MUGEN) */

    o = &fighters[1 - (unsigned char)(p - fighters)];
    sd = &states[p->state];

    if ((sd->flags & S_CONTROL) && p->y == 0) {
        /* auto-facing de solo; transicoes por precissao de borda em
         * UP/ataques (senao tecla segura reiniciaria o golpe todo frame). */
        p->facing = (o->x > p->x) ? 0 : 1;
        pressed = keys & ~p->keys_prev;
        if (p->facing) { fwdk = K_LEFT;  backk = K_RIGHT; }
        else           { fwdk = K_RIGHT; backk = K_LEFT;  }
        ns = p->state;
        if (pressed & K_LP)              ns = ST_PUNCH1;
        else if (pressed & K_HP)         ns = ST_PUNCH2;
        else if (pressed & K_UP)         ns = ST_JUMP;
        else if (keys & K_DOWN)          ns = ST_CROUCH;
        else if (keys & K_GUARD)         ns = ST_GUARD;
        else if (keys & fwdk)            ns = ST_WALK_F;
        else if (keys & backk)           ns = ST_WALK_B;
        else                             ns = ST_IDLE;
        p->keys_prev = keys;
        if (ns != p->state) { enter_state(p, ns); sd = &states[ns]; }
    }

    /* fisica */
    if (sd->flags & S_AIR) {
        p->vy -= GRAV;
        if (p->vy >= 0) {
            p->y += (unsigned int)p->vy;
        } else if ((signed int)p->y >= -p->vy) {
            p->y += (unsigned int)p->vy;
        } else {
            p->y = 0;
            p->vy = 0;
            enter_state(p, ST_IDLE);
            sd = &states[ST_IDLE];
        }
    } else if (sd->vel) {
        p->x = (unsigned int)((signed int)p->x +
                              (p->facing ? -sd->vel : sd->vel));
        clamp_x(p);
    }

    /* tick de animacao */
    {
        const Anim *a = &anims[p->anim];
        if (++p->tick >= a->frames[p->frame].dur) {
            p->tick = 0;
            if (p->frame + 1 >= a->n_frames) {
                if (a->loop) p->frame = 0;
                else enter_state(p, ST_IDLE);
            } else {
                p->frame++;
            }
        }
    }

    /* checagem de hit: janela = frame com caixa de golpe no blob CLSN
     * (destilado do HitDef trigger time=3 — o frame startup E a janela). */
    sd = &states[p->state];
    if ((sd->flags & S_HIT) && !p->hit_done) {
        Box hb, ob;
        Rect ra, rb;
        if (clsn_hit(cur_frame(p)->clsn, &hb)) {
            const unsigned char *oc = hurt_clsn(o);
            if (clsn_hurt(oc, &ob)) {
                box_rect(p, &hb, &ra);
                box_rect(o, &ob, &rb);
                if (ra.l < rb.r && rb.l < ra.r && ra.t < rb.b && rb.t < ra.b) {
                    unsigned char push;
                    p->hit_done = 1;
                    push = 16;
                    /* guarda so bloqueia de frente: frente a frente => facings
                     * opostos (destilado de attr=S,MA + guard do MUGEN). */
                    if ((states[o->state].flags & S_BLOCKABLE) && o->y == 0 &&
                        o->facing != p->facing) {
                        push = 8;          /* bloqueado: sem dano, empurra menos */
                    } else {
                        if (o->life >= sd->dmg) o->life -= sd->dmg;
                        else o->life = 0;
                    }
                    o->hitstop = 8;
                    p->hitstop = 8;
                    o->x = (unsigned int)((signed int)o->x +
                                          (p->facing ? -(signed int)push * 256
                                                     : (signed int)push * 256));
                    clamp_x(o);
                }
            }
        }
    }
}

void fight_draw(void) {
    unsigned char i;
    static unsigned char last_pal_slot = 0xFF;
    unsigned char pal_slot;

    /* projeteis antes dos lutadores: nenhum no corte atual */
    for (i = 0; i < 2; i++) {
        Fighter *p = &fighters[i];
        const Frame *f = cur_frame(p);
        signed int ax = rd16(f->axis), ay = rd16(f->axis + 2);
        signed int sx, sy;

        meta_rebase(p->facing ? f->metal : f->meta, f->base, meta_ram[i]);
        sx = (signed int)(p->x >> 8) + (p->facing ? -(ax + POSE_W) : ax);
        sy = FLOOR_PX + ay - (signed int)(p->y >> 8);
        SMS_addMetaSprite((unsigned char)sx, (unsigned char)sy, meta_ram[i]);
    }
    /* paleta do frame corrente do P1 (compromisso T4; cena 02 faz P2 por
     * shift de indice na MESMA subpaleta — GDD). */
    pal_slot = (unsigned char)(cur_frame(&fighters[0]) - frames_all);
    if (pal_slot != last_pal_slot) {
        const unsigned char *pal = frames_pal[pal_slot];
        unsigned char k;
        for (k = 0; k < 16; k++) SMS_setSpritePaletteColor(k, pal[k]);
        last_pal_slot = pal_slot;
    }
}
