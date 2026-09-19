#ifndef PLAYER_KEN_TABLE_H
#define PLAYER_KEN_TABLE_H
#include "ken.h"

typedef struct {
    const SpriteDefinition *def;
    u16 w;
    u16 h;
    s16 axisX;
    s16 axisY;
    u8 frames;
    u8 timing[12];
} KenStateAnim;

static inline const KenStateAnim *ken_anim_for(u16 state) {
    switch(state) {
    case 100: {
        static const KenStateAnim a = {
            &spr_ken_100, 64, 96, 32, 96, 4,
            { 8, 8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 101: {
        static const KenStateAnim a = {
            &spr_ken_101, 56, 88, 28, 88, 1,
            { 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 102: {
        static const KenStateAnim a = {
            &spr_ken_102, 96, 96, 48, 96, 2,
            { 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 104: {
        static const KenStateAnim a = {
            &spr_ken_104, 72, 104, 36, 104, 1,
            { 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 105: {
        static const KenStateAnim a = {
            &spr_ken_105, 88, 96, 44, 96, 3,
            { 3, 4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 106: {
        static const KenStateAnim a = {
            &spr_ken_106, 64, 104, 32, 104, 2,
            { 3, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 151: {
        static const KenStateAnim a = {
            &spr_ken_151, 120, 96, 60, 96, 2,
            { 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 200: {
        static const KenStateAnim a = {
            &spr_ken_200, 64, 104, 32, 104, 3,
            { 6, 6, 250, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 201: {
        static const KenStateAnim a = {
            &spr_ken_201, 128, 104, 64, 104, 6,
            { 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 300: {
        static const KenStateAnim a = {
            &spr_ken_300, 72, 128, 36, 128, 6,
            { 4, 4, 4, 4, 4, 99, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 420: {
        static const KenStateAnim a = {
            &spr_ken_420, 64, 96, 32, 96, 5,
            { 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 501: {
        static const KenStateAnim a = {
            &spr_ken_501, 112, 72, 56, 72, 2,
            { 4, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 550: {
        static const KenStateAnim a = {
            &spr_ken_550, 88, 96, 44, 96, 5,
            { 4, 4, 4, 4, 99, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 606: {
        static const KenStateAnim a = {
            &spr_ken_606, 88, 104, 44, 104, 1,
            { 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 700: {
        static const KenStateAnim a = {
            &spr_ken_700, 96, 96, 48, 96, 2,
            { 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 710: {
        static const KenStateAnim a = {
            &spr_ken_710, 112, 96, 56, 96, 4,
            { 2, 3, 3, 4, 0, 0, 0, 0, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 720: {
        static const KenStateAnim a = {
            &spr_ken_720, 112, 104, 56, 104, 8,
            { 3, 3, 3, 3, 3, 3, 3, 6, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 730: {
        static const KenStateAnim a = {
            &spr_ken_730, 120, 120, 60, 120, 9,
            { 3, 3, 3, 3, 3, 3, 3, 8, 0, 0, 0, 0 }
        };
        return &a;
    }
    case 610: case 607: case 611: case 612: case 615: return ken_anim_for(100);
    case 608: case 209: case 207: case 208: return ken_anim_for(200);
    case 103: case 113: case 107: case 108: case 109: case 110: case 152: return ken_anim_for(102);
    case 154: return ken_anim_for(104);
    case 155: return ken_anim_for(105);
    case 202: case 204: case 205: return ken_anim_for(201);
    case 301: case 302: case 304: case 305: case 306:
    case 310: case 311: case 312: case 314: case 315: case 316:
    case 320: case 321: case 322: case 324: case 325: case 326:
        return ken_anim_for(300);
    case 410: case 471: case 472: return ken_anim_for(420);
    case 502: case 503: case 506: case 511: case 512:
    case 551: case 552: case 570: return ken_anim_for(550);
    case 800: case 801: case 802: case 803: return ken_anim_for(102);
    default: return ken_anim_for(100);
    }
}
#endif
