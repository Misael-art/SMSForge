#ifndef GLOBALS_H
#define GLOBALS_H

#include "game_types.h"

//--- VARIAVEIS GLOBAIS ---//
extern u8   i;
extern u8   doubleHitStep;
extern u32  gFrames;
extern bool gPauseSystem;
extern u16  gPauseKoTimer;
extern u16  gResultTimer;
extern bool secretCharsAcvation;
extern bool gPodeMover;
extern u8   gWinnerID;
extern u8   gLoseID;
extern bool gContinueOption;
extern u8   gRoom;
extern u8   gTimerExit;
extern u8   gDescompressionExit;
extern s8   gClockTimer;
extern s8   gClockLTimer;
extern s8   gClockRTimer;
extern u8   gRound;
extern u8   gSombraStyle;
extern bool gDebug;
extern u16  gDebugFlags;     /* mascara DBG_*; so vale se gDebug==1 */
extern bool gRegionIsPal;    /* lido do VDP no boot, nao configuravel */
extern u8   gLogicRate;      /* LOGIC_RATE_60 ou LOGIC_RATE_50; so vale no perfil LEGACY */
extern u8   gTimingProfile;  /* TIMING_PROFILE_*; NORMAL e o default de entrega */
extern u8   gSubTick;        /* 0 no primeiro tick do frame de video, 1 no segundo */
extern bool gScreen240;      /* 240 linhas; so tem efeito em console PAL */
extern bool gFreeStepArmed;  /* free-step ligado: logica congelada */
extern bool gFreeStepAdvance;/* pedido de avancar exatamente 1 tick */
extern char gStr[64];
extern u16  gInd_tileset;
extern bool gASG_system;
extern u8   gPing2;
extern u8   gPing4;
extern u8   gPing10;
extern u8   gInputTimerCountDown;
extern u16  gDistancia;
extern u8   gAlturaPiso;
extern u8   gBgAnim;
extern u16  gLimiteCenarioE;
extern u16  gLimiteCenarioD;
extern u8   gravidadePadrao;
extern u8   impulsoPadrao;
extern u16  gBG_Width;
extern u16  gBG_Height;
extern u16  gScreenH;       /* altura ativa do VDP: 224 ou 240 (ver gScreen240) */
extern s16  camPosX;
extern s16  camPosXanterior;
extern s16  camPosY;
extern s16  camPosYanterior;
extern s16  gMeioDaTela;
extern s16  gScrollValues[28];
extern s16  gScrollValue;
extern u8   gBG_Choice;
extern u8   Spark1_countDown;
extern u8   Spark2_countDown;
extern s16  PetalaPX[40];
extern s16  PetalaPY[40];

extern int  frameAdvCounterP1;
extern int  lastFrameAdvCounterP1;
extern int  frameAdvCounterP2;
extern int  lastFrameAdvCounterP2;

//Char Selection Menu
extern u8   cursorP1linha;
extern u8   cursorP1coluna;
extern u8   cursorP1_ID;
extern u8   cursorP1ConfirmFX;
extern u8   cursorP1ColorChoice;
extern u8   cursorP2linha;
extern u8   cursorP2coluna;
extern u8   cursorP2_ID;
extern u8   cursorP2ConfirmFX;
extern u8   cursorP2ColorChoice;
extern u8   cursorConfirmTimer;
extern bool endP1Selection;
extern bool endP2Selection;
extern u8   stepRoom;
extern u8   mainMenuOption;
extern u8   charSelStep;

//LINKUEI INTRO
extern u16 palette[64];
extern s16 scrollvalues[224];
extern s16 scrollvaluesA[224];
extern int X;
extern int Y;
extern int px;
extern int py;
extern int x1;
extern int y1;
extern int fps;
extern int flicker;
extern int timer;
extern int framecount;

//Sprites
extern Sprite* Rect1BB1_Q1; extern Sprite* Rect1BB1_Q2; extern Sprite* Rect1BB1_Q3; extern Sprite* Rect1BB1_Q4;
extern Sprite* Rect1HB1_Q1; extern Sprite* Rect1HB1_Q2; extern Sprite* Rect1HB1_Q3; extern Sprite* Rect1HB1_Q4;
extern Sprite* Rect2BB1_Q1; extern Sprite* Rect2BB1_Q2; extern Sprite* Rect2BB1_Q3; extern Sprite* Rect2BB1_Q4;
extern Sprite* Rect2HB1_Q1; extern Sprite* Rect2HB1_Q2; extern Sprite* Rect2HB1_Q3; extern Sprite* Rect2HB1_Q4;

extern Sprite* ClockL;
extern Sprite* ClockR;
extern Sprite* HUD_Lethers;
extern Sprite* Spark[3];

//Inputs, Joystick
extern bool JOY1_UP, JOY1_DOWN, JOY1_LEFT, JOY1_RIGHT, JOY1_A, JOY1_B, JOY1_C, JOY1_X, JOY1_Y, JOY1_Z, JOY1_START, JOY1_MODE;
extern bool key_JOY1_UP_pressed, key_JOY1_UP_hold, key_JOY1_UP_released;
extern bool key_JOY1_DOWN_pressed, key_JOY1_DOWN_hold, key_JOY1_DOWN_released;
extern bool key_JOY1_LEFT_pressed, key_JOY1_LEFT_hold, key_JOY1_LEFT_released;
extern bool key_JOY1_RIGHT_pressed, key_JOY1_RIGHT_hold, key_JOY1_RIGHT_released;
extern bool key_JOY1_A_pressed, key_JOY1_A_hold, key_JOY1_A_released;
extern bool key_JOY1_B_pressed, key_JOY1_B_hold, key_JOY1_B_released;
extern bool key_JOY1_C_pressed, key_JOY1_C_hold, key_JOY1_C_released;
extern bool key_JOY1_X_pressed, key_JOY1_X_hold, key_JOY1_X_released;
extern bool key_JOY1_Y_pressed, key_JOY1_Y_hold, key_JOY1_Y_released;
extern bool key_JOY1_Z_pressed, key_JOY1_Z_hold, key_JOY1_Z_released;
extern bool key_JOY1_START_pressed, key_JOY1_START_hold, key_JOY1_START_released;
extern bool key_JOY1_MODE_pressed, key_JOY1_MODE_hold, key_JOY1_MODE_released;

extern bool JOY2_UP, JOY2_DOWN, JOY2_LEFT, JOY2_RIGHT, JOY2_A, JOY2_B, JOY2_C, JOY2_X, JOY2_Y, JOY2_Z, JOY2_START, JOY2_MODE;
extern bool key_JOY2_UP_pressed, key_JOY2_UP_hold, key_JOY2_UP_released;
extern bool key_JOY2_DOWN_pressed, key_JOY2_DOWN_hold, key_JOY2_DOWN_released;
extern bool key_JOY2_LEFT_pressed, key_JOY2_LEFT_hold, key_JOY2_LEFT_released;
extern bool key_JOY2_RIGHT_pressed, key_JOY2_RIGHT_hold, key_JOY2_RIGHT_released;
extern bool key_JOY2_A_pressed, key_JOY2_A_hold, key_JOY2_A_released;
extern bool key_JOY2_B_pressed, key_JOY2_B_hold, key_JOY2_B_released;
extern bool key_JOY2_C_pressed, key_JOY2_C_hold, key_JOY2_C_released;
extern bool key_JOY2_X_pressed, key_JOY2_X_hold, key_JOY2_X_released;
extern bool key_JOY2_Y_pressed, key_JOY2_Y_hold, key_JOY2_Y_released;
extern bool key_JOY2_Z_pressed, key_JOY2_Z_hold, key_JOY2_Z_released;
extern bool key_JOY2_START_pressed, key_JOY2_START_hold, key_JOY2_START_released;
extern bool key_JOY2_MODE_pressed, key_JOY2_MODE_hold, key_JOY2_MODE_released;

//Inteligencia Artificial PLAYER 2
extern bool IAP2;
extern u16 acaoIA;
extern u16 varIA;
extern u16 tempoIA;
extern u16 tempoIAacao;
extern u16 tempoIAataque;
extern u16 tempoIAmagia;
extern u16 esmurra;
extern u16 pulandoFrenteTras;
extern u16 defendeTempo;
extern bool ctrlResetInput;
//modo campanha
extern u8 P2fase[9];
extern const Image *BGfase[9];
extern u8 tempoMaxIAataque[9];
extern u8 tempoMinIAataque[9];
extern u8 defesaIA[9];
extern u8 fase;
extern u8 faseMAX;

extern struct PlayerDEF P[3];
extern struct GraphicElementDEF GE[25];

#endif // GLOBALS_H
