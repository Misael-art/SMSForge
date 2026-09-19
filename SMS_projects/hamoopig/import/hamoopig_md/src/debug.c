#include <genesis.h>
#include "debug.h"
#include "globals.h"
#include "game_types.h"
#include "hamoopig_runtime_probe.h"

/* Tira um conjunto de 4 cantos da tela.  Usado quando o toggle
   correspondente esta desligado, para que BB e HB sejam independentes. */
static void debug_park_quad(Sprite *q1, Sprite *q2, Sprite *q3, Sprite *q4)
{
	SPR_setPosition(q1, -8, -8); SPR_setPosition(q2, -8, -8);
	SPR_setPosition(q3, -8, -8); SPR_setPosition(q4, -8, -8);
}

/* init.c cria os 16 cantos como HIDDEN e o unico trecho que os tornava
   visiveis estava comentado -- por isso as caixas nunca apareciam.  A
   visibilidade agora acompanha o toggle correspondente. */
static void debug_show_quad(Sprite *q1, Sprite *q2, Sprite *q3, Sprite *q4, bool on)
{
	SpriteVisibility v = on ? VISIBLE : HIDDEN;
	SPR_setVisibility(q1, v); SPR_setVisibility(q2, v);
	SPR_setVisibility(q3, v); SPR_setVisibility(q4, v);
}

void DEBUG_syncMaster(void)
{
	gDebug = (gDebugFlags & (DBG_BBOX | DBG_HBOX | DBG_TEXT | DBG_PERF | DBG_FRAMEADV)) ? 1 : 0;
}


/* --- MENU DE PAUSA DA LUTA ------------------------------------------------
   Ate aqui o unico acesso ao debug era o menu de titulo, o que obrigava a
   reiniciar a partida so para trocar um toggle.  START na luta congela o jogo
   e abre este painel; C avanca exatamente 1 tick, o que torna o free-step
   utilizavel sem precisar arma-lo antes no titulo.

   Desenha no BG_A, que fica vazio durante a luta (init.c carrega so o BG_B),
   a partir da linha 10 para nao brigar com o texto de estado do FUNCAO_DEBUG
   (linhas 1 a 6) nem com a HUD, que vive no plano WINDOW.
   ------------------------------------------------------------------------- */
#define DBGPAUSE_ROW   10
#define DBGPAUSE_COL    2
#define DBGPAUSE_ITEMS  6   /* 5 toggles + RESUME */
#define DBGPAUSE_WIDTH 26

static u8   sPauseCursor;
static bool sPauseDirty;

static const u16 kPauseBits[5] = { DBG_BBOX, DBG_HBOX, DBG_TEXT, DBG_PERF, DBG_FRAMEADV };
static const char *kPauseNames[5] = { "BODYBOX", "HITBOX ", "TEXT   ", "PERF   ", "FRM ADV" };

/* Prioridade explicita no atributo do tile para o painel ganhar dos lutadores:
   todos os sprites do jogo sao criados com prioridade baixa, entao o plano A
   com bit de prioridade fica na frente deles.  O texto e preto sobre fundo
   transparente, entao o lutador continua visivel entre os tracos das letras.

   O indice tem de ser 0: VDP_drawTextEx ja soma TILE_FONT_INDEX internamente
   (sdk/sgdk-2.11/src/vdp_bg.c:253), entao passar o indice da fonte aqui o
   somaria duas vezes e desenharia tiles de cenario no lugar das letras. */
#define DBGPAUSE_ATTR TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, 0)

static void debug_pause_text(const char *s, u16 row)
{
	VDP_drawTextEx(BG_A, s, DBGPAUSE_ATTR, DBGPAUSE_COL, row, CPU);
}

static void debug_pause_draw(void)
{
	u8 i;

	debug_pause_text("-- PAUSE / DEBUG --       ", DBGPAUSE_ROW);

	for(i = 0; i < 5; i++)
	{
		sprintf(gStr, "%c %s %s        ",
			(sPauseCursor == i) ? '>' : ' ',
			kPauseNames[i],
			(gDebugFlags & kPauseBits[i]) ? "ON " : "OFF");
		debug_pause_text(gStr, (u16)(DBGPAUSE_ROW + 2 + i));
	}

	sprintf(gStr, "%c RESUME                  ", (sPauseCursor == 5) ? '>' : ' ');
	debug_pause_text(gStr, (u16)(DBGPAUSE_ROW + 7));

	debug_pause_text("A=TOGGLE C=STEP START=GO  ", (u16)(DBGPAUSE_ROW + 9));
}

void FUNCAO_DEBUG_PAUSE_ENTER(void)
{
	sPauseCursor = 0;
	sPauseDirty = TRUE;
}

void FUNCAO_DEBUG_PAUSE_UPDATE(u16 edge)
{
	if(edge & BUTTON_UP)  { if(sPauseCursor > 0){ sPauseCursor--; } else { sPauseCursor = DBGPAUSE_ITEMS - 1; } sPauseDirty = TRUE; }
	if(edge & BUTTON_DOWN){ sPauseCursor = (u8)((sPauseCursor + 1) % DBGPAUSE_ITEMS); sPauseDirty = TRUE; }

	if((edge & BUTTON_A) && sPauseCursor < 5)
	{
		gDebugFlags ^= kPauseBits[sPauseCursor];
		DEBUG_syncMaster();
		/* Com o jogo congelado FUNCAO_DEBUG nao roda -- sem esta chamada o
		   toggle so teria efeito visivel apos sair da pausa ou dar um step. */
		if(gDebug == 1){ FUNCAO_DEBUG(); }
		sPauseDirty = TRUE;
	}

	if(sPauseDirty){ debug_pause_draw(); sPauseDirty = FALSE; }
}

void FUNCAO_DEBUG_PAUSE_EXIT(void)
{
	u8 row;
	/* O painel fica no BG_A, que a luta nao redesenha: sem limpar, ele
	   permanece por cima do jogo depois de retomar. */
	for(row = 0; row <= 9; row++)
	{
		VDP_clearText(DBGPAUSE_COL, (u16)(DBGPAUSE_ROW + row), DBGPAUSE_WIDTH);
	}
	sPauseDirty = FALSE;
}


void FUNCAO_CHECK_FRAME_ADVANTAGE() {
	if ((P[1].control == TRUE  && P[2].control == TRUE  && frameAdvCounterP1 != 0) ||
	    (P[1].control == FALSE && P[2].control == FALSE && frameAdvCounterP1 != 0)) {
		
		//P!
		lastFrameAdvCounterP1 = frameAdvCounterP1;
		frameAdvCounterP1 = 0;

		//P2
		lastFrameAdvCounterP2 = frameAdvCounterP2;
		frameAdvCounterP2 = 0;

	} else {

		if (P[1].control && !P[2].control) {
			frameAdvCounterP1++;
			frameAdvCounterP2--;
			
		} else if (!P[1].control && P[2].control) {
			frameAdvCounterP1--;
			frameAdvCounterP2++;
			
		}
	}
}

void FUNCAO_DEBUG()
{
	//Atencao! O debug só é funcional se você não printar sprites em cima dos seus caracteres alfanuméricos!
	// Procure pelo comando: SPR_setVRAMTileIndex(GE[XX].sprite, 1441); 
	// Onde, 1441 é o comeco dos tiles alfanumericos, e 1535 é o final desses tiles!
	
	if(gDebugFlags & DBG_TEXT)
	{
		VDP_drawText("HAMOOPIG ENGINE", 1, 1);
		sprintf(gStr, "P1-> S:%i T:%i/%i F:%i/%i    ", P[1].state, P[1].frameTimeAtual, P[1].frameTimeTotal, P[1].animFrame, P[1].animFrameTotal );
		VDP_drawText(gStr, 1, 2);
		sprintf(gStr, "P2-> S:%i T:%i/%i F:%i/%i    ", P[2].state, P[2].frameTimeAtual, P[2].frameTimeTotal, P[2].animFrame, P[2].animFrameTotal );
		VDP_drawText(gStr, 1, 3);
	}

	if(gDebugFlags & DBG_PERF)
	{
		/* Mesmos picos que vao para a SRAM via HAMOOPIG_probeTick. */
		sprintf(gStr, "DMA:%u SPR:%u SL:%u VS:%u   ",
			HAMOOPIG_probePeakDma(), HAMOOPIG_probePeakActiveSprites(),
			HAMOOPIG_probePeakScanlineSprites(), HAMOOPIG_probePeakVdpSprites() );
		VDP_drawText(gStr, 1, 4);
		sprintf(gStr, "%s %uHZ TICK:%uHZ%s   ",
			gRegionIsPal ? "PAL" : "NTSC", gRegionIsPal ? 50u : 60u,
			(u16)gLogicRate, gFreeStepArmed ? " STEP" : "" );
		VDP_drawText(gStr, 1, 5);
	}

	if(gDebugFlags & DBG_FRAMEADV)
	{
		sprintf(gStr, "FRM ADV P1:%i P2:%i    ", lastFrameAdvCounterP1, lastFrameAdvCounterP2 );
		VDP_drawText(gStr, 1, 6);
	}



	/* KLog DESLIGADO -- medido no BlastEm 0.6.2: com estas chamadas ativas a
	   tela fica PRETA assim que gDebug vira 1, com o emulador seguindo a 61 fps
	   (assinatura de VDP travado, nao de crash). Sem elas, a luta renderiza
	   normalmente. Evidencia: out/emulator_evidence/val_dbg_noflags (preto) vs
	   val_noklog (ok). Reativar so depois de confirmar o transporte de debug
	   do emulador alvo. */
	//KLog_U2("P1 state: ", P[1].state, ", P2 state: ", P[2].state);
	//KLog_U2("P1 x: ", P[1].x, ", P2 x: ", P[2].x);
	//KLog_U2("P1 y: ", P[1].y, ", P2 y: ", P[2].y);
	//KLog_U1("Distancia entre P1 e P2: ", <dist>);
	//KLog_U2("P1 hits: ", P[1].hitCounter, ", P2 hits: ", P[2].hitCounter);

	FUNCAO_CHECK_FRAME_ADVANTAGE();
	//KLog_S2("P1 frame adv: ", lastFrameAdvCounterP1, ", P2 frame adv: ", lastFrameAdvCounterP2);



	if(RELEASE==0)
	{
		SPR_setPosition(GE[1].sprite, P[1].x-4-camPosX, P[1].y-5);
		SPR_setPosition(GE[2].sprite, P[2].x-4-camPosX, P[2].y-5);
	}
	
	if(RELEASE==0)
	{
		bool showBB = (gDebugFlags & DBG_BBOX) ? TRUE : FALSE;
		bool showHB = (gDebugFlags & DBG_HBOX) ? TRUE : FALSE;
		debug_show_quad(Rect1BB1_Q1, Rect1BB1_Q2, Rect1BB1_Q3, Rect1BB1_Q4, showBB);
		debug_show_quad(Rect2BB1_Q1, Rect2BB1_Q2, Rect2BB1_Q3, Rect2BB1_Q4, showBB);
		debug_show_quad(Rect1HB1_Q1, Rect1HB1_Q2, Rect1HB1_Q3, Rect1HB1_Q4, showHB);
		debug_show_quad(Rect2HB1_Q1, Rect2HB1_Q2, Rect2HB1_Q3, Rect2HB1_Q4, showHB);

		//P1
		//bodyboxes
		if(!(gDebugFlags & DBG_BBOX) || (P[1].dataBBox[0]==0 && P[1].dataBBox[2]==0)){
			debug_park_quad(Rect1BB1_Q1, Rect1BB1_Q2, Rect1BB1_Q3, Rect1BB1_Q4);
		}else{
			SPR_setPosition(Rect1BB1_Q1, P[1].x+P[1].dataBBox[0]  -camPosX, P[1].y+P[1].dataBBox[1]);
			SPR_setPosition(Rect1BB1_Q2, P[1].x+P[1].dataBBox[2]-8-camPosX, P[1].y+P[1].dataBBox[1]);
			SPR_setPosition(Rect1BB1_Q3, P[1].x+P[1].dataBBox[0]  -camPosX, P[1].y+P[1].dataBBox[3]-8);
			SPR_setPosition(Rect1BB1_Q4, P[1].x+P[1].dataBBox[2]-8-camPosX, P[1].y+P[1].dataBBox[3]-8);
		}
		//hitboxes
		if(!(gDebugFlags & DBG_HBOX) || (P[1].dataHBox[0]==0 && P[1].dataHBox[2]==0)){
			debug_park_quad(Rect1HB1_Q1, Rect1HB1_Q2, Rect1HB1_Q3, Rect1HB1_Q4);
		}else{
			SPR_setPosition(Rect1HB1_Q1, P[1].x+P[1].dataHBox[0]  -camPosX, P[1].y+P[1].dataHBox[1]);
			SPR_setPosition(Rect1HB1_Q2, P[1].x+P[1].dataHBox[2]-8-camPosX, P[1].y+P[1].dataHBox[1]);
			SPR_setPosition(Rect1HB1_Q3, P[1].x+P[1].dataHBox[0]  -camPosX, P[1].y+P[1].dataHBox[3]-8);
			SPR_setPosition(Rect1HB1_Q4, P[1].x+P[1].dataHBox[2]-8-camPosX, P[1].y+P[1].dataHBox[3]-8);
		}

		//P2
		//bodyboxes
		if(!(gDebugFlags & DBG_BBOX) || (P[2].dataBBox[0]==0 && P[2].dataBBox[2]==0)){
			debug_park_quad(Rect2BB1_Q1, Rect2BB1_Q2, Rect2BB1_Q3, Rect2BB1_Q4);
		}else{
			SPR_setPosition(Rect2BB1_Q1, P[2].x+P[2].dataBBox[0]  -camPosX, P[2].y+P[2].dataBBox[1]);
			SPR_setPosition(Rect2BB1_Q2, P[2].x+P[2].dataBBox[2]-8-camPosX, P[2].y+P[2].dataBBox[1]);
			SPR_setPosition(Rect2BB1_Q3, P[2].x+P[2].dataBBox[0]  -camPosX, P[2].y+P[2].dataBBox[3]-8);
			SPR_setPosition(Rect2BB1_Q4, P[2].x+P[2].dataBBox[2]-8-camPosX, P[2].y+P[2].dataBBox[3]-8);
		}
		//hitboxes
		if(!(gDebugFlags & DBG_HBOX) || (P[2].dataHBox[0]==0 && P[2].dataHBox[2]==0)){
			debug_park_quad(Rect2HB1_Q1, Rect2HB1_Q2, Rect2HB1_Q3, Rect2HB1_Q4);
		}else{
			SPR_setPosition(Rect2HB1_Q1, P[2].x+P[2].dataHBox[0]  -camPosX, P[2].y+P[2].dataHBox[1]);
			SPR_setPosition(Rect2HB1_Q2, P[2].x+P[2].dataHBox[2]-8-camPosX, P[2].y+P[2].dataHBox[1]);
			SPR_setPosition(Rect2HB1_Q3, P[2].x+P[2].dataHBox[0]  -camPosX, P[2].y+P[2].dataHBox[3]-8);
			SPR_setPosition(Rect2HB1_Q4, P[2].x+P[2].dataHBox[2]-8-camPosX, P[2].y+P[2].dataHBox[3]-8);
		}

		//hitboxes das magias para o P1
		if ((gDebugFlags & DBG_HBOX) && P[1].fball.active == 1) {
			SPR_setPosition(Rect1HB1_Q1, P[1].fball.x + P[1].fball.dataHBox[0]   -camPosX, P[1].fball.y + P[1].fball.dataHBox[1]);
			SPR_setPosition(Rect1HB1_Q2, P[1].fball.x + P[1].fball.dataHBox[2] -8-camPosX, P[1].fball.y + P[1].fball.dataHBox[1]);
			SPR_setPosition(Rect1HB1_Q3, P[1].fball.x + P[1].fball.dataHBox[0]   -camPosX, P[1].fball.y + P[1].fball.dataHBox[3] -8);
			SPR_setPosition(Rect1HB1_Q4, P[1].fball.x + P[1].fball.dataHBox[2] -8-camPosX, P[1].fball.y + P[1].fball.dataHBox[3] -8);
		}
		//hitboxes das magias para o P2
		if ((gDebugFlags & DBG_HBOX) && P[2].fball.active == 1) {
			SPR_setPosition(Rect2HB1_Q1, P[2].fball.x + P[2].fball.dataHBox[0]   -camPosX, P[2].fball.y + P[2].fball.dataHBox[1]);
			SPR_setPosition(Rect2HB1_Q2, P[2].fball.x + P[2].fball.dataHBox[2] -8-camPosX, P[2].fball.y + P[2].fball.dataHBox[1]);
			SPR_setPosition(Rect2HB1_Q3, P[2].fball.x + P[2].fball.dataHBox[0]   -camPosX, P[2].fball.y + P[2].fball.dataHBox[3] -8);
			SPR_setPosition(Rect2HB1_Q4, P[2].fball.x + P[2].fball.dataHBox[2] -8-camPosX, P[2].fball.y + P[2].fball.dataHBox[3] -8);
		}
		
		//metodo de display HBoxes Info, (piscando) = reduz os tiles simultaneos em tela (DESATIVADO)
		//para facilitar a vida de outros desenvolvedores, decidi manter a exibicao das caixas o tempo todo
		if(gPing2==0)
		{
			/*
			SPR_setVisibility(Rect1HB1_Q1, VISIBLE); SPR_setVisibility(Rect1HB1_Q2, VISIBLE);
			SPR_setVisibility(Rect1HB1_Q3, VISIBLE); SPR_setVisibility(Rect1HB1_Q4, VISIBLE);
			SPR_setVisibility(Rect1BB1_Q1, VISIBLE); SPR_setVisibility(Rect1BB1_Q2, VISIBLE);
			SPR_setVisibility(Rect1BB1_Q3, VISIBLE); SPR_setVisibility(Rect1BB1_Q4, VISIBLE);
			
			SPR_setVisibility(Rect2HB1_Q1, HIDDEN); SPR_setVisibility(Rect2HB1_Q2, HIDDEN);
			SPR_setVisibility(Rect2HB1_Q3, HIDDEN); SPR_setVisibility(Rect2HB1_Q4, HIDDEN);
			SPR_setVisibility(Rect2BB1_Q1, HIDDEN); SPR_setVisibility(Rect2BB1_Q2, HIDDEN);
			SPR_setVisibility(Rect2BB1_Q3, HIDDEN); SPR_setVisibility(Rect2BB1_Q4, HIDDEN);
		}else{
			SPR_setVisibility(Rect1HB1_Q1, HIDDEN); SPR_setVisibility(Rect1HB1_Q2, HIDDEN);
			SPR_setVisibility(Rect1HB1_Q3, HIDDEN); SPR_setVisibility(Rect1HB1_Q4, HIDDEN);
			SPR_setVisibility(Rect1BB1_Q1, HIDDEN); SPR_setVisibility(Rect1BB1_Q2, HIDDEN);
			SPR_setVisibility(Rect1BB1_Q3, HIDDEN); SPR_setVisibility(Rect1BB1_Q4, HIDDEN);
			
			SPR_setVisibility(Rect2HB1_Q1, VISIBLE); SPR_setVisibility(Rect2HB1_Q2, VISIBLE);
			SPR_setVisibility(Rect2HB1_Q3, VISIBLE); SPR_setVisibility(Rect2HB1_Q4, VISIBLE);
			SPR_setVisibility(Rect2BB1_Q1, VISIBLE); SPR_setVisibility(Rect2BB1_Q2, VISIBLE);
			SPR_setVisibility(Rect2BB1_Q3, VISIBLE); SPR_setVisibility(Rect2BB1_Q4, VISIBLE);
			*/
		}
	}
}
