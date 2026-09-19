#ifndef FSM_H
#define FSM_H

#include "globals.h"

void FUNCAO_FSM();
void FUNCAO_FSM_HITBOXES(u8 Player);
void FUNCAO_FSM_DEFENSE(u8 player, u8 enemy);
void FUNCAO_FSM_NORMAL_ATTACKS(u8 player);
void FUNCAO_FSM_SPECIAL_ATTACKS(u8 player);
void FUNCAO_FSM_COLLISION(u8 player, u8 enemy);

#endif // FSM_H
