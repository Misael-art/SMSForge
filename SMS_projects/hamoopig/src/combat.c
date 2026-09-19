#include "engine.h"

static Contact s_ev[CE_CAP];
static unsigned char s_n;
static unsigned char s_seen[2];

void combat_begin_tick(void)
{
    s_n = 0;
    s_seen[0] = 0;
    s_seen[1] = 0;
}

void combat_emit(unsigned char atk, unsigned char def, unsigned char kind,
                 unsigned char inst, unsigned char dmg, unsigned int st)
{
    unsigned char i;
    if (s_n >= CE_CAP) {
        return;
    }
    /* Mesma instancia nao emite de novo neste tick nem enquanto overlap. */
    for (i = 0; i < s_n; i++) {
        if (s_ev[i].attacker == atk && s_ev[i].inst == inst && s_ev[i].state == st) {
            return;
        }
    }
    if (s_seen[atk] == inst && P[atk].hit_used) {
        return;
    }
    s_ev[s_n].attacker = atk;
    s_ev[s_n].defender = def;
    s_ev[s_n].kind = kind;
    s_ev[s_n].inst = inst;
    s_ev[s_n].damage = dmg;
    s_ev[s_n].state = st;
    s_n++;
}

unsigned char combat_count(void)
{
    return s_n;
}

static void apply_one(const Contact *e)
{
    Fighter *a = &P[e->attacker];
    Fighter *d = &P[e->defender];
    unsigned char dmg = e->damage;
    signed int nx;

    if (a->hit_used) {
        return;
    }
    a->hit_used = 1;
    audio_hit();
    if (e->kind == CE_GUARD) {
        dmg = 2;
        if (d->hp > dmg) {
            d->hp = (unsigned char)(d->hp - dmg);
        } else {
            d->hp = 0;
        }
        d->stun = 8;
        if (a->sp < SP_MAX) {
            a->sp++;
        }
        fighter_set_state(e->defender, ST_GUARD);
        g_hitstop = HITSTOP_FRAMES;
        return;
    }
    if (d->hp > dmg) {
        d->hp = (unsigned char)(d->hp - dmg);
    } else {
        d->hp = 0;
    }
    if (a->sp + 4u < SP_MAX) {
        a->sp = (unsigned char)(a->sp + 4u);
    } else {
        a->sp = SP_MAX;
    }
    if (d->sp + 2u < SP_MAX) {
        d->sp = (unsigned char)(d->sp + 2u);
    } else {
        d->sp = SP_MAX;
    }
    nx = d->x + (a->facing ? 4 : -4);
    if (nx < STAGE_X_MIN) {
        nx = STAGE_X_MIN;
    }
    if (nx > STAGE_X_MAX) {
        nx = STAGE_X_MAX;
    }
    d->x = nx;
    g_hitstop = HITSTOP_FRAMES;
    if (d->hp == 0) {
        fighter_set_state(e->defender, ST_KO);
    } else {
        fighter_set_state(e->defender, ST_HIT);
    }
}

void combat_resolve(void)
{
    unsigned char i;
    /* Snapshot ja coletado: aplica os dois lados, trade permitido. */
    for (i = 0; i < s_n; i++) {
        apply_one(&s_ev[i]);
    }
}
