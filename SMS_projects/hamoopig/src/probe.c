#include "engine.h"

volatile unsigned char __at(0xC7D0) probe_hist[8];
volatile unsigned char __at(0xC7D8) probe_hist_i;
volatile unsigned char __at(0xC7D9) probe_qcf;
volatile unsigned char __at(0xC7DA) probe_dir;
volatile unsigned char __at(0xC7DB) probe_fire;
volatile unsigned char __at(0xC7DC) probe_p2g;
volatile unsigned char __at(0xC7DD) probe_ctrl;
volatile unsigned char __at(0xC7E0) probe_magic0;
volatile unsigned char __at(0xC7E1) probe_magic1;
volatile unsigned char __at(0xC7E2) probe_magic2;
volatile unsigned char __at(0xC7E3) probe_magic3;
volatile unsigned char __at(0xC7E4) probe_schema;
volatile unsigned char __at(0xC7E5) probe_timer;
volatile unsigned char __at(0xC7E6) probe_atkwin;
volatile unsigned char __at(0xC7E7) probe_gap;
volatile unsigned char __at(0xC7E8) probe_hitstop;
volatile unsigned char __at(0xC7E9) probe_hitused;
volatile unsigned char __at(0xC7EA) probe_vline;
volatile unsigned int  __at(0xC7EB) probe_vovf;
volatile unsigned char __at(0xC7ED) probe_phase;
volatile unsigned char __at(0xC7EE) probe_missed;
volatile unsigned char __at(0xC7EF) probe_sp;
volatile unsigned int  __at(0xC7F0) probe_frame;
volatile unsigned char __at(0xC7F2) probe_hp;
volatile unsigned char __at(0xC7F3) probe_score;
volatile unsigned char __at(0xC7F4) probe_boss;
volatile unsigned char __at(0xC7F5) probe_over;
volatile unsigned char __at(0xC7F6) probe_state;
volatile unsigned char __at(0xC7F7) probe_wave;
volatile unsigned char __at(0xC7F8) probe_keys;
volatile unsigned char __at(0xC7F9) probe_pose;
volatile unsigned char __at(0xC7FA) probe_px;
volatile unsigned char __at(0xC7FB) probe_py;
volatile unsigned char __at(0xC7FC) probe_p2x;

void probe_init(void)
{
    probe_magic0 = 'S';
    probe_magic1 = 'M';
    probe_magic2 = 'R';
    probe_magic3 = 'T';
    probe_schema = 1;
    probe_frame = 0;
    probe_vline = 0;
    probe_vovf = 0;
    probe_phase = 0;
    probe_missed = 0;
}

void probe_frame_end(unsigned int raw, unsigned char vline)
{
    signed int gap;
    (void)vline;
    probe_frame = g_frame;
    probe_hp = P[0].hp;
    probe_score = P[0].rounds;
    probe_boss = P[1].hp;
    probe_over = (unsigned char)(g_scene == SCENE_AFTER_MATCH);
    probe_state = g_scene;
    probe_wave = g_clock;
    probe_keys = (unsigned char)raw;
    probe_pose = (unsigned char)(P[0].pose | (P[0].facing ? 0x80 : 0));
    probe_px = (unsigned char)P[0].x;
    probe_py = (unsigned char)P[0].y;
    probe_p2x = (unsigned char)P[1].x;
    probe_timer = P[0].timer;
    probe_atkwin = (unsigned char)P[0].state;
    gap = P[1].x - P[0].x;
    if (gap < 0) {
        gap = -gap;
    }
    if (gap > 255) {
        gap = 255;
    }
    probe_gap = (unsigned char)gap;
    probe_hitstop = g_hitstop;
    probe_hitused = P[0].hit_used;
    probe_sp = P[0].sp;
    {
        unsigned char i;
        for (i = 0; i < 8; i++) {
            probe_hist[i] = P[0].hist[i];
        }
    }
    probe_hist_i = P[0].hist_i;
    probe_qcf = fighter_qcf(0);
    probe_dir = P[0].hist[(unsigned char)((P[0].hist_i - 1) & 7)];
    probe_fire = P[0].fire_on;
    probe_p2g = P[1].guard;
    probe_ctrl = g_control[1];
}
