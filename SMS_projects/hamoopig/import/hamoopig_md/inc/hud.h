#ifndef HUD_H
#define HUD_H

#include "globals.h"

void FUNCAO_RELOGIO();
void FUNCAO_BARRAS_DE_ENERGIA();
void hud_window_load(void);
void hud_window_init(void);
void hud_window_update(void);
void hud_window_off(void);
void hud_message_update(void);
void hud_message_clear(void);

#endif // HUD_H
