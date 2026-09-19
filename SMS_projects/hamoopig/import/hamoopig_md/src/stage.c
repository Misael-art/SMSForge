#include <genesis.h>
#include "stage.h"
#include "gfx.h"
#include "sprite.h"
#include "globals.h"

#define STAGE_GLINT_COUNT 3

static Sprite *sStageGlint[STAGE_GLINT_COUNT];
static const s16 sStageGlintWorldX[STAGE_GLINT_COUNT] = { 218, 278, 348 };
static const s16 sStageGlintWorldY[STAGE_GLINT_COUNT] = { 180, 174, 188 };
static const u8 sStageGlintPhase[STAGE_GLINT_COUNT] = { 0, 2, 1 };

void STAGE_ambient_off(void)
{
	for(u8 i = 0; i < STAGE_GLINT_COUNT; i++)
	{
		if(sStageGlint[i])
		{
			SPR_releaseSprite(sStageGlint[i]);
			sStageGlint[i] = NULL;
		}
	}
}

void STAGE_ambient_init(void)
{
	STAGE_ambient_off();
	if(gBG_Choice != 2) { return; }

	for(u8 i = 0; i < STAGE_GLINT_COUNT; i++)
	{
		sStageGlint[i] = SPR_addSpriteExSafe(
			&spr_stage_water_glint, -32, -32,
			TILE_ATTR(PAL0, FALSE, FALSE, FALSE),
			SPR_FLAG_AUTO_VISIBILITY | SPR_FLAG_AUTO_VRAM_ALLOC |
			SPR_FLAG_AUTO_TILE_UPLOAD);
		if(sStageGlint[i])
		{
			SPR_setDepth(sStageGlint[i], 1);
			SPR_setFrame(sStageGlint[i], sStageGlintPhase[i]);
		}
	}
	STAGE_ambient_update();
}

void STAGE_ambient_update(void)
{
	if(gBG_Choice != 2) { return; }
	if((gFrames & 7u) != 0u) { return; }

	const s16 stageTop = (s16)gBG_Height - (s16)gScreenH;
	for(u8 i = 0; i < STAGE_GLINT_COUNT; i++)
	{
		if(!sStageGlint[i]) { continue; }
		const u8 frame = (u8)(((gFrames >> 3) + sStageGlintPhase[i]) & 3u);
		SPR_setFrame(sStageGlint[i], frame);
		SPR_setPosition(sStageGlint[i],
			(s16)(sStageGlintWorldX[i] - camPosX),
			(s16)(sStageGlintWorldY[i] - stageTop + camPosY));
	}
}

static const StageDefinition kShowdown =
{
	.id = 1,
	.name = "SHOWDOWN",
	.width = 512, .height = 256, .floor = 219,
	.fightLeft = 30, .fightRight = 482, .supports240 = TRUE,
	.image = &gfx_showdown, .bgPlane = BG_B, .paletteSlot = PAL0,
	.layerCount = 1, .loadingModel = STAGE_LOAD_RESIDENT,
	.tileBudget = 864, .measuredUniqueTiles = 864,
	.bgm = "stage_showdown", .provenance = "rascunho/showdown_native_crop_preview.png; arcade study candidate",
	.camera = {
		.viewportWidth = 320, .viewportHeight = 224, .preloadTiles = 1,
		.preloadPeakTiles = 588, .horizontalTravel = 192,
		.verticalTravel224 = 32, .verticalTravel240 = 16,
		.parallaxFarQ8 = 110, .parallaxNearQ8 = 182, .motionEnabled = FALSE
	}
};

static const StageDefinition kStage2 =
{
	.id = 2,
	.name = "BGB2",
	.width = 512, .height = 256, .floor = 219,
	.fightLeft = 30, .fightRight = 482, .supports240 = TRUE,
	.image = &gfx_bgb2, .bgPlane = BG_B, .paletteSlot = PAL0,
	.layerCount = 1, .loadingModel = STAGE_LOAD_RESIDENT,
	.tileBudget = 864, .measuredUniqueTiles = 864,
	.bgm = "stage_bgb2", .provenance = "data/source_art/stage2_swamp/generated_stage2_v01.png; original candidate",
	.camera = {
		.viewportWidth = 320, .viewportHeight = 224, .preloadTiles = 1,
		.preloadPeakTiles = 588, .horizontalTravel = 192,
		.verticalTravel224 = 32, .verticalTravel240 = 16,
		.parallaxFarQ8 = 110, .parallaxNearQ8 = 182, .motionEnabled = FALSE
	}
};

const StageDefinition *STAGE_getDefinition(u8 choice)
{
	return (choice == 2) ? &kStage2 : &kShowdown;
}

const Image *STAGE_getImage(u8 choice)
{
	return STAGE_getDefinition(choice)->image;
}
