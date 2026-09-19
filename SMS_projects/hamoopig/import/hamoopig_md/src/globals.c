#include <genesis.h>
#include "globals.h"

//--- DEFINICAO DE VARIAVEIS GLOBAIS ---//
u8   i;
u8   doubleHitStep=0;
u32  gFrames = 0;
bool gPauseSystem = 0;
u16  gPauseKoTimer = 0;
u16  gResultTimer = 0;
bool secretCharsAcvation = 0;
bool gPodeMover = 1;
u8   gWinnerID;
u8   gLoseID;
bool gContinueOption;
u8   gRoom = 0; /* SCENE_OPENING */
u8   gTimerExit;
u8   gDescompressionExit;
s8   gClockTimer=60;
s8   gClockLTimer=9;
s8   gClockRTimer=9;
u8   gRound=1;
u8   gSombraStyle=1;
bool gDebug = 0;
u16  gDebugFlags = DBG_DEFAULT;
bool gRegionIsPal = FALSE;
u8   gLogicRate = LOGIC_RATE_60;
u8   gTimingProfile = TIMING_PROFILE_NORMAL;
u8   gSubTick = 0;
bool gScreen240 = FALSE;
bool gFreeStepArmed = FALSE;
bool gFreeStepAdvance = FALSE;
char gStr[64];
u16  gInd_tileset;
bool gASG_system;
u8   gPing2 = 0;
u8   gPing4 = 0;
u8   gPing10 = 0;
u8   gInputTimerCountDown=20;
u16  gDistancia;
u8   gAlturaPiso;
u8   gBgAnim;
u16  gLimiteCenarioE= 30;
u16  gLimiteCenarioD=290;
u8   gravidadePadrao = 3;
u8   impulsoPadrao = -14;
u16  gBG_Width;
u16  gBG_Height = 224;
u16  gScreenH = 224;
s16  camPosX = 0;
s16  camPosXanterior = 0;
s16  camPosY = 0;
s16  camPosYanterior = 0;
s16  gMeioDaTela = 0;
s16  gScrollValues[28] = { 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 };
s16  gScrollValue;
/* The authored swamp dock is the visual baseline; SHOWDOWN remains selectable
   from the front-end, but the default path must expose the reauthored stage. */
u8   gBG_Choice=2;
u8   Spark1_countDown;
u8   Spark2_countDown;
s16  PetalaPX[40];
s16  PetalaPY[40];

int  frameAdvCounterP1;
int  lastFrameAdvCounterP1;
int  frameAdvCounterP2;
int  lastFrameAdvCounterP2;

//Char Selection Menu
u8   cursorP1linha  = 1;
u8   cursorP1coluna = 1;
u8   cursorP1_ID;
u8   cursorP1ConfirmFX;
u8   cursorP1ColorChoice;
u8   cursorP2linha  = 1;
u8   cursorP2coluna = 1;
u8   cursorP2_ID;
u8   cursorP2ConfirmFX;
u8   cursorP2ColorChoice;
u8   cursorConfirmTimer;
bool endP1Selection;
bool endP2Selection;
u8   stepRoom=1;
u8   mainMenuOption=1;
u8   charSelStep=0;

//LINKUEI INTRO
u16 palette[64];
s16 scrollvalues[224];
s16 scrollvaluesA[224];
int X;
int Y;
int px;
int py;
int x1 = -8-(19*8);
int y1 = 84;
int fps;
int flicker;
int timer;
int framecount;

//Sprites
Sprite* Rect1BB1_Q1; Sprite* Rect1BB1_Q2; Sprite* Rect1BB1_Q3; Sprite* Rect1BB1_Q4;
Sprite* Rect1HB1_Q1; Sprite* Rect1HB1_Q2; Sprite* Rect1HB1_Q3; Sprite* Rect1HB1_Q4;
Sprite* Rect2BB1_Q1; Sprite* Rect2BB1_Q2; Sprite* Rect2BB1_Q3; Sprite* Rect2BB1_Q4;
Sprite* Rect2HB1_Q1; Sprite* Rect2HB1_Q2; Sprite* Rect2HB1_Q3; Sprite* Rect2HB1_Q4;

Sprite* ClockL;
Sprite* ClockR;
Sprite* HUD_Lethers;
Sprite* Spark[3];

//Inputs, Joystick
bool JOY1_UP, JOY1_DOWN, JOY1_LEFT, JOY1_RIGHT, JOY1_A, JOY1_B, JOY1_C, JOY1_X, JOY1_Y, JOY1_Z, JOY1_START, JOY1_MODE;
bool key_JOY1_UP_pressed, key_JOY1_UP_hold, key_JOY1_UP_released;
bool key_JOY1_DOWN_pressed, key_JOY1_DOWN_hold, key_JOY1_DOWN_released;
bool key_JOY1_LEFT_pressed, key_JOY1_LEFT_hold, key_JOY1_LEFT_released;
bool key_JOY1_RIGHT_pressed, key_JOY1_RIGHT_hold, key_JOY1_RIGHT_released;
bool key_JOY1_A_pressed, key_JOY1_A_hold, key_JOY1_A_released;
bool key_JOY1_B_pressed, key_JOY1_B_hold, key_JOY1_B_released;
bool key_JOY1_C_pressed, key_JOY1_C_hold, key_JOY1_C_released;
bool key_JOY1_X_pressed, key_JOY1_X_hold, key_JOY1_X_released;
bool key_JOY1_Y_pressed, key_JOY1_Y_hold, key_JOY1_Y_released;
bool key_JOY1_Z_pressed, key_JOY1_Z_hold, key_JOY1_Z_released;
bool key_JOY1_START_pressed, key_JOY1_START_hold, key_JOY1_START_released;
bool key_JOY1_MODE_pressed, key_JOY1_MODE_hold, key_JOY1_MODE_released;

bool JOY2_UP, JOY2_DOWN, JOY2_LEFT, JOY2_RIGHT, JOY2_A, JOY2_B, JOY2_C, JOY2_X, JOY2_Y, JOY2_Z, JOY2_START, JOY2_MODE;
bool key_JOY2_UP_pressed, key_JOY2_UP_hold, key_JOY2_UP_released;
bool key_JOY2_DOWN_pressed, key_JOY2_DOWN_hold, key_JOY2_DOWN_released;
bool key_JOY2_LEFT_pressed, key_JOY2_LEFT_hold, key_JOY2_LEFT_released;
bool key_JOY2_RIGHT_pressed, key_JOY2_RIGHT_hold, key_JOY2_RIGHT_released;
bool key_JOY2_A_pressed, key_JOY2_A_hold, key_JOY2_A_released;
bool key_JOY2_B_pressed, key_JOY2_B_hold, key_JOY2_B_released;
bool key_JOY2_C_pressed, key_JOY2_C_hold, key_JOY2_C_released;
bool key_JOY2_X_pressed, key_JOY2_X_hold, key_JOY2_X_released;
bool key_JOY2_Y_pressed, key_JOY2_Y_hold, key_JOY2_Y_released;
bool key_JOY2_Z_pressed, key_JOY2_Z_hold, key_JOY2_Z_released;
bool key_JOY2_START_pressed, key_JOY2_START_hold, key_JOY2_START_released;
bool key_JOY2_MODE_pressed, key_JOY2_MODE_hold, key_JOY2_MODE_released;

//Inteligencia Artificial PLAYER 2
bool IAP2;
u16 acaoIA;
u16 varIA;
u16 tempoIA;
u16 tempoIAacao;
u16 tempoIAataque;
u16 tempoIAmagia;
u16 esmurra;
u16 pulandoFrenteTras;
u16 defendeTempo;
bool ctrlResetInput = FALSE;
//modo campanha
u8 P2fase[9];
const Image *BGfase[9];
u8 tempoMaxIAataque[9];
u8 tempoMinIAataque[9];
u8 defesaIA[9];
u8 fase;
u8 faseMAX;

struct PlayerDEF P[3];
struct GraphicElementDEF GE[25];
