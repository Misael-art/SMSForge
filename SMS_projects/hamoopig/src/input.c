#include "engine.h"

/* Uma leitura de 16 bits cobre PORT_A e PORT_B. Status pressed/hold/released
 * e derivado por comparacao enquanto o valor ainda e 16 bits (M01 MSSF2T). */

static unsigned int s_prev;
static unsigned char s_status[2][INP_COUNT];

static unsigned int mask_of(unsigned char who, unsigned char btn)
{
    static const unsigned int a_mask[INP_COUNT] = {
        PORT_A_KEY_UP, PORT_A_KEY_DOWN, PORT_A_KEY_LEFT, PORT_A_KEY_RIGHT,
        PORT_A_KEY_1, PORT_A_KEY_2
    };
    static const unsigned int b_mask[INP_COUNT] = {
        PORT_B_KEY_UP, PORT_B_KEY_DOWN, PORT_B_KEY_LEFT, PORT_B_KEY_RIGHT,
        PORT_B_KEY_1, PORT_B_KEY_2
    };
    return who ? b_mask[btn] : a_mask[btn];
}

void input_tick(unsigned int raw)
{
    unsigned char who, btn;
    unsigned int m, now, was;

    for (who = 0; who < 2; who++) {
        for (btn = 0; btn < INP_COUNT; btn++) {
            m = mask_of(who, btn);
            now = raw & m;
            was = s_prev & m;
            if (!now) {
                s_status[who][btn] = was ? KEY_RELEASED : KEY_FREE;
            } else if (!was) {
                s_status[who][btn] = KEY_PRESSED;
            } else {
                s_status[who][btn] = KEY_HOLD;
            }
            P[who].keys[btn] = s_status[who][btn];
        }
    }
    s_prev = raw;
}

unsigned char input_status(unsigned char who, unsigned char btn)
{
    return s_status[who][btn];
}

unsigned char input_pressed(unsigned char who, unsigned char btn)
{
    return (unsigned char)(s_status[who][btn] == KEY_PRESSED);
}

unsigned char input_held(unsigned char who, unsigned char btn)
{
    unsigned char s = s_status[who][btn];
    return (unsigned char)(s == KEY_PRESSED || s == KEY_HOLD);
}
