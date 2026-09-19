#ifndef DEBUG_H
#define DEBUG_H

#include "globals.h"

void FUNCAO_DEBUG();
void FUNCAO_CHECK_FRAME_ADVANTAGE();

/* gDebug e o liga/desliga mestre lido por main.c; aqui ele e derivado das
   flags visuais.  Chamado pelo menu de titulo e pelo menu de pausa para que
   os dois nunca discordem. */
void DEBUG_syncMaster(void);

/* Menu de pausa da luta.  main.c congela a logica e delega a UI para ca.
   `edge` e a mascara de botoes que ACABARAM de ser pressionados neste frame,
   lida crua do joypad -- durante a pausa nao se pode chamar
   FUNCAO_INPUT_SYSTEM, que teria efeitos colaterais na FSM congelada. */
void FUNCAO_DEBUG_PAUSE_ENTER(void);
void FUNCAO_DEBUG_PAUSE_UPDATE(u16 edge);
void FUNCAO_DEBUG_PAUSE_EXIT(void);

#endif // DEBUG_H
