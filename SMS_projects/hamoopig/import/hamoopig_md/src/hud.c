#include <genesis.h>
#include "hud.h"
#include "globals.h"
#include "config.h"
#include "scene.h"
#include "timing.h"
#include "sprite.h"
#include "hud_gfx.h"
#include "hamoopig_runtime_probe.h"

static void hud_window_draw_clock(void);
static void hud_clock_background_update(void);
static void hud_combo_clear(void);
static void hud_combo_update(void);
static void hud_sync_segment_tile(void);
static void hud_identity_update(void);
static const SpriteDefinition *hud_portrait_definition(u8 id);
static void hud_draw_life_frames(void);

void FUNCAO_RELOGIO()
{
	/* TIME LIMIT OFF nao para o relogio "visualmente": para a CONTAGEM, entao
	   nao existe time-over. Esconder o mostrador e outra opcao (hudTimer). */
	if(gMatchRules.timeLimit == CONFIG_TIME_OFF){ return; }

	if(gClockTimer>0 && (gClockLTimer>0 || gClockRTimer>0) && (P[1].energiaBase>0 && P[2].energiaBase>0) ){ gClockTimer--; }

	if(gClockTimer==0)
	{
		gClockRTimer--;
		if(gClockRTimer==-1)
		{
			if(gClockLTimer>0)
			{
				gClockLTimer--;
				gClockRTimer=9;
			}
			else
			{
				gClockRTimer=0;
			}
		}
		gClockTimer=(s8)TIMING_roundClockTicks();
		hud_window_draw_clock();
	}
}

#define HUD_P1_X            32
#define HUD_P2_X            176
#define HUD_BAR_SEGMENTS    8
#define HUD_BAR_Y           8
#define HUD_BAR_STEP        16
#define HUD_CLK_L_X         144
#define HUD_CLK_R_X         160
#define HUD_CLK_Y           0
#define HUD_CLK_BG_X        17
#define HUD_CLK_BG_ROW      0
#define HUD_CLK_BG_COLS     6
#define HUD_FRAME_P1_COL    4
#define HUD_FRAME_P2_COL    22
#define HUD_SPECIAL_P1_COL  4
#define HUD_SPECIAL_P2_COL 22
#define HUD_SPECIAL_ROW     27
#define HUD_SPECIAL_LABEL_ROW 26
#define HUD_MESSAGE_ROW     5
#define HUD_MESSAGE_ROWS    6
#define HUD_COMBO_ROW       21
#define HUD_KO_BANNER_X     136
#define HUD_KO_BANNER_Y     96

static u16 sHudMessageTileBase;
static u16 sHudBlackTile;
static u16 sHudSpecialTileBase;
static u8 sHudMessage = 0xFF;
static u16 sHudMessageMap[40 * HUD_MESSAGE_ROWS];
static Sprite *sHudP1Segments[HUD_BAR_SEGMENTS];
static Sprite *sHudP2Segments[HUD_BAR_SEGMENTS];
static Sprite *sHudP1Damage[HUD_BAR_SEGMENTS];
static Sprite *sHudP2Damage[HUD_BAR_SEGMENTS];
static Sprite *sHudLifeTrackP1;
static Sprite *sHudLifeTrackP2;
static Sprite *sHudClockSpriteL;
static Sprite *sHudClockSpriteR;
static u16 sHudSegmentTile;
static u16 sHudDamageSegmentTile;
static s8  sHudClockDigitL = -1;
static s8  sHudClockDigitR = -1;
static u8  sHudWindowActive = 0;
static u8  sHudClockBgState = 0xFF;
static s8  sHudSpecialCount[2] = { -1, -1 };
static u8  sHudSpecialEnabled = 0xFF;
static u16 sHudComboMap[40 * 2];
static u8  sHudComboValue = 0xFF;
static u8  sHudComboPlayer = 0;
static u8  sHudFighterId[2] = { 0xFF, 0xFF };
static u8  sHudWins[2] = { 0xFF, 0xFF };
static Sprite *sHudPortrait[2];
static Sprite *sHudKoBanner;

/* PAL1 index 11 = black. Kept only for the transient result-message panel;
   the life bars themselves no longer paint a full-width WINDOW rectangle. */
static const u32 kHudBlackTile[8] =
{
	0xBBBBBBBB, 0xBBBBBBBB, 0xBBBBBBBB, 0xBBBBBBBB,
	0xBBBBBBBB, 0xBBBBBBBB, 0xBBBBBBBB, 0xBBBBBBBB
};

static const char *hud_fighter_name(u8 id)
{
	if(id == 2){ return "KEN"; }
	if(id == 3){ return "MUSGO"; }
	return "RYO";
}

static const SpriteDefinition *hud_portrait_definition(u8 id)
{
	if(id == 2){ return &spr_hud_portrait_ken; }
	if(id == 3){ return &spr_hud_portrait_musgo; }
	return &spr_hud_portrait_ryo;
}

	/* Identity is anchored to the portrait, not to a debug-like text row. */
static void hud_identity_update(void)
{
	u8 p;
	if(!sHudWindowActive){ return; }
	if(sHudFighterId[0] == P[1].id && sHudFighterId[1] == P[2].id &&
		sHudWins[0] == P[1].wins && sHudWins[1] == P[2].wins){ return; }
	VDP_setTextPalette(PAL1);
	VDP_drawText("      ", 0, 3);
	VDP_drawText("      ", 34, 3);
	VDP_drawText("      ", 0, 4);
	VDP_drawText("      ", 34, 4);
	VDP_drawText("      ", 0, 5);
	VDP_drawText("      ", 34, 5);
	VDP_drawText(hud_fighter_name(P[1].id), 0, 4);
	VDP_drawText(hud_fighter_name(P[2].id), 34, 4);
	for(p = 0; p < 2; p++)
	{
		u8 x = (p == 0) ? 0 : 34;
		VDP_drawText((p == 0 && P[1].wins >= 1) || (p == 1 && P[2].wins >= 1) ? "*" : ".", x, 5);
		VDP_drawText((p == 0 && P[1].wins >= 2) || (p == 1 && P[2].wins >= 2) ? "*" : ".", x + 2, 5);
	}
	sHudFighterId[0] = P[1].id; sHudFighterId[1] = P[2].id;
	sHudWins[0] = P[1].wins; sHudWins[1] = P[2].wins;
}

void hud_window_load(void)
{
	/* Bars and clock are sprites. Their definitions allocate VRAM from the
	   sprite pool and no longer consume the stage/plane tile range here. */
	sHudMessageTileBase = gInd_tileset;
	VDP_loadTileSet(&ts_hud_message_font, sHudMessageTileBase, DMA);
	gInd_tileset += ts_hud_message_font.numTile;
	sHudSpecialTileBase = gInd_tileset;
	VDP_loadTileSet(&ts_hud_special_segment, sHudSpecialTileBase, DMA);
	gInd_tileset += ts_hud_special_segment.numTile;
	sHudBlackTile = gInd_tileset;
	VDP_loadTileData(kHudBlackTile, sHudBlackTile, 1, CPU);
	HAMOOPIG_probeVramRange(sHudMessageTileBase,
		(u16)(ts_hud_message_font.numTile + ts_hud_special_segment.numTile + 1u));
	gInd_tileset += 1;
	sHudMessage = 0xFF;
	hud_combo_clear();
}

static u8 hud_clock_digit(s8 v)
{
	if(v < 0){ return 0; }
	if(v > 9){ return 9; }
	return (u8)v;
}

static void hud_window_put_digit(u8 side, u8 digit)
{
	Sprite *sprite = (side == 0) ? sHudClockSpriteL : sHudClockSpriteR;
	if(!sprite){ return; }
	SPR_setFrame(sprite, digit);
}

static void hud_combo_line(const char *str)
{
	u16 col = (40 - strlen(str) * 2) / 2;
	while(*str)
	{
		u8 ch = *str++;
		u16 glyph, base;
		if(ch >= 'A' && ch <= 'Z'){ glyph = ch - 'A'; }
		else if(ch >= '0' && ch <= '9'){ glyph = 26 + ch - '0'; }
		else { col += 2; continue; }
		base = sHudMessageTileBase + glyph * 2;
		sHudComboMap[col] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base);
		sHudComboMap[col+1] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base+1);
		sHudComboMap[40+col] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base+72);
		sHudComboMap[40+col+1] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base+73);
		col += 2;
	}
}

static void hud_combo_clear(void)
{
	memset(sHudComboMap, 0, sizeof(sHudComboMap));
	/* Combo text is a transient, two-row overlay.  Keep it out of the
	   per-frame DMA queue: the queue is shared with sprite tile uploads and
	   can otherwise push the NTSC worst frame over the VBlank envelope. */
	VDP_setTileMapDataRect(BG_A, sHudComboMap, 0, HUD_COMBO_ROW, 40, 2, 40, CPU);
	sHudComboValue = 0xFF;
	sHudComboPlayer = 0;
}

static void hud_combo_update(void)
{
	u8 p1 = P[1].hitCounter;
	u8 p2 = P[2].hitCounter;
	u8 player = (p1 >= p2) ? 1 : 2;
	u8 value = (player == 1) ? p1 : p2;
	char text[] = "00 HITS";
	if(!gConfig.hudHitCount){ if(sHudComboValue != 0){ hud_combo_clear(); sHudComboValue = 0; } return; }
	if(value < 2)
	{
		if(sHudComboValue != 0){ hud_combo_clear(); sHudComboValue = 0; }
		return;
	}
	if(value > 99){ value = 99; }
	if(value < 10){ text[0] = ' '; text[1] = '0' + value; }
	else { text[0] = '0' + (value / 10); text[1] = '0' + (value % 10); }
	if(value == sHudComboValue && player == sHudComboPlayer){ return; }
	memset(sHudComboMap, 0, sizeof(sHudComboMap));
	hud_combo_line(text);
	VDP_setTileMapDataRect(BG_A, sHudComboMap, 0, HUD_COMBO_ROW, 40, 2, 40, CPU);
	sHudComboValue = value;
	sHudComboPlayer = player;
}

static void hud_window_draw_clock(void)
{
	s8 left;
	s8 right;

	if(!sHudWindowActive){ return; }

	/* Esconder e so apresentacao: gClockLTimer/gClockRTimer continuam correndo
	   e o time-over continua valendo. */
	{
		SpriteVisibility v = gConfig.hudTimer ? VISIBLE : HIDDEN;
		if(sHudClockSpriteL){ SPR_setVisibility(sHudClockSpriteL, v); }
		if(sHudClockSpriteR){ SPR_setVisibility(sHudClockSpriteR, v); }
	}

	left = (s8)hud_clock_digit(gClockLTimer);
	right = (s8)hud_clock_digit(gClockRTimer);
	if(left == sHudClockDigitL && right == sHudClockDigitR){ return; }
	sHudClockDigitL = left;
	sHudClockDigitR = right;
	hud_window_put_digit(0, (u8)left);
	hud_window_put_digit(1, (u8)right);
}

/* TIMER BG é uma moldura compacta opcional, nunca uma faixa WINDOW global.
   O relógio ocupa as colunas 18..21; seis colunas por duas linhas dão apenas
   uma margem de 8 px e deixam o cenário visível no restante da tela. */
static void hud_clock_background_update(void)
{
	u8 row;
	u8 col;
	if(!sHudWindowActive){ return; }
	if(sHudClockBgState == (u8)gConfig.hudTimerBg){ return; }
	for(row = 0; row < 2; row++)
	{
		for(col = 0; col < HUD_CLK_BG_COLS; col++)
		{
			VDP_setTileMapXY(BG_A,
				gConfig.hudTimerBg ? TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, sHudBlackTile) : 0,
				HUD_CLK_BG_X + col, HUD_CLK_BG_ROW + row);
		}
	}
	sHudClockBgState = (u8)gConfig.hudTimerBg;
}

static void hud_draw_life_frames(void)
{
	/* The chassis is a sprite so it stays above the scrolling stage. The
	   yellow cells are separate sprites and remain the only state-bearing fill. */
	if(sHudLifeTrackP1){ SPR_setVisibility(sHudLifeTrackP1, VISIBLE); }
	if(sHudLifeTrackP2){ SPR_setVisibility(sHudLifeTrackP2, VISIBLE); }
}

static u8 hud_segment_count(s8 energy)
{
	u16 e = (energy < 0) ? 0 : (energy > 96 ? 96 : (u16)energy);
	return (u8)((e * HUD_BAR_SEGMENTS + 95) / 96);
}

static void hud_set_bar(Sprite **segments, u8 count, u16 baseX, u8 reverse)
{
	u8 i;
	/* Apresentacao apenas: energia, dano e KO continuam iguais com a barra
	   escondida. Por isso zera-se a contagem de segmentos visiveis, nao a
	   energia. */
	if(!gConfig.hudLifeBar){ count = 0; }
	for(i = 0; i < HUD_BAR_SEGMENTS; i++)
	{
		Sprite *sprite = segments[i];
		if(!sprite){ continue; }
		if(i < count)
		{
			u16 x = reverse ? (u16)(baseX + (HUD_BAR_SEGMENTS - 1 - i) * HUD_BAR_STEP)
			                : (u16)(baseX + i * HUD_BAR_STEP);
			SPR_setPosition(sprite, x, HUD_BAR_Y);
			SPR_setVisibility(sprite, VISIBLE);
		}
		else
		{
			SPR_setVisibility(sprite, HIDDEN);
		}
	}
}

	/* A barra de especial usa uma família azul autoral derivada do mesmo
	   segmento, mas com índice de acento distinto no PAL1. Fica no rodapé para
	   não parecer uma segunda vida. */
static u8 hud_special_count(s8 energy)
{
	u16 e = (energy < 0) ? 0 : (energy > 32 ? 32 : (u16)energy);
	return (u8)((e * HUD_BAR_SEGMENTS + 31) / 32);
}

static void hud_draw_special(u8 player, u8 count)
{
	u8 i;
	u8 base = (player == 0) ? HUD_SPECIAL_P1_COL : HUD_SPECIAL_P2_COL;
	u8 reverse = (player != 0);
	if(!gConfig.hudSpecialBar){ count = 0; }
	for(i = 0; i < HUD_BAR_SEGMENTS; i++)
	{
		u8 logical = reverse ? (HUD_BAR_SEGMENTS - 1 - i) : i;
		u16 tile = (i < count) ? sHudSpecialTileBase : sHudBlackTile;
		VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, tile),
			base + logical * 2, HUD_SPECIAL_ROW);
		VDP_setTileMapXY(BG_A, TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE,
			i < count ? tile + 1 : sHudBlackTile),
			base + logical * 2 + 1, HUD_SPECIAL_ROW);
	}
}

/* SPR_init() owns a movable VRAM region.  Releasing/recreating a fighter can
   compact that region and move the tile set of the first HUD segment.  The
   remaining 15 segment sprites intentionally alias that tile set, so their
   attributes (and the BG_A special-bar aliases) must follow the owner every
   frame instead of caching the old index. */
static void hud_sync_segment_tile(void)
{
	u16 current;
	u16 damageCurrent;
	u8 i;
	if(!sHudP1Segments[0]){ return; }
	current = (u16)(sHudP1Segments[0]->attribut & 0x07FF);
	damageCurrent = sHudP1Damage[0] ? (u16)(sHudP1Damage[0]->attribut & 0x07FF) : sHudDamageSegmentTile;
	if(current != sHudSegmentTile)
	{
		sHudSegmentTile = current;
		for(i = 1; i < HUD_BAR_SEGMENTS; i++)
		{
			/* Aliases do not own VRAM; only follow the owner tile bits. */
			if(sHudP1Segments[i]){ sHudP1Segments[i]->attribut = (sHudP1Segments[i]->attribut & 0xF800) | current; }
			if(sHudP2Segments[i]){ sHudP2Segments[i]->attribut = (sHudP2Segments[i]->attribut & 0xF800) | current; }
		}
		if(sHudP2Segments[0]){ sHudP2Segments[0]->attribut = (sHudP2Segments[0]->attribut & 0xF800) | current; }
	}
	if(damageCurrent != sHudDamageSegmentTile)
	{
		sHudDamageSegmentTile = damageCurrent;
		for(i = 1; i < HUD_BAR_SEGMENTS; i++)
		{
			if(sHudP1Damage[i]){ sHudP1Damage[i]->attribut = (sHudP1Damage[i]->attribut & 0xF800) | damageCurrent; }
			if(sHudP2Damage[i]){ sHudP2Damage[i]->attribut = (sHudP2Damage[i]->attribut & 0xF800) | damageCurrent; }
		}
		if(sHudP2Damage[0]){ sHudP2Damage[0]->attribut = (sHudP2Damage[0]->attribut & 0xF800) | damageCurrent; }
	}
	/* Force the compact BG_A aliases to be redrawn with the new owner. */
	sHudSpecialCount[0] = -1;
	sHudSpecialCount[1] = -1;
}

void hud_window_init(void)
{
	u16 attr;
	u8 i;
	const u16 autoFlags = SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY |
		SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD;
	const u16 sharedFlags = SPR_FLAG_DISABLE_DELAYED_FRAME_UPDATE | SPR_FLAG_AUTO_VISIBILITY;

	memset(sHudP1Segments, 0, sizeof(sHudP1Segments));
	memset(sHudP2Segments, 0, sizeof(sHudP2Segments));
	memset(sHudP1Damage, 0, sizeof(sHudP1Damage));
	memset(sHudP2Damage, 0, sizeof(sHudP2Damage));
	memset(sHudPortrait, 0, sizeof(sHudPortrait));
	sHudKoBanner = NULL;
	sHudLifeTrackP1 = NULL;
	sHudLifeTrackP2 = NULL;
	sHudLifeTrackP1 = SPR_addSpriteExSafe(&spr_hud_life_track, HUD_P1_X, 0,
		TILE_ATTR(PAL1, FALSE, FALSE, FALSE), autoFlags);
	sHudLifeTrackP2 = SPR_addSpriteExSafe(&spr_hud_life_track, HUD_P2_X, 0,
		TILE_ATTR(PAL1, FALSE, FALSE, FALSE), autoFlags);
	if(!sHudLifeTrackP1 || !sHudLifeTrackP2){ SYS_die("HUD life track allocation failed"); return; }
	SPR_setDepth(sHudLifeTrackP1, 5);
	SPR_setDepth(sHudLifeTrackP2, 5);
	SPR_setHFlip(sHudLifeTrackP2, TRUE);
	sHudSegmentTile = 0;
	sHudP1Segments[0] = SPR_addSpriteExSafe(&spr_hud_energy_segment, HUD_P1_X, HUD_BAR_Y,
		TILE_ATTR(PAL1, FALSE, FALSE, FALSE), autoFlags);
	if(!sHudP1Segments[0]){ SYS_die("HUD segment sprite allocation failed"); return; }
	sHudSegmentTile = (u16)(sHudP1Segments[0]->attribut & 0x07FF);
	for(i = 1; i < HUD_BAR_SEGMENTS; i++)
	{
		attr = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, sHudSegmentTile);
		sHudP1Segments[i] = SPR_addSpriteExSafe(&spr_hud_energy_segment, HUD_P1_X, HUD_BAR_Y, attr, sharedFlags);
		sHudP2Segments[i] = SPR_addSpriteExSafe(&spr_hud_energy_segment, HUD_P2_X, HUD_BAR_Y, attr, sharedFlags);
		if(!sHudP1Segments[i] || !sHudP2Segments[i]){ SYS_die("HUD segment sprite allocation failed"); return; }
	}
	attr = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, sHudSegmentTile);
	sHudP2Segments[0] = SPR_addSpriteExSafe(&spr_hud_energy_segment, HUD_P2_X, HUD_BAR_Y, attr, sharedFlags);
	if(!sHudP2Segments[0]){ SYS_die("HUD segment sprite allocation failed"); return; }
	for(i = 0; i < HUD_BAR_SEGMENTS; i++)
	{
		if(sHudP1Segments[i]){ SPR_setDepth(sHudP1Segments[i], 3); SPR_setVisibility(sHudP1Segments[i], HIDDEN); }
		if(sHudP2Segments[i]){ SPR_setDepth(sHudP2Segments[i], 3); SPR_setVisibility(sHudP2Segments[i], HIDDEN); }
	}
	sHudP1Damage[0] = SPR_addSpriteExSafe(&spr_hud_damage_segment, HUD_P1_X, HUD_BAR_Y,
		TILE_ATTR(PAL1, FALSE, FALSE, FALSE), autoFlags);
	if(!sHudP1Damage[0]){ SYS_die("HUD damage allocation failed"); return; }
	sHudDamageSegmentTile = (u16)(sHudP1Damage[0]->attribut & 0x07FF);
	for(i = 1; i < HUD_BAR_SEGMENTS; i++)
	{
		attr = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, sHudDamageSegmentTile);
		sHudP1Damage[i] = SPR_addSpriteExSafe(&spr_hud_damage_segment, HUD_P1_X, HUD_BAR_Y, attr, sharedFlags);
		sHudP2Damage[i] = SPR_addSpriteExSafe(&spr_hud_damage_segment, HUD_P2_X, HUD_BAR_Y, attr, sharedFlags);
		if(!sHudP1Damage[i] || !sHudP2Damage[i]){ SYS_die("HUD damage allocation failed"); return; }
	}
	attr = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, sHudDamageSegmentTile);
	sHudP2Damage[0] = SPR_addSpriteExSafe(&spr_hud_damage_segment, HUD_P2_X, HUD_BAR_Y, attr, sharedFlags);
	if(!sHudP2Damage[0]){ SYS_die("HUD damage allocation failed"); return; }
	for(i = 0; i < HUD_BAR_SEGMENTS; i++)
	{
		if(sHudP1Damage[i]){ SPR_setDepth(sHudP1Damage[i], 4); SPR_setVisibility(sHudP1Damage[i], HIDDEN); }
		if(sHudP2Damage[i]){ SPR_setDepth(sHudP2Damage[i], 4); SPR_setVisibility(sHudP2Damage[i], HIDDEN); }
	}

	sHudClockSpriteL = SPR_addSpriteExSafe(&spr_hud_clock_digit, HUD_CLK_L_X, HUD_CLK_Y,
		TILE_ATTR(PAL1, FALSE, FALSE, FALSE), autoFlags);
	if(!sHudClockSpriteL){ SYS_die("HUD clock sprite allocation failed"); return; }
	sHudClockSpriteR = SPR_addSpriteExSafe(&spr_hud_clock_digit, HUD_CLK_R_X, HUD_CLK_Y,
		TILE_ATTR(PAL1, FALSE, FALSE, FALSE), autoFlags);
	if(!sHudClockSpriteR){ SYS_die("HUD clock sprite allocation failed"); return; }
	if(sHudClockSpriteL){ SPR_setDepth(sHudClockSpriteL, 3); }
	if(sHudClockSpriteR){ SPR_setDepth(sHudClockSpriteR, 3); }
	sHudPortrait[0] = SPR_addSpriteExSafe(hud_portrait_definition(P[1].id), 0, 0,
		TILE_ATTR(PAL2, FALSE, FALSE, FALSE), autoFlags);
	sHudPortrait[1] = SPR_addSpriteExSafe(hud_portrait_definition(P[2].id), 288, 0,
		TILE_ATTR(PAL3, FALSE, FALSE, FALSE), autoFlags);
	if(!sHudPortrait[0] || !sHudPortrait[1]){ SYS_die("HUD portrait allocation failed"); return; }
	SPR_setHFlip(sHudPortrait[1], TRUE);
	SPR_setDepth(sHudPortrait[0], 4);
	SPR_setDepth(sHudPortrait[1], 4);
	sHudKoBanner = SPR_addSpriteExSafe(&spr_hud_ko_banner, HUD_KO_BANNER_X, HUD_KO_BANNER_Y,
		TILE_ATTR(PAL1, FALSE, FALSE, FALSE), autoFlags);
	if(!sHudKoBanner){ SYS_die("HUD KO banner allocation failed"); return; }
	SPR_setDepth(sHudKoBanner, 1);
	SPR_setVisibility(sHudKoBanner, HIDDEN);
	sHudClockDigitL = -1;
	sHudClockDigitR = -1;
	sHudSpecialCount[0] = -1;
	sHudSpecialCount[1] = -1;
	sHudSpecialEnabled = 0xFF;
	sHudClockBgState = 0xFF;
	sHudWindowActive = 1;
	hud_draw_life_frames();
	VDP_drawText("SP", HUD_SPECIAL_P1_COL, HUD_SPECIAL_LABEL_ROW);
	VDP_drawText("SP", HUD_SPECIAL_P2_COL + 1, HUD_SPECIAL_LABEL_ROW);
	hud_window_update();
	hud_identity_update();
	hud_combo_update();
	hud_window_draw_clock();
}

void hud_window_update(void)
{
	if(!sHudWindowActive){ return; }
	hud_sync_segment_tile();
	hud_identity_update();
	hud_clock_background_update();
	hud_set_bar(sHudP1Damage, hud_segment_count(P[1].energia), HUD_P1_X, FALSE);
	hud_set_bar(sHudP2Damage, hud_segment_count(P[2].energia), HUD_P2_X, TRUE);
	hud_set_bar(sHudP1Segments, hud_segment_count(P[1].energiaBase), HUD_P1_X, FALSE);
	hud_set_bar(sHudP2Segments, hud_segment_count(P[2].energiaBase), HUD_P2_X, TRUE);
	{
		u8 c1 = hud_special_count(P[1].energiaSP);
		u8 c2 = hud_special_count(P[2].energiaSP);
		if(c1 != (u8)sHudSpecialCount[0] || sHudSpecialEnabled != (u8)gConfig.hudSpecialBar){ hud_draw_special(0, c1); sHudSpecialCount[0] = (s8)c1; }
		if(c2 != (u8)sHudSpecialCount[1] || sHudSpecialEnabled != (u8)gConfig.hudSpecialBar){ hud_draw_special(1, c2); sHudSpecialCount[1] = (s8)c2; }
		sHudSpecialEnabled = (u8)gConfig.hudSpecialBar;
	}
}

void hud_window_off(void)
{
	u8 i;
	hud_message_clear();
	hud_combo_clear();
	for(i = 0; i < HUD_BAR_SEGMENTS; i++)
	{
		if(sHudP1Segments[i]){ SPR_releaseSprite(sHudP1Segments[i]); sHudP1Segments[i] = NULL; }
		if(sHudP2Segments[i]){ SPR_releaseSprite(sHudP2Segments[i]); sHudP2Segments[i] = NULL; }
		if(sHudP1Damage[i]){ SPR_releaseSprite(sHudP1Damage[i]); sHudP1Damage[i] = NULL; }
		if(sHudP2Damage[i]){ SPR_releaseSprite(sHudP2Damage[i]); sHudP2Damage[i] = NULL; }
	}
	if(sHudLifeTrackP1){ SPR_releaseSprite(sHudLifeTrackP1); sHudLifeTrackP1 = NULL; }
	if(sHudLifeTrackP2){ SPR_releaseSprite(sHudLifeTrackP2); sHudLifeTrackP2 = NULL; }
	if(sHudClockSpriteL){ SPR_releaseSprite(sHudClockSpriteL); sHudClockSpriteL = NULL; }
	if(sHudClockSpriteR){ SPR_releaseSprite(sHudClockSpriteR); sHudClockSpriteR = NULL; }
	if(sHudPortrait[0]){ SPR_releaseSprite(sHudPortrait[0]); sHudPortrait[0] = NULL; }
	if(sHudPortrait[1]){ SPR_releaseSprite(sHudPortrait[1]); sHudPortrait[1] = NULL; }
	if(sHudKoBanner){ SPR_releaseSprite(sHudKoBanner); sHudKoBanner = NULL; }
	sHudWindowActive = 0;
	sHudClockDigitL = -1;
	sHudClockDigitR = -1;
	sHudSegmentTile = 0;
	sHudSpecialCount[0] = -1;
	sHudSpecialCount[1] = -1;
	sHudSpecialEnabled = 0xFF;
	sHudClockBgState = 0xFF;
	sHudFighterId[0] = 0xFF; sHudFighterId[1] = 0xFF;
	sHudWins[0] = 0xFF; sHudWins[1] = 0xFF;
}

/* Atlas cells are 16x16 (2x2 tiles), 36 cells across in ROW order.
   PAL1 belongs to the HUD; fighter palettes can change independently. */
static void hud_message_line(const char *str, u16 row)
{
	u16 col = (40 - strlen(str) * 2) / 2;
	while(*str)
	{
		u8 ch = *str++;
		u16 glyph;
		u16 base;
		if(ch >= 'A' && ch <= 'Z'){ glyph = ch - 'A'; }
		else if(ch >= '0' && ch <= '9'){ glyph = 26 + ch - '0'; }
		else { col += 2; continue; }
		base = sHudMessageTileBase + glyph * 2;
		sHudMessageMap[(row-HUD_MESSAGE_ROW)*40+col] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base);
		sHudMessageMap[(row-HUD_MESSAGE_ROW)*40+col+1] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base+1);
		sHudMessageMap[(row-HUD_MESSAGE_ROW+1)*40+col] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base+72);
		sHudMessageMap[(row-HUD_MESSAGE_ROW+1)*40+col+1] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base+73);
		col += 2;
	}
}

void hud_message_clear(void)
{
	if(sHudKoBanner){ SPR_setVisibility(sHudKoBanner, HIDDEN); }
	memset(sHudMessageMap, 0, sizeof(sHudMessageMap));
	VDP_setTileMapDataRect(BG_A, sHudMessageMap, 0, HUD_MESSAGE_ROW, 40, HUD_MESSAGE_ROWS, 40, CPU);
	sHudMessage = 0;
}

void hud_message_update(void)
{
	u8 message = 0;
	if(gRoom == SCENE_AFTER_MATCH){ message = (gWinnerID == 1) ? 7 : 8; }
	else if(gPauseKoTimer > 0 && gPauseKoTimer < 330){ message = 3; }
	else if(P[1].state == 611 || P[1].state == 612){ message = 4; }
	else if(P[2].state == 611 || P[2].state == 612){ message = 5; }
	else if(P[1].state == 615 && P[2].state == 615){ message = 6; }
	else if(gFrames < 180){ message = 1; }
	else if(gFrames < 300){ message = 2; }
	if(sHudKoBanner){ SPR_setVisibility(sHudKoBanner, (message == 3) ? VISIBLE : HIDDEN); }
	if(message == sHudMessage){ return; }
	memset(sHudMessageMap, 0, sizeof(sHudMessageMap));
	sHudMessage = message;
	if(!message){ hud_message_clear(); return; }
	/* Round/FIGHT/KO are overlaid on the stage with transparent cells.  The
	   old implementation filled a 36-column black strip for every transient
	   message, which visually interrupted the scene and was especially harsh
	   over the timer area.  Result screens keep their compact black panel so
	   the two-line rematch prompt remains readable. */
	if(message >= 7)
	{
		u16 row, col;
		for(row=0; row < HUD_MESSAGE_ROWS; row++)
			for(col=2; col<38; col++)
				sHudMessageMap[row*40+col] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, sHudBlackTile);
	}
	if(message == 1){
		char roundText[] = "ROUND 0";
		roundText[6] = '0' + ((gRound > 9) ? 9 : gRound);
		hud_message_line(roundText, HUD_MESSAGE_ROW);
	}
	if(message == 2){ hud_message_line("FIGHT", HUD_MESSAGE_ROW); }
	if(message == 3){ /* Authored sprite banner replaces the old atlas text. */ }
	if(message == 4 || message == 7){ hud_message_line("PLAYER 1 WINS", HUD_MESSAGE_ROW); }
	if(message == 5 || message == 8){ hud_message_line("PLAYER 2 WINS", HUD_MESSAGE_ROW); }
	if(message == 6){ hud_message_line("DRAW", HUD_MESSAGE_ROW); }
	if(message >= 7){
		hud_message_line("A REMATCH", HUD_MESSAGE_ROW+2);
		hud_message_line("START SELECT", HUD_MESSAGE_ROW+4);
	}
	VDP_setTileMapDataRect(BG_A, sHudMessageMap, 0, HUD_MESSAGE_ROW, 40, HUD_MESSAGE_ROWS, 40, CPU);
}

void FUNCAO_BARRAS_DE_ENERGIA()
{
	
	for(i=1; i<=2; i++)
	{
		if( P[i].energia != P[i].energiaBase )
		{ 
			if(P[i].energia > P[i].energiaBase){ P[i].energia--; } //decrementa a 'energia' aos poucos, até igualar a 'energiaBase'
			if(P[i].energia < P[i].energiaBase){ P[i].energia++; } //incrementa a 'energia' aos poucos, até igualar a 'energiaBase'
		} 
		
		/* P1/P2 vida usam células compactas; a barra de especial é atualizada
		   uma vez abaixo no plano BG_A. */
		
	}

	hud_window_update();
	hud_combo_update();
	
}
