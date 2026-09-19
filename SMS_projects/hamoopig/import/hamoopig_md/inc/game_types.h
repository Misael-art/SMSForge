#ifndef GAME_TYPES_H
#define GAME_TYPES_H

#include <genesis.h>

//--- DEFINICOES ---//
/* Production runtime: hidden hitbox/axis sprites must not consume the sprite
   pool when debug rendering is disabled.  Keep the debug path available by
   rebuilding with RELEASE=0 in the development profile. */
#define RELEASE 1

/* Sub-toggles do modo debug (gDebugFlags).  gDebug continua sendo o
   liga/desliga mestre: se ele for 0, nada abaixo e desenhado. */
#define DBG_BBOX     0x01u /* caixas de corpo (bodybox, spr_rect_bb) */
#define DBG_HBOX     0x02u /* caixas de golpe (hitbox, spr_rect_hb) */
#define DBG_TEXT     0x04u /* estado/frame de cada player */
#define DBG_PERF     0x08u /* FPS, pico de DMA, sprites e scanline */
#define DBG_FRAMEADV 0x10u /* vantagem de frame */
#define DBG_FREESTEP 0x20u /* pausa com avanco de 1 frame por vez */
#define DBG_DEFAULT  (DBG_BBOX | DBG_HBOX | DBG_TEXT)

/* Taxa do tick logico.  Ver o contrato de taxa logica em main.c. */
/* Perfis de tempo; contrato completo em inc/timing.h */
#define TIMING_PROFILE_NORMAL 0u
#define TIMING_PROFILE_LEGACY 1u

#define LOGIC_RATE_60 60u
#define LOGIC_RATE_50 50u
#define WEAK   1
#define MEDIUM 2
#define FIERCE 3
#define LP     1
#define MP     2
#define HP     3
#define LK     4
#define MK     5
#define HK     6
#define INDEX_MAR 0xe3
#define CIGD 3
#define BODYSPACE 15
#define RAGETIMER 600
#define SPECIAL_METER_MAX  32
#define SPECIAL_METER_COST 32
#define HIT_COMBO_WINDOW_TICKS 60u
#define ROUND_CLOCK_TICKS 38
#define ROUNDS_TO_WIN 2
//SOUND DEFs
#define INGAME_SFX 64
#define P1_SFX     65
#define P2_SFX     66
#define SFX_ARG    70
#define SFX_FATAL  71

// Keys
#define KEY_FREE     0 
#define KEY_PRESSED  1 
#define KEY_HOLD     2 
#define KEY_RELEASED 3 

//--- ESTRUTURAS DE DADOS ---//

typedef struct {
	Sprite* spriteFBall;
	s8 direcao;
	u8 speedX;
	bool active;
	u8  countDown;
	u8  instance;
	s16 x;
	s16 y;
	u8  guardFlag;
	u16 dataHBox[4];
} FireballDEF;

struct PlayerDEF {
	Sprite* sprite;
	Sprite* sombra;
	FireballDEF fball;
	u16 bufferSpecial;
	int paleta;
	u8  palID;
	u8  wins;
	s8  energia;
	s8  energiaBase;
	s8  energiaSP;
	u16 bebado;
	u8  rageLvl;
	u16 rageTimerCountdown;

	u16 state;
	u8 stateMoveType;
	bool control;

	u8  joyDirTimer[10];
	u8  inputArray[5];
	u8  attackPower;
	u8  attackButton;
	u8  guardFlag;
	u8  id;
	s16 x;
	s16 y;
	u8  w;
	u8  h;
	u8  axisX;
	u8  axisY;
	s8  direcao;
	u8  hSpeed;

	u8  puloTimer;
	bool shotJump;
	u8  cicloInteracoesGravidade;
	u8  cicloInteracoesGravidadeCont;
	s8  impulsoY;
	s8  gravidadeY;

	bool setup;

	u16 frameTimeAtual;
	u16 frameTimeTotal;
	u16 animFrame;
	u16 animFrameTotal;

	u8  hitPause;
	u8  hitCounter;
	u8  hitComboTimer;
	u8  attackInstance;

	u16 dataAnim[60];
	u16 dataHBox[4];
	u16 dataBBox[4];
	u16 dataMBox[4];

	//JOYSTICK
	u8 key_JOY_UP_status; u8 key_JOY_DOWN_status; u8 key_JOY_LEFT_status; u8 key_JOY_RIGHT_status;
	u8 key_JOY_A_status; u8 key_JOY_B_status; u8 key_JOY_C_status;
	u8 key_JOY_X_status; u8 key_JOY_Y_status; u8 key_JOY_Z_status;
	u8 key_JOY_START_status; u8 key_JOY_MODE_status;
	u8 key_JOY_countdown[10];
	u8 key_JOY_status[12];
};

struct GraphicElementDEF {
	Sprite* sprite;
};

#endif // GAME_TYPES_H
