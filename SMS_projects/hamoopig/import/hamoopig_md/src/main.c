//////////////////////////////////////////////////////////////////////////////
// HAMOOPI(G) by GameDevBoss (Daniel Moura) 2015-2022                       //
// www.youtube.com/c/GameDevBoss                                            //
// HAMOOPIG É GRATUITO E SEMPRE SERÁ - HAMOOPIG IS FREE AND ALWAYS WILL BE  //
// O CONHECIMENTO DEVE SER COMPARTILHADO - KNOWLEDGE MUST BE SHARED         //
//////////////////////////////////////////////////////////////////////////////
// SPECIAL THANKS                                                           //
// SIR MACHO                                                                //
// TITAN DOOM                                                               //
//////////////////////////////////////////////////////////////////////////////

#include <genesis.h>
#include "sprite.h"
#include "gfx.h"
#include "sound.h"
#include "game_types.h"
#include "globals.h"
#include "config.h"
#include "hamoopig_runtime_probe.h"
#include "player.h"
#include "input.h"
#include "fsm.h"
#include "physics.h"
#include "graphics.h"
#include "hud.h"
#include "init.h"
#include "select.h"
#include "title.h"
#include "collision.h"
#include "debug.h"
#include "timing.h"
#include "scene.h"
#include "opening.h"
#include "combat_event.h"
#include "stage.h"



/* Um tick logico completo: contadores, cena e toda a simulacao.  Um frame
   de video roda esta funcao 1 ou 2 vezes (ver inc/timing.h).  Tudo que
   deve acontecer uma vez por FRAME -- SPR_update, sonda, VBlank -- fica
   fora daqui, no laco principal. */
static void run_logic_tick(void)
{
        gFrames++;

		/* 240 linhas dependem de regiao, cena e altura do cenario -- por isso
		   a altura e reavaliada por tick, e nao no instante do toggle. */
		FUNCAO_SCREEN_HEIGHT_APPLY();
		if(gPing2  == 1){ gPing2 = -1; } gPing2++;  //var 'gPing2'  (50%) variacao: 0 ; 1
		if(gPing4  == 3){ gPing4 = -1; } gPing4++;  //var 'gPing4'  (25%) variacao: 0 ; 1 ; 2 ; 3
		if(gPing10 == 9){ gPing10= -1; } gPing10++; //var 'gPing10' (10%) variacao: 0 ; 1 ; 2 ; 3 ; 4 ; 5 ; 6 ; 7 ; 8 ; 9
		
		if(gRoom==SCENE_OPENING) //ABERTURA -------------------------------------------------------
		{
			FUNCAO_INPUT_SYSTEM();
			if(gFrames==1){ FUNCAO_OPENING_INIT(); }
			else{ FUNCAO_OPENING_UPDATE(); }
		}

		if(gRoom==SCENE_TITLE) //TITULO -----------------------------------------------------------
		{
			FUNCAO_INPUT_SYSTEM(); //Verifica os joysticks 
			if(gFrames==1){ FUNCAO_TITLE_INIT(); }
			else{ FUNCAO_TITLE_UPDATE(); }
		}

		if(gRoom == SCENE_SELECT) //CHARACTER SELECT -----------------------------------------------------------
		{
			FUNCAO_INPUT_SYSTEM();
			if(gFrames==1)
			{
				FUNCAO_SELECT_INIT();
			}
			else
			{
				FUNCAO_SELECT_UPDATE();
			}
		}

		if(gRoom == SCENE_DECOMPRESSION) //DESCOMPRESSION -------------------------------------------------------------
		{
			GE[1].sprite = SPR_addSpriteExSafe(&spr_point,  0, 225, TILE_ATTR(PAL3, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
			GE[2].sprite = SPR_addSpriteExSafe(&spr_point,  0, 225, TILE_ATTR(PAL3, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
			GE[3].sprite = SPR_addSpriteExSafe(&spr_point,  0, 225, TILE_ATTR(PAL3, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
			
			if(gFrames==20)
			{
				if (GE[1].sprite){ SPR_releaseSprite(GE[1].sprite); GE[1].sprite = NULL; }
				if (GE[2].sprite){ SPR_releaseSprite(GE[2].sprite); GE[2].sprite = NULL; }
				if (GE[3].sprite){ SPR_releaseSprite(GE[3].sprite); GE[3].sprite = NULL; }
				SCENE_request(gDescompressionExit);
				CLEAR_VDP();
			}
			
		}
		
		if(gRoom == SCENE_FIGHT) //IN GAME -------------------------------------------------------------------
		{
			COMBAT_EVENTS_BEGIN_TICK((u16)gFrames);
			//buffer de especiais para P1
			if(P[1].hitPause==0 && P[1].bufferSpecial!=0){
				PLAYER_STATE(1, P[1].bufferSpecial);
				P[1].bufferSpecial=0;
			}

			//buffer de especiais para P2
			if(P[2].hitPause==0 && P[2].bufferSpecial!=0){
				PLAYER_STATE(2, P[2].bufferSpecial);
				P[2].bufferSpecial=0;
			}
			
			
			/*//HWA bebado
			if( P[1].id==8 && P[1].bebado>0){ P[1].bebado--; }
			if( P[1].bebado>1 ){
				if(P[1].palID==1){ PAL_setPalette(PAL2, spr_hwa_pal1b.palette->data, CPU); } //hwa
				if(P[1].palID==2){ PAL_setPalette(PAL2, spr_hwa_pal2b.palette->data, CPU); } //hwa
			}
			if( P[1].bebado==1 ){
				if(P[1].palID==1){ PAL_setPalette(PAL2, spr_hwa_pal1.palette->data, CPU); } //hwa
				if(P[1].palID==2){ PAL_setPalette(PAL2, spr_hwa_pal2.palette->data, CPU); } //hwa
			}
			if( P[2].id==8 && P[2].bebado>0){ P[2].bebado--;  }
			if( P[2].bebado>1 ){
				if(P[2].palID==1){ PAL_setPalette(PAL3, spr_hwa_pal1b.palette->data, CPU); } //hwa
				if(P[2].palID==2){ PAL_setPalette(PAL3, spr_hwa_pal2b.palette->data, CPU); } //hwa
			}
			if( P[2].bebado==1 ){
				if(P[2].palID==1){ PAL_setPalette(PAL3, spr_hwa_pal1.palette->data, CPU); } //hwa
				if(P[2].palID==2){ PAL_setPalette(PAL3, spr_hwa_pal2.palette->data, CPU); } //hwa
			}
			*/
			
			//codigo de "SLOW MOTION KO"
			if((P[1].energiaBase==0 || P[2].energiaBase==0) && gFrames>100)
			{
				/* Never throttle the landing states.  550/551 own the
				 * defeated fighter's fall; dropping every other logic tick here
				 * could leave Musgo suspended in mid-air when the result screen
				 * is sampled.  Slow motion remains available after both fighters
				 * reached the terminal 570 pose. */
				bool koNeedsLanding =
					((P[1].energiaBase==0) && (P[1].state==550 || P[1].state==551)) ||
					((P[2].energiaBase==0) && (P[2].state==550 || P[2].state==551));
				if(koNeedsLanding)
				{
					gPauseSystem=0;
				}
				else
				{
					gPauseSystem=1;
					gPauseKoTimer++;
					if(gPauseKoTimer>=90 && gPauseKoTimer<=320)
					{
						if(gPing2==0){gPauseSystem=0;}
						if(gPing2==1){gPauseSystem=1;}
					}
					if(gPauseKoTimer>320)
					{
						gPauseSystem=0;
					}
				}
			}else{
				gPauseKoTimer=0;
			}
			
			if(gFrames == 1){ 
				gPodeMover=0;
				FUNCAO_INICIALIZACAO(); //Inicializacao
				HAMOOPIG_probeFightInit();
				if(gConfig.audioMusic){ XGM_startPlay(bgm_ken_stage); }
			}

			/* MUSIC e imediata nos dois sentidos: OFF para a faixa, ON retoma a
			   faixa DESTA cena.  Antes so existia o start em gFrames==1, entao
			   religar a musica no meio da luta nao trazia nada de volta.

			   Age na BORDA da preferencia, nao por polling de XGM_isPlaying: se
			   ficasse checando todo tick, uma faixa que terminasse sozinha
			   seria reiniciada para sempre. */
			{
				static bool musicaLigadaAntes = TRUE;
				if(gConfig.audioMusic != musicaLigadaAntes)
				{
					if(gConfig.audioMusic){ XGM_startPlay(bgm_ken_stage); }
					else { XGM_stopPlay(); }
					musicaLigadaAntes = gConfig.audioMusic;
				}
			}
			if(gFrames<=355){ 
				FUNCAO_ROUND_INIT(); //Rotina de Letreiramento de inicio dos rounds
			}else{
				if(gPauseSystem==0) {
					u16 dmaStageMark = DMA_getQueueTransferSize();
					FUNCAO_RELOGIO(); //HUD relogio
					HAMOOPIG_probeStageDma(1, dmaStageMark);
				}
				/* Health is frozen during KO, but the zero frame must still reach
				   the WINDOW before the victory animation takes ownership. */
				u16 dmaStageMark = DMA_getQueueTransferSize();
				FUNCAO_BARRAS_DE_ENERGIA(); //HUD barras
				HAMOOPIG_probeStageDma(2, dmaStageMark);
				if(P[1].energiaBase==0 || P[2].energiaBase==0){ 
					gPodeMover=0; 
				}
			}
			if(P[1].energiaBase == 0 || P[2].energiaBase == 0 ||
			   (gClockLTimer == 0 && gClockRTimer == 0))
			{
				if(gResultTimer < 600){ gResultTimer++; }
			}
			u16 dmaStageMark = DMA_getQueueTransferSize();
			hud_message_update();
			HAMOOPIG_probeStageDma(3, dmaStageMark);
			
			//libera os graficos dos sparks
			if(Spark1_countDown>0){ 
				Spark1_countDown--; 
				if(Spark1_countDown==1) { 
					if(Spark[1]){ SPR_releaseSprite(Spark[1]); Spark[1] = NULL; }
				} 
			}
			if(Spark2_countDown>0){ 
				Spark2_countDown--; 
				if(Spark2_countDown==1) { 
					if(Spark[2]){ SPR_releaseSprite(Spark[2]); Spark[2] = NULL; }
				} 
			}
			
			if(doubleHitStep==1 && P[1].hitPause==0 && P[2].hitPause==0){ doubleHitStep=2; }
			
			if(gPauseSystem==0)
			{
				FUNCAO_UPDATE_HIT_COMBOS();
				FUNCAO_INPUT_SYSTEM(); //Verifica os joysticks 
				
				dmaStageMark = DMA_getQueueTransferSize();
				FUNCAO_ANIMACAO(); //Atualiza animacao
				HAMOOPIG_probeStageDma(4, dmaStageMark);
				
				/* A victory animation can change rooms. Do not mutate the old fight
				   after its owner has handed control to the after-match scene. */
				if(gRoom == SCENE_FIGHT)
				{
					dmaStageMark = DMA_getQueueTransferSize();
					FUNCAO_FSM(); //FSM = Finite State Machine (Maquina de Estados)
					HAMOOPIG_probeStageDma(5, dmaStageMark);
					/* A FSM apenas produz eventos de colisão. O consumo é único e
					   acontece depois dela, antes da física/efeitos, para que combo
					   não seja duplicado por hitstop ou por uma segunda leitura. */
					FUNCAO_CONSUME_COMBAT_EVENTS();
					HAMOOPIG_probeCombatEvents();
					FUNCAO_PHYSICS(); //Funcoes de Fisica
					FUNCAO_CAMERA_BGANIM();
					FUNCAO_SAMSHOFX(); //Efeitos do jogo SS2
					if(gDebug == 1){ FUNCAO_DEBUG(); } //Debug
				}
			}
			
		}
		
		if(gRoom == SCENE_AFTER_MATCH) //AFTER MATCH ---------------------------------------------------------------
		{
			FUNCAO_INPUT_SYSTEM(); //Verifica os joysticks 
			hud_message_update();
			if(P[1].key_JOY_A_status==1 || P[2].key_JOY_A_status==1)
			{
				/* Keep live sprite handles so fight initialization can release them. */
				VDP_clearPlane(BG_A, TRUE);
				hud_window_off();
				gPauseSystem=0;
				SCENE_request(SCENE_FIGHT);
			}
			else if(P[1].key_JOY_START_status==1 || P[2].key_JOY_START_status==1)
			{
				XGM_stopPlay();
				CLEAR_VDP();
				gPauseSystem=0;
				SCENE_request(SCENE_SELECT);
			}
			else if(P[1].key_JOY_B_status==1)
			{
				XGM_stopPlay();
				CLEAR_VDP();
				gPauseSystem=0;
				/* B is the explicit return-to-title path used to make the
				   OPENING/FADE session preferences observable after a match. */
				SCENE_request(gConfig.showOpening ? SCENE_OPENING : SCENE_TITLE);
			}
		}

		if(gRoom==SCENE_ROUND_RESET) //ROUND RESET COMMIT ------------------------------------------
		{
			FUNCAO_ROUND_RESTART();
		}

		/* Ponto UNICO de commit de cena: uma troca por tick, sempre aqui. */
		SCENE_commit();
		
}


int main(bool hardReset) /************** MAIN **************/
{
	/* BlastEm/console soft reset keeps 68k RAM; CRAM is wiped.
	   Without a hard reset, gFrames/gRoom survive and FUNCAO_INICIALIZACAO
	   never reloads fighter palettes. SGDK 2.11: sdk/sgdk-2.11/inc/sys.h */
	if(!hardReset)
	{
		SYS_hardReset();
	}

    //Inicializacao da VDP (Video Display Processor)
	SYS_disableInts();
	 VDP_init();                    //Inicializa a VDP (Video Display Processor)
	 VDP_setScreenWidth320();       //Resolucao padrao de 320x224 (Largura)
	 VDP_setScreenHeight224();      //Resolucao padrao de 320x224 (Altura)
	 VDP_setTextPlane(BG_A);        //Textos serao desenhados no BG_A
	 VDP_setTextPalette(PAL1);      //Textos serao desenhados com a ultima cor da PAL0
	 SPR_init();       				//SPR_initEx(u16 vramSize)
	 HAMOOPIG_probeInit();
	 VDP_setBackgroundColor(0);     //Range 0-63 //4 Paletas de 16 cores = 64 cores
	 /* A regiao e uma propriedade do console: IS_PAL_SYSTEM le o flag de
	    status do VDP.  Nao existe API para forcar 50Hz num console NTSC, entao
	    isto e detectado, nunca configurado.  O tick logico default acompanha a
	    regiao para que o jogo nao mude de velocidade sem o usuario pedir. */
	 gRegionIsPal = (IS_PAL_SYSTEM) ? TRUE : FALSE;
	 gLogicRate = gRegionIsPal ? LOGIC_RATE_50 : LOGIC_RATE_60;
	 TIMING_init();
	 CONFIG_setDefaults();
	SYS_enableInts();
	Z80_loadDriver(Z80_DRIVER_XGM, TRUE); 

	//////////////////////////////////////////////////////I.A. (config)
	fase = 4; //manter o valor igual a 1
	faseMAX = 8; //configurado para 8 fases no maximo (escolher valor de 1 a 8)
	
	IAP2 = FALSE;

	//DIFICULDADE DA IA

	//SE O TEMPO DE ATAQUE ESTIVER ENTRE tempoMinIAataque E tempoMaxIAataque SIGNIFICA QUE O PLAYER 2 ATACA
	tempoMinIAataque[1] =  60; //escolher valor de 2 a 255
	tempoMinIAataque[2] =  60;
	tempoMinIAataque[3] =  50;
	tempoMinIAataque[4] =  50;
	tempoMinIAataque[5] =  40;
	tempoMinIAataque[6] =  30;
	tempoMinIAataque[7] =  20;
	tempoMinIAataque[8] =  10;

	tempoMaxIAataque[1] = 100; //escolher valor de 2 a 255 (valor deve ser maior que o respectivo no tempoMinIAataque)
	tempoMaxIAataque[2] = 100;
	tempoMaxIAataque[3] = 100;
	tempoMaxIAataque[4] = 100;
	tempoMaxIAataque[5] =  55;
	tempoMaxIAataque[6] =  60;
 	tempoMaxIAataque[7] =  50;
	tempoMaxIAataque[8] =  80;

	//QUANTO MENOR O VALOR, MAIS A IA DO PLAYER 2 DEFENDE
	defesaIA[1] =  50; //escolher valor de 10 a 255, valor menor ou igual a 10 = sempre defende
	defesaIA[2] =  50;
	defesaIA[3] =  10;
	defesaIA[4] =  10;
	defesaIA[5] =  90;
	defesaIA[6] =  60;
	defesaIA[7] =  30;
	defesaIA[8] =  15;

	P2fase[1] = 2; //escolha do Player 2 em cada fase: 1="haohmaru", 2="gillius"
	P2fase[2] = 1;
	P2fase[3] = 2;
	P2fase[4] = 1;
	P2fase[5] = 2;
	P2fase[6] = 1;
	P2fase[7] = 2;
	P2fase[8] = 1;
	//////////////////////////////////////////////////////I.A. (config)
	
	/* --- CONTRATO DE CENAS ------------------------------------------------
	   As trocas de cena passam por SCENE_request/SCENE_commit (inc/scene.h).
	   Nenhum bloco abaixo escreve gRoom ou gFrames: o commit acontece num
	   ponto unico, no fim do tick, e sempre zera gFrames para que o tick
	   seguinte o leve a 1 e a cena inicialize.

	   A convencao POSICIONAL antiga morreu com isso.  Antes, escolher
	   gFrames=0 ou 1 dependia de o bloco alvo vir antes ou depois na cadeia
	   de ifs, e reordenar blocos quebrava as transicoes.  Hoje a ordem
	   textual dos blocos e indiferente ao fluxo.

	   Ordem atual: OPENING(0) -> TITLE(1) -> SELECT(2) -> 9 -> FIGHT(10)
	   -> AFTER_MATCH(11) -> ROUND_RESET(12).  Os numeros preservam os valores
	   historicos de gRoom porque a sonda HPRB exporta a cena na SRAM.

	   gRoom 9 (DESCOMPRESSION) continua sem produtor: nada pede essa cena
	   hoje.  Mantido como ponto de extensao via gDescompressionExit.
	   --------------------------------------------------------------------- */
	/* --- CONTRATO DE TAXA LOGICA -----------------------------------------
	   Um tick descartado nao roda NADA: nem gFrames, nem input, nem logica.
	   So atualiza sprites e espera o VBlank.  Assim o jogo inteiro desacelera
	   junto, inclusive o letreiro de round, que conta gFrames.

	   Consequencia intencional: com tick a 50Hz, a deteccao de borda de botao
	   passa a ser relativa ao tick logico anterior, nao ao frame de video.
	   Um toque que comece e termine dentro do frame descartado se perde --
	   e exatamente o que acontece num console PAL de verdade.
	   --------------------------------------------------------------------- */
    while(TRUE) /// LOOP PRINCIPAL ///
    {
		{
			static u16 stepPrevJoy = 0;
			static bool pausePanelUp = FALSE;
			bool frozen = FALSE;

			/* Leitura crua do joypad de proposito: chamar FUNCAO_INPUT_SYSTEM
			   aqui aplicaria efeitos colaterais (botao de ataque, troca de
			   lutador com MODE) num frame em que a FSM pode estar congelada. */
			u16 joy = JOY_readJoypad(JOY_1);
			u16 edge = (u16)(joy & ~stepPrevJoy);
			stepPrevJoy = joy;

			/* START sozinho congela/retoma a luta.  MODE+START ja e o atalho
			   historico que liga o debug em input.c, entao so pausa quando
			   MODE nao esta pressionado -- senao o combo dispararia os dois. */
			if(gRoom == SCENE_FIGHT && (edge & BUTTON_START) && !(joy & BUTTON_MODE))
			{
				gFreeStepArmed = !gFreeStepArmed;
				gFreeStepAdvance = FALSE;
			}

			/* A taxa logica nao e mais decidida aqui: TIMING_ticksForThisFrame
			   e a unica autoridade sobre quantos ticks o frame vale.  Este
			   bloco cuida so de congelamento por pausa/free-step. */

			/* So congela a luta.  Se valesse em qualquer cena, ligar STEP no
			   menu de titulo travaria o proprio menu que acabou de liga-lo.

			   gFrames>1 nao e detalhe: a cena entra com gFrames=1 e e esse
			   tick que roda FUNCAO_INICIALIZACAO.  Congelando antes dele, com
			   STEP ligado la no titulo, a luta nunca carregaria cenario nem
			   lutadores -- so uma tela vazia esperando o primeiro step. */
			if(gFreeStepArmed && gRoom == SCENE_FIGHT && gFrames > 1)
			{
				frozen = !gFreeStepAdvance;
				gFreeStepAdvance = FALSE;
			}

			/* O painel acompanha a pausa, nao o congelamento do frame. */
			{
				bool wantPanel = (gFreeStepArmed && gRoom == SCENE_FIGHT) ? TRUE : FALSE;
				if(wantPanel && !pausePanelUp){ FUNCAO_DEBUG_PAUSE_ENTER(); }
				if(!wantPanel && pausePanelUp){ FUNCAO_DEBUG_PAUSE_EXIT(); }
				pausePanelUp = wantPanel;
			}

			if(frozen)
			{
				/* C avanca 1 tick; B e a saida de emergencia, porque nao ha
				   como voltar ao menu de titulo a partir da luta. */
				if(gFreeStepArmed && gRoom == SCENE_FIGHT)
				{
					if(edge & BUTTON_C){ gFreeStepAdvance = TRUE; }
					if(edge & BUTTON_B){ gFreeStepArmed = FALSE; }
					FUNCAO_DEBUG_PAUSE_UPDATE(edge);
				}

				SPR_update();
				SYS_doVBlankProcess();
				continue;
			}
		}

        {
            /* Um frame de video pode valer 1 ou 2 ticks logicos.  gSubTick diz
               qual deles esta rodando: FUNCAO_INPUT_SYSTEM so produz borda no
               primeiro, porque no segundo previousJoyState ja igualou
               currentJoyState e o botao aparece como HOLD. */
            u8 ticks = TIMING_ticksForThisFrame();
            for(gSubTick = 0; gSubTick < ticks; gSubTick++)
            {
                run_logic_tick();
            }
            gSubTick = 0;
		}
		//--- FINALIZACOES ---//
		if(gRoom == SCENE_FIGHT){ STAGE_ambient_update(); }
		// VDP_showFPS(1, 1, 1);        //Mostra a taxa de FPS
		u16 dmaBeforeSpriteUpdate = DMA_getQueueTransferSize();
		SPR_update();          //Atualiza (desenha) os sprites
		HAMOOPIG_probeSpriteDma(dmaBeforeSpriteUpdate);
        HAMOOPIG_probeTick(gRoom); //Snapshot diagnóstico antes do VBlank.
        SYS_doVBlankProcess(); //Wait for screen refresh and do all SGDK VBlank tasks
    }
	
    return 0;
}

//--- FUNCOES ---//
