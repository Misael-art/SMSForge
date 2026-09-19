#include <genesis.h>
#include "player.h"
#include "combat_event.h"
#include "globals.h"
#include "config.h"
#include "sprite.h"
#include "sound.h"
#include "graphics.h"
#include "fsm.h"

#ifndef HAMOOPIG_DMA_LAB_REUSE_STATE_SPRITE
#define HAMOOPIG_DMA_LAB_REUSE_STATE_SPRITE 0
#endif

static bool player_is_attack_state(u16 state)
{
	return ((state >= 101 && state <= 106) ||
		(state >= 151 && state <= 156) ||
		(state >= 201 && state <= 206) ||
		(state >= 301 && state <= 306) ||
		(state >= 311 && state <= 316) ||
		(state >= 321 && state <= 326) ||
		(state >= 700 && state <= 790) || state == 113 ||
		state == 800 || state == 801 || state == 802);
}
#ifndef HAMOOPIG_DMA_LAB_DELAYED_FRAME
#define HAMOOPIG_DMA_LAB_DELAYED_FRAME 1
#endif
#ifndef HAMOOPIG_DMA_LAB_IDLE_SLOW
#define HAMOOPIG_DMA_LAB_IDLE_SLOW 0
#endif
#ifndef HAMOOPIG_STABLE_PLAYER_SPRITE
#define HAMOOPIG_STABLE_PLAYER_SPRITE 1
#endif
#if HAMOOPIG_DMA_LAB_DELAYED_FRAME
/* Let SGDK's sprite engine apply DMA back-pressure.  The old flag forced
   every fighter frame into the queue even when the NTSC envelope was already
   full, producing a visible one-frame overrun on large animation frames. */
#undef SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE
#define SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE 0
#endif

/* Keep one SGDK sprite object per fighter for the whole round.  Releasing and
   adding a large metasprite for every state repeatedly perturbs the movable
   VRAM allocator; after enough transitions the streamed frame can be shown
   before its upload has settled.  setDefinition keeps the object identity and
   only reallocates when the definition footprint changes. */
Sprite* PLAYER_SET_SPRITE(u8 Player, const SpriteDefinition *definition,
                          s16 x, s16 y, u16 attribut, u16 flags)
{
	Sprite *sprite = P[Player].sprite;
	if(!sprite)
	{
		return SPR_addSpriteExSafe(definition, x, y, attribut, flags);
	}
	if(!SPR_setDefinition(sprite, definition))
	{
		/* Keep the previous valid frame if a transient allocation fails. */
		return sprite;
	}
	SPR_setPosition(sprite, x, y);
	SPR_setPalette(sprite, (attribut & TILE_ATTR_PALETTE_MASK) >> TILE_ATTR_PALETTE_SFT);
	SPR_setPriority(sprite, (attribut & TILE_ATTR_PRIORITY_MASK) != 0);
	SPR_setHFlip(sprite, (attribut & TILE_ATTR_HFLIP_MASK) != 0);
	SPR_setVFlip(sprite, (attribut & TILE_ATTR_VFLIP_MASK) != 0);
	SPR_setFrame(sprite, 0);
	return sprite;
}

void PLAYER_STATE(u8 Player, u16 State)
{
	u16 previousState = P[Player].state;
	#if HAMOOPIG_DMA_LAB_REUSE_STATE_SPRITE
	/* Animation loops commonly re-enter the same logical state (idle, crouch,
	   walk). Keep the existing handle in that case; release/add would requeue
	   the entire frame's tiles and inflate the NTSC DMA peak. */
	if(P[Player].sprite && P[Player].state == State)
	{
		P[Player].animFrame = 1;
		P[Player].frameTimeAtual = 1;
		P[Player].dataAnim[1] = 1;
		P[Player].animFrameTotal = 1;
		if(P[Player].direcao == 1){ SPR_setHFlip(P[Player].sprite, FALSE); }
		else{ SPR_setHFlip(P[Player].sprite, TRUE); }
		SPR_setAnimAndFrame(P[Player].sprite, 0, 0);
		FUNCAO_DEPTH(Player);
		FUNCAO_SPR_POSITION();
		FUNCAO_FSM_HITBOXES(Player);
		return;
	}
	#endif
	
	#if !HAMOOPIG_STABLE_PLAYER_SPRITE
	if (P[Player].sprite){ SPR_releaseSprite(P[Player].sprite); P[Player].sprite = NULL; }
	#endif
	
	P[Player].animFrame      = 1;
	P[Player].frameTimeAtual = 1;
	P[Player].dataAnim[1]    = 1;
	P[Player].animFrameTotal = 1;
	P[Player].state = State;
	if(player_is_attack_state(State) && previousState != State)
	{
		P[Player].attackInstance++;
		if(P[Player].attackInstance == 0){ P[Player].attackInstance = 1; }
	}
	
	FUNCAO_PLAY_SND(Player, State); //SOUND; SFX!
	
	//bug fix temporario
	//ffone
	if(State==507){ State=502; }
	
	//virando de lado (mudanca de estado) //hpig 1.1
	if(Player==1)
	{
		if(P[1].direcao== 1 && P[2].x<P[1].x && State==100){ State=607; }
		if(P[1].direcao==-1 && P[1].x<P[2].x && State==100){ State=607; }
		if(P[1].direcao== 1 && P[2].x<P[1].x && State==200){ State=608; }
		if(P[1].direcao==-1 && P[1].x<P[2].x && State==200){ State=608; }
		
		if(P[1].y==P[2].y)
		{
			      if(P[1].direcao== 1 && P[2].x<P[1].x && (State>=501 && State<=550) ){ P[1].direcao=-1; 
			}else if(P[1].direcao==-1 && P[1].x<P[2].x && (State>=501 && State<=550) ){ P[1].direcao= 1; 
			}
		}
	}else{
		if(P[2].direcao== 1 && P[1].x<P[2].x && State==100){ State=607; }
		if(P[2].direcao==-1 && P[2].x<P[1].x && State==100){ State=607; }
		if(P[2].direcao== 1 && P[1].x<P[2].x && State==200){ State=608; }
		if(P[2].direcao==-1 && P[2].x<P[1].x && State==200){ State=608; }
		
		if(P[1].y==P[2].y)
		{
			      if(P[2].direcao== 1 && P[1].x<P[2].x && (State>=501 && State<=550) ){ P[2].direcao=-1; 
			}else if(P[2].direcao==-1 && P[2].x<P[1].x && (State>=501 && State<=550) ){ P[2].direcao= 1; 
			}
		}
	}
	if(State==550)//bugfix
	{
		if(Player==1)
		{
			if(P[1].x>P[2].x && P[1].direcao== 1){ P[1].direcao=-1; 
			}else if(P[1].x<P[2].x && P[1].direcao==-1){ P[1].direcao= 1; }
		}
		if(Player==2)
		{
			if(P[2].x>P[1].x && P[2].direcao== 1){ P[2].direcao=-1; 
			}else if(P[2].x<P[1].x && P[2].direcao==-1){ P[2].direcao= 1; }
		}
	}
	
	//hpig 1.1 bugfix special wrong side after jump
	if(State==606)
	{
		if(Player==1)
		{
			if(P[1].x>P[2].x && P[1].direcao== 1){ u8 a; a=P[1].joyDirTimer[6]; P[1].joyDirTimer[6]=P[1].joyDirTimer[4]; P[1].joyDirTimer[4]=a; }
			if(P[1].x<P[2].x && P[1].direcao==-1){ u8 a; a=P[1].joyDirTimer[6]; P[1].joyDirTimer[6]=P[1].joyDirTimer[4]; P[1].joyDirTimer[4]=a; }
		}
		if(Player==2)
		{
			if(P[2].x>P[1].x && P[2].direcao== 1){ u8 a; a=P[2].joyDirTimer[6]; P[2].joyDirTimer[6]=P[2].joyDirTimer[4]; P[2].joyDirTimer[4]=a; }
			if(P[2].x<P[1].x && P[2].direcao==-1){ u8 a; a=P[2].joyDirTimer[6]; P[2].joyDirTimer[6]=P[2].joyDirTimer[4]; P[2].joyDirTimer[4]=a; }
		}
	}
	if(State==700 || State==710 || State==720 || State==730 || State==740 || State==750 || State==760 || State==770 || State==780 || State==790)
	{
		if(Player==1)
		{
			if( (P[1].x>P[2].x && P[1].direcao== 1) || (P[1].x<P[2].x && P[1].direcao==-1) ){ if(P[1].direcao==1){ P[1].direcao=-1; }else{P[1].direcao=1;} }
		}
			if(Player==2)
			{
				if( (P[2].x>P[1].x && P[2].direcao== 1) || (P[2].x<P[1].x && P[2].direcao==-1) ){ if(P[2].direcao==1){ P[2].direcao=-1; }else{P[2].direcao=1;} }
			}
		
	}
	
	//cross hpig 1.1
	if(State==606)
	{
		if(Player==1)
		{
			if(P[2].state>=501 && P[2].state<550)
			{
				State=100;
				if(P[1].x>P[2].x){P[1].direcao=-1;}else{P[1].direcao=1;}
			}
		}
		if(Player==2)
		{
			if(P[1].state>=501 && P[1].state<550)
			{
				State=100;
				if(P[2].x>P[1].x){P[2].direcao=-1;}else{P[2].direcao=1;}
			}
		}
		
		if(State==100)
		{
			bool test=FALSE;
			if(P[Player].direcao== 1 && P[Player].key_JOY_LEFT_status <=2 && P[Player].key_JOY_LEFT_status !=0){ test=TRUE; PLAYER_STATE(Player, 410); State=410; }
			if(P[Player].direcao== 1 && P[Player].key_JOY_RIGHT_status<=2 && P[Player].key_JOY_RIGHT_status!=0){ test=TRUE; PLAYER_STATE(Player, 420); State=420; }
			if(P[Player].direcao==-1 && P[Player].key_JOY_LEFT_status <=2 && P[Player].key_JOY_LEFT_status !=0){ test=TRUE; PLAYER_STATE(Player, 420); State=420; }
			if(P[Player].direcao==-1 && P[Player].key_JOY_RIGHT_status<=2 && P[Player].key_JOY_RIGHT_status!=0){ test=TRUE; PLAYER_STATE(Player, 410); State=410; }
			if(test==FALSE){ PLAYER_STATE(Player, 100); State=100; }
		}
		
	}
	
	//metodo2 SPR (desativado)
	//SPR_setDefinition (P[Player].sprite, &spr_raiden_100);
	
	//--- DEBUG_CHARACTER_TEST ---// #ID:0
	if(P[Player].id==0)
	{
		if(State==100 || State==610){
			P[Player].y = gAlturaPiso;
			P[Player].w = 8;
			P[Player].h = 8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 250;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_point, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
	}
	
	//--- RYO KOF94 ---// #ID:1
	if(P[Player].id==1)
	{
		if(State==100 || State==610){ //OK
			P[Player].y = gAlturaPiso;
			P[Player].w = 8*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+4;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 5;
			P[Player].dataAnim[2]  = 5;
			P[Player].dataAnim[3]  = 5;
			P[Player].dataAnim[4]  = 5;
			P[Player].dataAnim[5]  = 5;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_100, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==101){ //OK
			P[Player].w = 11*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+15;
			P[Player].axisY = P[Player].h-1;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 3;
			P[Player].dataAnim[3]  = 4;
			P[Player].animFrameTotal = 3;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_101, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==102){ //OK
			P[Player].w = 12*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+16;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 3;
			P[Player].dataAnim[2]  = 3;
			P[Player].dataAnim[3]  = 8;
			P[Player].dataAnim[4]  = 8;
			P[Player].dataAnim[5]  = 8;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_102, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==103 || State==153 || State==203){  //OK
			P[Player].state=103;
			P[Player].w = 9*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 4;
			P[Player].dataAnim[2]  = 5;
			P[Player].dataAnim[3]  = 16;
			P[Player].dataAnim[4]  = 4;
			P[Player].dataAnim[5]  = 7;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_103, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==104){ //OK
			P[Player].w = 12*8;
			P[Player].h = 14*8;
			P[Player].axisX = (P[Player].w/2)+8;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 2;
			P[Player].dataAnim[3]  = 4;
			P[Player].dataAnim[4]  = 4;
			P[Player].animFrameTotal = 4;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_104, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==105){ //OK
			P[Player].w = 14*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+40;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 3;
			P[Player].dataAnim[2]  = 3;
			P[Player].dataAnim[3]  = 8;
			P[Player].dataAnim[4]  = 8;
			P[Player].dataAnim[5]  = 9;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_105, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==106 || State==156 || State==206){ //OK
			P[Player].state=106;
			P[Player].w = 16*8;
			P[Player].h = 14*8;
			P[Player].axisX = (P[Player].w/2)+24;
			P[Player].axisY = P[Player].h-1;
			P[Player].dataAnim[1]  = 3;
			P[Player].dataAnim[2]  = 5;
			P[Player].dataAnim[3]  = 12;
			P[Player].dataAnim[4]  = 8;
			P[Player].dataAnim[5]  = 9;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_106, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==107){ //OK
			P[Player].w = 7*8;
			P[Player].h = 13*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 4;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_107, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==108){ //OK
			P[Player].w = 7*8;
			P[Player].h = 13*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 12;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_108, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==109){ //OK
			P[Player].w = 7*8;
			P[Player].h = 13*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 4;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_107, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==110){ //OK
			P[Player].w = 7*8;
			P[Player].h = 13*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 12;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_108, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==113){ //OK
			P[Player].w = 12*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+15;
			P[Player].axisY = P[Player].h-1;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 2;
			P[Player].dataAnim[3]  = 2;
			P[Player].dataAnim[4]  = 2;
			P[Player].dataAnim[5]  = 2;
			P[Player].dataAnim[6]  = 10;
			P[Player].dataAnim[7]  = 8;
			P[Player].animFrameTotal = 7;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_113, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==151){ //OK
			P[Player].w = 10*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+5;
			P[Player].axisY = P[Player].h-1;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 3;
			P[Player].dataAnim[3]  = 3;
			P[Player].dataAnim[4]  = 4;
			P[Player].animFrameTotal = 4;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_151, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==152){ //OK
			P[Player].w = 11*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+15;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 2;
			P[Player].dataAnim[3]  = 8;
			P[Player].dataAnim[4]  = 9;
			P[Player].animFrameTotal = 4;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_152, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==154){ //OK
			P[Player].w = 14*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+24;
			P[Player].axisY = P[Player].h+1;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 4;
			P[Player].dataAnim[3]  = 4;
			P[Player].animFrameTotal = 3;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_154, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==155){ //OK
			P[Player].w = 12*8;
			P[Player].h = 17*8;
			P[Player].axisX = (P[Player].w/2)+17;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 3;
			P[Player].dataAnim[2]  = 3;
			P[Player].dataAnim[3]  = 6;
			P[Player].dataAnim[4]  = 5;
			P[Player].dataAnim[5]  = 4;
			P[Player].dataAnim[6]  = 3;
			P[Player].dataAnim[7]  = 3;
			P[Player].animFrameTotal = 7;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_155, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==200){ //OK
			P[Player].w = 7*8;
			P[Player].h = 9*8;
			P[Player].axisX = (P[Player].w/2)+2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 250;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_200, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==201){ //OK
			P[Player].w = 9*8;
			P[Player].h = 10*8;
			P[Player].axisX = (P[Player].w/2)+10;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 3;
			P[Player].dataAnim[3]  = 4;
			P[Player].animFrameTotal = 3;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_201, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}		
		if(State==202){ //OK
			P[Player].w = 10*8;
			P[Player].h = 16*8;
			P[Player].axisX = (P[Player].w/2)+14;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 2;
			P[Player].dataAnim[3]  = 2;
			P[Player].dataAnim[4]  = 8;
			P[Player].dataAnim[5]  = 8;
			P[Player].dataAnim[6]  = 9;
			P[Player].animFrameTotal = 6;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_202, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==204){ //OK
			P[Player].w = 12*8;
			P[Player].h = 9*8;
			P[Player].axisX = (P[Player].w/2)+18;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 3;
			P[Player].dataAnim[3]  = 4;
			P[Player].animFrameTotal = 3;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_204, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==205){ //OK
			P[Player].w = 16*8;
			P[Player].h = 10*8;
			P[Player].axisX = (P[Player].w/2)+36;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 3;
			P[Player].dataAnim[2]  = 8;
			P[Player].dataAnim[3]  = 7;
			P[Player].dataAnim[4]  = 6;
			P[Player].dataAnim[5]  = 6;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_205, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==207){ //OK
			P[Player].w = 7*8;
			P[Player].h = 9*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h-1;
			P[Player].dataAnim[1]  = 4;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_207, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==208){ //OK
			P[Player].w = 7*8;
			P[Player].h = 9*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h-1;
			P[Player].dataAnim[1]  = 12;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_208, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==209){ //OK
			P[Player].w = 7*8;
			P[Player].h = 9*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h-1;
			P[Player].dataAnim[1]  = 4;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_207, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==210){ //OK
			P[Player].w = 7*8;
			P[Player].h = 9*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h-1;
			P[Player].dataAnim[1]  = 12;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_208, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==300){ //OK
			P[Player].w = 8*8;
			P[Player].h = 15*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 4;
			P[Player].dataAnim[2]  = 5;
			P[Player].dataAnim[3]  = 6;
			P[Player].dataAnim[4]  = 8;
			P[Player].dataAnim[5]  = 99;//18
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_300, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==301 || State==311 || State==321 || State==303 || State==313 || State==323){ //OK
			P[Player].w = 8*8;
			P[Player].h = 10*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h+24;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 99;
			P[Player].animFrameTotal = 2;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_301, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==302 || State==312 || State==322){ //OK
			P[Player].w = 9*8;
			P[Player].h = 15*8;
			P[Player].axisX = (P[Player].w/2)+8;
			P[Player].axisY = P[Player].h-4;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 2;
			P[Player].dataAnim[3]  = 8;
			P[Player].dataAnim[4]  = 4;
			P[Player].dataAnim[5]  = 99;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_302, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==304 || State==305){ //OK
			P[Player].w = 14*8;
			P[Player].h = 11*8;
			P[Player].axisX = (P[Player].w/2)+16;
			P[Player].axisY = P[Player].h+20;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 99;
			P[Player].animFrameTotal = 2;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_304, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==306 || State==316 || State==326){ //OK
			P[Player].w = 14*8;
			P[Player].h = 11*8;
			P[Player].axisX = (P[Player].w/2)-8;
			P[Player].axisY = P[Player].h+26;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 3;
			P[Player].dataAnim[3]  = 2;
			P[Player].dataAnim[4]  = 3;
			P[Player].dataAnim[5]  = 4;
			P[Player].dataAnim[6]  = 4;
			P[Player].dataAnim[7]  = 99;
			P[Player].animFrameTotal = 7;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_306, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==310){ //OK
			P[Player].w = 10*8;
			P[Player].h = 15*8;
			P[Player].axisX = (P[Player].w/2)-8;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 7;
			P[Player].dataAnim[2]  = 4;
			P[Player].dataAnim[3]  = 4;
			P[Player].dataAnim[4]  = 4;
			P[Player].dataAnim[5]  = 5;
			P[Player].dataAnim[6]  = 5;
			P[Player].dataAnim[7]  = 5;
			P[Player].dataAnim[8]  = 99;
			P[Player].animFrameTotal = 8;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_310, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==320){ //OK
			P[Player].w = 10*8;
			P[Player].h = 15*8;
			P[Player].axisX = (P[Player].w/2)-8;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 7;
			P[Player].dataAnim[2]  = 4;
			P[Player].dataAnim[3]  = 4;
			P[Player].dataAnim[4]  = 4;
			P[Player].dataAnim[5]  = 5;
			P[Player].dataAnim[6]  = 5;
			P[Player].dataAnim[7]  = 5;
			P[Player].dataAnim[8]  = 99;
			P[Player].animFrameTotal = 8;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_320, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==314 || State==324){ //OK
			P[Player].w = 12*8;
			P[Player].h = 11*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h+12;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 99;
			P[Player].animFrameTotal = 2;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_324, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==315 || State==325){ //OK
			P[Player].w = 12*8;
			P[Player].h = 15*8;
			P[Player].axisX = (P[Player].w/2)+4;
			P[Player].axisY = P[Player].h-12;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 2;
			P[Player].dataAnim[3]  = 2;
			P[Player].dataAnim[4]  = 8;
			P[Player].dataAnim[5]  = 3;
			P[Player].dataAnim[6]  = 99;
			P[Player].animFrameTotal = 6;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_325, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==410){ //OK
			P[Player].w = 7*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+4;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 7;
			P[Player].dataAnim[2]  = 7;
			P[Player].dataAnim[3]  = 7;
			P[Player].dataAnim[4]  = 7;
			P[Player].dataAnim[5]  = 7;
			P[Player].dataAnim[6]  = 7;
			P[Player].animFrameTotal = 6;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_410, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==420){ //OK
			P[Player].w = 8*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+4;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 6;
			P[Player].dataAnim[2]  = 6;
			P[Player].dataAnim[3]  = 6;
			P[Player].dataAnim[4]  = 6;
			P[Player].dataAnim[5]  = 6;
			P[Player].dataAnim[6]  = 6;
			P[Player].animFrameTotal = 6;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_420, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==471){ //OK
			P[Player].w = 10*8;
			P[Player].h = 13*8;
			P[Player].axisX = ((P[Player].w)/2);
			P[Player].axisY =  (P[Player].h);
			P[Player].dataAnim[1]  = 18;
			P[Player].dataAnim[2]  = 2;
			P[Player].animFrameTotal = 2;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_471, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==472){ //OK
			P[Player].w = 9*8;
			P[Player].h = 13*8;
			P[Player].axisX = ((P[Player].w)/2);
			P[Player].axisY =  (P[Player].h);
			P[Player].dataAnim[1]  = 18;
			P[Player].dataAnim[2]  = 2;
			P[Player].animFrameTotal = 2;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_472, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==501){
			P[Player].w = 9*8;
			P[Player].h = 13*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 12;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_501, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==502){
			P[Player].w = 9*8;
			P[Player].h = 13*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 6;
			P[Player].dataAnim[2]  = 6;
			P[Player].dataAnim[3]  = 6;
			P[Player].animFrameTotal = 3;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_501, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==503){
			P[Player].w = 11*8;
			P[Player].h = 12*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 12;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_502, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==504){
			P[Player].w = 11*8;
			P[Player].h = 12*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 6;
			P[Player].dataAnim[2]  = 6;
			P[Player].dataAnim[3]  = 6;
			P[Player].animFrameTotal = 3;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_502, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==505){
			P[Player].w = 10*8;
			P[Player].h = 10*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 12;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_503, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==506){
			P[Player].w = 10*8;
			P[Player].h = 10*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 6;
			P[Player].dataAnim[2]  = 6;
			P[Player].dataAnim[3]  = 6;
			P[Player].animFrameTotal = 3;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_503, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==550){
			P[Player].gravidadeY = gravidadePadrao; 
			P[Player].impulsoY = impulsoPadrao;
			P[Player].y-=(7*8)-4; //Compensa o deslocamento do eixo Y (.axisY)
			P[Player].w = 14*8;
			P[Player].h = 15*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = (P[Player].h)-(7*8)-4;
			P[Player].dataAnim[1]  = 9;
			P[Player].dataAnim[2]  = 9;
			P[Player].dataAnim[3]  = 9;
			P[Player].dataAnim[4]  = 99;
			P[Player].animFrameTotal = 4;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_550, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==551){
			P[Player].w = 15*8;
			P[Player].h =  8*8;
			P[Player].axisX = ((P[Player].w)/2);
			P[Player].axisY =  (P[Player].h);
			P[Player].dataAnim[1]  = 6;
			P[Player].dataAnim[2]  = 99;
			P[Player].animFrameTotal = 2;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_551, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==552){
			P[Player].w = 12*8;
			P[Player].h = 12*8;
			P[Player].axisX = ((P[Player].w)/2);
			P[Player].axisY =  (P[Player].h);
			P[Player].dataAnim[1]  = 4;
			P[Player].dataAnim[2]  = 4;
			P[Player].dataAnim[3]  = 4;
			P[Player].animFrameTotal = 3;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_552, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==570){
			P[Player].w = 14*8;
			P[Player].h =  4*8;
			P[Player].axisX = ((P[Player].w)/2);
			P[Player].axisY =  (P[Player].h)-4;
			P[Player].dataAnim[1]  = 30;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_570, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==601){ //OK
			P[Player].w = 7*8;
			P[Player].h = 12*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 4;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_606, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==602){ //OK
			P[Player].w = 7*8;
			P[Player].h = 12*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 4;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_606, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==603 || State==604 || State==605){ //OK
			P[Player].w = 7*8;
			P[Player].h = 12*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 2;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_606, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==606){ //OK
			P[Player].w = 7*8;
			P[Player].h = 12*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 2;
			P[Player].animFrameTotal = 1;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_606, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==607){ //OK
			P[Player].w = 7*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 4;
			P[Player].dataAnim[2]  = 4;
			P[Player].animFrameTotal = 2;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_607, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==608){ //OK
			P[Player].w = 6*8;
			P[Player].h = 9*8;
			P[Player].axisX = (P[Player].w/2);
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 4;
			P[Player].dataAnim[2]  = 4;
			P[Player].animFrameTotal = 2;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_608, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==611){ //OK
			P[Player].w = 8*8;
			P[Player].h = 14*8;
			P[Player].axisX = ((P[Player].w)/2);
			P[Player].axisY =  (P[Player].h);
			P[Player].dataAnim[1]  = 4;
			P[Player].dataAnim[2]  = 4;
			P[Player].dataAnim[3]  = 4;
			P[Player].dataAnim[4]  = 4;
			P[Player].dataAnim[5]  = 4;
			P[Player].dataAnim[6]  = 4;
			P[Player].dataAnim[7]  = 4;
			P[Player].dataAnim[8]  = 250;
			P[Player].animFrameTotal = 8;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_611, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==612 || State==613){ //OK
			P[Player].w = 8*8;
			P[Player].h = 17*8;
			P[Player].axisX = ((P[Player].w)/2);
			P[Player].axisY =  (P[Player].h);
			P[Player].dataAnim[1]  = 4;
			P[Player].dataAnim[2]  = 4;
			P[Player].dataAnim[3]  = 4;
			P[Player].dataAnim[4]  = 4;
			P[Player].dataAnim[5]  = 4;
			P[Player].dataAnim[6]  = 4;
			P[Player].dataAnim[7]  = 4;
			P[Player].dataAnim[8]  = 4;
			P[Player].dataAnim[9]  = 4;
			P[Player].dataAnim[10] = 4;
			P[Player].dataAnim[11] = 250;
			P[Player].animFrameTotal = 11;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_612, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==615){ //OK
			P[Player].w = 9*8;
			P[Player].h = 12*8;
			P[Player].axisX = P[Player].w/2;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 4;
			P[Player].dataAnim[2]  = 4;
			P[Player].dataAnim[3]  = 4;
			P[Player].dataAnim[4]  = 4;
			P[Player].dataAnim[5]  = 250;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_615, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==700){ //OK
			//P[Player].fBallCountDown=74; //caso queira que a fball desapareca depois de um tempo
			P[Player].w = 15*8;
			P[Player].h = 14*8;
			P[Player].axisX = (P[Player].w/2)+8;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 2;
			P[Player].dataAnim[2]  = 1;
			P[Player].dataAnim[3]  = 1;
			P[Player].dataAnim[4]  = 1;
			P[Player].dataAnim[5]  = 1;
			P[Player].dataAnim[6]  = 1;
			P[Player].dataAnim[7]  = 1;
			P[Player].dataAnim[8]  = 1;
			P[Player].dataAnim[9]  = 1;
			P[Player].dataAnim[10] = 1;
			P[Player].dataAnim[11] = 2;
			P[Player].dataAnim[12] = 34;
			P[Player].dataAnim[13] = 2;
			P[Player].animFrameTotal = 13;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_700, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==710){
			P[Player].w = 12*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)-8;
			if(P[Player].direcao==-1){ P[Player].axisX+=56; } //hack
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 3;
			P[Player].dataAnim[2]  = 3;
			P[Player].dataAnim[3]  = 4;
			P[Player].dataAnim[4]  = 5;
			P[Player].animFrameTotal = 4;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_710, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==730){
			P[Player].y = gAlturaPiso;
			P[Player].w = 10*8;
			P[Player].h = 19*8;
			P[Player].axisX = (P[Player].w/2)+10;
			P[Player].axisY = P[Player].h-1;
			P[Player].dataAnim[1] = 2;
			P[Player].dataAnim[2] = 2;
			P[Player].dataAnim[3] = 3;
			if(P[Player].attackPower==1){ P[Player].dataAnim[4] = 11; }else{ P[Player].dataAnim[4] = 22; }
			P[Player].dataAnim[5] = 2;
			P[Player].dataAnim[6] = 3;
			P[Player].dataAnim[7] = 3;
			P[Player].dataAnim[8] = 99;
			P[Player].animFrameTotal = 8;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_730, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}

		if(State==800){ //Agarrao
			P[Player].w = 11*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+15;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 1;
			P[Player].dataAnim[2]  = 1;
			P[Player].dataAnim[3]  = 1;
			P[Player].dataAnim[4]  = 1;
			P[Player].animFrameTotal = 4;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_152, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==801){
			P[Player].w = 11*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+15;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 1;
			P[Player].dataAnim[2]  = 2;
			P[Player].dataAnim[3]  = 8;
			P[Player].dataAnim[4]  = 9;
			P[Player].animFrameTotal = 4;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_152, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==802){ //OK
			P[Player].w = 16*8;
			P[Player].h = 10*8;
			P[Player].axisX = (P[Player].w/2)+36;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 3;
			P[Player].dataAnim[2]  = 8;
			P[Player].dataAnim[3]  = 7;
			P[Player].dataAnim[4]  = 6;
			P[Player].dataAnim[5]  = 6;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_205, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
		if(State==803){
			P[Player].y = gAlturaPiso;
			P[Player].w = 8*8;
			P[Player].h = 13*8;
			P[Player].axisX = (P[Player].w/2)+4;
			P[Player].axisY = P[Player].h;
			P[Player].dataAnim[1]  = 5;
			P[Player].dataAnim[2]  = 5;
			P[Player].dataAnim[3]  = 5;
			P[Player].dataAnim[4]  = 5;
			P[Player].dataAnim[5]  = 5;
			P[Player].animFrameTotal = 5;
			P[Player].sprite = PLAYER_SET_SPRITE(Player, &spr_ryo_100, P[Player].x-P[Player].axisX, P[Player].y-P[Player].axisY, TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE), SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
		}
	}

	//--- KEN SSF2 arcade sheet, native size, id==2 ---//
	if(P[Player].id==2)
	{
		PLAYER_STATE_KEN(Player, State);
	}

	//--- MUSGO original swamp grappler, id==3 ---//
	if(P[Player].id==3)
	{
		PLAYER_STATE_MUSGO(Player, State);
	}
		

	//guardFlag
	// 0 = Sem defesa
	// 1 = Pode defende em pe ou abaixado
	// 2 = Tem que defender abaixado
	// 3 = Tem que defender em pe
	if( State == 101 || State == 102  || State == 104 || State == 105 || State == 106 || State == 201 || State == 202 || State == 113){
		P[Player].guardFlag = 1;
	}
	if( State >= 700 && State <= 790 ){
		P[Player].guardFlag = 1;
	}
	if( State == 204 || State == 205 ){
		P[Player].guardFlag = 2;
	}
	if( State >= 301 && State <= 326 ){
		P[Player].guardFlag = 3;
	}
	if( State == 800 ){ //Agarrao
		P[Player].guardFlag = 0;
	}

	//stateMoveType
	//0 = estado neutro; 1 = atacando; 2 = acertado por ataques fisicos; 3 = acertado por projeteis
	if (State==100 || State==200 || State==300 || State==310 || State==320 ||State==410 || State==420) {
		P[Player].stateMoveType = 0;
		P[Player].control = TRUE;
	} else {
		P[Player].control = FALSE;
	}

	if ((State>=101 && State<=106) || (State>=151 && State<=156) || 
		(State>=201 && State<=206) || (State>=301 && State<=306) || 
		(State>=311 && State<=316) || (State>=321 && State<=326) || 
	    (State>=700 && State<=790) ||  State==113 || State==800)
	{
		P[Player].stateMoveType = 1;
	} 

	/* Combo lifetime is event-driven, not tied to the animation state.  A
	   successful hit can be followed by a new attack after returning to idle;
	   only the timer (or the KO state) ends that combo. */
	if (State==570) {
		P[Player].hitCounter = 0;
		P[Player].hitComboTimer = 0;
	}

	if(P[Player].sprite){
		if(P[Player].direcao==1){
			SPR_setHFlip(P[Player].sprite, FALSE);
		}else{
			SPR_setHFlip(P[Player].sprite, TRUE);
		}
		SPR_setAnimAndFrame(P[Player].sprite, 0, P[Player].animFrame-1);
	}

	if (State==730) {
		 P[Player].setup = TRUE;
	}

	#if HAMOOPIG_DMA_LAB_IDLE_SLOW
	if(State==100 || State==200 || State==108 || State==208 || State==410 || State==420)
	{
		u8 animIndex;
		for(animIndex=1; animIndex<=P[Player].animFrameTotal && animIndex<16; animIndex++)
		{
			if(P[Player].dataAnim[animIndex] < 120) P[Player].dataAnim[animIndex] *= 2;
		}
	}
	#endif
	P[Player].frameTimeTotal  = P[Player].dataAnim[1];

	if (P[Player].sprite){ FUNCAO_DEPTH(Player); } //Define a prioridade de desenho (se sprite completamente carregado)

	FUNCAO_SPR_POSITION(); //Define a posicao do Sprite
	FUNCAO_FSM_HITBOXES(Player); //Atualiza as Hurt / Hitboxes
}


void FUNCAO_PLAY_SND(u8 Player, u16 State)
{
	if(!gConfig.audioSfx){ return; }
	//P1 utiliza o 'P1_SFX' e 'SOUND_PCM_CH3'
	//P2 utiliza o 'P2_SFX' e 'SOUND_PCM_CH4'
	
	//Samurai Shodown 2 (SS2) nota:
	//Os golpes <FRACOS> geralmente alternam entre 2 sons
	//Os golpes <MEDIOS> e <FORTES> geralmente, alternam entre 4 sons
	
	if(Player==1)
	{
		if(P[1].id==1 || P[1].id==2 || P[1].id==3) //ryo / ken / musgo (Musgo reuses HAMOOPI GPL SFX)
		{
			if(
				State==101 || State==104 || 
				State==201 || State==204 || 
				State==301 || State==304 || 
				State==311 || State==314 || 
				State==321 || State==324
			)
			{
				if(gPing2==0){ XGM_setPCM(P1_SFX, snd_101 , sizeof(snd_101 )); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
				if(gPing2==1){ XGM_setPCM(P1_SFX, snd_101b, sizeof(snd_101b)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			}
			if(
			State==151 || State==154
			)
			{
				XGM_setPCM(P1_SFX, snd_151 , sizeof(snd_151 )); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3);
			}
			if(
				State==102 || State==105 || 
				State==152 || State==155 || 
				State==202 || State==205 || 
				State==302 || State==305 || 
				State==312 || State==315 || 
				State==322 || State==325 ||
				State==113 || 
				State==106 || State==206 || State==306 || State==316 || State==326 
			)
			{
				if(gPing2==0){ XGM_setPCM(P1_SFX, snd_102 , sizeof(snd_102 )); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
				if(gPing2==1){ XGM_setPCM(P1_SFX, snd_102b, sizeof(snd_102b)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			}
			if(State==110 || State==210){ XGM_setPCM(P1_SFX, snd_110, sizeof(snd_110)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			if(State==103 || State==300 || State==310 || State==320 || State==471 || State==472){ XGM_setPCM(P1_SFX, snd_300, sizeof(snd_300)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			if(State==501 || State==506 || State==511){ XGM_setPCM(P1_SFX, snd_501, sizeof(snd_501)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			if(State==502 || State==507 || State==512 || State==550){ XGM_setPCM(P1_SFX, snd_502, sizeof(snd_502)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			if(State==551){ XGM_setPCM(P1_SFX, snd_551, sizeof(snd_551)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			if(State==606){ XGM_setPCM(P1_SFX, snd_606, sizeof(snd_606)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			//if(State==618){ XGM_setPCM(P1_SFX, snd_haohmaru_618, sizeof(snd_haohmaru_618)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			if(State==700){ XGM_setPCM(P1_SFX, snd_ryo_700, sizeof(snd_ryo_700)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			if(State==710){ XGM_setPCM(P1_SFX, snd_ryo_710, sizeof(snd_ryo_710)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			if(State==720){ XGM_setPCM(P1_SFX, snd_ryo_720, sizeof(snd_ryo_720)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
			if(State==730){ XGM_setPCM(P1_SFX, snd_ryo_730, sizeof(snd_ryo_730)); XGM_startPlayPCM(P1_SFX, 1, SOUND_PCM_CH3); }
		}
	}
	
	if(Player==2)
	{
		if(P[2].id==1 || P[2].id==2 || P[2].id==3) //ryo / ken / musgo (Musgo reuses HAMOOPI GPL SFX)
		{
			if(
				State==101 || State==104 || 
				State==201 || State==204 || 
				State==301 || State==304 || 
				State==311 || State==314 || 
				State==321 || State==324
			)
			{
				if(gPing2==0){ XGM_setPCM(P2_SFX, snd_101 , sizeof(snd_101 )); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
				if(gPing2==1){ XGM_setPCM(P2_SFX, snd_101b, sizeof(snd_101b)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			}
			if(
			State==151 || State==154
			)
			{
				XGM_setPCM(P2_SFX, snd_151 , sizeof(snd_151 )); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4);
			}
			if(
				State==102 || State==105 || 
				State==152 || State==155 || 
				State==202 || State==205 || 
				State==302 || State==305 || 
				State==312 || State==315 || 
				State==322 || State==325 ||
				State==113 || 
				State==106 || State==206 || State==306 || State==316 || State==326 
			)
			{
				if(gPing2==0){ XGM_setPCM(P2_SFX, snd_102 , sizeof(snd_102 )); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
				if(gPing2==1){ XGM_setPCM(P2_SFX, snd_102b, sizeof(snd_102b)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			}
			if(State==110 || State==210){ XGM_setPCM(P2_SFX, snd_110, sizeof(snd_110)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			if(State==103 || State==300 || State==310 || State==320 || State==471 || State==472){ XGM_setPCM(P2_SFX, snd_300, sizeof(snd_300)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			if(State==501 || State==506 || State==511){ XGM_setPCM(P2_SFX, snd_501, sizeof(snd_501)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			if(State==502 || State==507 || State==512 || State==550){ XGM_setPCM(P2_SFX, snd_502, sizeof(snd_502)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			if(State==551){ XGM_setPCM(P2_SFX, snd_551, sizeof(snd_551)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			if(State==606){ XGM_setPCM(P2_SFX, snd_606, sizeof(snd_606)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			//if(State==618){ XGM_setPCM(P2_SFX, snd_haohmaru_618, sizeof(snd_haohmaru_618)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			if(State==700){ XGM_setPCM(P2_SFX, snd_ryo_700, sizeof(snd_ryo_700)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			if(State==710){ XGM_setPCM(P2_SFX, snd_ryo_710, sizeof(snd_ryo_710)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			if(State==720){ XGM_setPCM(P2_SFX, snd_ryo_720, sizeof(snd_ryo_720)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
			if(State==730){ XGM_setPCM(P2_SFX, snd_ryo_730, sizeof(snd_ryo_730)); XGM_startPlayPCM(P2_SFX, 1, SOUND_PCM_CH4); }
		}
	}
	
	
	
}





void FUNCAO_DEPTH(u8 Player)
{
	//Qto menor o 'depth', mais para frente o objeto fica na tela
	u8 depth = Player + 4;
	if(P[Player].state>=500 && P[Player].state<=572)                         {depth = Player+20;} //Hurts, Caindo
	if(P[Player].state==100)                                                 {depth = Player+18;} //Parado
	if(P[Player].state==471 || P[Player].state==472)                         {depth = Player+16;} //Rolamento, Dash, Esquiva
	if(P[Player].state==410 || P[Player].state==420)                         {depth = Player+14;} //Andando
	if(P[Player].state>=107 && P[Player].state<=110)                         {depth = Player+12;} //Defesa em Pe
	if(P[Player].state>=207 && P[Player].state<=210)                         {depth = Player+12;} //Defesa Abaixado
	if(P[Player].state>=101 && P[Player].state<=156)                         {depth = Player+ 8;} //Golpes em Pe
	if(P[Player].state>=200 && P[Player].state<=206)                         {depth = Player+ 6;} //Golpes Abaixados
	if(P[Player].state==300 || P[Player].state==310 || P[Player].state==320) {depth = Player+ 4;} //Pulos
	if(P[Player].state>=301 && P[Player].state<=326)                         {depth = Player+ 2;} //Golpes Aereos
	if(P[Player].state>=611 && P[Player].state<=614)                         {depth = Player+ 2;} //Vitoria
	if(P[Player].state>=700 && P[Player].state<=790)                         {depth = Player+ 2;} //Magias
	//define o Depth, SE e SOMENTE SE o sprite estiver carregado. 
	//O comando 'SPR_setDepth' pode ser potencialmente perigoso e TRAVAR o jogo se o SPRITE nao estiver completamente carregado na VRAM
	if(P[Player].sprite){ SPR_setDepth(P[Player].sprite, depth); }
}


static void player_apply_special_delta(u8 Player, s8 Value)
{
	s16 next;
	if(!gConfig.specialRules){ P[Player].energiaSP = 0; return; }
	next = (s16)P[Player].energiaSP + (s16)Value;
	if(next < 0){ next = 0; }
	if(next > SPECIAL_METER_MAX){ next = SPECIAL_METER_MAX; }
	P[Player].energiaSP = (s8)next;
}

static void player_apply_health_delta(u8 Player, s8 Value)
{
	s16 previous = P[Player].energiaBase;
	s16 next = previous + (s16)Value;
	if(next < 0){ next = 0; }
	if(next > 96){ next = 96; }
	P[Player].energiaBase = (s8)next;
	if(next == 0)
	{
		P[Player].energia = 0;
		if(previous > 0 && P[Player].state != 550){ PLAYER_STATE(Player,550); }
	}
}

void FUNCAO_UPDATE_LIFESP(u8 Player, u8 EnergyType, s8 Value)
{
	/* Special-meter updates follow every damage call. They must never
	   re-enter 550: Musgo's entry applies another upward displacement. */
	if(EnergyType==1)
	{
		/* O evento assume a aplicação uma vez depois da FSM. Se não existe
		   evento (cura/reset/ferramenta legada), mantém-se o caminho direto. */
		if(COMBAT_EVENTS_ATTACH_HEALTH_DELTA(Player, Value) != COMBAT_EVENT_ATTACH_NONE){ return; }
		player_apply_health_delta(Player, Value);
	}
	/*bugado
	if(P[Player].state==110 && P[Player].state==210){
		if(P[Player].energiaBase==0){ PLAYER_STATE(Player, 550); }
	}else{
		if(P[Player].energiaBase==0){  PLAYER_STATE(Player, 550); P[Player].y=gAlturaPiso-8; }
	}
	*/
	
	if(EnergyType==2) // energia especial: faixa fechada 0..32
	{
		if(!gConfig.specialRules){ P[Player].energiaSP = 0; return; }
		/* O acerto já foi emitido pela FSM; guardar o delta no evento evita
		   que o valor legado seja aplicado em paralelo ao ganho central. */
		if(COMBAT_EVENTS_ATTACH_METER_DELTA(Player, Value)){ return; }
		player_apply_special_delta(Player, Value);
	}
	
}

bool FUNCAO_SPEND_SPECIAL(u8 Player)
{
	if(!gConfig.specialRules){ P[Player].energiaSP = 0; return TRUE; }
	if(P[Player].energiaSP < SPECIAL_METER_COST){ return FALSE; }
	P[Player].energiaSP -= SPECIAL_METER_COST;
	return TRUE;
}

void FUNCAO_REGISTER_HIT(u8 Player)
{
	u8 kind;
	if(Player < 1 || Player > 2){ return; }
	/* O caminho de colisão só produz o evento. Combo, medidor e feedback não
	   devem ser atualizados em paralelo aqui: o consumidor central roda uma vez
	   depois da FSM e preserva a ordem declarada dos eventos do tick. */
	kind = (P[Player].state == 801 || P[Player].state == 802) ? COMBAT_EVENT_THROW : COMBAT_EVENT_HIT;
	COMBAT_EVENTS_EMIT_SOURCE(Player, (Player == 1) ? 2 : 1, P[Player].state,
		kind,
		(P[Player].state == 801 || P[Player].state == 802) ? COMBAT_EVENT_SOURCE_THROW : COMBAT_EVENT_SOURCE_BODY,
		P[Player].attackInstance);
}

void FUNCAO_CONSUME_COMBAT_EVENTS(void)
{
	u8 index;
	u8 count;
	const CombatEvent *event;

	if(!COMBAT_EVENTS_CLAIM_CONSUMPTION()){ return; }
	count = COMBAT_EVENTS_COUNT();
	for(index = 0; index < count; index++)
	{
		event = COMBAT_EVENTS_AT(index);
		if(!event){ continue; }
		if(event->healthAttached){
			player_apply_health_delta(event->defender, event->healthDelta);
			COMBAT_EVENTS_SET_RESULT(index, (P[event->defender].energiaBase == 0) ? COMBAT_EVENT_RESULT_KO : COMBAT_EVENT_RESULT_HIT);
		}
		if((event->kind != COMBAT_EVENT_HIT && event->kind != COMBAT_EVENT_THROW) || event->attacker < 1 || event->attacker > 2){ continue; }
		if(P[event->attacker].hitCounter < 255){ P[event->attacker].hitCounter++; }
		P[event->attacker].hitComboTimer = HIT_COMBO_WINDOW_TICKS;
		if(gConfig.specialRules){
			player_apply_special_delta(event->attacker, event->meterAttackerDelta);
			player_apply_special_delta(event->defender, event->meterDefenderDelta);
		}
	}
	/* GUARD não incrementa combo, mas a política central dá +1 ao atacante. */
	for(index = 0; index < count; index++)
	{
		event = COMBAT_EVENTS_AT(index);
		if(event && event->kind == COMBAT_EVENT_GUARD && gConfig.specialRules && event->attacker >= 1 && event->attacker <= 2)
		{
			player_apply_special_delta(event->attacker, event->meterAttackerDelta);
		}
	}
}

void FUNCAO_UPDATE_HIT_COMBOS(void)
{
	u8 player;
	for(player = 1; player <= 2; player++)
	{
		if(P[player].hitComboTimer > 0)
		{
			P[player].hitComboTimer--;
			if(P[player].hitComboTimer == 0){ P[player].hitCounter = 0; }
		}
	}
}
