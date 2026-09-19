#ifndef PLAYER_H
#define PLAYER_H

#include "globals.h"

void PLAYER_STATE(u8 Player, u16 State);
void PLAYER_STATE_KEN(u8 Player, u16 State);
void PLAYER_STATE_MUSGO(u8 Player, u16 State);
Sprite* PLAYER_SET_SPRITE(u8 Player, const SpriteDefinition *definition,
                          s16 x, s16 y, u16 attribut, u16 flags);
void FUNCAO_PLAY_SND(u8 Player, u16 State);
void FUNCAO_DEPTH(u8 Player);
void FUNCAO_UPDATE_LIFESP(u8 Player, u8 EnergyType, s8 Value);
bool FUNCAO_SPEND_SPECIAL(u8 Player);
void FUNCAO_REGISTER_HIT(u8 Player);
void FUNCAO_CONSUME_COMBAT_EVENTS(void);
void FUNCAO_UPDATE_HIT_COMBOS(void);
void FUNCAO_APPLY_FIGHTER_PALETTE(u8 Player);
void FUNCAO_CYCLE_FIGHTER(u8 Player);

#endif // PLAYER_H
