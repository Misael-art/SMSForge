#ifndef HAMOOPIG_STAGE_H
#define HAMOOPIG_STAGE_H

#include <genesis.h>

typedef enum
{
	STAGE_LOAD_RESIDENT = 0,
	STAGE_LOAD_STREAM_WINDOW = 1
} StageLoadingModel;

/* Runtime camera contract.  Values are data, not formulas hidden in init.c;
   this lets a future stage use the same loader with a larger world and a
   measured preload window.  Ratios are Q8 (256 == 1.0). */
typedef struct
{
	u16 viewportWidth;
	u16 viewportHeight;
	u16 preloadTiles;
	u16 preloadPeakTiles;
	u16 horizontalTravel;
	u16 verticalTravel224;
	u16 verticalTravel240;
	u16 parallaxFarQ8;
	u16 parallaxNearQ8;
	bool motionEnabled;
} StageCameraContract;

typedef struct
{
	u8 id;
	const char *name;
	u16 width;
	u16 height;
	u16 floor;
	u16 fightLeft;
	u16 fightRight;
	bool supports240;
	const Image *image;
	u8 bgPlane;
	u8 paletteSlot;
	u8 layerCount;
	StageLoadingModel loadingModel;
	u16 tileBudget;
	u16 measuredUniqueTiles;
	const char *bgm;
	const char *provenance;
	StageCameraContract camera;
} StageDefinition;

const StageDefinition *STAGE_getDefinition(u8 choice);
const Image *STAGE_getImage(u8 choice);

/* BGB2's ambient layer is a small, measured sprite-graft.  It owns only its
   own handles and is torn down at every scene commit. */
void STAGE_ambient_init(void);
void STAGE_ambient_update(void);
void STAGE_ambient_off(void);

#endif
