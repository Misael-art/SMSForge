/* main.c -- integrated runtime study: 72-88 px Ken vs Ryu, shared pair pool
 * with the assembly streaming loop, per-row flicker scheduler (option 3),
 * FSM from fight.c driven by real pads.
 *
 * Scope of this build (budgeted in the memory bank 2026-09-29): idle, guard
 * and punch only. Button 1 = punch, button 2 = guard; directions are masked
 * because walk/jump/crouch poses are not in the pool/SAT budget yet.
 * P1 = port A, P2 = port B. Black stage, no HUD, no audio.
 *
 * Telemetry at 0xC7A0.. (read over DAP), per player p (0/1):
 *   lat_*: frames from the button edge to FSM accept, to the first pose of
 *   the new action being visible, to its hitbox being visible; max values
 *   too. dur_hist: visible pose held (AIR dur + delta) frames, delta
 *   0,1,2,3+ (poses with dur 255 excluded). Pool: slots used/peak, alloc
 *   failures, dropped stale uploads. Phase VCounter samples.
 */
#include "SMSlib.h"
#include "luta.h"
#include "fight.h"
#include "stream.h"

SMS_EMBED_SEGA_ROM_HEADER(0, 0);

#define WORST_FRAME_WINDOW 3000u

__sfr __at (0x7e) SMS_VCounterPort;

volatile unsigned char __at(0xC7E0) probe_magic0;
volatile unsigned char __at(0xC7E1) probe_magic1;
volatile unsigned char __at(0xC7E2) probe_magic2;
volatile unsigned char __at(0xC7E3) probe_magic3;
volatile unsigned char __at(0xC7E4) probe_schema;
volatile unsigned char __at(0xC7EA) probe_vline;
volatile unsigned int  __at(0xC7EB) probe_vovf;
volatile unsigned char __at(0xC7ED) probe_phase;
volatile unsigned char __at(0xC7EE) probe_worst_done;
volatile unsigned char __at(0xC7EF) probe_vline_min;
volatile unsigned int  __at(0xC7F0) probe_frame;
volatile unsigned char __at(0xC7D0) probe_profile_wait;
volatile unsigned char __at(0xC7D1) probe_profile_stream;
volatile unsigned char __at(0xC7D2) probe_profile_palette;
volatile unsigned char __at(0xC7D3) probe_profile_hud;
volatile unsigned char __at(0xC7D4) probe_profile_sat;
volatile unsigned char __at(0xC7D6) probe_vline_spill_max;
/* runtime probe snapshot bytes: state and life of both fighters */
volatile unsigned char __at(0xC7F2) probe_hp;
volatile unsigned char __at(0xC7F3) probe_score;
volatile unsigned char __at(0xC7F4) probe_boss;
volatile unsigned char __at(0xC7F5) probe_over;
volatile unsigned char __at(0xC7F6) probe_state;
volatile unsigned char __at(0xC7F8) probe_keys;

/* integration telemetry */
volatile unsigned char __at(0xC7A0) tl_lat_accept[2];
volatile unsigned char __at(0xC7A2) tl_lat_visible[2];
volatile unsigned char __at(0xC7A4) tl_lat_hitbox[2];
volatile unsigned char __at(0xC7A6) tl_lat_visible_max[2];
volatile unsigned char __at(0xC7A8) tl_lat_hitbox_max[2];
volatile unsigned char __at(0xC7AA) tl_presses[2];
volatile unsigned char __at(0xC7AC) tl_dur_hist[2][4];
volatile unsigned char __at(0xC7B4) tl_slots_used;
volatile unsigned char __at(0xC7B5) tl_slots_peak;
volatile unsigned char __at(0xC7B6) tl_alloc_fail;
volatile unsigned char __at(0xC7B7) tl_dropped;
volatile unsigned char __at(0xC7B8) tl_render_dropped_max;
volatile unsigned char __at(0xC7B9) tl_logic_end;
volatile unsigned char __at(0xC7BA) tl_render_end;
volatile unsigned char __at(0xC7BB) tl_render_end_max;
volatile unsigned char __at(0xC7BC) tl_magic;           /* 'I' when valid */
volatile unsigned char __at(0xC7BD) tl_ph_track;        /* phase stamps */
volatile unsigned char __at(0xC7BE) tl_ph_step0;
volatile unsigned char __at(0xC7BF) tl_ph_step1;
/* Atomic per-iteration copy of the phase stamps (read over DAP): stream end,
 * track, step0, step1, logic end, render start, fighters, sched, emit, add. */
volatile unsigned char __at(0xC790) tl_snap[10];
volatile unsigned char __at(0xC79A) tl_snap_seq;

extern unsigned char render_dropped;

/* per-player latency tracking */
static unsigned char track_on[2], track_t[2], track_pose0[2];
static unsigned char track_vis_done[2], track_hit_done[2], track_state[2];
static unsigned char keys_prev[2];
/* per-player visible pose duration */
static unsigned char vis_pose[2], vis_frames[2], vis_dur[2];

static unsigned char read_pad(unsigned char who) {
    unsigned int h = SMS_getKeysHeld();
    unsigned char k = 0;
    if (who) {
        if (h & PORT_B_KEY_1) k |= K_LP;
        if (h & PORT_B_KEY_2) k |= K_GUARD;
    } else {
        if (h & PORT_A_KEY_1) k |= K_LP;
        if (h & PORT_A_KEY_2) k |= K_GUARD;
    }
    return k;
}

static void track_after_sat(unsigned char who) {
    unsigned char pose = fight_visible_pose(who);
    unsigned char delta;
    /* visible pose duration vs AIR */
    if (pose == vis_pose[who]) {
        if (vis_frames[who] < 255u) vis_frames[who]++;
    } else {
        if (vis_dur[who] != 255u && vis_frames[who]) {
            delta = vis_frames[who] > vis_dur[who] ? vis_frames[who] - vis_dur[who] : 0;
            tl_dur_hist[who][delta > 3u ? 3u : delta]++;
        }
        vis_pose[who] = pose;
        vis_frames[who] = 1;
        vis_dur[who] = fight_visible_dur(who);
    }
    /* latency: pose and hitbox first visible after the press */
    if (!track_on[who]) return;
    if (!track_vis_done[who] && pose == track_pose0[who]) {
        track_vis_done[who] = 1;
        tl_lat_visible[who] = track_t[who];
        if (track_t[who] > tl_lat_visible_max[who]) tl_lat_visible_max[who] = track_t[who];
    }
    if (track_vis_done[who] && !track_hit_done[who] && track_state[who] == 1u &&
        fight_visible_hitbox(who)) {
        track_hit_done[who] = 1;
        tl_lat_hitbox[who] = track_t[who];
        if (track_t[who] > tl_lat_hitbox_max[who]) tl_lat_hitbox_max[who] = track_t[who];
    }
    if (track_vis_done[who] && (track_hit_done[who] || track_state[who] != 1u))
        track_on[who] = 0;
    else if (track_t[who] < 250u)
        track_t[who]++;
    else
        track_on[who] = 0;
}

static void track_input(unsigned char who, unsigned char k, unsigned char ev,
                        unsigned char state_before) {
    unsigned char pressed = (unsigned char)(k & ~keys_prev[who]);
    keys_prev[who] = k;
    if (!pressed) return;
    if (fighters[who].state == state_before) return;   /* not accepted */
    tl_presses[who]++;
    track_on[who] = 1;
    track_t[who] = 0;
    track_vis_done[who] = track_hit_done[who] = 0;
    track_state[who] = (unsigned char)(ev == FIGHT_EVENT_PUNCH ? 1u : 2u);
    track_pose0[who] = fight_state_pose0(who);
    tl_lat_accept[who] = 0;          /* accepted in the frame of the edge */
}

static void sample_worst_frame(void) {
    unsigned char vline;
    probe_phase = 2;
    vline = SMS_VCounterPort;
    if (!probe_worst_done) {
        probe_vline = vline;
        if (vline < probe_vline_min) probe_vline_min = vline;
        if (vline < 0xC0u) probe_vovf++;
        if (vline < 0xC0u && vline > probe_vline_spill_max)
            probe_vline_spill_max = vline;
        if (probe_frame == (WORST_FRAME_WINDOW - 1u)) probe_worst_done = 1;
    }
    probe_frame++;
    probe_phase = 3;
}

void main(void) {
    unsigned char i, k[2], ev[2], before[2];

    SMS_displayOff();
    SMS_init();
    SMS_VRAMmemsetW(0x0000u, 0x0000u, 16384u);
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_useFirstHalfTilesforSprites(1);
    sat_setup();
    SMS_setBGPaletteColor(0, RGB(0, 0, 0));
    fight_upload_palette();             /* sprite palette from the scene header */
    SMS_VRAMmemsetW(0x3800u, 0x00ffu, 1536u);

    for (i = 0; i < 2; i++) {
        tl_lat_accept[i] = tl_lat_visible[i] = tl_lat_hitbox[i] = 0;
        tl_lat_visible_max[i] = tl_lat_hitbox_max[i] = tl_presses[i] = 0;
        tl_dur_hist[i][0] = tl_dur_hist[i][1] = tl_dur_hist[i][2] = tl_dur_hist[i][3] = 0;
        track_on[i] = 0;
        keys_prev[i] = 0;
        vis_pose[i] = 0xFFu;
        vis_frames[i] = 0;
        vis_dur[i] = 255u;
    }
    tl_render_dropped_max = tl_render_end_max = 0;

    fight_init();
    fight_reset(&fighters[0], 0);
    fight_reset(&fighters[1], 1);

    /* First SAT before the display turns on, display enabled in VBlank
     * (both boot glitches were caught by audit_render_glitch). */
    fight_draw();
    sat_upload();
    fight_sat_copied();
    SMS_waitForVBlank();
    SMS_displayOn();

    probe_magic0 = 'S';
    probe_magic1 = 'M';
    probe_magic2 = 'R';
    probe_magic3 = 'T';
    probe_schema = 1;
    probe_vline = 0;
    probe_vovf = 0;
    probe_phase = 0;
    probe_worst_done = 0;
    probe_vline_min = 0xff;
    probe_frame = 0;
    probe_vline_spill_max = 0;
    tl_magic = 'I';

    for (;;) {
        SMS_waitForVBlank();
        probe_profile_wait = SMS_VCounterPort;
        sat_upload();                        /* own RAM SAT, OUTI in VBlank */
        fight_sat_copied();
        probe_profile_sat = SMS_VCounterPort;
        sample_worst_frame();                /* only the SAT is VBlank-bound */
        stream_step();
        probe_profile_stream = SMS_VCounterPort;
        stream_reclaim();

        track_after_sat(0);
        track_after_sat(1);
        tl_ph_track = SMS_VCounterPort;

        k[0] = read_pad(0);
        k[1] = read_pad(1);
        for (i = 0; i < 2; i++) before[i] = fighters[i].state;
        ev[0] = fight_step(&fighters[0], k[0], k[1]);
        tl_ph_step0 = SMS_VCounterPort;
        ev[1] = fight_step(&fighters[1], k[1], k[0]);
        tl_ph_step1 = SMS_VCounterPort;
        track_input(0, k[0], ev[0], before[0]);
        track_input(1, k[1], ev[1], before[1]);
        tl_logic_end = SMS_VCounterPort;

        fight_draw();
        tl_render_end = SMS_VCounterPort;
        if (tl_render_end < 0xC0u && tl_render_end > tl_render_end_max)
            tl_render_end_max = tl_render_end;
        if (render_dropped > tl_render_dropped_max) tl_render_dropped_max = render_dropped;

        tl_snap[0] = probe_profile_stream;
        tl_snap[1] = tl_ph_track;
        tl_snap[2] = tl_ph_step0;
        tl_snap[3] = tl_ph_step1;
        tl_snap[4] = tl_logic_end;
        tl_snap[5] = *(volatile unsigned char *)0xC7C5;
        tl_snap[6] = *(volatile unsigned char *)0xC7C1;
        tl_snap[7] = *(volatile unsigned char *)0xC7C2;
        tl_snap[8] = *(volatile unsigned char *)0xC7C3;
        tl_snap[9] = *(volatile unsigned char *)0xC7C4;
        tl_snap_seq++;
        tl_slots_used = stream_slots_used;
        tl_slots_peak = stream_slots_peak;
        tl_alloc_fail = stream_alloc_fail;
        tl_dropped = stream_dropped;
        probe_hp = (unsigned char)fighters[0].life;
        probe_boss = (unsigned char)fighters[1].life;
        probe_state = fighters[0].state;
        probe_over = fighters[1].state;
        probe_keys = (unsigned char)(k[0] | (k[1] << 4));
    }
}
