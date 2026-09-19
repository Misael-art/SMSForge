#include <genesis.h>
#include "player.h"
#include "globals.h"
#include "sprite.h"
#include "player_ken_table.h"
#include "musgo.h"

#ifndef HAMOOPIG_DMA_LAB_DELAYED_FRAME
#define HAMOOPIG_DMA_LAB_DELAYED_FRAME 1
#endif
#if HAMOOPIG_DMA_LAB_DELAYED_FRAME
#undef SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE
#define SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE 0
#endif

void PLAYER_STATE_KEN(u8 Player, u16 State)
{
	const KenStateAnim *a = ken_anim_for(State);
	u8 i;

	if(State==100 || State==610 || State==607 || State==611 || State==612 || State==615
		|| State==200 || State==201 || State==207 || State==208 || State==209 || State==608
		|| State==410 || State==420 || State==471 || State==472
		|| State==101 || State==102 || State==104 || State==105 || State==106
		|| State==107 || State==108 || State==109 || State==110 || State==113 || State==151
		|| State==152 || State==154 || State==155
		|| State==700)
	{
		P[Player].y = gAlturaPiso;
	}

	P[Player].w = a->w;
	P[Player].h = a->h;
	P[Player].axisX = a->axisX;
	P[Player].axisY = a->axisY;
	P[Player].animFrameTotal = a->frames;
	for(i = 0; i < 12; i++)
	{
		P[Player].dataAnim[i + 1] = a->timing[i];
	}

	if(State==550)
	{
		/* Same launch as Ryo 550. Without impulsoY/gravidadeY, physics does
		   impulsoY -= 1 every tick and Ken flies up off the screen. */
		P[Player].gravidadeY = 3;
		P[Player].impulsoY = -14;
		P[Player].y -= (7 * 8) - 4;
	}

	P[Player].sprite = PLAYER_SET_SPRITE(Player,
		a->def,
		P[Player].x - P[Player].axisX,
		P[Player].y - P[Player].axisY,
		TILE_ATTR(P[Player].paleta, FALSE, FALSE, FALSE),
		SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
}

void FUNCAO_APPLY_FIGHTER_PALETTE(u8 Player)
{
	u16 pal = (Player == 1) ? PAL2 : PAL3;

	if(P[Player].id == 1)
	{
		if(P[Player].palID == 2){ PAL_setPalette(pal, spr_ryo_pal2.palette->data, CPU); }
		else { PAL_setPalette(pal, spr_ryo_pal1.palette->data, CPU); }
	}
	else if(P[Player].id == 2)
	{
		if(P[Player].palID == 2){ PAL_setPalette(pal, spr_ken_pal2.palette->data, CPU); }
		else { PAL_setPalette(pal, spr_ken_pal1.palette->data, CPU); }
	}
	else if(P[Player].id == 3)
	{
		if(P[Player].palID == 2){ PAL_setPalette(pal, spr_musgo_pal2.palette->data, CPU); }
		else { PAL_setPalette(pal, spr_musgo_pal1.palette->data, CPU); }
	}
}

void FUNCAO_CYCLE_FIGHTER(u8 Player)
{
	P[Player].id = (P[Player].id == 1) ? 2 : ((P[Player].id == 2) ? 3 : 1);
	if(P[1].id == P[2].id && P[1].palID == P[2].palID)
	{
		P[Player].palID = (P[Player].palID == 1) ? 2 : 1;
	}
	FUNCAO_APPLY_FIGHTER_PALETTE(Player);
	PLAYER_STATE(Player, 100);
}
