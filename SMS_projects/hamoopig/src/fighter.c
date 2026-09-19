#include "engine.h"

static const MoveDef mv_punch = {4, 4, 8, 7, 12, 8, 4, 0, {12, 10, 12, 8}};
static const MoveDef mv_kick  = {6, 4, 10, 10, 14, 10, 5, 0, {8, 20, 14, 10}};
static const MoveDef mv_hadou = {10, 4, 18, 12, 16, 12, 6, MF_PROJ, {12, 8, 16, 10}};
static const MoveDef mv_slam  = {8, 6, 16, 14, 18, 12, 8, 0, {8, 8, 16, 20}};

static const FighterDef def_ryo = {
    FID_RYO, 2, 8, 1, &mv_punch, &mv_kick, &mv_hadou
};
static const FighterDef def_ken = {
    FID_KEN, 2, 8, 1, &mv_punch, &mv_kick, &mv_hadou
};
static const FighterDef def_musgo = {
    FID_MUSGO, 1, 7, 1, &mv_punch, &mv_slam, &mv_slam
};

const FighterDef *fighter_def(unsigned char id)
{
    if (id == FID_MUSGO) {
        return &def_musgo;
    }
    if (id == FID_KEN) {
        return &def_ken;
    }
    return &def_ryo;
}

static unsigned char is_attack(unsigned int st)
{
    return (unsigned char)(st == ST_PUNCH || st == ST_KICK || st == ST_SPECIAL);
}

static unsigned char is_busy(unsigned int st)
{
    return (unsigned char)(is_attack(st) || st == ST_HIT || st == ST_KO ||
                           st == ST_WIN || st == ST_GUARD);
}

void fighter_set_state(unsigned char who, unsigned int st)
{
    Fighter *f = &P[who];
    if (is_attack(st) && f->state != st) {
        f->attack_inst++;
        if (f->attack_inst == 0) {
            f->attack_inst = 1;
        }
        f->hit_used = 0;
    }
    f->state = st;
    f->timer = 0;
    if (st == ST_PUNCH || st == ST_KICK || st == ST_SPECIAL) {
        f->pose = POSE_PUNCH;
    } else if (st == ST_HIT || st == ST_KO) {
        f->pose = POSE_PUNCH;
    } else {
        f->pose = POSE_IDLE;
    }
    if (st == ST_SPECIAL && (fighter_def(f->id)->special->flags & MF_PROJ) &&
        f->fire_on == 0) {
        f->fire_on = 1;
        f->fx = f->x + (f->facing ? 16 : -8);
        f->fy = f->y + 8;
        f->fvx = (signed char)(f->facing ? 3 : -3);
    }
}

static unsigned char heldk(unsigned char who, unsigned char btn);
static unsigned char pressk(unsigned char who, unsigned char btn);

static const MoveDef *move_of(const Fighter *f)
{
    const FighterDef *d = fighter_def(f->id);
    if (f->state == ST_KICK) {
        return d->kick;
    }
    if (f->state == ST_SPECIAL) {
        return d->special;
    }
    return d->punch;
}

static void hist_push(unsigned char who)
{
    Fighter *f = &P[who];
    unsigned char d = 5;
    unsigned char down = heldk(who, INP_DOWN);
    unsigned char fwd, back;
    if (f->facing) {
        fwd = heldk(who, INP_RIGHT);
        back = heldk(who, INP_LEFT);
    } else {
        fwd = heldk(who, INP_LEFT);
        back = heldk(who, INP_RIGHT);
    }
    if (down && fwd) {
        d = 3;
    } else if (down) {
        d = 2;
    } else if (fwd) {
        d = 6;
    } else if (back) {
        d = 4;
    }
    f->hist[f->hist_i & 7] = d;
    f->hist_i++;
}

unsigned char fighter_qcf(unsigned char who)
{
    unsigned char i, seen2 = 0;
    unsigned char idx;
    /* Mais antigo -> mais recente. SMS: baixo (ou diagonal) depois frente. */
    for (i = 0; i < 8; i++) {
        idx = (unsigned char)((P[who].hist_i + i) & 7);
        if (!seen2 && (P[who].hist[idx] == 2 || P[who].hist[idx] == 3)) {
            seen2 = 1;
        } else if (seen2 && P[who].hist[idx] == 6) {
            return 1;
        }
    }
    return 0;
}

static void apply_gravity(unsigned char who)
{
    Fighter *f = &P[who];
    const FighterDef *d = fighter_def(f->id);
    if (f->y < GROUND_Y || f->vy != 0) {
        f->vy = (signed char)(f->vy + (signed char)d->grav);
        f->y += f->vy;
        if (f->y >= GROUND_Y) {
            f->y = GROUND_Y;
            f->vy = 0;
            if (f->state == ST_JUMP) {
                fighter_set_state(who, ST_IDLE);
            }
        }
    }
}

static void update_facing(unsigned char who)
{
    unsigned char other = (unsigned char)(who ^ 1);
    if (P[who].state == ST_IDLE || P[who].state == ST_WALK_F ||
        P[who].state == ST_WALK_B || P[who].state == ST_CROUCH) {
        P[who].facing = (unsigned char)(P[who].x < P[other].x);
    }
}

static unsigned char heldk(unsigned char who, unsigned char btn)
{
    unsigned char s = P[who].keys[btn];
    return (unsigned char)(s == KEY_PRESSED || s == KEY_HOLD);
}

static unsigned char pressk(unsigned char who, unsigned char btn)
{
    return (unsigned char)(P[who].keys[btn] == KEY_PRESSED);
}

static void dummy_ai(unsigned char who)
{
    unsigned char other = (unsigned char)(who ^ 1);
    signed int gap = P[other].x - P[who].x;
    unsigned char b;
    for (b = 0; b < INP_COUNT; b++) {
        P[who].keys[b] = KEY_FREE;
    }
    if (g_lock) {
        return;
    }
    if (gap > 28) {
        P[who].keys[INP_RIGHT] = KEY_HOLD;
    } else if (gap < -28) {
        P[who].keys[INP_LEFT] = KEY_HOLD;
    } else if ((g_frame & 31) == 0) {
        P[who].keys[INP_B1] = KEY_PRESSED;
    }
}

static void fighter_logic(unsigned char who)
{
    Fighter *f = &P[who];
    const FighterDef *d = fighter_def(f->id);
    unsigned char back, fwd;
    signed int nx;

    if (f->control == CONTROL_CPU) {
        dummy_ai(who);
    }
    hist_push(who);
    apply_gravity(who);
    update_facing(who);

    if (f->facing) {
        fwd = heldk(who, INP_RIGHT);
        back = heldk(who, INP_LEFT);
    } else {
        fwd = heldk(who, INP_LEFT);
        back = heldk(who, INP_RIGHT);
    }
    f->guard = (unsigned char)(back && !fwd &&
        (f->state == ST_IDLE || f->state == ST_WALK_B || f->state == ST_WALK_F ||
         f->state == ST_CROUCH || f->state == ST_GUARD));

    if (g_lock || f->state == ST_KO || f->state == ST_WIN) {
        f->timer++;
        return;
    }
    if (f->stun) {
        f->stun--;
        f->timer++;
        return;
    }

    if (is_attack(f->state)) {
        const MoveDef *mv = move_of(f);
        f->timer++;
        if (f->timer >= (unsigned char)(mv->startup + mv->active + mv->recovery)) {
            fighter_set_state(who, (f->y < GROUND_Y) ? ST_JUMP : ST_IDLE);
        }
        return;
    }
    if (f->state == ST_HIT) {
        f->timer++;
        if (f->timer > 12) {
            fighter_set_state(who, ST_IDLE);
        }
        return;
    }
    if (f->state == ST_GUARD) {
        if (!f->guard) {
            fighter_set_state(who, ST_IDLE);
        }
        return;
    }
    if (f->state == ST_JUMP) {
        if (fwd) {
            nx = f->x + (f->facing ? (signed int)d->walk_spd : -(signed int)d->walk_spd);
        } else if (back) {
            nx = f->x + (f->facing ? -(signed int)d->walk_spd : (signed int)d->walk_spd);
        } else {
            nx = f->x;
        }
        if (nx < STAGE_X_MIN) {
            nx = STAGE_X_MIN;
        }
        if (nx > STAGE_X_MAX) {
            nx = STAGE_X_MAX;
        }
        f->x = nx;
        return;
    }

    /* B1 hold (nao so a borda): o QCF SMS cabe em 8 ticks, mas o botao
     * pode cair 1-3 frames depois do 6. Nao alarga o hist. */
    if ((pressk(who, INP_B1) || heldk(who, INP_B1)) && fighter_qcf(who)
        && f->sp >= SP_COST) {
        f->sp = (unsigned char)(f->sp - SP_COST);
        fighter_set_state(who, ST_SPECIAL);
        return;
    }
    if (pressk(who, INP_B1)) {
        fighter_set_state(who, ST_PUNCH);
        return;
    }
    if (pressk(who, INP_B2)) {
        fighter_set_state(who, ST_KICK);
        return;
    }
    if (pressk(who, INP_UP) && f->y >= GROUND_Y) {
        f->vy = (signed char)(-(signed char)d->jump_imp);
        fighter_set_state(who, ST_JUMP);
        return;
    }
    if (heldk(who, INP_DOWN)) {
        fighter_set_state(who, ST_CROUCH);
        return;
    }
    if (f->guard) {
        fighter_set_state(who, ST_WALK_B);
        nx = f->x + (f->facing ? -(signed int)d->walk_spd : (signed int)d->walk_spd);
        if (nx < STAGE_X_MIN) {
            nx = STAGE_X_MIN;
        }
        if (nx > STAGE_X_MAX) {
            nx = STAGE_X_MAX;
        }
        f->x = nx;
        return;
    }
    if (fwd) {
        fighter_set_state(who, ST_WALK_F);
        nx = f->x + (f->facing ? (signed int)d->walk_spd : -(signed int)d->walk_spd);
        if (nx < STAGE_X_MIN) {
            nx = STAGE_X_MIN;
        }
        if (nx > STAGE_X_MAX) {
            nx = STAGE_X_MAX;
        }
        f->x = nx;
        return;
    }
    fighter_set_state(who, ST_IDLE);
}

static unsigned char boxes_hit(unsigned char atk, unsigned char def)
{
    Fighter *a = &P[atk];
    Fighter *d = &P[def];
    const MoveDef *mv;
    int hx, hy, hw, hh;
    int bx, by, bw, bh;
    unsigned char start, end;

    if (!is_attack(a->state) || a->hit_used) {
        return 0;
    }
    mv = move_of(a);
    start = mv->startup;
    end = (unsigned char)(mv->startup + mv->active);
    if (a->timer < start || a->timer >= end) {
        return 0;
    }
    hw = mv->hit.w;
    hh = mv->hit.h;
    hy = a->y + mv->hit.y;
    if (a->facing) {
        hx = a->x + mv->hit.x;
    } else {
        hx = a->x + FIGHTER_W - mv->hit.x - mv->hit.w;
    }
    bx = d->x + 2;
    bw = 12;
    if (d->state == ST_CROUCH) {
        by = d->y + 16;
        bh = 16;
    } else {
        by = d->y + 4;
        bh = 28;
    }
    if (hx < bx + bw && hx + hw > bx && hy < by + bh && hy + hh > by) {
        return 1;
    }
    return 0;
}

static void separate(void)
{
    signed int gap, mid;
    if (P[0].y < GROUND_Y || P[1].y < GROUND_Y) {
        return;
    }
    gap = P[1].x - P[0].x;
    if (gap < 0) {
        gap = -gap;
    }
    if (gap >= PUSH_W * 2) {
        return;
    }
    mid = (PUSH_W * 2 - gap) / 2;
    if (P[0].x <= P[1].x) {
        P[0].x -= mid;
        P[1].x += mid;
    } else {
        P[1].x -= mid;
        P[0].x += mid;
    }
    if (P[0].x < STAGE_X_MIN) {
        P[0].x = STAGE_X_MIN;
    }
    if (P[1].x < STAGE_X_MIN) {
        P[1].x = STAGE_X_MIN;
    }
    if (P[0].x > STAGE_X_MAX) {
        P[0].x = STAGE_X_MAX;
    }
    if (P[1].x > STAGE_X_MAX) {
        P[1].x = STAGE_X_MAX;
    }
}

static void fire_tick(unsigned char who)
{
    Fighter *f = &P[who];
    Fighter *d = &P[who ^ 1];
    int bx, by, bw, bh;

    if (f->fire_on != 1) {
        return;
    }
    f->fx += f->fvx;
    if (f->fx < 0 || f->fx > 248) {
        f->fire_on = 0;
        return;
    }
    bx = d->x + 2;
    bw = 12;
    by = (d->state == ST_CROUCH) ? (d->y + 16) : (d->y + 4);
    bh = (d->state == ST_CROUCH) ? 16 : 28;
    if (f->fx < bx + bw && f->fx + 8 > bx &&
        f->fy < by + bh && f->fy + 16 > by) {
        combat_emit(who, (unsigned char)(who ^ 1),
                    d->guard ? CE_GUARD : CE_HIT,
                    (unsigned char)(f->attack_inst | 0x80),
                    fighter_def(f->id)->special->damage,
                    ST_SPECIAL);
        f->fire_on = 2;
    }
}

static void collect_contacts(void)
{
    unsigned char a, d, kind;
    for (a = 0; a < 2; a++) {
        d = (unsigned char)(a ^ 1);
        if (boxes_hit(a, d)) {
            kind = P[d].guard ? CE_GUARD : CE_HIT;
            combat_emit(a, d, kind, P[a].attack_inst, move_of(&P[a])->damage,
                        P[a].state);
        }
        fire_tick(a);
    }
}

static void round_logic(void)
{
    if (g_lock) {
        if (g_banner) {
            g_banner--;
            if (g_banner == 0) {
                if (g_banner_id == BN_ROUND) {
                    g_banner_id = BN_FIGHT;
                    g_banner = 40;
                } else {
                    g_banner_id = BN_NONE;
                    g_lock = 0;
                }
            }
        }
        return;
    }
    if (g_result != RES_NONE) {
        if (g_banner) {
            g_banner--;
        }
        if (g_banner == 0) {
            if (P[0].rounds >= ROUNDS_TO_WIN || P[1].rounds >= ROUNDS_TO_WIN) {
                scene_request(SCENE_AFTER_MATCH);
            } else {
                fight_reset_round();
            }
        }
        return;
    }
    if (P[0].hp == 0 && P[1].hp == 0) {
        g_result = RES_DRAW;
        g_banner_id = BN_DRAW;
        g_banner = 90;
        return;
    }
    if (P[0].hp == 0) {
        P[1].rounds++;
        g_result = RES_P2;
        g_banner_id = BN_KO;
        g_banner = 90;
        fighter_set_state(1, ST_WIN);
        return;
    }
    if (P[1].hp == 0) {
        P[0].rounds++;
        g_result = RES_P1;
        g_banner_id = BN_KO;
        g_banner = 90;
        fighter_set_state(0, ST_WIN);
        return;
    }
    if (g_clock == 0) {
        if (P[0].hp > P[1].hp) {
            P[0].rounds++;
            g_result = RES_P1;
            g_banner_id = BN_TIME;
        } else if (P[1].hp > P[0].hp) {
            P[1].rounds++;
            g_result = RES_P2;
            g_banner_id = BN_TIME;
        } else {
            g_result = RES_DRAW;
            g_banner_id = BN_DRAW;
        }
        g_banner = 90;
    }
}

void fight_reset_round(void)
{
    unsigned char i;
    for (i = 0; i < 2; i++) {
        P[i].hp = HP_MAX;
        P[i].sp = 0;
        P[i].y = GROUND_Y;
        P[i].vy = 0;
        P[i].timer = 0;
        P[i].hit_used = 0;
        P[i].guard = 0;
        P[i].stun = 0;
        P[i].fire_on = 0;
        P[i].hist_i = 0;
        fighter_set_state(i, ST_IDLE);
    }
    P[0].x = 40;
    P[1].x = 180;
    P[0].facing = 1;
    P[1].facing = 0;
    g_clock = CLOCK_START;
    g_clock_div = 0;
    g_hitstop = 0;
    g_result = RES_NONE;
    g_lock = 1;
    g_round++;
    g_banner_id = BN_ROUND;
    g_banner = 50;
}

static void fighter_clear(unsigned char who, unsigned char id, unsigned char ctrl)
{
    unsigned char r;
    for (r = 0; r < sizeof(Fighter); r++) {
        ((unsigned char *)&P[who])[r] = 0;
    }
    P[who].id = id;
    P[who].control = ctrl;
    P[who].hp = HP_MAX;
}

void fight_enter(void)
{
    unsigned char col, row;
    fighter_clear(0, g_sel_p1, g_control[0]);
    fighter_clear(1, g_sel_p2, g_control[1]);
    P[0].rounds = 0;
    P[1].rounds = 0;
    g_round = 0;
    for (row = 18; row < 24; row++) {
        SMS_setNextTileatXY(0, row);
        for (col = 0; col < 32; col++) {
            SMS_setTile(TILE_FLOOR);
        }
    }
    hud_enter_fight();
    fight_reset_round();
}

void fight_update(void)
{
    if (g_hitstop) {
        g_hitstop--;
        return;
    }
    if (!g_lock && g_result == RES_NONE) {
        g_clock_div++;
        if (g_clock_div >= 60) {
            g_clock_div = 0;
            if (g_clock) {
                g_clock--;
            }
        }
    }
    combat_begin_tick();
    fighter_logic(0);
    fighter_logic(1);
    separate();
    collect_contacts();
    combat_resolve();
    round_logic();
}

static const signed char meta_idle[] = {
    0, 0, 0,
    8, 0, 2,
    0, 16, 4,
    8, 16, 6,
    (signed char)METASPRITE_END
};

static unsigned char tile_base(unsigned char who)
{
    Fighter *f = &P[who];
    unsigned char punch = (unsigned char)(f->pose == POSE_PUNCH);
    if (who == 0) {
        if (f->facing) {
            return punch ? TILE_P1_PUNCH : TILE_P1_IDLE;
        }
        return punch ? TILE_P1_PUNCH_L : TILE_P1_IDLE_L;
    }
    if (f->facing) {
        return punch ? TILE_P2_PUNCH : TILE_P2_IDLE;
    }
    return punch ? TILE_P2_PUNCH_L : TILE_P2_IDLE_L;
}

void fight_present(void)
{
    unsigned char who, i;
    signed char meta[13];
    unsigned char base;
    SMS_initSprites();
    for (who = 0; who < 2; who++) {
        base = tile_base(who);
        for (i = 0; i < 12; i++) {
            meta[i] = meta_idle[i];
        }
        meta[12] = (signed char)METASPRITE_END;
        meta[2] = (signed char)(base + 0);
        meta[5] = (signed char)(base + 2);
        meta[8] = (signed char)(base + 4);
        meta[11] = (signed char)(base + 6);
        SMS_addMetaSprite((unsigned char)P[who].x, (unsigned char)P[who].y, meta);
        if (P[who].fire_on == 1) {
            SMS_addSprite((unsigned char)P[who].fx, (unsigned char)P[who].fy,
                          TILE_FB);
        }
    }
    SMS_copySpritestoSAT();
    hud_draw();
}
