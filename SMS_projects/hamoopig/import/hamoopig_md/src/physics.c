#include <genesis.h>
#include "physics.h"
#include "globals.h"
#include "player.h"
#include "collision.h"

void FUNCAO_PHYSICS() //FISICA!
{
	for(i=1; i<=2; i++)
	{
		/*KOF94*/
		//-----------------------------------------------------------------------------------------
		if(P[i].id==1) //RYO
		{
			
			//106
			if(P[i].state==106 && P[i].hitPause==0)
			{
				if(P[i].animFrame==3){ if(gPing2==1){ P[i].x+=1*P[i].direcao; } }
			}
			
			//velocidade da magia - Hadouken Type
			if(P[i].state==700 && P[i].animFrame==5)
			{
				if(P[i].attackPower==1){ P[i].fball.speedX = 2; }
				if(P[i].attackPower==2){ P[i].fball.speedX = 4; }
			}
			
			//710
			if(P[i].state==710 && P[i].hitPause==0)
			{
				if(P[i].animFrame>=4 && P[i].animFrame<=7)
				{
					//X
					if(P[i].attackPower==1){ if(P[i].direcao==1){ P[i].x+=4; }else{ P[i].x-=4; } }
					if(P[i].attackPower==2){ if(P[i].direcao==1){ P[i].x+=7; }else{ P[i].x-=7; } }
					
					//Y
					if(P[i].animFrame==4){ P[i].y-=2; }
					if(P[i].animFrame==5)
					{ 
						if(P[i].frameTimeAtual==1){ P[i].y--; }
						if(P[i].frameTimeAtual==2){ P[i].y--; }
						if(P[i].frameTimeAtual==3){  }
						if(P[i].frameTimeAtual==4){  }
					}
					if(P[i].animFrame==6)
					{ 
						if(P[i].frameTimeAtual==1){  }
						if(P[i].frameTimeAtual==2){  }
						if(P[i].frameTimeAtual==3){ P[i].y++; }
						if(P[i].frameTimeAtual==4){ P[i].y++; }
					}
					if(P[i].animFrame==7){ P[i].y+=2; }
				}
			}
			
			//720
			if(P[i].state==720 && P[i].hitPause==0) 
			{
				//X
				if(P[i].animFrame==5)
				{
					if(P[i].direcao==1){ P[i].x+=9; }else{ P[i].x-=9; }
				}
				if(P[i].animFrame>=6 && P[i].animFrame<=7)
				{
					if(P[i].direcao==1){ P[i].x+=7; }else{ P[i].x-=7; }
				}
				if(P[i].animFrame==8)
				{
					if(P[i].direcao==1){ P[i].x+=3; }else{ P[i].x-=3; }
				}
				//Y
				if(P[i].animFrame>=5 && P[i].animFrame<=6)
				{
					if(P[i].attackPower==1){ P[i].y-=1; }
					if(P[i].attackPower==2){ P[i].y-=3; }
				}
				if(P[i].animFrame>=7 && P[i].animFrame<=8)
				{
					P[i].y+=3;
				}
				
				if(P[i].y>gAlturaPiso)
				{
					P[i].y=gAlturaPiso;
					PLAYER_STATE(i, 606);
				}
				
			}
			
			//730 - Roris Type
			if(P[i].state==730 && P[i].hitPause==0) 
			{
				if (i == 1) { //P1
					//Y
					if (P[i].animFrame >= 4) {
						if (P[i].animFrame == 4 && P[i].setup) {
							P[i].gravidadeY = 2;

							if(P[i].attackPower == 1){
								P[i].impulsoY = -14;
							} else {
								P[i].impulsoY = -18;
							}

							P[i].setup = FALSE;
						}

						if (P[i].animFrame == 5 && P[i].frameTimeAtual == 1) {
							P[i].impulsoY = 0;
						}

						P[i].cicloInteracoesGravidadeCont++;
						if(P[i].cicloInteracoesGravidadeCont >= P[i].cicloInteracoesGravidade + 1){
							P[i].cicloInteracoesGravidadeCont = 0;

							P[i].y += P[i].impulsoY;
							P[i].impulsoY += P[i].gravidadeY;
						}
					}
				}

				if (i == 2) { //P2
					//Y
					if(P[i].animFrame < 5){
						if(P[i].animFrame==4){ P[i].y-=4; }
					}else{
						if(P[i].animFrame==5){ P[i].y+=0; }
						if(P[i].animFrame==6){ P[i].y+=2; }
						if(P[i].animFrame==7){ P[i].y+=4; }
						if(P[i].animFrame==8){ P[i].y+=6; }
					}
				}

				//X
				if(P[i].animFrame == 4){
					if(P[i].attackPower == 1){
						P[i].x += 1 * P[i].direcao; 
					}else{
						P[i].x += 2 * P[i].direcao; 
					}
				}

				if (P[i].y > gAlturaPiso) {
					P[i].y = gAlturaPiso;
					PLAYER_STATE(i, 606); 
				}
			}
		}
		//-----------------------------------------------------------------------------------------
		
		//Hits Movement, deslocamento dos Players para tras, durante os ataques
		if(P[i].state>=500 && P[i].state<=550 && P[i].hitPause==0)
		{
			u8 PA=0; //Player que Ataca
			u8 PR=0; //Player que Recebe o Ataque
			if(i == 1){ PA = 2; PR = 1; }else{ PA = 1; PR = 2; }
			
			//Nota, sem as condicoes abaixo, o deslocamento sera continuo, enquanto durar a animacao de Hit
			//Esse algoritimo simples simula a desaceleracao, ou friccao, causada pelo atrito com o solo
			if(P[PR].animFrame<=3)
			{ 
				if(P[PR].animFrame==1) {
					P[PR].hSpeed = 3;
					if(P[PA].state>=301 && P[PA].state<=326){
						P[PR].hSpeed = 2;
					} 
				} //vel 2 ou 3
				if(P[PR].animFrame==2) {
					P[PR].hSpeed = 2; 
				} //vel 2
				if(P[PR].animFrame==3) {
					P[PR].hSpeed = 1; 
				} //vel 1
				
				//ryo; state:730
				if((P[PA].id==1 && P[PA].state==730 && P[PA].animFrame<=3))
				{
					P[PR].hSpeed=1;
				}
				
				P[PR].x += P[PR].hSpeed*(P[PR].direcao*-1);
			}
			
			//Limites laterais
			if(P[PR].x >= gLimiteCenarioD && P[PR].stateMoveType == 2)
			{
				if (P[PA].attackPower==1) { 
					P[PA].hSpeed = 2; 
				} else { 
					P[PA].hSpeed = 4; 
				}
				if (gPing2 == 1 && P[PR].state != 550) {
					P[PA].x += P[PA].hSpeed*(P[PA].direcao*-1); 
				}
			}
			if(P[PR].x <= gLimiteCenarioE && P[PR].stateMoveType == 2)
			{
				if (P[PA].attackPower==1) {
					P[PA].hSpeed = 2;
				} else {
					P[PA].hSpeed = 4;
				}
				if (gPing2 == 1 && P[PR].state != 550) {
					P[PA].x += P[PA].hSpeed*(P[PA].direcao*-1);
				}
			}
		}
		
		//andar
		if(P[i].state==410 || P[i].state==420)
		{
			P[i].hSpeed=2;
			if(P[i].state==410){P[i].x+=P[i].hSpeed*(P[i].direcao*-1);}
			if(P[i].state==420){P[i].x+=P[i].hSpeed*(P[i].direcao);}
		}
		
		//esquiva frente e tras
		if(P[i].state==471 || P[i].state==472)
		{
			if(P[i].animFrame>=1){ P[i].hSpeed=6; if(P[i].state==471){ P[i].hSpeed=7; } }
			if(P[i].animFrame>=2){ P[i].hSpeed=3; }
			if(P[i].animFrame>=3){ P[i].hSpeed=2; }
			if(P[i].animFrame>=4){ P[i].hSpeed=1; } //anula o deslocamento
			
			if(P[i].id==5)
			{
				if(P[i].animFrame>=1){ P[i].hSpeed=0; if(P[i].state==471){ P[i].hSpeed=0; } }
				if(P[i].animFrame>=2){ P[i].hSpeed=6; }
				if(P[i].animFrame>=3){ P[i].hSpeed=6; }
				if(P[i].animFrame>=4){ P[i].hSpeed=4; } //anula o deslocamento
			}
			
			if(P[i].state==471){P[i].x+=P[i].hSpeed*(P[i].direcao*-1);}
			if(P[i].state==472){P[i].x+=P[i].hSpeed*(P[i].direcao);}
		}
		
		//defesas
		if( (P[i].state==110 || P[i].state==210) && P[i].hitPause==0)
		{
			P[i].hSpeed=4;
			if(P[i].state==110){P[i].x+=P[i].hSpeed*(P[i].direcao*-1);}//defesa em pe
			if(P[i].state==210){P[i].x+=P[i].hSpeed*(P[i].direcao*-1);}//defesa abaixado
			
			u8 PA=0; //Player que Ataca
			u8 PR=0; //Player que Recebe o Ataque
			if(i == 1){ PA = 2; PR = 1; }else{ PA = 1; PR = 2; }
			
			//Limites laterais
			if(P[PR].x >= gLimiteCenarioD && P[PR].stateMoveType == 2)
			{
				if(P[PA].attackPower==1){
					P[PA].hSpeed = 3;
				}else{
					P[PA].hSpeed = 5; 
				} 
				if(gPing2 == 1){ 
					P[PA].x += P[PA].hSpeed*(P[PA].direcao*-1); 
				}
			}
			if(P[PR].x <= gLimiteCenarioE && P[PR].stateMoveType == 2)
			{
				if(P[PA].attackPower==1){ 
					P[PA].hSpeed = 3; 
				}else{ 
					P[PA].hSpeed = 5; 
				} 
				if(gPing2 == 1){
					P[PA].x += P[PA].hSpeed*(P[PA].direcao*-1); 
				}
			}
		}
		
		//pulos
		if(P[i].hitPause==0)
		{
			if(P[i].puloTimer!=0){ P[i].puloTimer++; }

			if (i == 1) { //P1
				if (P[i].state >= 300 && P[i].state <= 326) {

					if (P[i].puloTimer == 2) {
						P[i].gravidadeY = 2;
						P[i].impulsoY = -20;
						P[i].hSpeed = 3;
						P[i].shotJump = FALSE;
					}

					if (P[i].puloTimer == 8 && P[i].key_JOY_UP_status == 0) {
						P[i].shotJump = TRUE;
						P[i].impulsoY = -8;
					}

					P[i].cicloInteracoesGravidadeCont++;
					if(P[i].cicloInteracoesGravidadeCont >= P[i].cicloInteracoesGravidade + 1){
						P[i].cicloInteracoesGravidadeCont = 0;

						P[i].y += P[i].impulsoY;
						P[i].impulsoY += P[i].gravidadeY;
					}

					if(P[i].state >= 320 && P[i].state <= 326){
						P[i].x += P[i].hSpeed *(P[i].direcao);
					}
					if(P[i].state >= 310 && P[i].state <= 316){
						P[i].x += P[i].hSpeed *(P[i].direcao*-1);
					}
					if(P[i].y > gAlturaPiso)
					{
						P[i].y = gAlturaPiso;
						P[i].impulsoY = 0;
					}
				}
			}

			if (i == 2) { //P2
				if(P[i].state>=300 && P[i].state<=326)
				{ 
					P[i].hSpeed=3;
					/*samsho2*/ //hard code :P
					//o metodo a seguir eh extremamente preciso, mas exige notacao manual!
					//para outros metodos de movimento, ver fisica no state 550, ou outros golpes por exemplo
					if(P[i].puloTimer== 1){ P[i].y-=11; P[i].shotJump=FALSE; }
					if(P[i].puloTimer== 2){ P[i].y-=11; P[i].shotJump=FALSE; }
					if(P[i].puloTimer== 3){ P[i].y-=10; }
					if(P[i].puloTimer== 4){ P[i].y-= 9; }
					if(P[i].puloTimer== 5){ P[i].y-= 9; }
					if(P[i].puloTimer== 6){ P[i].y-= 8; }
					if(P[i].puloTimer== 7){ P[i].y-= 8; }
					if(P[i].puloTimer== 8){ P[i].y-= 8; }
					
					if(P[i].puloTimer== 8){ if(P[i].key_JOY_UP_status==0){ P[i].shotJump=TRUE; } }
					
					//pulo curto
					if(P[i].shotJump==TRUE)
					{
						if(P[i].puloTimer== 9){ P[i].y-= 4; }
						if(P[i].puloTimer==10){ P[i].y-= 2; }
						if(P[i].puloTimer==11){ P[i].y-= 2; } 
						if(P[i].puloTimer==12){ P[i].y-= 1; }
						if(P[i].puloTimer==13){ P[i].y-= 1; }
						if(P[i].puloTimer==14){ P[i].y+= 0; }
						if(P[i].puloTimer==15){ P[i].y+= 0; }
						if(P[i].puloTimer==16){ P[i].y+= 0; }
						if(P[i].puloTimer==17){ P[i].y+= 0; }
						if(P[i].puloTimer==18){ P[i].y+= 1; }
						if(P[i].puloTimer==19){ P[i].y+= 1; }
						if(P[i].puloTimer==20){ P[i].y+= 2; }
						if(P[i].puloTimer==21){ P[i].y+= 2; }
						if(P[i].puloTimer==22){ P[i].y+= 2; }
						if(P[i].puloTimer==23){ P[i].y+= 2; }
						if(P[i].puloTimer==24){ P[i].y+= 4; }
						if(P[i].puloTimer==25){ P[i].y+= 4; } 
						if(P[i].puloTimer==26){ P[i].y+= 6; }
						if(P[i].puloTimer==27){ P[i].y+= 7; }
						if(P[i].puloTimer==28){ P[i].y+= 8; }
						if(P[i].puloTimer==29){ P[i].y+= 9; }
						if(P[i].puloTimer==30){ P[i].y+= 10; }
						if(P[i].puloTimer==31){ P[i].y+= 11; }
						if(P[i].puloTimer==32){ P[i].y+= 11; }
						if(P[i].puloTimer==33){ P[i].puloTimer=45; P[i].y+= 1; }
					}
					
					//pulo longo
					if(P[i].shotJump==FALSE)
					{
						if(P[i].puloTimer== 9){ P[i].y-= 7; }
						if(P[i].puloTimer==10){ P[i].y-= 6; } 
						if(P[i].puloTimer==11){ P[i].y-= 6; }
						if(P[i].puloTimer==12){ P[i].y-= 5; }
						if(P[i].puloTimer==13){ P[i].y-= 5; }
						if(P[i].puloTimer==14){ P[i].y-= 4; }
						if(P[i].puloTimer==15){ P[i].y-= 4; }
						if(P[i].puloTimer==16){ P[i].y-= 3; }
						if(P[i].puloTimer==17){ P[i].y-= 3; }
						if(P[i].puloTimer==18){ P[i].y-= 3; }
						if(P[i].puloTimer==19){ P[i].y-= 1; }
						if(P[i].puloTimer==20){ P[i].y-= 2; } 
						if(P[i].puloTimer==21){ P[i].y-= 0; }
						if(P[i].puloTimer==22){ P[i].y-= 1; }
						if(P[i].puloTimer==23){ P[i].y+= 1; }
						if(P[i].puloTimer==24){ P[i].y+= 0; }
						if(P[i].puloTimer==25){ P[i].y+= 2; }
						if(P[i].puloTimer==26){ P[i].y+= 1; }
						if(P[i].puloTimer==27){ P[i].y+= 3; }
						if(P[i].puloTimer==28){ P[i].y+= 3; }
						if(P[i].puloTimer==29){ P[i].y+= 3; }
						if(P[i].puloTimer==30){ P[i].y+= 4; } 
						if(P[i].puloTimer==31){ P[i].y+= 4; }
						if(P[i].puloTimer==32){ P[i].y+= 5; }
						if(P[i].puloTimer==33){ P[i].y+= 5; }
						if(P[i].puloTimer==34){ P[i].y+= 6; }
						if(P[i].puloTimer==35){ P[i].y+= 6; }
						if(P[i].puloTimer==36){ P[i].y+= 7; }
						if(P[i].puloTimer==37){ P[i].y+= 8; }
						if(P[i].puloTimer==38){ P[i].y+= 8; }
						if(P[i].puloTimer==39){ P[i].y+= 8; }
						if(P[i].puloTimer==40){ P[i].y+= 9; } 
						if(P[i].puloTimer==41){ P[i].y+= 9; }
						if(P[i].puloTimer==42){ P[i].y+=10; }
						if(P[i].puloTimer==43){ P[i].y+=11; }
						if(P[i].puloTimer==44){ P[i].y+=11; }
						if(P[i].puloTimer==45){ P[i].y+= 1; }
					}
					
					if(P[i].state>=320 && P[i].state<=326){ P[i].x+=P[i].hSpeed*(P[i].direcao); }
					if(P[i].state>=310 && P[i].state<=316){ P[i].x+=P[i].hSpeed*(P[i].direcao*-1); }
				}
				
				if(P[i].state==1310)
				{
					P[i].hSpeed=4;
					
					if(P[i].puloTimer== 1){ P[i].y-=6; }
					if(P[i].puloTimer== 2){ P[i].y-=6; }
					if(P[i].puloTimer== 3){ P[i].y-=6; }
					if(P[i].puloTimer== 4){ P[i].y-=6; }
					if(P[i].puloTimer== 5){ P[i].y-=4; }
					if(P[i].puloTimer== 6){ P[i].y-=4; }
					if(P[i].puloTimer== 7){ P[i].y-=4; }
					if(P[i].puloTimer== 8){ P[i].y-=4; }
					if(P[i].puloTimer== 9){ P[i].y+=4; }
					if(P[i].puloTimer==10){ P[i].y+=4; } 
					if(P[i].puloTimer==11){ P[i].y+=4; }
					if(P[i].puloTimer==12){ P[i].y+=4; }
					if(P[i].puloTimer==13){ P[i].y+=6; }
					if(P[i].puloTimer==14){ P[i].y+=6; }
					if(P[i].puloTimer==15){ P[i].y+=6; }
					if(P[i].puloTimer==16){ P[i].y=gAlturaPiso; PLAYER_STATE(i, 606); P[i].puloTimer=0; }
					
					P[i].x+=P[i].hSpeed*(P[i].direcao*-1);
				}
			}
		}
		
		/*samsho2*/
		//'516' CAINDO (Apos Magia do Haohmaru)
		if( P[i].hitPause==0)
		{
			P[i].cicloInteracoesGravidadeCont++;
			
			if(P[i].state==516)
			{
				if(P[i].cicloInteracoesGravidadeCont>=P[i].cicloInteracoesGravidade){
					P[i].cicloInteracoesGravidadeCont=0;
					P[i].impulsoY = P[i].impulsoY+P[i].gravidadeY;
					P[i].impulsoY-=1;
				}
				P[i].y += P[i].impulsoY;
				if(gPing2==1){ if(P[i].direcao==1){ P[i].x-=1; }else{ P[i].x+=1; } }
			}
		}
		
		//'516' > Altura Piso
		if(P[i].state==516 && P[i].y>gAlturaPiso)
		{
			P[i].y=gAlturaPiso-1;
			P[i].gravidadeY = gravidadePadrao;
			P[i].impulsoY = -6;//-14
			PLAYER_STATE(i,551);
		}
		
		//'550' CAINDO
		if( P[i].hitPause==0)
		{
			P[i].cicloInteracoesGravidadeCont++;
			
			if(P[i].state==550)
			{
				if(P[i].cicloInteracoesGravidadeCont>=P[i].cicloInteracoesGravidade){
					P[i].cicloInteracoesGravidadeCont=0;
					P[i].impulsoY = P[i].impulsoY+P[i].gravidadeY;
					P[i].impulsoY-=1;
				}
				P[i].y += P[i].impulsoY;
				if(P[i].direcao==1){ P[i].x-=2; }else{ P[i].x+=2; }
			}
		}
		
		//'550' > Altura Piso
		if(P[i].state==550 && P[i].y>gAlturaPiso)
		{
			P[i].y=gAlturaPiso-1;
			P[i].gravidadeY = gravidadePadrao;
			P[i].impulsoY = -6;//-14
			PLAYER_STATE(i,551);
		}
		
		if(P[i].state==551){
			if(P[i].cicloInteracoesGravidadeCont>=P[i].cicloInteracoesGravidade){
				P[i].cicloInteracoesGravidadeCont=0;
				P[i].impulsoY = P[i].impulsoY+P[i].gravidadeY;
				P[i].impulsoY-=1;
			}
			P[i].y += P[i].impulsoY;
			/*
			 * 551 is the grounded settle phase.  The knock-back belongs to
			 * 550 (airborne fall); continuing it here let a defeated fighter
			 * walk out of the camera before state 570 could display the
			 * authored grounded pose.
			 */
		}
		
		//'551' > Altura Piso
		if(P[i].state==551 && P[i].y>gAlturaPiso)
		{
			P[i].y=gAlturaPiso;
			if(P[i].x < gLimiteCenarioE) P[i].x = gLimiteCenarioE;
			if(P[i].x > gLimiteCenarioD) P[i].x = gLimiteCenarioD;
			PLAYER_STATE(i,570);
		}
		
		//-----------------------------------------------------------------------------------------
		
		//'MAGIAS' FISICA
		/*
		if( P[i].hitPause==0)
		{
			//P[i].cicloInteracoesGravidadeCont++;
			
			if( (P[i].state==710 || P[i].state==720 || P[i].state==730 || P[i].state==740 || P[i].state==750) && P[i].y!=gAlturaPiso )
			{
				if(P[i].cicloInteracoesGravidadeCont>=P[i].cicloInteracoesGravidade){
					P[i].cicloInteracoesGravidadeCont=0;
					P[i].impulsoY = P[i].impulsoY+P[i].gravidadeY;
					P[i].impulsoY-=1;
				}
				P[i].y += P[i].impulsoY;
				if(P[i].direcao==-1){ P[i].x-=2; }else{ P[i].x+=2; }
			}
		}
		*/
		
		//'MAGIAS' FISICA > Altura Piso
		//HAOHMARU (magia 720)
		/*
		if( (P[i].state==720) && P[i].y+2>gAlturaPiso)
		{
			P[i].y = gAlturaPiso;
			P[i].frameTimeAtual = P[i].frameTimeTotal; //Passa para o proximo frame de animacao
		}
		*/
		
		//-----------------------------------------------------------------------------------------
		
		//Movimento das Magias
		if(P[i].fball.active == 1)
		{
			P[i].fball.x += P[i].fball.speedX * P[i].fball.direcao;
			SPR_setPosition( P[i].fball.spriteFBall, P[i].fball.x-camPosX, P[i].fball.y+camPosY );
			//if(P[i].fBallX<gLimiteCenarioE-100){ SPR_releaseSprite(P[i].fBall); P[i].fBallActive=0; P[i].fBallX=-255; P[i].fBallY=-255; }
			//if(P[i].fBallX>gLimiteCenarioD+100){ SPR_releaseSprite(P[i].fBall); P[i].fBallActive=0; P[i].fBallX=-255; P[i].fBallY=-255; }

			if((P[i].fball.x < camPosX-60) || (P[i].fball.x > camPosX+320-20)) {
				SPR_releaseSprite(P[i].fball.spriteFBall); 
				P[i].fball.spriteFBall = NULL; 
				P[i].fball.active=0; 
				P[i].fball.x=-255; 
				P[i].fball.y=-255; 
			}
		}

		//hitpause shake
		if(P[i].hitPause>0)
		{
			if(P[i].energiaBase>0 && (P[i].stateMoveType == 2 || P[i].stateMoveType == 3))
			{
				if(gPing2==0){ P[i].x-=2; }
				if(gPing2==1){ P[i].x+=2; }
			}			
			P[i].hitPause--;
		}

		//Colisao Mass Boxes
		if(P[1].state!=472 && P[2].state!=472)
		{
			if(FUNCAO_COLISAO(
				P[1].x+P[1].dataMBox[0], P[1].y+P[1].dataMBox[1], P[1].x+P[1].dataMBox[2], P[1].y+P[1].dataMBox[3], 
				P[2].x+P[2].dataMBox[0], P[2].y+P[2].dataMBox[1], P[2].x+P[2].dataMBox[2], P[2].y+P[2].dataMBox[3]
			)){

				if (P[1].y < gAlturaPiso || P[2].y < gAlturaPiso) { //Um dos lutadores esta no ar

					u8 PAir = 0; //Player que esta no ar
					u8 PGround = 0; //Player que esta no chao
					if(P[1].y < gAlturaPiso){
						PAir = 1; PGround = 2;
					}else{
						PAir = 2; PGround = 1;
					}

					if (P[PAir].x <= P[PGround].x) {
						P[PAir].x -= 5;
					} else if (P[PAir].x >= P[PGround].x) {
						P[PAir].x += 5;
					}

				} else { //Os dois lutadoes estao no chao
					u8 tempBigHSpeed=0;

					if(P[1].hSpeed >= P[2].hSpeed){
						tempBigHSpeed = P[1].hSpeed;
					}else{
						tempBigHSpeed = P[2].hSpeed;
					}
					if(tempBigHSpeed == 0){
						tempBigHSpeed = 5;
					}

					if(P[1].x < P[2].x){
						P[1].x -= tempBigHSpeed;
						P[2].x += tempBigHSpeed;
					}else{
						P[1].x += tempBigHSpeed;
						P[2].x -= tempBigHSpeed;
					}
				}
			}
		}

		//-----------------------------------------------------------------------------------------
		//corrige posX //limites do cenario //Essa parte tem que ficar aqui no final
		//metoo novo, hamoopig 1.1
		if (P[i].x < gLimiteCenarioE) {
			P[i].x = gLimiteCenarioE;
			if (P[i].y < gAlturaPiso) {
				P[i].x += 5;
			}
		}
		if(P[i].x > gLimiteCenarioD) {
			P[i].x = gLimiteCenarioD;
			if (P[i].y < gAlturaPiso) {
				P[i].x -= 5;
			}
		}

		if (P[1].x <= P[2].x) {
			gDistancia = P[2].x-P[1].x;
		} else {
			gDistancia = P[1].x-P[2].x;
		}
		
		if (gDistancia > 260) { //Verifica a distancia maxima entre os lutadores
			if (P[1].x < P[2].x) {
				if (i == 1) {
					P[1].x += gDistancia - 260;
				} else if (i == 2) {
					P[2].x -= gDistancia - 260;
				}
			} else {
				if (i == 1) {
					P[1].x -= gDistancia - 260;
				} else if (i == 2) {
					P[2].x += gDistancia - 260;
				}
			}
		}
	}
}

