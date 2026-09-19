#include "engine.h"

void scene_request(unsigned char id)
{
    if (g_scene_req == SCENE_NONE) {
        g_scene_req = id;
    }
}

void scene_enter(unsigned char id)
{
    g_scene = id;
    g_scene_req = SCENE_NONE;
    SMS_displayOff();
    SMS_initSprites();
    SMS_copySpritestoSAT();
    gfx_clear_nametable();
    switch (id) {
    case SCENE_OPENING:
        opening_enter();
        break;
    case SCENE_TITLE:
        title_enter();
        break;
    case SCENE_SELECT:
        select_enter();
        break;
    case SCENE_FIGHT:
        fight_enter();
        break;
    case SCENE_AFTER_MATCH:
        text_at(8, 10, "RESULT");
        if (g_result == RES_P1) {
            text_at(8, 12, "P1 WINS");
        } else if (g_result == RES_P2) {
            text_at(8, 12, "P2 WINS");
        } else {
            text_at(8, 12, "DRAW");
        }
        text_at(6, 16, "B1 REMATCH");
        text_at(6, 18, "PAUSE TITLE");
        break;
    default:
        break;
    }
    SMS_displayOn();
}

void scene_commit(void)
{
    unsigned char next;
    if (g_scene_req == SCENE_NONE) {
        return;
    }
    next = g_scene_req;
    g_scene_req = SCENE_NONE;
    scene_enter(next);
}
