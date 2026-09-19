#include <genesis.h>
#include "select.h"
#include "globals.h"
#include "scene.h"
#include "sprite.h"
#include "ken.h"
#include "musgo.h"
#include "init.h"
#include "player.h"
#include "config.h"
#include "stage.h"
#include "gfx.h"
#include "hud_gfx.h"
#include "hamoopig_runtime_probe.h"

static Sprite *sPreview[2];
static Sprite *sPortrait[2];
static u8 sLocked[3];
static u16 sSelectPalette[16];

/* Select is a presentation screen, so its cards are UI composition rather
   than character pixels.  The two tiles live in the user VRAM band before the
   sprite allocator and use the existing PAL1 blue/accent language. */
#define SELECT_UI_TILE_BASE 900
#define SELECT_CARD_TILE (SELECT_UI_TILE_BASE)
#define SELECT_FRAME_TILE (SELECT_UI_TILE_BASE + 1)

static const u32 kSelectCardTile[8] =
{
	0x99999999, 0x99999999, 0x99999999, 0x99999999,
	0x99999999, 0x99999999, 0x99999999, 0x99999999
};

static const u32 kSelectFrameTile[8] =
{
	0x66666666, 0x66666666, 0x66666666, 0x66666666,
	0x66666666, 0x66666666, 0x66666666, 0x66666666
};

static void draw_card(u8 x, u8 y, u8 width, u8 height)
{
	u8 row;
	u8 col;
	const u16 card = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, SELECT_CARD_TILE);
	const u16 frame = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, SELECT_FRAME_TILE);
	VDP_fillTileMapRect(BG_A, card, x, y, width, height);
	for(row = y; row < (u8)(y + height); row++)
	{
		VDP_setTileMapXY(BG_A, frame, x, row);
		VDP_setTileMapXY(BG_A, frame, (u8)(x + width - 1), row);
	}
	for(col = x; col < (u8)(x + width); col++)
	{
		VDP_setTileMapXY(BG_A, frame, col, y);
		VDP_setTileMapXY(BG_A, frame, col, (u8)(y + height - 1));
	}
}

static void draw_select_status(void)
{
	VDP_drawText(sLocked[1] ? "LOCKED" : "SELECT", 3, 6);
	VDP_drawText(sLocked[2] ? "LOCKED" : "SELECT", 29, 6);
}

static const SpriteDefinition *portrait_def(u8 id)
{
	if(id == 2){ return &spr_hud_portrait_ken; }
	if(id == 3){ return &spr_hud_portrait_musgo; }
	return &spr_hud_portrait_ryo;
}

static const char *stage_name(void)
{
	return STAGE_getDefinition(gBG_Choice)->name;
}

static void draw_stage_choice(void)
{
	VDP_drawText("                         ", 7, 25);
	VDP_drawText("STAGE //", 12, 25);
	VDP_drawText(stage_name(), 21, 25);
}

static const char *fighter_name(u8 id)
{
	if(id == 2){ return "KEN  "; }
	if(id == 3){ return "MUSGO"; }
	return "RYO  ";
}

static void preview_def(u8 slot, u8 id)
{
	if(sPreview[slot])
	{
		SPR_releaseSprite(sPreview[slot]);
		sPreview[slot] = NULL;
	}
	if(sPortrait[slot])
	{
		SPR_releaseSprite(sPortrait[slot]);
		sPortrait[slot] = NULL;
	}
	if(id == 2)
	{
		sPreview[slot] = SPR_addSpriteExSafe(&spr_ken_100, (slot == 0) ? 48 : 208, 88,
			TILE_ATTR((slot == 0) ? PAL2 : PAL3, FALSE, FALSE, FALSE),
			SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
	}
	else if(id == 3)
	{
		sPreview[slot] = SPR_addSpriteExSafe(&spr_musgo_100, (slot == 0) ? 40 : 200, 80,
			TILE_ATTR((slot == 0) ? PAL2 : PAL3, FALSE, FALSE, FALSE),
			SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
	}
	else
	{
		sPreview[slot] = SPR_addSpriteExSafe(&spr_ryo_100, (slot == 0) ? 48 : 208, 80,
			TILE_ATTR((slot == 0) ? PAL2 : PAL3, FALSE, FALSE, FALSE),
			SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
	}
	if(sPreview[slot] && slot == 1)
	{
		SPR_setHFlip(sPreview[slot], TRUE);
	}
	sPortrait[slot] = SPR_addSpriteExSafe(portrait_def(id), (slot == 0) ? 8 : 280, 64,
		TILE_ATTR((slot == 0) ? PAL2 : PAL3, FALSE, FALSE, FALSE),
		SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
	if(sPortrait[slot] && slot == 1){ SPR_setHFlip(sPortrait[slot], TRUE); }
}

static void apply_slot_palette(u8 slot, u8 id)
{
	u16 pal = (slot == 0) ? PAL2 : PAL3;
	if(id == 2){ PAL_setPalette(pal, spr_ken_pal1.palette->data, CPU); }
	else if(id == 3){ PAL_setPalette(pal, spr_musgo_pal1.palette->data, CPU); }
	else { PAL_setPalette(pal, spr_ryo_pal1.palette->data, CPU); }
}

void FUNCAO_SELECT_INIT()
{
	u16 i;

	sPreview[0] = NULL;
	sPreview[1] = NULL;
	sPortrait[0] = NULL;
	sPortrait[1] = NULL;
	sLocked[1] = 0;
	sLocked[2] = 0;
	cursorP1_ID = 1;
	cursorP2_ID = 3;
	endP1Selection = FALSE;
	endP2Selection = FALSE;
	charSelStep = 0;
	if(!gConfig.stage2Enabled){ gBG_Choice = 1; }

	/* Formal front-end composition: keep the title language without putting the
	   logo/pig over the fighter previews. The dedicated backdrop leaves the
	   center quiet and reserves PAL0 for the background only. */
	VDP_setBackgroundColor(0);
	VDP_clearPlane(BG_A, TRUE);
	PAL_setPalette(PAL0, title_backdrop.palette->data, CPU);
	VDP_drawImageEx(BG_B, &title_backdrop,
		TILE_ATTR_FULL(PAL0, FALSE, FALSE, FALSE, 1),
		0, 0, FALSE, TRUE);
	HAMOOPIG_probeVramRange(1u, title_backdrop.tileset->numTile);
	memcpy(sSelectPalette, spr_hud_energy_y.palette->data, sizeof(sSelectPalette));
	/* The card uses PAL1 index 9 and the frame index 6.  The stock text atlas
	   also uses index 11 for its glyph ink; make that ink white only on this
	   screen so blue cards remain readable without changing fighter palettes. */
	sSelectPalette[11] = sSelectPalette[1];
	PAL_setPalette(PAL1, sSelectPalette, CPU);
	VDP_loadTileData(kSelectCardTile, SELECT_CARD_TILE, 1, CPU);
	VDP_loadTileData(kSelectFrameTile, SELECT_FRAME_TILE, 1, CPU);
	HAMOOPIG_probeVramRange(SELECT_UI_TILE_BASE, 2);
	draw_card(1, 4, 15, 20);
	draw_card(24, 4, 15, 20);
	VDP_setTextPalette(PAL1);
	VDP_drawText("ROSTER // VS", 14, 2);
	VDP_drawText("P1", 2, 5);
	VDP_drawText("P2", 36, 5);
	VDP_drawText("LEFT RIGHT", 10, 7);
	VDP_drawText("A LOCK", 17, 8);
	VDP_drawText("B BACK  C STAGE", 12, 27);
	VDP_drawText("VS", 19, 14);
	VDP_drawText(fighter_name(cursorP1_ID), 8, 24);
	VDP_drawText(fighter_name(cursorP2_ID), 28, 24);
	draw_select_status();
	draw_stage_choice();

	apply_slot_palette(0, cursorP1_ID);
	apply_slot_palette(1, cursorP2_ID);
	preview_def(0, cursorP1_ID);
	preview_def(1, cursorP2_ID);

	for(i = 0; i < 12; i++)
	{
		P[1].key_JOY_status[i] = KEY_FREE;
		P[2].key_JOY_status[i] = KEY_FREE;
	}
}

static void cycle_id(u8 *id)
{
	*id = (*id == 1) ? 2 : ((*id == 2) ? 3 : 1);
}

static void select_return_to_title(void)
{
	if(sPreview[0]){ SPR_releaseSprite(sPreview[0]); sPreview[0] = NULL; }
	if(sPreview[1]){ SPR_releaseSprite(sPreview[1]); sPreview[1] = NULL; }
	if(sPortrait[0]){ SPR_releaseSprite(sPortrait[0]); sPortrait[0] = NULL; }
	if(sPortrait[1]){ SPR_releaseSprite(sPortrait[1]); sPortrait[1] = NULL; }
	CLEAR_VDP();
	/* OPENING/FADE now have an observable session path.  B from SELECT returns
	   through the configured opening, or directly to TITLE when INTRO is OFF. */
	SCENE_request(gConfig.showOpening ? SCENE_OPENING : SCENE_TITLE);
}

void FUNCAO_SELECT_UPDATE()
{
	if(P[1].key_JOY_B_status == KEY_PRESSED)
	{
		select_return_to_title();
		return;
	}

	if(P[1].key_JOY_C_status == 1 && gConfig.stage2Enabled)
	{
		gBG_Choice = (gBG_Choice == 1) ? 2 : 1;
		draw_stage_choice();
	}

	if(!sLocked[1])
	{
		if(P[1].key_JOY_LEFT_status == 1 || P[1].key_JOY_RIGHT_status == 1)
		{
			cycle_id(&cursorP1_ID);
			apply_slot_palette(0, cursorP1_ID);
			preview_def(0, cursorP1_ID);
			VDP_drawText("     ", 8, 24);
			VDP_drawText(fighter_name(cursorP1_ID), 8, 24);
		}
		if(P[1].key_JOY_A_status == 1 || P[1].key_JOY_START_status == 1)
		{
			sLocked[1] = 1;
			endP1Selection = TRUE;
			draw_select_status();
		}
	}
	if(!sLocked[2])
	{
		if(P[2].key_JOY_LEFT_status == 1 || P[2].key_JOY_RIGHT_status == 1)
		{
			cycle_id(&cursorP2_ID);
			apply_slot_palette(1, cursorP2_ID);
			preview_def(1, cursorP2_ID);
			VDP_drawText("     ", 28, 24);
			VDP_drawText(fighter_name(cursorP2_ID), 28, 24);
		}
		if(P[2].key_JOY_A_status == 1 || P[2].key_JOY_START_status == 1)
		{
			sLocked[2] = 1;
			endP2Selection = TRUE;
			draw_select_status();
		}
	}

	if(sLocked[1] && !sLocked[2] && P[1].key_JOY_START_status == 1 && gFrames > 4)
	{
		/* P1 confirmed and pressed Start again: P2 keeps current cursor */
		sLocked[2] = 1;
		endP2Selection = TRUE;
		draw_select_status();
	}

	if(gPing2 == 0)
	{
		VDP_drawText("<P1>", 5, 3);
		VDP_drawText("<P2>", 31, 3);
	}

	if(sLocked[1] && sLocked[2])
	{
		charSelStep++;
		if(charSelStep >= 20)
		{
			FUNCAO_SELECT_EXIT();
		}
	}
}

void FUNCAO_SELECT_EXIT()
{
	P[1].id = cursorP1_ID;
	P[2].id = cursorP2_ID;
	P[1].palID = 1;
	P[2].palID = (P[1].id == P[2].id) ? 2 : 1;
	cursorP1ColorChoice = P[1].palID;
	cursorP2ColorChoice = P[2].palID;
	if(sPreview[0]){ SPR_releaseSprite(sPreview[0]); sPreview[0] = NULL; }
	if(sPreview[1]){ SPR_releaseSprite(sPreview[1]); sPreview[1] = NULL; }
	if(sPortrait[0]){ SPR_releaseSprite(sPortrait[0]); sPortrait[0] = NULL; }
	if(sPortrait[1]){ SPR_releaseSprite(sPortrait[1]); sPortrait[1] = NULL; }
	CLEAR_VDP();
	SCENE_request(SCENE_FIGHT);
}
