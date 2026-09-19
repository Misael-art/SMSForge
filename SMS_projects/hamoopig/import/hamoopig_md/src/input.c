#include <genesis.h>
#include "input.h"
#include "globals.h"
#include "scene.h"
#include "player.h"

void FUNCAO_INPUT_SYSTEM()
{
    static u16 currentJoyState[2] = {0};
    static u16 previousJoyState[2] = {0};
	u16 buttons[] = {BUTTON_UP, BUTTON_DOWN, BUTTON_LEFT, BUTTON_RIGHT, BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_X, BUTTON_Y, BUTTON_Z, BUTTON_START, BUTTON_MODE};
	
    for (int player = 0; player < 2; player++) {
        previousJoyState[player] = currentJoyState[player];
		if(player==0){ currentJoyState[player] = JOY_readJoypad(JOY_1); }
		else if(player==1){ currentJoyState[player] = JOY_readJoypad(JOY_2); }
		
        int numButtons = sizeof(buttons) / sizeof(buttons[0]);

		/* P[] is 1-based for gameplay (P[1]=player 1, P[2]=player 2); P[0] is
		   unused.  The per-button array must land in the same slot as the
		   named *_status fields, otherwise the input flushes in
		   FUNCAO_SELECT_INIT/FUNCAO_INICIALIZACAO address the wrong player. */
		const int slot = player + 1;

        for (int i = 0; i < numButtons; i++) {
            u16 button = buttons[i];

            if (!(currentJoyState[player] & button)) {
                P[slot].key_JOY_status[i] = KEY_FREE;
            } else if ((currentJoyState[player] & button) && !(previousJoyState[player] & button)) {
                P[slot].key_JOY_status[i] = KEY_PRESSED;
            } else if (currentJoyState[player] & button) {
                P[slot].key_JOY_status[i] = KEY_HOLD;
            } else if (!(currentJoyState[player] & button) && (previousJoyState[player] & button)) {
                P[slot].key_JOY_status[i] = KEY_RELEASED;
            }

			if(i==numButtons-1) //end of loop, assignments
			{
				P[slot].key_JOY_UP_status    = P[slot].key_JOY_status[ 0];
				P[slot].key_JOY_DOWN_status  = P[slot].key_JOY_status[ 1];
				P[slot].key_JOY_LEFT_status  = P[slot].key_JOY_status[ 2];
				P[slot].key_JOY_RIGHT_status = P[slot].key_JOY_status[ 3];
				P[slot].key_JOY_A_status     = P[slot].key_JOY_status[ 4];
				P[slot].key_JOY_B_status     = P[slot].key_JOY_status[ 5];
				P[slot].key_JOY_C_status     = P[slot].key_JOY_status[ 6];
				P[slot].key_JOY_X_status     = P[slot].key_JOY_status[ 7];
				P[slot].key_JOY_Y_status     = P[slot].key_JOY_status[ 8];
				P[slot].key_JOY_Z_status     = P[slot].key_JOY_status[ 9];
				P[slot].key_JOY_START_status = P[slot].key_JOY_status[10];
				P[slot].key_JOY_MODE_status  = P[slot].key_JOY_status[11];
			}
        }
    }


	//joystick P1
	u16 JOY1 = JOY_readJoypad(JOY_1);
	if(JOY1 & BUTTON_UP    ) { JOY1_UP    = TRUE; } else { JOY1_UP    = FALSE; }
	if(JOY1 & BUTTON_DOWN  ) { JOY1_DOWN  = TRUE; } else { JOY1_DOWN  = FALSE; }
	if(JOY1 & BUTTON_LEFT  ) { JOY1_LEFT  = TRUE; } else { JOY1_LEFT  = FALSE; }
	if(JOY1 & BUTTON_RIGHT ) { JOY1_RIGHT = TRUE; } else { JOY1_RIGHT = FALSE; }
	if(JOY1 & BUTTON_A     ) { JOY1_A     = TRUE; } else { JOY1_A     = FALSE; }
	if(JOY1 & BUTTON_B     ) { JOY1_B     = TRUE; } else { JOY1_B     = FALSE; }
	if(JOY1 & BUTTON_C     ) { JOY1_C     = TRUE; } else { JOY1_C     = FALSE; }
	if(JOY1 & BUTTON_X     ) { JOY1_X     = TRUE; } else { JOY1_X     = FALSE; }
	if(JOY1 & BUTTON_Y     ) { JOY1_Y     = TRUE; } else { JOY1_Y     = FALSE; }
	if(JOY1 & BUTTON_Z     ) { JOY1_Z     = TRUE; } else { JOY1_Z     = FALSE; }
	if(JOY1 & BUTTON_START ) { JOY1_START = TRUE; } else { JOY1_START = FALSE; }
	if(JOY1 & BUTTON_MODE  ) { JOY1_MODE  = TRUE; } else { JOY1_MODE  = FALSE; }
	
	//joystick P2
	u16 JOY2 = JOY_readJoypad(JOY_2);
	if(JOY2 & BUTTON_UP    ) { JOY2_UP    = TRUE; } else { JOY2_UP    = FALSE; }
	if(JOY2 & BUTTON_DOWN  ) { JOY2_DOWN  = TRUE; } else { JOY2_DOWN  = FALSE; }
	if(JOY2 & BUTTON_LEFT  ) { JOY2_LEFT  = TRUE; } else { JOY2_LEFT  = FALSE; }
	if(JOY2 & BUTTON_RIGHT ) { JOY2_RIGHT = TRUE; } else { JOY2_RIGHT = FALSE; }
	if(JOY2 & BUTTON_A     ) { JOY2_A     = TRUE; } else { JOY2_A     = FALSE; }
	if(JOY2 & BUTTON_B     ) { JOY2_B     = TRUE; } else { JOY2_B     = FALSE; }
	if(JOY2 & BUTTON_C     ) { JOY2_C     = TRUE; } else { JOY2_C     = FALSE; }
	if(JOY2 & BUTTON_X     ) { JOY2_X     = TRUE; } else { JOY2_X     = FALSE; }
	if(JOY2 & BUTTON_Y     ) { JOY2_Y     = TRUE; } else { JOY2_Y     = FALSE; }
	if(JOY2 & BUTTON_Z     ) { JOY2_Z     = TRUE; } else { JOY2_Z     = FALSE; }
	if(JOY2 & BUTTON_START ) { JOY2_START = TRUE; } else { JOY2_START = FALSE; }
	if(JOY2 & BUTTON_MODE  ) { JOY2_MODE  = TRUE; } else { JOY2_MODE  = FALSE; }
	
	if(gPodeMover==0)
	{
		JOY1_UP    = FALSE; JOY2_UP    = FALSE;
		JOY1_DOWN  = FALSE; JOY2_DOWN  = FALSE;
		JOY1_LEFT  = FALSE; JOY2_LEFT  = FALSE;
		JOY1_RIGHT = FALSE; JOY2_RIGHT = FALSE;
		JOY1_B     = FALSE; JOY2_B     = FALSE;
		JOY1_C     = FALSE; JOY2_C     = FALSE;
		JOY1_X     = FALSE; JOY2_X     = FALSE;
		JOY1_Y     = FALSE; JOY2_Y     = FALSE;
		JOY1_Z     = FALSE; JOY2_Z     = FALSE;
		JOY1_MODE  = FALSE; JOY2_MODE  = FALSE;
		/* The fight freezes movement during KO/round transitions, but room 11
		   still owns A/START as menu input. */
		if(gRoom != SCENE_AFTER_MATCH)
		{
			JOY1_A = FALSE; JOY2_A = FALSE;
			JOY1_START = FALSE; JOY2_START = FALSE;
		}
	}
	
	//---P1
	
	if (JOY1_UP) {
	if (key_JOY1_UP_pressed==1 && key_JOY1_UP_hold==0) { key_JOY1_UP_hold=1; key_JOY1_UP_pressed=0; }
	if (key_JOY1_UP_pressed==0 && key_JOY1_UP_hold==0) { key_JOY1_UP_pressed=1; }}
	if (!JOY1_UP) {
	if (key_JOY1_UP_released==1) { key_JOY1_UP_released=0; key_JOY1_UP_pressed=0; key_JOY1_UP_hold=0; }
	if (key_JOY1_UP_pressed>0 || key_JOY1_UP_hold>0) {key_JOY1_UP_released=1;}}
	if (key_JOY1_UP_pressed==0 && key_JOY1_UP_hold==0 && key_JOY1_UP_released==0){ P[1].key_JOY_UP_status=0; }
	if (key_JOY1_UP_pressed  ==1 ) { P[1].key_JOY_UP_status=1; }
	if (key_JOY1_UP_hold     ==1 ) { P[1].key_JOY_UP_status=2; }
	if (key_JOY1_UP_released ==1 ) { P[1].key_JOY_UP_status=3; }
	
	if (JOY1_DOWN) {
	if (key_JOY1_DOWN_pressed==1 && key_JOY1_DOWN_hold==0) { key_JOY1_DOWN_hold=1; key_JOY1_DOWN_pressed=0; }
	if (key_JOY1_DOWN_pressed==0 && key_JOY1_DOWN_hold==0) { key_JOY1_DOWN_pressed=1; }}
	if (!JOY1_DOWN) {
	if (key_JOY1_DOWN_released==1) { key_JOY1_DOWN_released=0; key_JOY1_DOWN_pressed=0; key_JOY1_DOWN_hold=0; }
	if (key_JOY1_DOWN_pressed>0 || key_JOY1_DOWN_hold>0) {key_JOY1_DOWN_released=1;}}
	if (key_JOY1_DOWN_pressed==0 && key_JOY1_DOWN_hold==0 && key_JOY1_DOWN_released==0){ P[1].key_JOY_DOWN_status=0; }
	if (key_JOY1_DOWN_pressed  ==1 ) { P[1].key_JOY_DOWN_status=1; }
	if (key_JOY1_DOWN_hold     ==1 ) { P[1].key_JOY_DOWN_status=2; }
	if (key_JOY1_DOWN_released ==1 ) { P[1].key_JOY_DOWN_status=3; }
	
	if (JOY1_LEFT) {
	if (key_JOY1_LEFT_pressed==1 && key_JOY1_LEFT_hold==0) { key_JOY1_LEFT_hold=1; key_JOY1_LEFT_pressed=0; }
	if (key_JOY1_LEFT_pressed==0 && key_JOY1_LEFT_hold==0) { key_JOY1_LEFT_pressed=1; }}
	if (!JOY1_LEFT) {
	if (key_JOY1_LEFT_released==1) { key_JOY1_LEFT_released=0; key_JOY1_LEFT_pressed=0; key_JOY1_LEFT_hold=0; }
	if (key_JOY1_LEFT_pressed>0 || key_JOY1_LEFT_hold>0) {key_JOY1_LEFT_released=1;}}
	if (key_JOY1_LEFT_pressed==0 && key_JOY1_LEFT_hold==0 && key_JOY1_LEFT_released==0){ P[1].key_JOY_LEFT_status=0; }
	if (key_JOY1_LEFT_pressed  ==1 ) { P[1].key_JOY_LEFT_status=1; }
	if (key_JOY1_LEFT_hold     ==1 ) { P[1].key_JOY_LEFT_status=2; }
	if (key_JOY1_LEFT_released ==1 ) { P[1].key_JOY_LEFT_status=3; }
	
	if (JOY1_RIGHT) {
	if (key_JOY1_RIGHT_pressed==1 && key_JOY1_RIGHT_hold==0) { key_JOY1_RIGHT_hold=1; key_JOY1_RIGHT_pressed=0; }
	if (key_JOY1_RIGHT_pressed==0 && key_JOY1_RIGHT_hold==0) { key_JOY1_RIGHT_pressed=1; }}
	if (!JOY1_RIGHT) {
	if (key_JOY1_RIGHT_released==1) { key_JOY1_RIGHT_released=0; key_JOY1_RIGHT_pressed=0; key_JOY1_RIGHT_hold=0; }
	if (key_JOY1_RIGHT_pressed>0 || key_JOY1_RIGHT_hold>0) {key_JOY1_RIGHT_released=1;}}
	if (key_JOY1_RIGHT_pressed==0 && key_JOY1_RIGHT_hold==0 && key_JOY1_RIGHT_released==0){ P[1].key_JOY_RIGHT_status=0; }
	if (key_JOY1_RIGHT_pressed  ==1 ) { P[1].key_JOY_RIGHT_status=1; }
	if (key_JOY1_RIGHT_hold     ==1 ) { P[1].key_JOY_RIGHT_status=2; }
	if (key_JOY1_RIGHT_released ==1 ) { P[1].key_JOY_RIGHT_status=3; }
	
	if (JOY1_A) {
	if (key_JOY1_A_pressed==1 && key_JOY1_A_hold==0) { key_JOY1_A_hold=1; key_JOY1_A_pressed=0; }
	if (key_JOY1_A_pressed==0 && key_JOY1_A_hold==0) { key_JOY1_A_pressed=1; }}
	if (!JOY1_A) {
	if (key_JOY1_A_released==1) { key_JOY1_A_released=0; key_JOY1_A_pressed=0; key_JOY1_A_hold=0; }
	if (key_JOY1_A_pressed>0 || key_JOY1_A_hold>0) {key_JOY1_A_released=1;}}
	if (key_JOY1_A_pressed==0 && key_JOY1_A_hold==0 && key_JOY1_A_released==0){ P[1].key_JOY_A_status=0; }
	if (key_JOY1_A_pressed  ==1 ) { P[1].key_JOY_A_status=1; }
	if (key_JOY1_A_hold     ==1 ) { P[1].key_JOY_A_status=2; }
	if (key_JOY1_A_released ==1 ) { P[1].key_JOY_A_status=3; }
	
	if (JOY1_B) {
	if (key_JOY1_B_pressed==1 && key_JOY1_B_hold==0) { key_JOY1_B_hold=1; key_JOY1_B_pressed=0; }
	if (key_JOY1_B_pressed==0 && key_JOY1_B_hold==0) { key_JOY1_B_pressed=1; }}
	if (!JOY1_B) {
	if (key_JOY1_B_released==1) { key_JOY1_B_released=0; key_JOY1_B_pressed=0; key_JOY1_B_hold=0; }
	if (key_JOY1_B_pressed>0 || key_JOY1_B_hold>0) {key_JOY1_B_released=1;}}
	if (key_JOY1_B_pressed==0 && key_JOY1_B_hold==0 && key_JOY1_B_released==0){ P[1].key_JOY_B_status=0; }
	if (key_JOY1_B_pressed  ==1 ) { P[1].key_JOY_B_status=1; }
	if (key_JOY1_B_hold     ==1 ) { P[1].key_JOY_B_status=2; }
	if (key_JOY1_B_released ==1 ) { P[1].key_JOY_B_status=3; }
	
	if (JOY1_C) {
	if (key_JOY1_C_pressed==1 && key_JOY1_C_hold==0) { key_JOY1_C_hold=1; key_JOY1_C_pressed=0; }
	if (key_JOY1_C_pressed==0 && key_JOY1_C_hold==0) { key_JOY1_C_pressed=1; }}
	if (!JOY1_C) {
	if (key_JOY1_C_released==1) { key_JOY1_C_released=0; key_JOY1_C_pressed=0; key_JOY1_C_hold=0; }
	if (key_JOY1_C_pressed>0 || key_JOY1_C_hold>0) {key_JOY1_C_released=1;}}
	if (key_JOY1_C_pressed==0 && key_JOY1_C_hold==0 && key_JOY1_C_released==0){ P[1].key_JOY_C_status=0; }
	if (key_JOY1_C_pressed  ==1 ) { P[1].key_JOY_C_status=1; }
	if (key_JOY1_C_hold     ==1 ) { P[1].key_JOY_C_status=2; }
	if (key_JOY1_C_released ==1 ) { P[1].key_JOY_C_status=3; }
	
	if (JOY1_X) {
	if (key_JOY1_X_pressed==1 && key_JOY1_X_hold==0) { key_JOY1_X_hold=1; key_JOY1_X_pressed=0; }
	if (key_JOY1_X_pressed==0 && key_JOY1_X_hold==0) { key_JOY1_X_pressed=1; }}
	if (!JOY1_X) {
	if (key_JOY1_X_released==1) { key_JOY1_X_released=0; key_JOY1_X_pressed=0; key_JOY1_X_hold=0; }
	if (key_JOY1_X_pressed>0 || key_JOY1_X_hold>0) {key_JOY1_X_released=1;}}
	if (key_JOY1_X_pressed==0 && key_JOY1_X_hold==0 && key_JOY1_X_released==0){ P[1].key_JOY_X_status=0; }
	if (key_JOY1_X_pressed  ==1 ) { P[1].key_JOY_X_status=1; }
	if (key_JOY1_X_hold     ==1 ) { P[1].key_JOY_X_status=2; }
	if (key_JOY1_X_released ==1 ) { P[1].key_JOY_X_status=3; }
	
	if (JOY1_Y) {
	if (key_JOY1_Y_pressed==1 && key_JOY1_Y_hold==0) { key_JOY1_Y_hold=1; key_JOY1_Y_pressed=0; }
	if (key_JOY1_Y_pressed==0 && key_JOY1_Y_hold==0) { key_JOY1_Y_pressed=1; }}
	if (!JOY1_Y) {
	if (key_JOY1_Y_released==1) { key_JOY1_Y_released=0; key_JOY1_Y_pressed=0; key_JOY1_Y_hold=0; }
	if (key_JOY1_Y_pressed>0 || key_JOY1_Y_hold>0) {key_JOY1_Y_released=1;}}
	if (key_JOY1_Y_pressed==0 && key_JOY1_Y_hold==0 && key_JOY1_Y_released==0){ P[1].key_JOY_Y_status=0; }
	if (key_JOY1_Y_pressed  ==1 ) { P[1].key_JOY_Y_status=1; }
	if (key_JOY1_Y_hold     ==1 ) { P[1].key_JOY_Y_status=2; }
	if (key_JOY1_Y_released ==1 ) { P[1].key_JOY_Y_status=3; }
	
	if (JOY1_Z) {
	if (key_JOY1_Z_pressed==1 && key_JOY1_Z_hold==0) { key_JOY1_Z_hold=1; key_JOY1_Z_pressed=0; }
	if (key_JOY1_Z_pressed==0 && key_JOY1_Z_hold==0) { key_JOY1_Z_pressed=1; }}
	if (!JOY1_Z) {
	if (key_JOY1_Z_released==1) { key_JOY1_Z_released=0; key_JOY1_Z_pressed=0; key_JOY1_Z_hold=0; }
	if (key_JOY1_Z_pressed>0 || key_JOY1_Z_hold>0) {key_JOY1_Z_released=1;}}
	if (key_JOY1_Z_pressed==0 && key_JOY1_Z_hold==0 && key_JOY1_Z_released==0){ P[1].key_JOY_Z_status=0; }
	if (key_JOY1_Z_pressed  ==1 ) { P[1].key_JOY_Z_status=1; }
	if (key_JOY1_Z_hold     ==1 ) { P[1].key_JOY_Z_status=2; }
	if (key_JOY1_Z_released ==1 ) { P[1].key_JOY_Z_status=3; }
	
	if (JOY1_START) {
	if (key_JOY1_START_pressed==1 && key_JOY1_START_hold==0) { key_JOY1_START_hold=1; key_JOY1_START_pressed=0; }
	if (key_JOY1_START_pressed==0 && key_JOY1_START_hold==0) { key_JOY1_START_pressed=1; }}
	if (!JOY1_START) {
	if (key_JOY1_START_released==1) { key_JOY1_START_released=0; key_JOY1_START_pressed=0; key_JOY1_START_hold=0; }
	if (key_JOY1_START_pressed>0 || key_JOY1_START_hold>0) {key_JOY1_START_released=1;}}
	if (key_JOY1_START_pressed==0 && key_JOY1_START_hold==0 && key_JOY1_START_released==0){ P[1].key_JOY_START_status=0; }
	if (key_JOY1_START_pressed  ==1 ) { P[1].key_JOY_START_status=1; }
	if (key_JOY1_START_hold     ==1 ) { P[1].key_JOY_START_status=2; }
	if (key_JOY1_START_released ==1 ) { P[1].key_JOY_START_status=3; }
	
	if (JOY1_MODE) {
	if (key_JOY1_MODE_pressed==1 && key_JOY1_MODE_hold==0) { key_JOY1_MODE_hold=1; key_JOY1_MODE_pressed=0; }
	if (key_JOY1_MODE_pressed==0 && key_JOY1_MODE_hold==0) { key_JOY1_MODE_pressed=1; }}
	if (!JOY1_MODE) {
	if (key_JOY1_MODE_released==1) { key_JOY1_MODE_released=0; key_JOY1_MODE_pressed=0; key_JOY1_MODE_hold=0; }
	if (key_JOY1_MODE_pressed>0 || key_JOY1_MODE_hold>0) {key_JOY1_MODE_released=1;}}
	if (key_JOY1_MODE_pressed==0 && key_JOY1_MODE_hold==0 && key_JOY1_MODE_released==0){ P[1].key_JOY_MODE_status=0; }
	if (key_JOY1_MODE_pressed  ==1 ) { P[1].key_JOY_MODE_status=1; }
	if (key_JOY1_MODE_hold     ==1 ) { P[1].key_JOY_MODE_status=2; }
	if (key_JOY1_MODE_released ==1 ) { P[1].key_JOY_MODE_status=3; }
	
	//---P2
	
	if (JOY2_UP) {
	if (key_JOY2_UP_pressed==1 && key_JOY2_UP_hold==0) { key_JOY2_UP_hold=1; key_JOY2_UP_pressed=0; }
	if (key_JOY2_UP_pressed==0 && key_JOY2_UP_hold==0) { key_JOY2_UP_pressed=1; }}
	if (!JOY2_UP) {
	if (key_JOY2_UP_released==1) { key_JOY2_UP_released=0; key_JOY2_UP_pressed=0; key_JOY2_UP_hold=0; }
	if (key_JOY2_UP_pressed>0 || key_JOY2_UP_hold>0) {key_JOY2_UP_released=1;}}
	if (key_JOY2_UP_pressed==0 && key_JOY2_UP_hold==0 && key_JOY2_UP_released==0){ P[2].key_JOY_UP_status=0; }
	if (key_JOY2_UP_pressed  ==1 ) { P[2].key_JOY_UP_status=1; }
	if (key_JOY2_UP_hold     ==1 ) { P[2].key_JOY_UP_status=2; }
	if (key_JOY2_UP_released ==1 ) { P[2].key_JOY_UP_status=3; }
	
	if (JOY2_DOWN) {
	if (key_JOY2_DOWN_pressed==1 && key_JOY2_DOWN_hold==0) { key_JOY2_DOWN_hold=1; key_JOY2_DOWN_pressed=0; }
	if (key_JOY2_DOWN_pressed==0 && key_JOY2_DOWN_hold==0) { key_JOY2_DOWN_pressed=1; }}
	if (!JOY2_DOWN) {
	if (key_JOY2_DOWN_released==1) { key_JOY2_DOWN_released=0; key_JOY2_DOWN_pressed=0; key_JOY2_DOWN_hold=0; }
	if (key_JOY2_DOWN_pressed>0 || key_JOY2_DOWN_hold>0) {key_JOY2_DOWN_released=1;}}
	if (key_JOY2_DOWN_pressed==0 && key_JOY2_DOWN_hold==0 && key_JOY2_DOWN_released==0){ P[2].key_JOY_DOWN_status=0; }
	if (key_JOY2_DOWN_pressed  ==1 ) { P[2].key_JOY_DOWN_status=1; }
	if (key_JOY2_DOWN_hold     ==1 ) { P[2].key_JOY_DOWN_status=2; }
	if (key_JOY2_DOWN_released ==1 ) { P[2].key_JOY_DOWN_status=3; }
	
	if (JOY2_LEFT) {
	if (key_JOY2_LEFT_pressed==1 && key_JOY2_LEFT_hold==0) { key_JOY2_LEFT_hold=1; key_JOY2_LEFT_pressed=0; }
	if (key_JOY2_LEFT_pressed==0 && key_JOY2_LEFT_hold==0) { key_JOY2_LEFT_pressed=1; }}
	if (!JOY2_LEFT) {
	if (key_JOY2_LEFT_released==1) { key_JOY2_LEFT_released=0; key_JOY2_LEFT_pressed=0; key_JOY2_LEFT_hold=0; }
	if (key_JOY2_LEFT_pressed>0 || key_JOY2_LEFT_hold>0) {key_JOY2_LEFT_released=1;}}
	if (key_JOY2_LEFT_pressed==0 && key_JOY2_LEFT_hold==0 && key_JOY2_LEFT_released==0){ P[2].key_JOY_LEFT_status=0; }
	if (key_JOY2_LEFT_pressed  ==1 ) { P[2].key_JOY_LEFT_status=1; }
	if (key_JOY2_LEFT_hold     ==1 ) { P[2].key_JOY_LEFT_status=2; }
	if (key_JOY2_LEFT_released ==1 ) { P[2].key_JOY_LEFT_status=3; }
	
	if (JOY2_RIGHT) {
	if (key_JOY2_RIGHT_pressed==1 && key_JOY2_RIGHT_hold==0) { key_JOY2_RIGHT_hold=1; key_JOY2_RIGHT_pressed=0; }
	if (key_JOY2_RIGHT_pressed==0 && key_JOY2_RIGHT_hold==0) { key_JOY2_RIGHT_pressed=1; }}
	if (!JOY2_RIGHT) {
	if (key_JOY2_RIGHT_released==1) { key_JOY2_RIGHT_released=0; key_JOY2_RIGHT_pressed=0; key_JOY2_RIGHT_hold=0; }
	if (key_JOY2_RIGHT_pressed>0 || key_JOY2_RIGHT_hold>0) {key_JOY2_RIGHT_released=1;}}
	if (key_JOY2_RIGHT_pressed==0 && key_JOY2_RIGHT_hold==0 && key_JOY2_RIGHT_released==0){ P[2].key_JOY_RIGHT_status=0; }
	if (key_JOY2_RIGHT_pressed  ==1 ) { P[2].key_JOY_RIGHT_status=1; }
	if (key_JOY2_RIGHT_hold     ==1 ) { P[2].key_JOY_RIGHT_status=2; }
	if (key_JOY2_RIGHT_released ==1 ) { P[2].key_JOY_RIGHT_status=3; }
	
	if (JOY2_A) {
	if (key_JOY2_A_pressed==1 && key_JOY2_A_hold==0) { key_JOY2_A_hold=1; key_JOY2_A_pressed=0; }
	if (key_JOY2_A_pressed==0 && key_JOY2_A_hold==0) { key_JOY2_A_pressed=1; }}
	if (!JOY2_A) {
	if (key_JOY2_A_released==1) { key_JOY2_A_released=0; key_JOY2_A_pressed=0; key_JOY2_A_hold=0; }
	if (key_JOY2_A_pressed>0 || key_JOY2_A_hold>0) {key_JOY2_A_released=1;}}
	if (key_JOY2_A_pressed==0 && key_JOY2_A_hold==0 && key_JOY2_A_released==0){ P[2].key_JOY_A_status=0; }
	if (key_JOY2_A_pressed  ==1 ) { P[2].key_JOY_A_status=1; }
	if (key_JOY2_A_hold     ==1 ) { P[2].key_JOY_A_status=2; }
	if (key_JOY2_A_released ==1 ) { P[2].key_JOY_A_status=3; }
	
	if (JOY2_B) {
	if (key_JOY2_B_pressed==1 && key_JOY2_B_hold==0) { key_JOY2_B_hold=1; key_JOY2_B_pressed=0; }
	if (key_JOY2_B_pressed==0 && key_JOY2_B_hold==0) { key_JOY2_B_pressed=1; }}
	if (!JOY2_B) {
	if (key_JOY2_B_released==1) { key_JOY2_B_released=0; key_JOY2_B_pressed=0; key_JOY2_B_hold=0; }
	if (key_JOY2_B_pressed>0 || key_JOY2_B_hold>0) {key_JOY2_B_released=1;}}
	if (key_JOY2_B_pressed==0 && key_JOY2_B_hold==0 && key_JOY2_B_released==0){ P[2].key_JOY_B_status=0; }
	if (key_JOY2_B_pressed  ==1 ) { P[2].key_JOY_B_status=1; }
	if (key_JOY2_B_hold     ==1 ) { P[2].key_JOY_B_status=2; }
	if (key_JOY2_B_released ==1 ) { P[2].key_JOY_B_status=3; }
	
	if (JOY2_C) {
	if (key_JOY2_C_pressed==1 && key_JOY2_C_hold==0) { key_JOY2_C_hold=1; key_JOY2_C_pressed=0; }
	if (key_JOY2_C_pressed==0 && key_JOY2_C_hold==0) { key_JOY2_C_pressed=1; }}
	if (!JOY2_C) {
	if (key_JOY2_C_released==1) { key_JOY2_C_released=0; key_JOY2_C_pressed=0; key_JOY2_C_hold=0; }
	if (key_JOY2_C_pressed>0 || key_JOY2_C_hold>0) {key_JOY2_C_released=1;}}
	if (key_JOY2_C_pressed==0 && key_JOY2_C_hold==0 && key_JOY2_C_released==0){ P[2].key_JOY_C_status=0; }
	if (key_JOY2_C_pressed  ==1 ) { P[2].key_JOY_C_status=1; }
	if (key_JOY2_C_hold     ==1 ) { P[2].key_JOY_C_status=2; }
	if (key_JOY2_C_released ==1 ) { P[2].key_JOY_C_status=3; }
	
	if (JOY2_X) {
	if (key_JOY2_X_pressed==1 && key_JOY2_X_hold==0) { key_JOY2_X_hold=1; key_JOY2_X_pressed=0; }
	if (key_JOY2_X_pressed==0 && key_JOY2_X_hold==0) { key_JOY2_X_pressed=1; }}
	if (!JOY2_X) {
	if (key_JOY2_X_released==1) { key_JOY2_X_released=0; key_JOY2_X_pressed=0; key_JOY2_X_hold=0; }
	if (key_JOY2_X_pressed>0 || key_JOY2_X_hold>0) {key_JOY2_X_released=1;}}
	if (key_JOY2_X_pressed==0 && key_JOY2_X_hold==0 && key_JOY2_X_released==0){ P[2].key_JOY_X_status=0; }
	if (key_JOY2_X_pressed  ==1 ) { P[2].key_JOY_X_status=1; }
	if (key_JOY2_X_hold     ==1 ) { P[2].key_JOY_X_status=2; }
	if (key_JOY2_X_released ==1 ) { P[2].key_JOY_X_status=3; }
	
	if (JOY2_Y) {
	if (key_JOY2_Y_pressed==1 && key_JOY2_Y_hold==0) { key_JOY2_Y_hold=1; key_JOY2_Y_pressed=0; }
	if (key_JOY2_Y_pressed==0 && key_JOY2_Y_hold==0) { key_JOY2_Y_pressed=1; }}
	if (!JOY2_Y) {
	if (key_JOY2_Y_released==1) { key_JOY2_Y_released=0; key_JOY2_Y_pressed=0; key_JOY2_Y_hold=0; }
	if (key_JOY2_Y_pressed>0 || key_JOY2_Y_hold>0) {key_JOY2_Y_released=1;}}
	if (key_JOY2_Y_pressed==0 && key_JOY2_Y_hold==0 && key_JOY2_Y_released==0){ P[2].key_JOY_Y_status=0; }
	if (key_JOY2_Y_pressed  ==1 ) { P[2].key_JOY_Y_status=1; }
	if (key_JOY2_Y_hold     ==1 ) { P[2].key_JOY_Y_status=2; }
	if (key_JOY2_Y_released ==1 ) { P[2].key_JOY_Y_status=3; }
	
	if (JOY2_Z) {
	if (key_JOY2_Z_pressed==1 && key_JOY2_Z_hold==0) { key_JOY2_Z_hold=1; key_JOY2_Z_pressed=0; }
	if (key_JOY2_Z_pressed==0 && key_JOY2_Z_hold==0) { key_JOY2_Z_pressed=1; }}
	if (!JOY2_Z) {
	if (key_JOY2_Z_released==1) { key_JOY2_Z_released=0; key_JOY2_Z_pressed=0; key_JOY2_Z_hold=0; }
	if (key_JOY2_Z_pressed>0 || key_JOY2_Z_hold>0) {key_JOY2_Z_released=1;}}
	if (key_JOY2_Z_pressed==0 && key_JOY2_Z_hold==0 && key_JOY2_Z_released==0){ P[2].key_JOY_Z_status=0; }
	if (key_JOY2_Z_pressed  ==1 ) { P[2].key_JOY_Z_status=1; }
	if (key_JOY2_Z_hold     ==1 ) { P[2].key_JOY_Z_status=2; }
	if (key_JOY2_Z_released ==1 ) { P[2].key_JOY_Z_status=3; }
	
	if (JOY2_START) {
	if (key_JOY2_START_pressed==1 && key_JOY2_START_hold==0) { key_JOY2_START_hold=1; key_JOY2_START_pressed=0; }
	if (key_JOY2_START_pressed==0 && key_JOY2_START_hold==0) { key_JOY2_START_pressed=1; }}
	if (!JOY2_START) {
	if (key_JOY2_START_released==1) { key_JOY2_START_released=0; key_JOY2_START_pressed=0; key_JOY2_START_hold=0; }
	if (key_JOY2_START_pressed>0 || key_JOY2_START_hold>0) {key_JOY2_START_released=1;}}
	if (key_JOY2_START_pressed==0 && key_JOY2_START_hold==0 && key_JOY2_START_released==0){ P[2].key_JOY_START_status=0; }
	if (key_JOY2_START_pressed  ==1 ) { P[2].key_JOY_START_status=1; }
	if (key_JOY2_START_hold     ==1 ) { P[2].key_JOY_START_status=2; }
	if (key_JOY2_START_released ==1 ) { P[2].key_JOY_START_status=3; }
	
	if (JOY2_MODE) {
	if (key_JOY2_MODE_pressed==1 && key_JOY2_MODE_hold==0) { key_JOY2_MODE_hold=1; key_JOY2_MODE_pressed=0; }
	if (key_JOY2_MODE_pressed==0 && key_JOY2_MODE_hold==0) { key_JOY2_MODE_pressed=1; }}
	if (!JOY2_MODE) {
	if (key_JOY2_MODE_released==1) { key_JOY2_MODE_released=0; key_JOY2_MODE_pressed=0; key_JOY2_MODE_hold=0; }
	if (key_JOY2_MODE_pressed>0 || key_JOY2_MODE_hold>0) {key_JOY2_MODE_released=1;}}
	if (key_JOY2_MODE_pressed==0 && key_JOY2_MODE_hold==0 && key_JOY2_MODE_released==0){ P[2].key_JOY_MODE_status=0; }
	if (key_JOY2_MODE_pressed  ==1 ) { P[2].key_JOY_MODE_status=1; }
	if (key_JOY2_MODE_hold     ==1 ) { P[2].key_JOY_MODE_status=2; }
	if (key_JOY2_MODE_released ==1 ) { P[2].key_JOY_MODE_status=3; }
	
	//---InputTimerCountDown; InputArray
	u8 dir=0;
	
	if(P[1].key_JOY_UP_status   ==1){ P[1].joyDirTimer[8]=gInputTimerCountDown+1; dir=8; }
	if(P[1].key_JOY_DOWN_status ==1){ P[1].joyDirTimer[2]=gInputTimerCountDown+1; dir=2; }
	if(P[1].key_JOY_LEFT_status ==1){ P[1].joyDirTimer[4]=gInputTimerCountDown+1; dir=4; }
	if(P[1].key_JOY_RIGHT_status==1){ P[1].joyDirTimer[6]=gInputTimerCountDown+1; dir=6; }
	
	if(dir!=0)
	{
		P[1].inputArray[4] = P[1].inputArray[3];
		P[1].inputArray[3] = P[1].inputArray[2];
		P[1].inputArray[2] = P[1].inputArray[1];
		P[1].inputArray[1] = P[1].inputArray[0];
		P[1].inputArray[0] = dir;
	}
	
	dir=0;
	
	if(P[2].key_JOY_UP_status   ==1){ P[2].joyDirTimer[8]=gInputTimerCountDown+1; dir=8; }
	if(P[2].key_JOY_DOWN_status ==1){ P[2].joyDirTimer[2]=gInputTimerCountDown+1; dir=2; }
	if(P[2].key_JOY_LEFT_status ==1){ P[2].joyDirTimer[4]=gInputTimerCountDown+1; dir=4; }
	if(P[2].key_JOY_RIGHT_status==1){ P[2].joyDirTimer[6]=gInputTimerCountDown+1; dir=6; }
	
	if(dir!=0)
	{
		P[2].inputArray[4] = P[2].inputArray[3];
		P[2].inputArray[3] = P[2].inputArray[2];
		P[2].inputArray[2] = P[2].inputArray[1];
		P[2].inputArray[1] = P[2].inputArray[0];
		P[2].inputArray[0] = dir;
	}
	
	if( P[1].joyDirTimer[8]>0 ){ P[1].joyDirTimer[8]--; }
	if( P[1].joyDirTimer[2]>0 ){ P[1].joyDirTimer[2]--; }
	if( P[1].joyDirTimer[4]>0 ){ P[1].joyDirTimer[4]--; }
	if( P[1].joyDirTimer[6]>0 ){ P[1].joyDirTimer[6]--; }
	
	if( P[2].joyDirTimer[8]>0 ){ P[2].joyDirTimer[8]--; }
	if( P[2].joyDirTimer[2]>0 ){ P[2].joyDirTimer[2]--; }
	if( P[2].joyDirTimer[4]>0 ){ P[2].joyDirTimer[4]--; }
	if( P[2].joyDirTimer[6]>0 ){ P[2].joyDirTimer[6]--; }
	//---AttackPower & AttackButton
	//P[1].attackPower =0;
	P[1].attackButton=0;
	//P[2].attackPower =0;
	P[2].attackButton=0;
	
	if(P[1].key_JOY_A_status==1){ P[1].attackPower=1; P[1].attackButton=4; }
	if(P[1].key_JOY_B_status==1){ P[1].attackPower=2; P[1].attackButton=5; }
	if(P[1].key_JOY_C_status==1){ P[1].attackPower=3; P[1].attackButton=6; }
	if(P[1].key_JOY_X_status==1){ P[1].attackPower=1; P[1].attackButton=1; }
	if(P[1].key_JOY_Y_status==1){ P[1].attackPower=2; P[1].attackButton=2; }
	if(P[1].key_JOY_Z_status==1){ P[1].attackPower=3; P[1].attackButton=3; }
	
	if(P[2].key_JOY_A_status==1){ P[2].attackPower=1; P[2].attackButton=4; }
	if(P[2].key_JOY_B_status==1){ P[2].attackPower=2; P[2].attackButton=5; }
	if(P[2].key_JOY_C_status==1){ P[2].attackPower=3; P[2].attackButton=6; }
	if(P[2].key_JOY_X_status==1){ P[2].attackPower=1; P[2].attackButton=1; }
	if(P[2].key_JOY_Y_status==1){ P[2].attackPower=2; P[2].attackButton=2; }
	if(P[2].key_JOY_Z_status==1){ P[2].attackPower=3; P[2].attackButton=3; }
	//---
	if((P[1].key_JOY_MODE_status>=1 && P[1].key_JOY_START_status==1) && gDebug==0) //Ativa o Debug com P1_MODE
	{ 
		gDebug=1; 
		P[1].key_JOY_MODE_status=0; 
		P[1].key_JOY_START_status=0; 
		SPR_setVisibility(GE[1].sprite, VISIBLE);
		SPR_setVisibility(GE[2].sprite, VISIBLE);
	} 
	if((P[1].key_JOY_MODE_status>=1 && P[1].key_JOY_START_status==1) && gDebug==1) //Desativa o Debug com P1_MODE
	{ 
		gDebug=0; 
		P[1].key_JOY_MODE_status=0; 
		P[1].key_JOY_START_status=0; 
		VDP_drawText("                              ", 1, 1);
		VDP_drawText("                              ", 1, 2);
		VDP_drawText("                              ", 1, 3);
		SPR_setPosition(Rect1BB1_Q1,-8,-8); SPR_setPosition(Rect1BB1_Q2,-8,-8); SPR_setPosition(Rect1BB1_Q3,-8,-8); SPR_setPosition(Rect1BB1_Q4,-8,-8);
		SPR_setPosition(Rect1HB1_Q1,-8,-8); SPR_setPosition(Rect1HB1_Q2,-8,-8); SPR_setPosition(Rect1HB1_Q3,-8,-8); SPR_setPosition(Rect1HB1_Q4,-8,-8);
		SPR_setPosition(Rect2BB1_Q1,-8,-8); SPR_setPosition(Rect2BB1_Q2,-8,-8); SPR_setPosition(Rect2BB1_Q3,-8,-8); SPR_setPosition(Rect2BB1_Q4,-8,-8);
		SPR_setPosition(Rect2HB1_Q1,-8,-8); SPR_setPosition(Rect2HB1_Q2,-8,-8); SPR_setPosition(Rect2HB1_Q3,-8,-8); SPR_setPosition(Rect2HB1_Q4,-8,-8);
		SPR_setVisibility(GE[1].sprite, HIDDEN);
		SPR_setVisibility(GE[2].sprite, HIDDEN);
	} 
	//---
	
	// MODE/SELECT sozinho: troca o lutador (Ryo <-> Ken). MODE+START continua debug.
	if(gRoom == SCENE_FIGHT && P[1].key_JOY_MODE_status==1 && P[1].key_JOY_START_status==0)
	{
		FUNCAO_CYCLE_FIGHTER(1);
	}
	if(gRoom == SCENE_FIGHT && P[2].key_JOY_MODE_status==1 && P[2].key_JOY_START_status==0)
	{
		FUNCAO_CYCLE_FIGHTER(2);
	}
}
