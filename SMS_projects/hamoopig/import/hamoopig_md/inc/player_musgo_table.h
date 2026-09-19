#ifndef PLAYER_MUSGO_TABLE_H
#define PLAYER_MUSGO_TABLE_H
#include "musgo.h"

typedef struct {
    const SpriteDefinition *def;
    u16 w;
    u16 h;
    s16 axisX;
    s16 axisY;
    u8 frames;
    u8 timing[12];
} MusgoStateAnim;

static inline const MusgoStateAnim *musgo_anim_for(u16 state) {
    switch(state) {
    case 100: {
        static const MusgoStateAnim a = {
            &spr_musgo_100, 80, 104, 40, 104, 4,
            { 8, 8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 101: {
        static const MusgoStateAnim a = {
            &spr_musgo_101, 80, 104, 40, 104, 1,
            { 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 102: {
        static const MusgoStateAnim a = {
            &spr_musgo_102, 80, 104, 40, 104, 3,
            { 4, 4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 104: {
        static const MusgoStateAnim a = {
            &spr_musgo_104, 96, 120, 48, 120, 2,
            { 6, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 105: {
        static const MusgoStateAnim a = {
            &spr_musgo_105, 80, 104, 40, 104, 3,
            { 4, 4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 106: {
        static const MusgoStateAnim a = {
            &spr_musgo_106, 80, 104, 40, 104, 2,
            { 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 151: {
        static const MusgoStateAnim a = {
            &spr_musgo_151, 80, 104, 40, 104, 3,
            { 4, 4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 200: {
        static const MusgoStateAnim a = {
            &spr_musgo_200, 64, 88, 32, 88, 1,
            { 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 201: {
        static const MusgoStateAnim a = {
            &spr_musgo_201, 72, 88, 36, 88, 3,
            { 6, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 300: {
        static const MusgoStateAnim a = {
            &spr_musgo_300, 88, 112, 44, 112, 3,
            { 4, 4, 99, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 420: {
        static const MusgoStateAnim a = {
            &spr_musgo_420, 88, 104, 44, 104, 6,
            { 6, 6, 6, 6, 6, 6, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 501: {
        static const MusgoStateAnim a = {
            &spr_musgo_501, 80, 96, 40, 96, 2,
            { 6, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 550: {
        static const MusgoStateAnim a = {
            &spr_musgo_550, 72, 88, 36, 88, 3,
            { 4, 4, 99, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 606: {
        static const MusgoStateAnim a = {
            &spr_musgo_606, 64, 88, 32, 88, 1,
            { 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 700: {
        static const MusgoStateAnim a = {
            &spr_musgo_700, 96, 120, 48, 120, 2,
            { 4, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 710: {
        static const MusgoStateAnim a = {
            &spr_musgo_710, 96, 120, 48, 120, 3,
            { 3, 4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 720: {
        static const MusgoStateAnim a = {
            &spr_musgo_720, 88, 104, 44, 104, 4,
            { 3, 3, 3, 6, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 730: {
        static const MusgoStateAnim a = {
            &spr_musgo_730, 88, 112, 44, 112, 3,
            { 3, 3, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    // defeat_v1 asset: authored terminal ground pose.
    case 570: {
        static const MusgoStateAnim a = {
            &spr_musgo_fall_v1, 120, 120, 60, 120, 2,
            { 6, 99, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 611: case 612: {
        static const MusgoStateAnim a = {
            &spr_musgo_victory_v1, 88, 128, 44, 128, 1,
            { 120, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 610: case 607: case 615: return musgo_anim_for(100);
    case 608: case 209: case 207: case 208: return musgo_anim_for(200);
    case 103: case 113: case 107: case 108: case 109: case 110: case 152: return musgo_anim_for(102);
    case 154: return musgo_anim_for(104);
    case 155: return musgo_anim_for(105);
    case 202: case 204: case 205: return musgo_anim_for(201);
    case 301: case 302: case 304: case 305: case 306:
    case 310: case 311: case 312: case 314: case 315: case 316:
    case 320: case 321: case 322: case 324: case 325: case 326:
        return musgo_anim_for(300);
    case 410: case 471: case 472: return musgo_anim_for(420);
    case 502: case 503: case 506: case 511: case 512:
    case 551: case 552: return musgo_anim_for(550);
    case 800: case 801: case 802: case 803: return musgo_anim_for(102);
    default: return musgo_anim_for(100);
    }
}

#endif

