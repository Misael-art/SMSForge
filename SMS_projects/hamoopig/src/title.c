#include "engine.h"

static unsigned int s_local;

void opening_enter(void)
{
    s_local = 0;
    text_at(8, 6, "HAMOOPIG");
    text_at(5, 8, "SMS FIGHT ENGINE");
    text_at(4, 12, "GAMEDEVBOSS 2015");
    text_at(6, 14, "PORT SMSFORGE");
    text_at(7, 20, "TECH BUILD");
}

void opening_update(void)
{
    s_local++;
    if (s_local > 120 || input_pressed(0, INP_B1)) {
        scene_request(SCENE_TITLE);
    }
}

void title_enter(void)
{
    s_local = 0;
    text_at(8, 4, "HAMOOPIG");
    text_at(6, 6, "MASTER SYSTEM");
    text_at(7, 10, "B1  START");
    text_at(7, 12, "PAUSE EXIT");
    text_at(4, 16, "P1 RYO  P2 MUSGO");
    text_at(5, 18, "TECHNICAL ARENA");
    text_at(3, 22, "NOT FINAL ART");
}

void title_update(void)
{
    s_local++;
    if (input_pressed(0, INP_B1)) {
        scene_request(SCENE_SELECT);
    }
}

void title_present(void)
{
    SMS_initSprites();
    SMS_copySpritestoSAT();
}

void select_enter(void)
{
    s_local = 0;
    text_at(6, 4, "SELECT");
    text_at(4, 8, "P1 RYO");
    text_at(4, 10, "P2 MUSGO");
    text_at(4, 14, "LEFT RIGHT ID");
    text_at(4, 16, "B1 CONFIRM");
    g_sel_p1 = FID_RYO;
    g_sel_p2 = FID_MUSGO;
}

void select_update(void)
{
    if (input_pressed(0, INP_LEFT)) {
        g_sel_p1 = (g_sel_p1 == FID_RYO) ? FID_MUSGO : FID_RYO;
        text_at(7, 8, (g_sel_p1 == FID_RYO) ? "RYO  " : "MUSGO");
    }
    if (input_pressed(0, INP_RIGHT)) {
        g_sel_p1 = (g_sel_p1 == FID_RYO) ? FID_MUSGO : FID_RYO;
        text_at(7, 8, (g_sel_p1 == FID_RYO) ? "RYO  " : "MUSGO");
    }
    if (input_pressed(1, INP_LEFT) || input_pressed(1, INP_RIGHT)) {
        g_sel_p2 = (g_sel_p2 == FID_MUSGO) ? FID_RYO : FID_MUSGO;
        text_at(7, 10, (g_sel_p2 == FID_RYO) ? "RYO  " : "MUSGO");
    }
    if (input_pressed(0, INP_B1) || s_local > 300) {
        scene_request(SCENE_FIGHT);
    }
    s_local++;
}
