#include <genesis.h>
#include "fsm.h"
#include "globals.h"
#include "player.h"
#include "collision.h"
#include "combat_event.h"
#include "sound.h"
#include "sprite.h"

#ifndef HAMOOPIG_DMA_LAB_REDUCED
#define HAMOOPIG_DMA_LAB_REDUCED 0
#endif

/* A mass-box separation can move a fighter across the opponent's origin in
   the same frame that a close-range command is sampled.  For throws, the
   meaningful direction is therefore the input toward the opponent, not a
   stale facing bit from before the separation. */
static bool fsm_throw_forward_held(u8 player, u8 enemy)
{
	if(P[player].x < P[enemy].x)
		return (P[player].key_JOY_RIGHT_status == 1 || P[player].key_JOY_RIGHT_status == 2);
	if(P[player].x > P[enemy].x)
		return (P[player].key_JOY_LEFT_status == 1 || P[player].key_JOY_LEFT_status == 2);
	return (P[player].direcao == 1)
		? (P[player].key_JOY_RIGHT_status == 1 || P[player].key_JOY_RIGHT_status == 2)
		: (P[player].key_JOY_LEFT_status == 1 || P[player].key_JOY_LEFT_status == 2);
}

void FUNCAO_FSM_DEFENSE(u8 player, u8 enemy){

	//O calculo abaixo eh usado para defender magias :)
	u8 distancia_Player_X_Magia = 250;
	if(P[enemy].fball.active)
	{
		if(P[player].direcao == 1){
			distancia_Player_X_Magia = P[enemy].fball.x - P[player].x + 25;
		}
		if(P[player].direcao ==-1){
			distancia_Player_X_Magia = P[player].x - P[enemy].fball.x;
		}
	}
	
	//defesa start - EM PE e ABAIXADO!
	if ((P[enemy].stateMoveType == 1 || (P[enemy].fball.active == TRUE && distancia_Player_X_Magia <= 200)) && 
	  (((P[player].direcao ==  1 && P[player].key_JOY_LEFT_status  == 2) ||
		(P[player].direcao == -1 && P[player].key_JOY_RIGHT_status == 2)) &&
		(P[player].state == 100 || P[player].state == 200 || P[player].state == 410 || P[player].state == 420)))
	{
		//defesa (107 = em pe ; 207 = abaixado)
		if(P[player].key_JOY_DOWN_status == 2){ 
			PLAYER_STATE(player,207); 
		}else{ 
			PLAYER_STATE(player,107); 
		}
	}
	
	//soltou a defesa - EM PE
	if((P[player].state == 107 || P[player].state == 108) && 
	  ((P[player].direcao ==  1 && P[player].key_JOY_LEFT_status  == 0) || 
	   (P[player].direcao == -1 && P[player].key_JOY_RIGHT_status == 0)))
	{ PLAYER_STATE(player,109);} 
	
	//defesa se encerrou com o final do ataque do inimigo - EM PE
	if(P[player].state == 108 && P[enemy].stateMoveType == 0)
	{ PLAYER_STATE(player,109); } 
	
	//soltou a defesa - ABAIXADO
	if((P[player].state == 207 || P[player].state == 208) && 
	  ((P[player].direcao ==  1 && P[player].key_JOY_LEFT_status  == 0) || 
	   (P[player].direcao == -1 && P[player].key_JOY_RIGHT_status == 0))
	){ PLAYER_STATE(player,209); } 
	
	//defesa se encerrou com o final do ataque do inimigo - ABAIXADO
	if(P[player].state == 208 && P[enemy].stateMoveType == 0)
	{ PLAYER_STATE(player,209); } 
	
	//variacao de defesa em pe e abaixado
	if(P[player].state == 108 && P[player].key_JOY_DOWN_status == 2){ PLAYER_STATE(player,208); }
	if(P[player].state == 208 && P[player].key_JOY_DOWN_status == 0){ PLAYER_STATE(player,108); }
}

void FUNCAO_FSM_NORMAL_ATTACKS(u8 player) {
	
	//golpes normais!
	if(gDistancia > 45)
	{
		//golpes em pe de longe
		if(P[player].key_JOY_X_status==1 && (P[player].state==100 || P[player].state==410 || P[player].state==420))
		{ 
			if((player==1 && Spark2_countDown>0) || (player==2 && Spark1_countDown>0))
			{
				if(P[player].state==101){ P[player].x+=4*(P[player].direcao*-1); }
			}
			PLAYER_STATE(player,101); 
		}
		if(P[player].key_JOY_Y_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420)){ PLAYER_STATE(player,102); }
		if(P[player].key_JOY_Z_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420))
		{ 
			if(P[player].state==410 || P[player].state==420){
				if(P[player].state==410){ PLAYER_STATE(player,471); }
				if(P[player].state==420){ PLAYER_STATE(player,472); }
			}else{
				PLAYER_STATE(player,103); 
			}
		}
		if(P[player].key_JOY_A_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420))
		{ 
			if((player==1 && Spark2_countDown>0) || (player==2 && Spark1_countDown>0))
			{
				if(P[player].state==104){ P[player].x+=4*(P[player].direcao*-1); }
			}
			PLAYER_STATE(player,104); 
		}
		if(P[player].key_JOY_B_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420)){ PLAYER_STATE(player,105); }
		if(P[player].key_JOY_C_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420)){ PLAYER_STATE(player,106); }
	
	}else{
		//golpes em pe de perto
		if(P[player].key_JOY_X_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420 || P[player].state==606)){ PLAYER_STATE(player,151); }
		if(P[player].key_JOY_Y_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420 || P[player].state==606)){ PLAYER_STATE(player,152); }
		if(P[player].key_JOY_Z_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420))
		{ 
			if(P[player].state==410 || P[player].state==420){
				if(P[player].state==410){ PLAYER_STATE(player,471); }
				if(P[player].state==420){ PLAYER_STATE(player,472); }
			}else{
				PLAYER_STATE(player,103); 
			}
		}
		if(P[player].key_JOY_A_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420 || P[player].state==606)){ PLAYER_STATE(player,154); }
		if(P[player].key_JOY_B_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420 || P[player].state==606)){ PLAYER_STATE(player,155); }
		if(P[player].key_JOY_C_status==1 && (P[player].state==100 || P[player].state==481 || P[player].state==410 || P[player].state==420 || P[player].state==606)){ PLAYER_STATE(player,106); }
	}
	
	//golpes abaixados
	if(P[player].key_JOY_X_status==1 && (P[player].state==200) )
	{ 
		if((player==1 && Spark2_countDown>0) || (player==2 && Spark1_countDown>0))
		{
			if(P[player].state==201){ P[player].x+=4*(P[player].direcao*-1); }
		}
		PLAYER_STATE(player,201); 
	}
	if(P[player].key_JOY_Y_status==1 && P[player].state==200){ PLAYER_STATE(player,202); }
	if(P[player].key_JOY_Z_status==1 && P[player].state==200){ PLAYER_STATE(player,203); }
	if(P[player].key_JOY_A_status==1 && (P[player].state==200) )
	{ 
		if((player==1 && Spark2_countDown>0) || (player==2 && Spark1_countDown>0))
		{
			if(P[player].state==204){ P[player].x+=4*(P[player].direcao*-1); }
		}
		PLAYER_STATE(player,204); 
	}
	if(P[player].key_JOY_B_status==1 && P[player].state==200){ PLAYER_STATE(player,205); }
	if(P[player].key_JOY_C_status==1 && P[player].state==200){ PLAYER_STATE(player,106); }


	//golpes aereos, pulo neutro
	if(P[player].key_JOY_X_status==1 && P[player].state==300){ PLAYER_STATE(player,301); }
	if(P[player].key_JOY_Y_status==1 && P[player].state==300){ PLAYER_STATE(player,302); }
	if(P[player].key_JOY_Z_status==1 && P[player].state==300){ PLAYER_STATE(player,303); }
	if(P[player].key_JOY_A_status==1 && P[player].state==300){ PLAYER_STATE(player,304); }
	if(P[player].key_JOY_B_status==1 && P[player].state==300){ PLAYER_STATE(player,305); }
	if(P[player].key_JOY_C_status==1 && P[player].state==300){ PLAYER_STATE(player,306); }
	
	//golpes aereos, pulo para tras
	if(P[player].key_JOY_X_status==1 && P[player].state==310){ PLAYER_STATE(player,311); }
	if(P[player].key_JOY_Y_status==1 && P[player].state==310){ PLAYER_STATE(player,312); }
	if(P[player].key_JOY_Z_status==1 && P[player].state==310){ PLAYER_STATE(player,313); }
	if(P[player].key_JOY_A_status==1 && P[player].state==310){ PLAYER_STATE(player,314); }
	if(P[player].key_JOY_B_status==1 && P[player].state==310){ PLAYER_STATE(player,315); }
	if(P[player].key_JOY_C_status==1 && P[player].state==310){ PLAYER_STATE(player,316); }
	
	//golpes aereos, pulo para frente
	if(P[player].key_JOY_X_status==1 && P[player].state==320){ PLAYER_STATE(player,321); }
	if(P[player].key_JOY_Y_status==1 && P[player].state==320){ PLAYER_STATE(player,322); }
	if(P[player].key_JOY_Z_status==1 && P[player].state==320){ PLAYER_STATE(player,323); }
	if(P[player].key_JOY_A_status==1 && P[player].state==320){ PLAYER_STATE(player,324); }
	if(P[player].key_JOY_B_status==1 && P[player].state==320){ PLAYER_STATE(player,325); }
	if(P[player].key_JOY_C_status==1 && P[player].state==320){ PLAYER_STATE(player,326); }
}

static bool fsm_try_start_special(u8 player, u16 state)
{
	if(!FUNCAO_SPEND_SPECIAL(player)){ return FALSE; }
	if(P[player].hitPause==0)
	{
		PLAYER_STATE(player, state);
	}
	else
	{
		/* O custo é pago na aceitação do comando; o buffer só guarda a
		   transição e nunca pode cobrar duas vezes. */
		P[player].bufferSpecial = state;
	}
	return TRUE;
}

void FUNCAO_FSM_SPECIAL_ATTACKS(u8 player) {

	//MAGIAS STARTUP (FSM CHANGESTATE)!!!!!!
	//Condicoes para que se possa soltar as magias, e posterior Acionamento delas!
	//ACIONAMENTO DAS MAGIAS //INICIO DAS MAGIAS
	
	//bug fix para longo acionamento do shoryuken hpig 1.1
	if(P[player].joyDirTimer[4]==0 && P[player].inputArray[0]==4){ P[player].inputArray[0]=0; }
	if(P[player].joyDirTimer[6]==0 && P[player].inputArray[0]==6){ P[player].inputArray[0]=0; }
	
	if(((P[player].state >= 100 && P[player].state <= 156) || 
		(P[player].state >= 200 && P[player].state <= 256) || 
		 P[player].state == 410 || P[player].state == 420 || 
		 P[player].state == 471 || P[player].state == 472 || 
		 P[player].state == 602 || P[player].state == 606 ))
	{
		u8 magic_avaliable=1;
		
		if(P[player].id==1 || P[player].id==2 || P[player].id==3) //RYO / KEN / MUSGO (Musgo 700 is slam, no fireball)
		{
			//730
			//Shoryuken Roris type
			if // >, v, v>, > + P ; frente, baixo, baixo+frente, frente + Soco
			(
				magic_avaliable==1 &&
				(
					//(P[player].direcao== 1 && ( P[player].inputArray[2]==6 && P[player].joyDirTimer[2] < P[player].joyDirTimer[6] ) && (P[player].joyDirTimer[2]!=0) ) 
					( P[player].direcao== 1 && P[player].inputArray[2]==6 && P[player].inputArray[1]==2 && P[player].inputArray[0]==6 && P[player].joyDirTimer[6]!=0 )
					|| 
					//(P[player].direcao==-1 && ( P[player].inputArray[2]==4 && P[player].joyDirTimer[2] < P[player].joyDirTimer[4] ) && (P[player].joyDirTimer[2]!=0) )
					( P[player].direcao==-1 && P[player].inputArray[2]==4 && P[player].inputArray[1]==2 && P[player].inputArray[0]==4 && P[player].joyDirTimer[4]!=0 )
				) &&
				( P[player].attackButton==1 ||  P[player].attackButton==2)
			)
			{
				if(Spark1_countDown>0){ SPR_releaseSprite(Spark[1]); Spark1_countDown=0; }
				if(Spark2_countDown>0){ SPR_releaseSprite(Spark[2]); Spark2_countDown=0; }

				fsm_try_start_special(player,730);
				magic_avaliable=0;
			}
			
			//700
			//hadouken type
			if // v, v>, > + P ; baixo, baixo+frente, frente + Soco
			(
				magic_avaliable==1 && P[player].fball.active == FALSE &&
				(
					//(P[player].direcao== 1 && ( P[player].joyDirTimer[2] < P[player].joyDirTimer[6] ) && (P[player].joyDirTimer[2]!=0) ) 
					( P[player].direcao== 1 && P[player].inputArray[1]==2 && P[player].inputArray[0]==6 && P[player].joyDirTimer[6]!=0 )
					|| 
					//(P[player].direcao==-1 && ( P[player].joyDirTimer[2] < P[player].joyDirTimer[4] ) && (P[player].joyDirTimer[2]!=0) )
					( P[player].direcao==-1 && P[player].inputArray[1]==2 && P[player].inputArray[0]==4 && P[player].joyDirTimer[4]!=0 )
				) &&			
				( P[player].attackButton==1 ||  P[player].attackButton==2)
			)
			{
				if(Spark1_countDown>0){ SPR_releaseSprite(Spark[1]); Spark1_countDown=0; }
				if(Spark2_countDown>0){ SPR_releaseSprite(Spark[2]); Spark2_countDown=0; }

				fsm_try_start_special(player,700);
				magic_avaliable=0;
			}
			
			/*
			//710
			//Tatsumaki type
			if // v, <v, < + P ; baixo, baixo+tras, tras + Soco
			(
				magic_avaliable==1 && 
				(
					//(P[player].direcao==-1 && ( P[player].joyDirTimer[2] < P[player].joyDirTimer[6] ) && (P[player].joyDirTimer[2]!=0) ) 
					( P[player].direcao== 1 && P[player].inputArray[1]==2 && P[player].inputArray[0]==4 && P[player].joyDirTimer[4]!=0 )
					|| 
					//(P[player].direcao== 1 && ( P[player].joyDirTimer[2] < P[player].joyDirTimer[4] ) && (P[player].joyDirTimer[2]!=0) )
					( P[player].direcao==-1 && P[player].inputArray[1]==2 && P[player].inputArray[0]==6 && P[player].joyDirTimer[6]!=0 )
				) &&			
				( P[player].attackButton==1 ||  P[player].attackButton==2)
			)
			{
				if(P[1].hitPause==0 && P[2].hitPause==0){
					PLAYER_STATE(player,710);
					magic_avaliable=0;
				}else{
					P[player].bufferSpecial = 710;
					magic_avaliable=0; 
				}
			}
			
			//720
			//Tatsumaki type
			if // v, <v, < + P ; baixo, baixo+tras, tras + Chute
			(
				magic_avaliable==1 && 
				(
					//(P[player].direcao==-1 && ( P[player].joyDirTimer[2] < P[player].joyDirTimer[6] ) && (P[player].joyDirTimer[2]!=0) ) 
					( P[player].direcao== 1 && P[player].inputArray[1]==2 && P[player].inputArray[0]==4 && P[player].joyDirTimer[4]!=0 )
					|| 
					//(P[player].direcao== 1 && ( P[player].joyDirTimer[2] < P[player].joyDirTimer[4] ) && (P[player].joyDirTimer[2]!=0) )
					( P[player].direcao==-1 && P[player].inputArray[1]==2 && P[player].inputArray[0]==6 && P[player].joyDirTimer[6]!=0 )
				) &&			
				( P[player].attackButton==4 ||  P[player].attackButton==5)
			)
			{
				if(P[1].hitPause==0 && P[2].hitPause==0){
					PLAYER_STATE(player,720);
					magic_avaliable=0;
				}else{
					P[player].bufferSpecial = 720;
					magic_avaliable=0; 
				}
			}
			*/
			
		}//---end char; ryo
		
		if(magic_avaliable==0)
		{
			//reset input array
			P[player].inputArray[0]=0; P[player].inputArray[1]=0; P[player].inputArray[2]=0; P[player].inputArray[3]=0; P[player].inputArray[4]=0;
		}
	}
	
	//ryo MAGIA 701 (FIREBALL)
	if(P[player].id==1 && P[player].state==700 && P[player].animFrame==12 && P[player].frameTimeAtual==1)
	{
		if(P[player].fball.active==TRUE){ 
			if(P[player].fball.spriteFBall){ 
				SPR_releaseSprite(P[player].fball.spriteFBall); 
				P[player].fball.spriteFBall = NULL; 
			} 
		}
		P[player].fball.active=TRUE;
		P[player].fball.instance++;
		if(P[player].fball.instance==0){ P[player].fball.instance=1; }
		P[player].fball.x = P[player].x+(18*P[player].direcao);
		if(P[player].direcao==-1){
			P[player].fball.x-=70;
		}
		P[player].fball.y = P[player].y-90;

		P[player].fball.dataHBox[0] = +10;
		P[player].fball.dataHBox[1] = +5;
		P[player].fball.dataHBox[2] = +50;
		P[player].fball.dataHBox[3] = +40;

		P[player].fball.guardFlag = 1;

		if(player==1)
		{
			P[player].fball.spriteFBall = SPR_addSpriteExSafe(&spr_ryo_701, 
				P[player].fball.x, P[player].fball.y, TILE_ATTR(PAL2, FALSE, FALSE, FALSE), 
				SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(player==2)
		{
			P[player].fball.spriteFBall = SPR_addSpriteExSafe(&spr_ryo_701, 
				P[player].fball.x, P[player].fball.y, TILE_ATTR(PAL3, FALSE, FALSE, FALSE), 
				SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		
		if(P[player].fball.spriteFBall){ 
			SPR_setDepth(P[player].fball.spriteFBall, 1); 
		}
		if(P[player].direcao == -1){ 
			SPR_setHFlip(P[player].fball.spriteFBall, TRUE); 
		}
		P[player].fball.direcao = P[player].direcao;
	}
}

void FUNCAO_FSM_COLLISION(u8 player, u8 enemy) {

	/////////////
	// Colisao //
	/////////////
	
	if( FUNCAO_COLISAO(
		P[player].x+P[player].dataHBox[0], P[player].y+P[player].dataHBox[1], P[player].x+P[player].dataHBox[2], P[player].y+P[player].dataHBox[3], 
		P[enemy].x+P[enemy].dataBBox[0], P[enemy].y+P[enemy].dataBBox[1], P[enemy].x+P[enemy].dataBBox[2], P[enemy].y+P[enemy].dataBBox[3]
	)==1 )
	{
		if(FUNCAO_CHECK_GUARD(P[player].guardFlag, enemy))
		{
			//DEFENDEU! em pe
			if(P[enemy].state>=107 && P[enemy].state<=110){
				PLAYER_STATE(enemy,110);
			}
			//DEFENDEU! em abaixado
			if(P[enemy].state>=207 && P[enemy].state<=210){
				PLAYER_STATE(enemy,210);
			}

			if(P[player].attackPower==1){
				P[player].hitPause=8;
				P[enemy].hitPause=8; 
			}else{ 
				P[player].hitPause=12;
				P[enemy].hitPause=12;  
			} 

			P[enemy].stateMoveType = 2;
			/* Guard é um evento válido, mas não inicia combo. O consumidor
			   central poderá usar esta borda para o ganho de medidor sem
			   confundir bloqueio com dano confirmado. */
			COMBAT_EVENTS_EMIT_SOURCE(player, enemy, P[player].state, COMBAT_EVENT_GUARD,
				COMBAT_EVENT_SOURCE_BODY, P[player].attackInstance);
			
			u8 AlturaDoHit = P[player].y+P[player].dataHBox[3];
			P[player].dataHBox[0]=0; P[player].dataHBox[1]=0; P[player].dataHBox[2]=0; P[player].dataHBox[3]=0; //desativa a hitbox
			
			//dano de magias, geral
			if(P[player].state==700){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			if(P[player].state==710){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			if(P[player].state==720){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			if(P[player].state==730){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			if(P[player].state==740){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			if(P[player].state==750){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			if(P[player].state==760){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			if(P[player].state==770){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			if(P[player].state==780){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			if(P[player].state==790){ FUNCAO_UPDATE_LIFESP(enemy,1,-2); }
			
			if(Spark1_countDown>0){ SPR_releaseSprite(Spark[1]); }
			if(Spark2_countDown>0){ SPR_releaseSprite(Spark[2]); }
			
			if(enemy==1){Spark1_countDown=28-1;}
			if(enemy==2){Spark2_countDown=28-1;}
			Spark[enemy] = SPR_addSpriteExSafe( &spr_spark0, P[enemy].x-14-camPosX, AlturaDoHit-14+camPosY, TILE_ATTR(PAL1, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
			
			if(P[enemy].direcao == -1){ SPR_setHFlip(Spark[enemy], TRUE); }
			SPR_setDepth(Spark[enemy], 1);
			
		}else{
			//NAO DEFENDEU!
			u8 AlturaDoHit = P[player].y+P[player].dataHBox[3];
			P[player].dataHBox[0]=0; P[player].dataHBox[1]=0; P[player].dataHBox[2]=0; P[player].dataHBox[3]=0; //desativa a hitbox
			
			//Agarrao
			if(P[player].state == 800){
				if ((P[enemy].y > gAlturaPiso) || P[enemy].state == 602) { //O agarrao nao pega
					PLAYER_STATE(player,152); //Se o agarrao errar, faz o lutador dar um soco forte

				} else {
					PLAYER_STATE(player,801); //Se o agarrao pegar, primeiro movimento do player
					PLAYER_STATE(enemy,803); //Se o agarrao pegar, estado do inimigo
				}

			} else {

				u8 SparkType = 0;

				if(P[player].attackPower==1){
					P[player].hitPause=8;
					P[enemy].hitPause=8; 
				}else{ 
					P[player].hitPause=12;
					P[enemy].hitPause=12;  
				} 
				
				P[enemy].stateMoveType = 2;
				/* O contador pertence ao atacante: cada acerto válido soma uma vez;
				   a janela temporal decide quando o combo expira. */
				FUNCAO_REGISTER_HIT(player);

				//golpes de longe
				if(P[player].state==101)
				{ 
					if(P[enemy].y!=gAlturaPiso)
					{
						PLAYER_STATE(enemy,550);
					}else{
						if(P[enemy].state>=200 && P[enemy].state<=206)
						{
							PLAYER_STATE(enemy,505);
						}else{
							PLAYER_STATE(enemy,501);
						}
					} 
					FUNCAO_UPDATE_LIFESP(enemy,1,-4); //decrementa 4 da energia 
					FUNCAO_UPDATE_LIFESP(enemy,2,3); 
					SparkType= 1; 
				}
				if(P[player].state==102){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,506);}else{PLAYER_STATE(enemy,502);}} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType= 2; }
				if(P[player].state==104){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,505);}else{PLAYER_STATE(enemy,501);}} FUNCAO_UPDATE_LIFESP(enemy,1,-4); FUNCAO_UPDATE_LIFESP(enemy,2,3); SparkType= 1; }
				if(P[player].state==105){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,506);}else{PLAYER_STATE(enemy,502);}} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType= 2; }
				if(P[player].state==106){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{PLAYER_STATE(enemy,550);} FUNCAO_UPDATE_LIFESP(enemy,1,-12); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType= 3; }
				if(P[player].state==113){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{PLAYER_STATE(enemy,550);} FUNCAO_UPDATE_LIFESP(enemy,1,- 8); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType= 2; }
				
				//golpes de perto
				if(P[player].state==151){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,505);}else{PLAYER_STATE(enemy,503);}} FUNCAO_UPDATE_LIFESP(enemy,1,- 5); FUNCAO_UPDATE_LIFESP(enemy,2,3); SparkType= 1; }
				if(P[player].state==152){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,506);}else{PLAYER_STATE(enemy,504);}} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType= 2; }
				if(P[player].state==154){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,505);}else{PLAYER_STATE(enemy,503);}} FUNCAO_UPDATE_LIFESP(enemy,1,- 5); FUNCAO_UPDATE_LIFESP(enemy,2,3); SparkType= 1; }
				if(P[player].state==155){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,506);}else{PLAYER_STATE(enemy,504);}} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType= 2; }
				
				//golpes abaixado
				if(P[player].state==201){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,505);}else{PLAYER_STATE(enemy,503);}} FUNCAO_UPDATE_LIFESP(enemy,1,- 4); FUNCAO_UPDATE_LIFESP(enemy,2,3); SparkType=  1; }
				if(P[player].state==202){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,506);}else{PLAYER_STATE(enemy,504);}} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType=  2; }
				if(P[player].state==204){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,505);}else{PLAYER_STATE(enemy,503);}} FUNCAO_UPDATE_LIFESP(enemy,1,- 4); FUNCAO_UPDATE_LIFESP(enemy,2,3); SparkType=  1; }
				if(P[player].state==205){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{PLAYER_STATE(enemy,550);} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType=  2; }
				
				//golpes aereos
				
				//cross hpig 1.1
				if(P[player].state>=301 && P[player].state<=326)
				{
					if(P[enemy].state==607 || P[enemy].state==608)
					{
						if(P[enemy].direcao==1){P[enemy].direcao=-1;}else{P[enemy].direcao=1;}
					}
				}
				if(P[player].state==301 || P[player].state==311 || P[player].state==321){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=256){PLAYER_STATE(enemy,505);}else{PLAYER_STATE(enemy,501);}} FUNCAO_UPDATE_LIFESP(enemy,1,- 5); FUNCAO_UPDATE_LIFESP(enemy,2, 3); SparkType= 1; }
				if(P[player].state==302 || P[player].state==312 || P[player].state==322){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=256){PLAYER_STATE(enemy,506);}else{PLAYER_STATE(enemy,502);}} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2, 6); SparkType= 2; }
				if(P[player].state==303 || P[player].state==313 || P[player].state==323){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=256){PLAYER_STATE(enemy,506);}else{PLAYER_STATE(enemy,501);}} FUNCAO_UPDATE_LIFESP(enemy,1,- 5); FUNCAO_UPDATE_LIFESP(enemy,2,11); SparkType= 1; }
				if(P[player].state==304 || P[player].state==314 || P[player].state==324){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=256){PLAYER_STATE(enemy,505);}else{PLAYER_STATE(enemy,501);}} FUNCAO_UPDATE_LIFESP(enemy,1,- 5); FUNCAO_UPDATE_LIFESP(enemy,2, 3); SparkType= 1; }
				if(P[player].state==305 || P[player].state==315 || P[player].state==325){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=256){PLAYER_STATE(enemy,506);}else{PLAYER_STATE(enemy,502);}} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2, 6); SparkType= 2; }
				if(P[player].state==306 || P[player].state==316 || P[player].state==326){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{PLAYER_STATE(enemy,550);} FUNCAO_UPDATE_LIFESP(enemy,1,- 8); FUNCAO_UPDATE_LIFESP(enemy,2,11); SparkType= 3; }
				

				//Agarrao
				if(P[player].state==801){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{if(P[enemy].state>=200 && P[enemy].state<=206){PLAYER_STATE(enemy,506);}else{PLAYER_STATE(enemy,504);}} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType= 2; }
				if(P[player].state==802){ if(P[enemy].y!=gAlturaPiso){PLAYER_STATE(enemy,550);}else{PLAYER_STATE(enemy,550);} FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,6); SparkType=  2; }
				

				//u8 customHitPause = 0;
				
				//MAGIAS HITS /////////////////////////////
				//RYO ID:1
				if(P[player].id==1)
				{
					if(P[player].state==710)
					{ 
						if(P[player].animFrame<=3){PLAYER_STATE(enemy,503);}else{PLAYER_STATE(enemy,550);} 
						FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,5); SparkType= 1; 
					}
					if(P[player].state==720)
					{ 
						if(P[enemy].y!=gAlturaPiso){ PLAYER_STATE(enemy,550); }else{if(P[player].animFrame<=6){ PLAYER_STATE(enemy,503); }else{ PLAYER_STATE(enemy,550); } } 
						FUNCAO_UPDATE_LIFESP(enemy,1,-5); FUNCAO_UPDATE_LIFESP(enemy,2,5); SparkType= 1; 
					}
					if(P[player].state==730)
					{ 
						if(P[player].animFrame<=3){PLAYER_STATE(enemy,503);}else{PLAYER_STATE(enemy,550);}
						FUNCAO_UPDATE_LIFESP(enemy,1,-10); FUNCAO_UPDATE_LIFESP(enemy,2,5); SparkType=2; 
					}
				}
				///////////////////////////////////////////

				//Spark, efeito FX, do golpe acertando o oponente
				if(SparkType!=0)
				{
					//P[enemy].hitPause=16+customHitPause; //hitpause Shake
					
					if(Spark1_countDown>0){ if(Spark[1]){ SPR_releaseSprite(Spark[1]); Spark[1] = NULL; } }
					if(Spark2_countDown>0){ if(Spark[2]){ SPR_releaseSprite(Spark[2]); Spark[2] = NULL; } }
					
					if(SparkType== 1)
					{ 
						if(enemy==1){Spark1_countDown=28-1;}
						if(enemy==2){Spark2_countDown=28-1;}
						Spark[enemy] = SPR_addSprite(&spr_spark1, P[enemy].x-16-camPosX, AlturaDoHit-16+camPosY, TILE_ATTR(PAL1, FALSE, FALSE, FALSE)); 
						//SPR_setVRAMTileIndex(Spark[PR], 1519); //define uma posicao especifica para o GFX na VRAM
					}
					//SPR_addSpriteExSafe( &spr_spark1, P[PR].x-16, AlturaDoHit-32, TILE_ATTR(PAL1, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD); }
					if(SparkType== 2)
					{ 
						if(enemy==1){Spark1_countDown=28-1;}
						if(enemy==2){Spark2_countDown=28-1;}
						Spark[enemy] = SPR_addSprite(&spr_spark2, P[enemy].x-24-camPosX, AlturaDoHit-24+camPosY, TILE_ATTR(PAL1, FALSE, FALSE, FALSE)); 
						//SPR_setVRAMTileIndex(Spark[PR], 1519); //define uma posicao especifica para o GFX na VRAM
					}
					//SPR_addSpriteExSafe( &spr_spark2, P[PR].x-16, AlturaDoHit-32, TILE_ATTR(PAL1, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD); }
					if(SparkType== 3)
					{ 
						if(enemy==1){Spark1_countDown=44-1;}
						if(enemy==2){Spark2_countDown=44-1;}
						#if HAMOOPIG_DMA_LAB_REDUCED
						Spark[enemy] = SPR_addSprite(&spr_spark2, P[enemy].x-24-camPosX, AlturaDoHit-24+camPosY, TILE_ATTR(PAL1, FALSE, FALSE, FALSE));
						#else
						Spark[enemy] = SPR_addSprite(&spr_spark3, P[enemy].x-52-camPosX, AlturaDoHit-90+camPosY, TILE_ATTR(PAL1, FALSE, FALSE, FALSE)); 
						#endif
						//SPR_setVRAMTileIndex(Spark[PR], 1519); //define uma posicao especifica para o GFX na VRAM
					}
					//SPR_addSpriteExSafe( &spr_spark3, P[PR].x-16, AlturaDoHit-32, TILE_ATTR(PAL1, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD); }
					
					if(P[enemy].direcao == 1){ if(Spark[enemy]){ SPR_setHFlip(Spark[enemy], TRUE); }}
					if(Spark[enemy]){ SPR_setDepth(Spark[enemy], 1); }
				}
			}
		}
	}
	
	/////////////////////////
	// COLISAO DE HITBOXES //
	/////////////////////////
	
	if( FUNCAO_COLISAO(
			P[player].x+P[player].dataHBox[0], P[player].y+P[player].dataHBox[1], P[player].x+P[player].dataHBox[2], P[player].y+P[player].dataHBox[3], 
			P[enemy].x+P[enemy].dataHBox[0], P[enemy].y+P[enemy].dataHBox[1], P[enemy].x+P[enemy].dataHBox[2], P[enemy].y+P[enemy].dataHBox[3]
		)==1 )
	{
		if(P[player].dataBBox[0]==0 && P[player].dataBBox[1]==0 && P[player].dataBBox[2]==0 && P[player].dataBBox[3]==0)
		{
			//nao faz nada, esta invencivel. ex shoryuken
		}else{
			
			P[player].stateMoveType = 2;
			COMBAT_EVENTS_EMIT_SOURCE(player, enemy, P[player].state, COMBAT_EVENT_HIT,
				COMBAT_EVENT_SOURCE_DOUBLE, P[player].attackInstance);

			P[enemy].stateMoveType = 2;
			COMBAT_EVENTS_EMIT_SOURCE(enemy, player, P[enemy].state, COMBAT_EVENT_HIT,
				COMBAT_EVENT_SOURCE_DOUBLE, P[enemy].attackInstance);

			if(doubleHitStep==0)
			{
				if(P[player].attackPower==1){
					P[enemy].hitPause= 8;
				}else{
					P[enemy].hitPause=12;
				}
				if(P[enemy].attackPower==1){
					P[player].hitPause= 8;
				}else{
					P[player].hitPause=12;
				}
				
				doubleHitStep=1;
			}
			
			if(doubleHitStep==2)
			{
				FUNCAO_UPDATE_LIFESP(1,1,-2); 
				FUNCAO_UPDATE_LIFESP(2,1,-2); 
				if(P[player].state>=100 && P[player].state<=199){ PLAYER_STATE(player, 501); }
				if(P[player].state>=200 && P[player].state<=299){ PLAYER_STATE(player, 511); }
				if(P[player].state>=300 && P[player].state<=399){ PLAYER_STATE(player, 550); }
				if(P[player].state>=700 && P[player].state<=799)
				{
					if(P[player].y!=gAlturaPiso){ PLAYER_STATE(player, 550); }else{ PLAYER_STATE(player, 501); }
				}
			}
			
		}
		if(player==2 && doubleHitStep==2)
		{
			u8 AlturaDoHit = P[player].y+P[player].dataHBox[3];
			
			if(Spark1_countDown>0){ if(Spark[1]){ SPR_releaseSprite(Spark[1]); Spark[1] = NULL; } }
			if(Spark2_countDown>0){ if(Spark[2]){ SPR_releaseSprite(Spark[2]); Spark[2] = NULL; } }
			
			Spark1_countDown=28-1;
			Spark2_countDown=28-1;
			
			Spark[1] = SPR_addSprite(&spr_spark1, P[1].x-16-camPosX, AlturaDoHit-16+camPosY, TILE_ATTR(PAL1, FALSE, FALSE, FALSE)); 
			Spark[2] = SPR_addSprite(&spr_spark1, P[2].x-16-camPosX, AlturaDoHit-16+camPosY, TILE_ATTR(PAL1, FALSE, FALSE, FALSE)); 
			
			SPR_setVRAMTileIndex(Spark[1], 1519); //define uma posicao especifica para o GFX na VRAM
			SPR_setVRAMTileIndex(Spark[2], 1519); //define uma posicao especifica para o GFX na VRAM
			
			if(Spark[1]){ SPR_setDepth(Spark[1], 1); }
			if(Spark[2]){ SPR_setDepth(Spark[2], 1); }
			
			P[1].dataHBox[0]=0; P[1].dataHBox[1]=0; P[1].dataHBox[2]=0; P[1].dataHBox[3]=0;
			P[2].dataHBox[0]=0; P[2].dataHBox[1]=0; P[2].dataHBox[2]=0; P[2].dataHBox[3]=0;
			
			//XGM_setPCM(P1_SFX, snd_501, sizeof(snd_501)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3);
			
			doubleHitStep=0;
		}
		//101 102 104 105 106 113
		//151 152 154 155 
		//201 202 204 205 
	}
	
	////////////////////
	// CORPO x MAGIAS //
	//////////////////// -=≡ΣO)) x PLAYER
	
	if( P[player].fball.active && FUNCAO_COLISAO(
			P[player].fball.x + P[player].fball.dataHBox[0], P[player].fball.y + P[player].fball.dataHBox[1], P[player].fball.x + P[player].fball.dataHBox[2], P[player].fball.y + P[player].fball.dataHBox[3],
			P[enemy].x+P[enemy].dataBBox[0], P[enemy].y+P[enemy].dataBBox[1], P[enemy].x+P[enemy].dataBBox[2], P[enemy].y+P[enemy].dataBBox[3]
		)==1)
	{
		if(FUNCAO_CHECK_GUARD(P[player].fball.guardFlag, enemy))
		{
			/* Emitir antes do chip garante que o delta de vida do projétil
			   também seja consumido pelo ledger, como nos golpes corporais. */
			COMBAT_EVENTS_EMIT_SOURCE(player, enemy, P[player].state, COMBAT_EVENT_GUARD,
				COMBAT_EVENT_SOURCE_PROJECTILE, P[player].fball.instance);
			//DEFENDEU! em pe
			if(P[enemy].state>=107 && P[enemy].state<=109){
				PLAYER_STATE(enemy,110);
				FUNCAO_UPDATE_LIFESP(enemy,1,-2);
			}
			//DEFENDEU! em baixado
			if(P[enemy].state>=207 && P[enemy].state<=209){
				PLAYER_STATE(enemy,210);
				FUNCAO_UPDATE_LIFESP(enemy,1,-2);
			}

			if(P[player].attackPower==1){
				P[enemy].hitPause=16;
			}else{
				P[enemy].hitPause=20;
			} 

			P[enemy].stateMoveType = 3;
		}else{
			//NAO DEFENDEU!
			if(P[player].attackPower==1){
				P[enemy].hitPause=16;
			}else{
				P[enemy].hitPause=20;
			} 
			P[enemy].stateMoveType = 3;
			/* Registrar antes do delta de especial permite ao ledger carregar
			   também a contribuição da magia para o consumidor central. */
			COMBAT_EVENTS_EMIT_SOURCE(player, enemy, P[player].state, COMBAT_EVENT_HIT,
				COMBAT_EVENT_SOURCE_PROJECTILE, P[player].fball.instance);
			FUNCAO_UPDATE_LIFESP(enemy,1,-8); 
			FUNCAO_UPDATE_LIFESP(enemy,2, 11);

			/*
			if(P[enemy].y<gAlturaPiso || (P[enemy].state>=300 && P[enemy].state<=326) )
			{ 
				PLAYER_STATE(enemy,550); //cai apos cair sobre a magia
			}else{
				PLAYER_STATE(enemy,502); //recebe o hit da magia em pe
			}*/
			if(P[enemy].y==gAlturaPiso){ PLAYER_STATE(enemy,502); }else{ P[enemy].puloTimer=0; PLAYER_STATE(enemy,550); }
			
		}
		
		//desativa a magia ja que colidiu
		if(P[player].fball.active==1)
		{ 
			if(P[player].fball.spriteFBall)
			{ 
				SPR_releaseSprite(P[player].fball.spriteFBall); 
				P[player].fball.spriteFBall = NULL; 
			} 
			P[player].fball.active=0;
		}			
		
		//SPARK DE MAGIA SUMINDO
		if(Spark1_countDown>0){ SPR_releaseSprite(Spark[1]); }
		if(Spark2_countDown>0){ SPR_releaseSprite(Spark[2]); }
		if(player==1){Spark1_countDown=20;}
		if(player==2){Spark2_countDown=20;}
		
		if(player==1)//p1
		{
			//ryo
			if(P[player].direcao == 1)
			{
				if(P[player].id==1){ Spark[player] = SPR_addSpriteExSafe( &spr_ryo_702, P[enemy].x-80-camPosX, P[player].fball.y+camPosY, TILE_ATTR(PAL2, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD); }
			}else{
				if(P[player].id==1){ Spark[player] = SPR_addSpriteExSafe( &spr_ryo_702, P[enemy].x-camPosX, P[player].fball.y+camPosY, TILE_ATTR(PAL2, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD); }
			}
			
		}
		if(player==2)//p2
		{
			//ryo
			if(P[player].direcao == 1)
			{
				// Sprite* SPR_addSpriteExSafe(const SpriteDefinition* spriteDef, s16 x, s16 y, u16 attribut, u16 flag)

				if(P[player].id==1){ Spark[player] = SPR_addSpriteExSafe( &spr_ryo_702, P[enemy].x-80-camPosX, P[player].fball.y+camPosY, TILE_ATTR(PAL3, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC |SPR_FLAG_AUTO_TILE_UPLOAD); }
			}else{
				if(P[player].id==1){ Spark[player] = SPR_addSpriteExSafe( &spr_ryo_702, P[enemy].x-camPosX, P[player].fball.y+camPosY, TILE_ATTR(PAL3, FALSE, FALSE, FALSE), SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD); }
			}
			
		}
		
		//se o spark foi carregado com sucesso...
		if (Spark[player])
		{ 
			if(P[player].direcao == -1){ SPR_setHFlip(Spark[player], TRUE); }
			SPR_setDepth(Spark[player], 1); 
		}
		
		//reseta posicao da magia
		P[player].fball.x=-250;
		P[player].fball.y=-250; 
	}
	
	/////////////////////
	// MAGIAS x MAGIAS //
	///////////////////// -=≡ΣO)) x ((O3≡=-
	
	if( (P[player].fball.active && P[enemy].fball.active) && FUNCAO_COLISAO(
			P[player].fball.x + P[player].fball.dataHBox[0], P[player].fball.y + P[player].fball.dataHBox[1], P[player].fball.x + P[player].fball.dataHBox[2], P[player].fball.y + P[player].fball.dataHBox[3],
			P[enemy].fball.x + P[enemy].fball.dataHBox[0], P[enemy].fball.y + P[enemy].fball.dataHBox[1], P[enemy].fball.x + P[enemy].fball.dataHBox[2], P[enemy].fball.y + P[enemy].fball.dataHBox[3]
		)==1
		&& ( (P[player].fball.x!=0 && P[player].fball.y!=0) && (P[player].fball.x!=-250 && P[player].fball.y!=-250) ) )
	{
		//desativa a magia
		if(P[player].fball.active==1)
		{ 
			if(P[player].fball.spriteFBall)
			{ 
				SPR_releaseSprite(P[player].fball.spriteFBall); 
				P[player].fball.spriteFBall = NULL; 
			} 
			P[player].fball.active=0;
		}			
		if(P[enemy].fball.active==1)
		{ 
			if(P[enemy].fball.spriteFBall)
			{ 
				SPR_releaseSprite(P[enemy].fball.spriteFBall); 
				P[enemy].fball.spriteFBall = NULL; 
			} 
			P[enemy].fball.active=0;
		}	
		
		//SPARK DE MAGIA SUMINDO
		if(Spark1_countDown>0){ SPR_releaseSprite(Spark[1]); }
		if(Spark2_countDown>0){ SPR_releaseSprite(Spark[2]); }
		if(player==1){Spark1_countDown=20;}
		if(player==2){Spark2_countDown=20;}
		
		//se o spark foi carregado com sucesso...
		if (Spark[player])
		{ 
			if(P[player].direcao == -1){ SPR_setHFlip(Spark[player], TRUE); }
			SPR_setDepth(Spark[player], 1); 
		}
		if (Spark[enemy])
		{ 
			if(P[enemy].direcao == -1){ SPR_setHFlip(Spark[enemy], TRUE); }
			SPR_setDepth(Spark[enemy], 1); 
		}
		
		//reseta posicao da magia
		P[player].fball.x=-250;
		P[player].fball.y=-250; 
		P[enemy].fball.x=-250;
		P[enemy].fball.y=-250;
	}
}

void FUNCAO_FSM()
{
	
	/* Distance is an unsigned gameplay metric.  Deriving it from P1's facing
	   made a left-of-opponent pair produce a negative s16 that wrapped to a
	   huge u16 after a mass-box turn, disabling close-range throws. */
	{
		s16 delta = (s16)(P[2].x - P[1].x);
		gDistancia = (delta < 0) ? (u16)(-delta) : (u16)delta;
	}

	for(i=1; i<=2; i++)
	{
		u8 PA; //Player Attack (Player que ataca)
		u8 PR; //Player Receive (Player que recebe o dano)
		if(i==1){ PA=1; PR=2; }else{ PA=2; PR=1; }
		
		//hpig 1.1 bugfix - virar enquanto anda
		if((P[PA].state==410 || P[PA].state==420) && P[PA].direcao== 1 && (P[PA].x>P[PR].x)){ PLAYER_STATE(i,100); }
		if((P[PA].state==410 || P[PA].state==420) && P[PA].direcao==-1 && (P[PA].x<P[PR].x)){ PLAYER_STATE(i,100); }
		
		//Ataque depois da Esquiva
		if(P[i].state==103 && (
			P[i].key_JOY_A_status==1 || 
			P[i].key_JOY_B_status==1 || 
			P[i].key_JOY_C_status==1 || 
			P[i].key_JOY_X_status==1 || 
			P[i].key_JOY_Y_status==1 
		)	
		){ PLAYER_STATE(i,113); }

		//abaixando ; esquivando; levantando
		if((P[i].key_JOY_DOWN_status==1 || P[i].key_JOY_DOWN_status==2) && (P[i].state==100 || P[i].state==410 || P[i].state==420))
		{ 
			if(P[i].key_JOY_countdown[2]==0){ PLAYER_STATE(i,601); }else{ PLAYER_STATE(i,601);/*antigo 470*/ } //abaixar ou esquivar
		}
		if(P[i].key_JOY_DOWN_status==0 && P[i].state==200){ PLAYER_STATE(i,602); } //levantar
		
		//interrupcao da esquiva abaixada
		if(P[i].state==470 && P[i].animFrame==2 && P[i].key_JOY_DOWN_status==0)
		{ 
			P[i].animFrame=3; 
			P[i].frameTimeAtual=1; 
			P[i].frameTimeTotal=P[i].dataAnim[3]; 
		}
		
		//virando de lado (mudanca de estado)
		if(P[PA].direcao== 1 && P[PR].x<P[PA].x && P[PA].state==100){ PLAYER_STATE(i,607); P[PA].direcao=-1; }
		if(P[PA].direcao==-1 && P[PA].x<P[PR].x && P[PA].state==100){ PLAYER_STATE(i,607); P[PA].direcao= 1; }
		if(P[PA].direcao== 1 && P[PR].x<P[PA].x && P[PA].state==200){ PLAYER_STATE(i,608); P[PA].direcao=-1; }
		if(P[PA].direcao==-1 && P[PA].x<P[PR].x && P[PA].state==200){ PLAYER_STATE(i,608); P[PA].direcao= 1; }
		
		//ini pulos
		if((P[i].key_JOY_UP_status==1 || P[i].key_JOY_UP_status==2) && (P[i].state==100 || P[i].state==410 || P[i].state==420 || P[i].state==602))
		{ 
			if(P[i].key_JOY_RIGHT_status==2){ if(P[i].direcao==1){PLAYER_STATE(i,605);}else{PLAYER_STATE(i,603);} }
			if(P[i].key_JOY_RIGHT_status==0 && P[i].key_JOY_LEFT_status==0)PLAYER_STATE(i,604); 
			if(P[i].key_JOY_LEFT_status ==2){ if(P[i].direcao==1){PLAYER_STATE(i,603);}else{PLAYER_STATE(i,605);} }
		}
		
		//end pulos
		if((P[i].state==300 || P[i].state==310 || P[i].state==320) && P[i].y>=gAlturaPiso)
		{ 
			P[i].y=gAlturaPiso; P[i].puloTimer=0; P[i].hSpeed=0; 
			if(P[i].key_JOY_DOWN_status==2){PLAYER_STATE(i,200);}else{PLAYER_STATE(i,606);}
		}
		if((P[i].state>=301 && P[i].state<=326) && P[i].y>=gAlturaPiso)
		{ 
			P[i].y=gAlturaPiso; P[i].hSpeed=0; 
			if(P[i].key_JOY_DOWN_status==2){PLAYER_STATE(i,200);}else{PLAYER_STATE(i,606);}
		}
		
		//andando - andar ou correr
		if(P[i].direcao==1)
		{
			if(P[i].key_JOY_LEFT_status>0 && P[i].state==100){ 
				if(P[i].key_JOY_countdown[4]==0){ PLAYER_STATE(i,410); }else{ 
					if(P[i].inputArray[1]==4 && P[i].inputArray[0]==4){ PLAYER_STATE(i,471);  }else{ PLAYER_STATE(i,410); }
				}
			}
			if(P[i].key_JOY_RIGHT_status>0 && P[i].state==100){ 
				if(P[i].key_JOY_countdown[6]==0){ PLAYER_STATE(i,420); }else{ 
					if(P[i].inputArray[1]==6 && P[i].inputArray[0]==6){ PLAYER_STATE(i,472);  }else{ PLAYER_STATE(i,420); } 
				}
			}
			
			if(P[i].key_JOY_LEFT_status==0 && P[i].state==410){ PLAYER_STATE(i,100); } //end walk
			if(P[i].key_JOY_RIGHT_status==0 && P[i].state==420){ PLAYER_STATE(i,100); }

		}else{
			if(P[i].key_JOY_LEFT_status>0 && P[i].state==100){ 
				if(P[i].key_JOY_countdown[4]==0){ PLAYER_STATE(i,420); }else{ 
					if(P[i].inputArray[1]==4 && P[i].inputArray[0]==4){ PLAYER_STATE(i,472);  }else{ PLAYER_STATE(i,420); } 
				}
			}
			
			if(P[i].key_JOY_RIGHT_status>0 && P[i].state==100){ 
				if(P[i].key_JOY_countdown[6]==0){ PLAYER_STATE(i,410); }else{ 
					if(P[i].inputArray[1]==6 && P[i].inputArray[0]==6){ PLAYER_STATE(i,471);  }else{ PLAYER_STATE(i,410); }
				}
			}
			
			if(P[i].key_JOY_LEFT_status ==0 && P[i].state==420){ P[i].hSpeed=0; PLAYER_STATE(i,100); } //end walk
			if(P[i].key_JOY_RIGHT_status==0 && P[i].state==410){ P[i].hSpeed=0; PLAYER_STATE(i,100); }
		}
		
		//key_JOY_countdown eh um timer regressivo, ativado quando se aperta algum botao direcional, usado para Corrida e Esquiva, entre outros...
		if(P[i].key_JOY_countdown[8]>0){ P[i].key_JOY_countdown[8]--; }
		if(P[i].key_JOY_countdown[2]>0){ P[i].key_JOY_countdown[2]--; }
		if(P[i].key_JOY_countdown[4]>0){ P[i].key_JOY_countdown[4]--; }
		if(P[i].key_JOY_countdown[6]>0){ P[i].key_JOY_countdown[6]--; }
		
		//ativacao de 'key_JOY_countdown'...
		if(P[i].state==410 || P[i].state==420 || P[i].state==601 || P[i].state==603 || P[i].state==604 || P[i].state==605)
		{
			if(P[i].key_JOY_UP_status   ==1){ P[i].key_JOY_countdown[8]=12; P[i].key_JOY_countdown[2]=0; }
			if(P[i].key_JOY_LEFT_status ==1){ P[i].key_JOY_countdown[4]=12; P[i].key_JOY_countdown[6]=0; }
			if(P[i].key_JOY_RIGHT_status==1){ P[i].key_JOY_countdown[6]=12; P[i].key_JOY_countdown[4]=0; }
			if(P[i].key_JOY_DOWN_status ==1){ P[i].key_JOY_countdown[2]=12; P[i].key_JOY_countdown[8]=0; P[i].key_JOY_countdown[4]=0; P[i].key_JOY_countdown[6]=0; }
		}
		
		//time over decision; timeover
		if((gClockLTimer==0 && gClockRTimer==0) && P[1].state!=611 && P[1].state!=615)
		{
			bool updateWinsFlag=0;
			if(P[1].energiaBase> P[2].energiaBase){ PLAYER_STATE(1,611); P[1].wins++; updateWinsFlag=1; PLAYER_STATE(2,615); }
			if(P[1].energiaBase< P[2].energiaBase){ PLAYER_STATE(2,611); P[2].wins++; updateWinsFlag=2; PLAYER_STATE(1,615); }
			if(P[1].energiaBase==P[2].energiaBase){ PLAYER_STATE(1,615); PLAYER_STATE(2,615); }
			if(updateWinsFlag!=0){
				if(updateWinsFlag==1) //P1
				{
					//if(P[1].wins>=1){ SPR_setVisibility(GE[12].sprite, VISIBLE); }
					//if(P[1].wins>=2){ SPR_setVisibility(GE[13].sprite, VISIBLE); }
				}
				if(updateWinsFlag==2) //P2
				{
					//if(P[2].wins>=1){ SPR_setVisibility(GE[15].sprite, VISIBLE); }
					//if(P[2].wins>=2){ SPR_setVisibility(GE[14].sprite, VISIBLE); }
				}
			}
		}
		
		//Destroi Magias!
		if(P[i].fball.countDown>0){ P[i].fball.countDown--; }
		if(P[i].fball.countDown==1)
		{
			if(P[i].fball.active==1)
			{ 
				if(P[i].id==1 || P[i].id==2 || P[i].id==3)//ryo & ANDY & JOE
				{
					if(P[i].fball.spriteFBall)
					{ 
						SPR_releaseSprite(P[i].fball.spriteFBall); 
						P[i].fball.spriteFBall = NULL; 
						P[i].fball.x=-250;
						P[i].fball.y=-250; 
					} 
					P[i].fball.active=0;
				}
			}		
		}
		
		
		//------------------------------------------------------
		//Agarrao
		/* Throws share the close-range command window with the normal Y attack.
		   The authored body boxes keep fighters about 94 px apart on the stock
		   512 px stage, so the playable close band is 0..100 world pixels;
		   keeping this check before NORMAL_ATTACKS prevents a valid grab from
		   becoming state 152 instead. */
		/* Physics may have moved/separated the pair after the global distance
		   snapshot taken at FSM entry.  Use the live world X positions for the
		   throw edge so a point-blank Y press cannot observe a stale range. */
		s16 throwDelta = (s16)(P[2].x - P[1].x);
		u16 throwDistance = (throwDelta < 0) ? (u16)(-throwDelta) : (u16)throwDelta;
		if(P[i].key_JOY_Y_status==1 && throwDistance <= 100 &&
			 (fsm_throw_forward_held(i, (i==1) ? 2 : 1) || throwDistance <= 30) &&
			 (P[i].state==100 || P[i].state==410 || P[i].state==420 ||
			  P[i].state==481 || P[i].state==606))
		{ 
			PLAYER_STATE(i,800); //Inicio do agarrao
		}

		if (P[i].state == 801 && P[i].animFrame == 4) {
			PLAYER_STATE(i,802); //Se o agarrao pegar, segundo movimento do player
		}
		//------------------------------------------------------


		FUNCAO_FSM_DEFENSE(PA, PR); //Verifica o estado de defesa
		FUNCAO_FSM_NORMAL_ATTACKS(PA); //Verifica os ataques normais
		FUNCAO_FSM_SPECIAL_ATTACKS(PA); //Verificando os ataques especiais
		FUNCAO_FSM_COLLISION(PA, PR); //Verificando colisoes

		
		//Rage Explosion! Rage timer!
		/*
		if( 
		P[i].rageTimerCountdown==RAGETIMER && P[i].energiaSP>=32 
		&& (P[i].state==100 || P[i].state==200 || P[i].state==410 || P[i].state==420) 
		&& gPodeMover==1
		)
		{
			P[i].rageTimerCountdown--;
			PLAYER_STATE(i,618);
		}
		if(P[i].energiaSP>=32 && P[i].rageTimerCountdown<RAGETIMER && P[i].energiaBase>0 && gFrames>350){ if(P[i].rageTimerCountdown>0){ P[i].rageTimerCountdown--; } }
		if(P[i].rageTimerCountdown==0 && (P[i].state==100 || P[i].state==200)){ P[i].rageTimerCountdown=RAGETIMER; P[i].energiaSP=0; }
		*/
		
		//Vitoria
		if(
		 (P[PA].state==100 || P[PA].state==200 || P[PA].state==410 || P[PA].state==420) 
			 && (P[PA].state!=611 && P[PA].state!=612 && P[PA].state!=613 && P[PA].state!=614)
		 && (P[PR].energiaBase<=0)
		)
		{
			//Carrega 1 entre 4 poses de vitoria
			//2 neste caso :) 611;612
			//Ajuste a probabilidade conforme preferir. gPing10 = 10% ; variacao de 0 a 9
			if(gPing10>=1 && gPing10<=5){ PLAYER_STATE(PA,611); P[PA].wins++; }
			if(gPing10>=6 && gPing10<=9){ PLAYER_STATE(PA,612); P[PA].wins++; }
			//if(gPing10>=7 && gPing10<=9){ PLAYER_STATE(PA,613); P[PA].wins++; }
			if(gPing10==0              ){ PLAYER_STATE(PA,612); P[PA].wins++; } //Vc pode carregar uma pose diferente aqui, eu estou usando 3!
			
			//Exibe o contador de Wins correspondente
			if(PA==1) //P1
			{
				if(P[PA].wins>=1 && GE[12].sprite){ SPR_setVisibility(GE[12].sprite, VISIBLE); }
				if(P[PA].wins>=2 && GE[13].sprite){ SPR_setVisibility(GE[13].sprite, VISIBLE); }
			}
			if(PA==2) //P2
			{
				if(P[PA].wins>=1 && GE[15].sprite){ SPR_setVisibility(GE[15].sprite, VISIBLE); }
				if(P[PA].wins>=2 && GE[14].sprite){ SPR_setVisibility(GE[14].sprite, VISIBLE); }
			}
		}
	}
}

void FUNCAO_FSM_HITBOXES(u8 Player)
{
	bool reset_BBox=0;
	bool reset_HBox=0;
	
	switch ( P[Player].id )
	{

		case 0: //char_default
			switch ( P[Player].state )
			{
				case 100:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 15; P[Player].dataBBox[3]=  0; }
				break;
			
				case 101:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				//...
				break;
				
				case 102:
				//...
				break;
				
				case 103:
				reset_HBox=1; 
				reset_BBox=1;
				break;
				
				case 104:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				//...
				break;
				
				case 105:
				//...
				break;
				
				case 106:
				//...
				break;
				
				case 113:
				//...
				break;
				
				case 151:
				//...
				break;
				
				case 152:
				//...
				break;
				
				case 154:
				//...
				break;
				
				case 155:
				//...
				break;
				
				case 200:
				//...
				break;
				
				case 201:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				//...
				break;
				
				case 202:
				//...
				break;
				
				case 204:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				//...
				break;
				
				case 205:
				//...
				break;
				
				case 301:
				case 311:
				case 321:
				//...
				break;
				
				case 302:
				case 312:
				case 322:
				//...
				break;
				
				case 304:
				case 314:
				case 324:
				//...
				break;
				
				case 305:
				case 315:
				case 325:
				//...
				break;
				
				case 306:
				case 316:
				case 326:
				//...
				break;
				
				case 601:
				case 602:
				case 603:
				case 604:
				case 605:
				case 606:
				reset_HBox=1;
				break;
			}
		break;
		
		case 1: //RYO
			switch ( P[Player].state )
			{
				case 100:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 15; P[Player].dataBBox[3]=  0; }
				break;
			
				case 101:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 92; P[Player].dataHBox[2]= 60; P[Player].dataHBox[3]=-72; }
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;
				
				case 102:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 85; P[Player].dataHBox[2]= 67; P[Player].dataHBox[3]=-70; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
				
				case 103:
				reset_HBox=1; 
				reset_BBox=1;
				break;
				
				case 104:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]=  0; P[Player].dataHBox[1]=-110; P[Player].dataHBox[2]= 60; P[Player].dataHBox[3]=-85; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
				
				case 105:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 95; P[Player].dataHBox[2]= 95; P[Player].dataHBox[3]=-75; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
				
				case 106:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 35; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 90; P[Player].dataHBox[2]= 90; P[Player].dataHBox[3]=-70; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
				
				case 113:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==5){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 90; P[Player].dataHBox[2]= 65; P[Player].dataHBox[3]=-60; }
				if(P[Player].animFrame==6){ reset_HBox=1; }
				break;
				
				case 151:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 80; P[Player].dataHBox[2]= 45; P[Player].dataHBox[3]=-60; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
				
				case 152:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 90; P[Player].dataHBox[2]= 65; P[Player].dataHBox[3]=-60; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
				
				case 154:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 30; P[Player].dataHBox[2]= 80; P[Player].dataHBox[3]=-10; }
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;
				
				case 155:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=   0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-130; P[Player].dataHBox[2]= 60; P[Player].dataHBox[3]=- 50; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
				
				case 200:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 65; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==1){ reset_HBox=1; }
				break;
				
				case 201:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 65; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 70; P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=-50; }
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;
				
				case 202:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 65; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 15; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 90; P[Player].dataHBox[2]= 60; P[Player].dataHBox[3]=-70; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
				
				case 204:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 65; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 20; P[Player].dataHBox[2]= 65; P[Player].dataHBox[3]=  0; }
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;
				
				case 205:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 65; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 20; P[Player].dataHBox[2]=100; P[Player].dataHBox[3]=  0; }
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;
				
				case 300:
				case 310:
				case 320:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=-60; }
				/* fall through: jump start-up shares the airborne hitbox below */
				__attribute__((fallthrough));
				case 301:
				case 311:
				case 321:
				case 303:
				case 313:
				case 323:
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]=  0; P[Player].dataHBox[1]=- 80; P[Player].dataHBox[2]= 40; P[Player].dataHBox[3]=-40; }
				break;
				
				case 302:
				case 312:
				case 322:
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]=  0; P[Player].dataHBox[1]=- 70; P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=-40; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
				
				case 304:
				case 305:
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 65; P[Player].dataHBox[2]= 75; P[Player].dataHBox[3]=-45; }
				break;
				
				case 314:
				case 324:
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]=  0; P[Player].dataHBox[1]=- 40; P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=  0; }
				break;
				
				case 315:
				case 325:
				if(P[Player].animFrame==4){ P[Player].dataHBox[0]=  0; P[Player].dataHBox[1]=- 40; P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=-10; }
				if(P[Player].animFrame==5){ reset_HBox=1; }
				break;
				
				case 306:
				case 316:
				case 326:
				if(P[Player].animFrame==4){ P[Player].dataHBox[0]=-30; P[Player].dataHBox[1]=- 70; P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=-50; }
				if(P[Player].animFrame==5){ reset_HBox=1; }
				break;
				
				case 601:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 80; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==1){ reset_HBox=1; }
				break;
				
				case 602:
				case 603:
				case 604:
				case 605:
				case 606:
				reset_HBox=1;
				break;
				
				case 710:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 70; P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=-40; }
				if(P[Player].animFrame==4){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-100; P[Player].dataHBox[2]= 80; P[Player].dataHBox[3]=-70; }
				if(P[Player].animFrame==8){ reset_HBox=1; }
				if(P[Player].animFrame==4){ reset_BBox=1; }
				if(P[Player].animFrame==8){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 15; P[Player].dataBBox[3]=  0; }
				break;
				
				case 720:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==5){ P[Player].dataHBox[0]=-30; P[Player].dataHBox[1]=-100; P[Player].dataHBox[2]= 40; P[Player].dataHBox[3]=-50; }
				if(P[Player].animFrame==6){ P[Player].dataHBox[0]=-30; P[Player].dataHBox[1]=-130; P[Player].dataHBox[2]= 40; P[Player].dataHBox[3]=-50; }
				if(P[Player].animFrame==7){ P[Player].dataHBox[0]=-30; P[Player].dataHBox[1]=-100; P[Player].dataHBox[2]= 80; P[Player].dataHBox[3]=-50; }
				if(P[Player].animFrame==8){ reset_HBox=1; }
				if(P[Player].animFrame==5){ reset_BBox=1; }
				if(P[Player].animFrame==8){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 15; P[Player].dataBBox[3]=  0; }
				break;
				
				case 730:
				if(P[Player].animFrame== 1){ reset_BBox=1; }
				if(P[Player].animFrame== 7){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=-120; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=-70; }
				if(P[Player].animFrame== 3){ P[Player].dataHBox[0]=-10; P[Player].dataHBox[1]=- 80; P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=-60; }
				if(P[Player].animFrame== 4){ P[Player].dataHBox[0]=-10; P[Player].dataHBox[1]=-130; P[Player].dataHBox[2]= 40; P[Player].dataHBox[3]=-70; }
				if(P[Player].animFrame== 5){ reset_HBox=1; }
				break;

				//----------------------------------------------------------------
				//Agarrao
				case 800:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 90; P[Player].dataHBox[2]= 65; P[Player].dataHBox[3]=-60; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;

				case 801:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==3){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 90; P[Player].dataHBox[2]= 65; P[Player].dataHBox[3]=-60; }
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;

				case 802:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 65; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=  0; }
				if(P[Player].animFrame==2){ P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=- 20; P[Player].dataHBox[2]=100; P[Player].dataHBox[3]=  0; }
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;

				case 803:
				if(P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 15; P[Player].dataBBox[3]=  0; }
				break;
				//----------------------------------------------------------------
			}
		break;

		case 2: //KEN — strips are shorter than Ryo; active frames must match ken_anim_for()
			if(P[Player].animFrame==1)
			{
				P[Player].dataBBox[0]=-18; P[Player].dataBBox[1]=-90;
				P[Player].dataBBox[2]= 18; P[Player].dataBBox[3]=  0;
			}
			switch ( P[Player].state )
			{
				case 100:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				break;

				case 101: /* 1-frame jab, held */
				if(P[Player].animFrame==1){
					P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-80;
					P[Player].dataHBox[2]= 52; P[Player].dataHBox[3]=-48;
				}
				break;

				case 102:
				case 103:
				case 107:
				case 108:
				case 109:
				case 110:
				case 113:
				case 152:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-85;
					P[Player].dataHBox[2]= 72; P[Player].dataHBox[3]=-50;
				}
				break;

				case 104:
				case 154:
				if(P[Player].animFrame==1){
					P[Player].dataHBox[0]=  4; P[Player].dataHBox[1]=-100;
					P[Player].dataHBox[2]= 56; P[Player].dataHBox[3]=-60;
				}
				break;

				case 105:
				case 155:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-90;
					P[Player].dataHBox[2]= 70; P[Player].dataHBox[3]=-50;
				}
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;

				case 106:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]=  8; P[Player].dataHBox[1]=-90;
					P[Player].dataHBox[2]= 58; P[Player].dataHBox[3]=-40;
				}
				break;

				case 151:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-80;
					P[Player].dataHBox[2]= 70; P[Player].dataHBox[3]=-50;
				}
				break;

				case 200:
				if(P[Player].animFrame==1){
					P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=-65;
					P[Player].dataBBox[2]= 22; P[Player].dataBBox[3]=  0;
					reset_HBox=1;
				}
				break;

				case 201:
				case 202:
				case 204:
				case 205:
				if(P[Player].animFrame==1){
					P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=-65;
					P[Player].dataBBox[2]= 22; P[Player].dataBBox[3]=  0;
					reset_HBox=1;
				}
				if(P[Player].animFrame==3 || P[Player].animFrame==4){
					P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-50;
					P[Player].dataHBox[2]= 90; P[Player].dataHBox[3]=  0;
				}
				if(P[Player].animFrame==6){ reset_HBox=1; }
				break;

				case 301:
				case 302:
				case 304:
				case 305:
				case 306:
				case 311:
				case 312:
				case 314:
				case 315:
				case 316:
				case 321:
				case 322:
				case 324:
				case 325:
				case 326:
				if(P[Player].animFrame==2 || P[Player].animFrame==3){
					P[Player].dataHBox[0]=  0; P[Player].dataHBox[1]=-80;
					P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=-30;
				}
				if(P[Player].animFrame==5){ reset_HBox=1; }
				break;

				case 550:
				case 601:
				case 602:
				case 603:
				case 604:
				case 605:
				case 606:
				reset_HBox=1;
				break;

				case 710:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==2 || P[Player].animFrame==3){
					P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-90;
					P[Player].dataHBox[2]= 70; P[Player].dataHBox[3]=-40;
				}
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;

				case 720:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame>=4 && P[Player].animFrame<=6){
					P[Player].dataHBox[0]=-30; P[Player].dataHBox[1]=-100;
					P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=-40;
				}
				if(P[Player].animFrame==8){ reset_HBox=1; }
				break;

				case 730:
				if(P[Player].animFrame==1){ reset_BBox=1; reset_HBox=1; }
				if(P[Player].animFrame==3 || P[Player].animFrame==4){
					P[Player].dataHBox[0]=-10; P[Player].dataHBox[1]=-110;
					P[Player].dataHBox[2]= 50; P[Player].dataHBox[3]=-40;
				}
				if(P[Player].animFrame==6){ reset_HBox=1; }
				break;

				case 800:
				case 801:
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-90;
					P[Player].dataHBox[2]= 60; P[Player].dataHBox[3]=-50;
				}
				if(P[Player].animFrame==4){ reset_HBox=1; }
				break;
			}
		break;

		case 3: /* MUSGO — idle 80x104; active on last/only strip frame */
			if(P[Player].animFrame==1)
			{
				P[Player].dataBBox[0]=-24; P[Player].dataBBox[1]=-100;
				P[Player].dataBBox[2]= 24; P[Player].dataBBox[3]=  0;
			}
			switch ( P[Player].state )
			{
				case 100:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				break;

				case 101:
				if(P[Player].animFrame==1){
					P[Player].dataHBox[0]= 12; P[Player].dataHBox[1]=-85;
					P[Player].dataHBox[2]= 62; P[Player].dataHBox[3]=-40;
				}
				break;

				case 102:
				case 103:
				case 107:
				case 108:
				case 109:
				case 110:
				case 113:
				case 152:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]= 12; P[Player].dataHBox[1]=-90;
					P[Player].dataHBox[2]= 74; P[Player].dataHBox[3]=-42;
				}
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;

				case 104:
				case 154:
				case 700:
				if(P[Player].animFrame==1){
					P[Player].dataHBox[0]=  4; P[Player].dataHBox[1]=-110;
					P[Player].dataHBox[2]= 48; P[Player].dataHBox[3]=-30;
				}
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]= 12; P[Player].dataHBox[1]=-90;
					P[Player].dataHBox[2]= 72; P[Player].dataHBox[3]=-40;
				}
				break;

				case 105:
				case 155:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]= 12; P[Player].dataHBox[1]=-90;
					P[Player].dataHBox[2]= 72; P[Player].dataHBox[3]=-45;
				}
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;

				case 106:
				case 151:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-88;
					P[Player].dataHBox[2]= 68; P[Player].dataHBox[3]=-40;
				}
				break;

				case 200:
				if(P[Player].animFrame==1){
					P[Player].dataBBox[0]=-24; P[Player].dataBBox[1]=-70;
					P[Player].dataBBox[2]= 24; P[Player].dataBBox[3]=  0;
					reset_HBox=1;
				}
				break;

				case 201:
				case 202:
				case 204:
				case 205:
				if(P[Player].animFrame==1){
					P[Player].dataBBox[0]=-24; P[Player].dataBBox[1]=-70;
					P[Player].dataBBox[2]= 24; P[Player].dataBBox[3]=  0;
					reset_HBox=1;
				}
				if(P[Player].animFrame==2){
					P[Player].dataHBox[0]= 10; P[Player].dataHBox[1]=-50;
					P[Player].dataHBox[2]= 80; P[Player].dataHBox[3]=  0;
				}
				if(P[Player].animFrame==3){ reset_HBox=1; }
				break;

				case 301:
				case 302:
				case 304:
				case 305:
				case 306:
				case 311:
				case 312:
				case 314:
				case 315:
				case 316:
				case 321:
				case 322:
				case 324:
				case 325:
				case 326:
				if(P[Player].animFrame==2 || P[Player].animFrame==3){
					P[Player].dataHBox[0]=  0; P[Player].dataHBox[1]=-90;
					P[Player].dataHBox[2]= 52; P[Player].dataHBox[3]=-28;
				}
				if(P[Player].animFrame==5){ reset_HBox=1; }
				break;

				case 550:
				case 601:
				case 602:
				case 603:
				case 604:
				case 605:
				case 606:
				reset_HBox=1;
				break;

				case 710:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame==2 || P[Player].animFrame==3){
					P[Player].dataHBox[0]=  8; P[Player].dataHBox[1]=-110;
					P[Player].dataHBox[2]= 64; P[Player].dataHBox[3]=-30;
				}
				break;

				case 720:
				case 730:
				if(P[Player].animFrame==1){ reset_HBox=1; }
				if(P[Player].animFrame>=2){
					P[Player].dataHBox[0]=-20; P[Player].dataHBox[1]=-100;
					P[Player].dataHBox[2]= 56; P[Player].dataHBox[3]=-30;
				}
				break;
			}
		break;
	}
	
	if(P[Player].direcao==-1)//P[Player].dataHBox[0]<P[Player].dataHBox[2]) //Normaliza a box
	{
		s16 a;
		a = P[Player].dataHBox[0];
		P[Player].dataHBox[0] = P[Player].dataHBox[2];
		P[Player].dataHBox[2] = a;
		P[Player].dataHBox[0] = P[Player].dataHBox[0] * P[Player].direcao;
		P[Player].dataHBox[2] = P[Player].dataHBox[2] * P[Player].direcao;
	}
	
	//padroes
	if(P[Player].state==100 && P[Player].animFrame==1){ reset_HBox=1; } //parado
	//if( (P[Player].state==471 || P[Player].state==472) && P[Player].animFrame==1){ reset_BBox=1; } //esquiva dash
	
	if( (P[Player].state==471 || P[Player].state==472) && P[Player].animFrame==1){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 15; P[Player].dataBBox[3]=  0; }
	
	if( (P[Player].state>=610 && P[Player].state<=618) /*&& P[Player].animFrame==1*/ ){ reset_BBox=1; } //win poses, time over; rage explosion
	if( (P[Player].state==550) /*&& P[Player].animFrame==1*/ ){ reset_BBox=1; } //win poses, time over; rage explosion
	
	if(P[Player].state==300 || P[Player].state==310 || P[Player].state==320)
	{ 
		P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=-120; P[Player].dataBBox[2]= 25; P[Player].dataBBox[3]=-70; 
		reset_HBox=1; 
	}
	
	if(P[Player].state==606){ P[Player].dataBBox[0]=-20; P[Player].dataBBox[1]=- 90; P[Player].dataBBox[2]= 15; P[Player].dataBBox[3]=  0; }
	
	if(Player==1 && (P[2].state==110 || P[2].state==210)){ reset_HBox=1; }
	if(Player==2 && (P[1].state==110 || P[1].state==210)){ reset_HBox=1; }
	
	//resets
	if(reset_HBox==1){ P[Player].dataHBox[0]=0; P[Player].dataHBox[1]=0; P[Player].dataHBox[2]=0; P[Player].dataHBox[3]=0; } //Hit Boxes
	if(reset_BBox==1){ P[Player].dataBBox[0]=0; P[Player].dataBBox[1]=0; P[Player].dataBBox[2]=0; P[Player].dataBBox[3]=0; } //Body Boxes
	
}
