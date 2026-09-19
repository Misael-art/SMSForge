#include <genesis.h>
#include "title.h"
#include "globals.h"
#include "config.h"
#include "scene.h"
#include "gfx.h"
#include "hud_gfx.h"
#include "sprite.h"
#include "sound.h"
#include "init.h"
#include "debug.h"
#include "hamoopig_runtime_probe.h"

/* Title backdrop/logo/BGA are resident in disjoint ranges.  Keep the
   16x16 message atlas and cursor above them, outside both title planes. */
#define TITLE_SCENE_TILE_BASE 1
#define TITLE_FONT_TILE_BASE 1000
#define TITLE_CURSOR_TILE (TITLE_FONT_TILE_BASE + 144)
#define TITLE_PANEL_X 1
#define TITLE_PANEL_W 20
/* Cada glifo ocupa 2 linhas, entao um painel de H linhas comporta H/2 slots.

   UMA geometria para todas as paginas, ancorada abaixo da arte.  O logo
   HAMOOPIG ocupa as linhas 4..11 do BG_B, entao um painel que comece na 13
   nunca o cobre.  Antes, OPTIONS crescia para cima ate a linha 4 e a pagina de
   debug ate a 6 -- as duas engoliam o logo.

   Quem nao cabe em 5 itens PAGINA.  A pagina e derivada do cursor global
   (pagina = cursor / itens por pagina), entao Cima/Baixo viram de pagina
   sozinhos e nao existe estado de paginacao para dessincronizar. */
#define TITLE_PANEL_Y 13
#define TITLE_PANEL_H 13
#define TITLE_ITEMS_PER_PAGE 5
#define TITLE_PANEL_MAX_H TITLE_PANEL_H
/* O titulo carrega a composicao com a tela protegida e so entao revela.
   O tempo de CARGA e medido separado do fade: misturar os dois faz um DMA
   lento parecer um fade lento. */
#define TITLE_FADE_IN_TICKS 15u  /* 0,25 s */

u8 titlePage = TITLE_PAGE_MAIN;
u8 titleCursor = TITLE_MAIN_START;

static u8 sPanelY = TITLE_PANEL_Y;
static u8 sPanelH = TITLE_PANEL_H;
static u16 sTitleMap[TITLE_PANEL_W * TITLE_PANEL_MAX_H];
static u16 sTitleBlackTile;
static u16 sTitlePanelTile;
static u16 sTitleFrameTile;
static bool sTitleReady;
static bool sTitleDirty;
static bool sTitleInitialCommit;
static u8 sMainSelectionLatched;
static u8 sTitlePageInputLock;
static u8 sTitlePhase;
static u16 sTitleFadeTicks;

static void title_render_main(void);

static void copy_title_palette(u16 *destination, const Palette *source)
{
	u16 colorCount = 0;
	memset(destination, 0, 16 * sizeof(u16));
	if(source && source->data)
	{
		colorCount = (source->length < 16) ? source->length : 16;
		memcpy(destination, source->data, colorCount * sizeof(u16));
	}
}
static void title_menu_sfx(void);

enum
{
	TITLE_PHASE_LOADING = 0,  /* tela protegida, DMA da composicao */
	TITLE_PHASE_FADE_IN = 1,
	TITLE_PHASE_ACTIVE  = 2,
	TITLE_PHASE_FADE_OUT = 3
};

/* A small, authorial-looking chevron uses the same PAL1 as the menu font.
   It is a UI marker, not gameplay art, and costs one tile only. */
static const u32 kTitleCursorTile[8] =
{
	0x20000000, 0x22000000, 0x22200000, 0x22220000,
	0x22200000, 0x22000000, 0x20000000, 0x00000000
};

static const u32 kTitleBlackTile[8] =
{
	0xBBBBBBBB, 0xBBBBBBBB, 0xBBBBBBBB, 0xBBBBBBBB,
	0xBBBBBBBB, 0xBBBBBBBB, 0xBBBBBBBB, 0xBBBBBBBB
};

/* UI-only tiles: PAL1 index 9 is the HUD's deep blue and index 2 is its warm
   accent. The menu now has a deliberate card boundary instead of a raw black
   rectangle, while remaining a transient interface composition. */
static const u32 kTitlePanelTile[8] =
{
	0x99999999, 0x99999999, 0x99999999, 0x99999999,
	0x99999999, 0x99999999, 0x99999999, 0x99999999
};

static const u32 kTitleFrameTile[8] =
{
	0x66666666, 0x66666666, 0x66666666, 0x66666666,
	0x66666666, 0x66666666, 0x66666666, 0x66666666
};

static u8 title_glyph(const char c)
{
	if(c >= 'A' && c <= 'Z'){ return (u8)(c - 'A'); }
	if(c >= '0' && c <= '9'){ return (u8)(26 + c - '0'); }
	return 0xFF;
}

static void title_map_fill(void)
{
	u16 row;
	u16 col;
	for(row = 0; row < sPanelH; row++)
	{
		for(col = 0; col < TITLE_PANEL_W; col++)
		{
			sTitleMap[(row * TITLE_PANEL_W) + col] = TILE_ATTR_FULL(
				PAL1, FALSE, FALSE, FALSE, sTitlePanelTile);
		}
	}
	for(row = 0; row < sPanelH; row++)
	{
		sTitleMap[(row * TITLE_PANEL_W)] = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, sTitleFrameTile);
		sTitleMap[(row * TITLE_PANEL_W) + TITLE_PANEL_W - 1] = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, sTitleFrameTile);
	}
	for(col = 0; col < TITLE_PANEL_W; col++)
	{
		sTitleMap[col] = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, sTitleFrameTile);
		sTitleMap[((sPanelH - 1) * TITLE_PANEL_W) + col] = TILE_ATTR_FULL(PAL1, FALSE, FALSE, FALSE, sTitleFrameTile);
	}
}

static void title_put_text_at(const char *text, u8 col, u8 row)
{
	u8 glyph;
	u16 base;
	while(*text && col < TITLE_PANEL_W)
	{
		glyph = title_glyph(*text++);
		if(glyph != 0xFF && col + 1 < TITLE_PANEL_W && row + 1 < sPanelH)
		{
			base = TITLE_FONT_TILE_BASE + ((u16)glyph * 2);
			sTitleMap[(row * TITLE_PANEL_W) + col] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base);
			sTitleMap[(row * TITLE_PANEL_W) + col + 1] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base + 1);
			sTitleMap[((row + 1) * TITLE_PANEL_W) + col] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base + 72);
			sTitleMap[((row + 1) * TITLE_PANEL_W) + col + 1] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, base + 73);
			col += 2;
		}
		else
		{
			col++;
		}
	}
}

static u8 title_text_width(const char *text)
{
	u8 length = 0;
	while(*text++){ length++; }
	return (u8)(length * 2);
}

static void title_put_centered(const char *text, u8 row)
{
	u8 width = title_text_width(text);
	u8 col = (width < TITLE_PANEL_W) ? (u8)((TITLE_PANEL_W - width) / 2) : 0;
	title_put_text_at(text, col, row);
}

static void title_put_cursor(u8 row, bool visible)
{
	if(visible && row + 1 < sPanelH)
	{
		sTitleMap[(row * TITLE_PANEL_W)] = TILE_ATTR_FULL(PAL1, TRUE, FALSE, FALSE, TITLE_CURSOR_TILE);
	}
}

static void title_commit_map(void)
{
	/* O primeiro mapa precisa estar residente antes de PAL_fadeIn. Depois da
	   carga inicial, a arte é restaurada por uma DMA própria; a página do menu
	   segue pela fila para não iniciar duas DMAs síncronas consecutivas. */
	VDP_setTileMapDataRect(BG_A, sTitleMap, TITLE_PANEL_X, sPanelY,
		TITLE_PANEL_W, sPanelH, TITLE_PANEL_W,
		sTitleInitialCommit ? DMA : CPU);
	sTitleDirty = FALSE;
}

static void title_restore_artwork(void)
{
	VDP_setTileMapEx(BG_B, title_scene.tilemap,
		TILE_ATTR_FULL(PAL0, 0, FALSE, FALSE, TITLE_SCENE_TILE_BASE),
		0, 0, 0, 0, 40, 28, DMA);
	/* DMA deixa o VDP ocupado. A página do menu é escrita logo depois no
	   mesmo plano por CPU; sem esta barreira a escrita podia disputar o DMA e
	   revelar uma composição parcial (arte ausente por alguns frames). */
	VDP_waitDMACompletion();
}

/* Carrega a composicao PROPRIA do titulo.  A abertura ja fez CLEAR_VDP, entao
   isto nao desenha por cima da arte dela: sao duas cenas com composicoes
   distintas, e os creditos da abertura nao ficam mais atras do painel. */
static void title_load_composition(void)
{
	PAL_setColors(0, (u16*)palette_black, 64, CPU);
	/* Do not inherit a queued/old opening tilemap.  Clearing both planes before
	   installing the title composition removes stale legal text even when the
	   previous scene ended with a pending DMA. */
	VDP_clearPlane(BG_A, TRUE);
	VDP_clearPlane(BG_B, TRUE);

	VDP_loadTileSet(title_scene.tileset, TITLE_SCENE_TILE_BASE, DMA);
	HAMOOPIG_probeVramRange(TITLE_SCENE_TILE_BASE, title_scene.tileset->numTile);
	title_restore_artwork();

	VDP_loadTileSet(&ts_hud_message_font, TITLE_FONT_TILE_BASE, DMA);
	VDP_loadTileData(kTitleCursorTile, TITLE_CURSOR_TILE, 1, CPU);
	sTitlePanelTile = TITLE_CURSOR_TILE + 1;
	sTitleFrameTile = TITLE_CURSOR_TILE + 2;
	VDP_loadTileData(kTitlePanelTile, sTitlePanelTile, 1, CPU);
	VDP_loadTileData(kTitleFrameTile, sTitleFrameTile, 1, CPU);
	/* Keep the legacy black tile index reserved after the frame tiles so old
	   captures cannot accidentally read a stale tile if the page is extended. */
	sTitleBlackTile = TITLE_CURSOR_TILE + 3;
	VDP_loadTileData(kTitleBlackTile, sTitleBlackTile, 1, CPU);
	HAMOOPIG_probeVramRange(TITLE_FONT_TILE_BASE, (u16)(ts_hud_message_font.numTile + 4u));
	sTitleReady = TRUE;

	title_render_main();
	sTitleInitialCommit = FALSE;
}

static const char *title_timelimit_label(void)
{
	if(gConfig.timeLimit == CONFIG_TIME_OFF){ return "TIME OFF"; }
	return (gConfig.timeLimit == CONFIG_TIME_60) ? "TIME 60" : "TIME 99";
}

static const char *title_options_label(u8 item)
{
	switch(item)
	{
		case TITLE_OPTION_SFX:      return gConfig.audioSfx    ? "SFX ON"    : "SFX OFF";
		case TITLE_OPTION_MUSIC:    return gConfig.audioMusic  ? "MUSIC ON"  : "MUSIC OFF";
		case TITLE_OPTION_LIFEBAR:  return gConfig.hudLifeBar  ? "LIFE ON"   : "LIFE OFF";
		case TITLE_OPTION_TIMER:    return gConfig.hudTimer    ? "CLOCK ON"  : "CLOCK OFF";
		case TITLE_OPTION_TIMERBG:  return gConfig.hudTimerBg  ? "TBG ON" : "TBG OFF";
		case TITLE_OPTION_TIMELIM:  return title_timelimit_label();
		case TITLE_OPTION_SPECIALBAR: return gConfig.hudSpecialBar ? "SPCL ON" : "SPCL OFF";
		case TITLE_OPTION_HITCOUNT: return gConfig.hudHitCount ? "HITS ON" : "HITS OFF";
		case TITLE_OPTION_SPECIALRULES: return gConfig.specialRules ? "RULES ON" : "RULE FREE";
		case TITLE_OPTION_STAGE2: return gConfig.stage2Enabled ? "STG2 ON" : "STG2 OFF";
		case TITLE_OPTION_OPENING: return gConfig.showOpening ? "INTRO ON" : "INTRO OFF";
		case TITLE_OPTION_FADE: return gConfig.useFade ? "FADE ON" : "FADE OFF";
		case TITLE_OPTION_DEBUG:    return "DEBUG";
		case TITLE_OPTION_DEFAULTS: return "DEFAULTS";
		default:                    return "BACK";
	}
}

static const char *title_debug_label(u8 item)
{
	switch(item)
	{
		case TITLE_DEBUG_BBOX:     return (gDebugFlags & DBG_BBOX)     ? "BOX ON"  : "BOX OFF";
		case TITLE_DEBUG_HBOX:     return (gDebugFlags & DBG_HBOX)     ? "HIT ON"  : "HIT OFF";
		case TITLE_DEBUG_TEXT:     return (gDebugFlags & DBG_TEXT)     ? "TEXT ON" : "TEXT OFF";
		case TITLE_DEBUG_PERF:     return (gDebugFlags & DBG_PERF)     ? "PERF ON" : "PERF OFF";
		case TITLE_DEBUG_FRAMEADV: return (gDebugFlags & DBG_FRAMEADV) ? "FRM ON"  : "FRM OFF";
		case TITLE_DEBUG_FREESTEP: return gFreeStepArmed               ? "STEP ON" : "STEP OFF";
		case TITLE_DEBUG_TICK:
			return (gTimingProfile == TIMING_PROFILE_NORMAL) ? "TICK NORM"
				: ((gLogicRate == LOGIC_RATE_50) ? "TICK L50" : "TICK L60");
		/* 240 linhas so existe em console PAL; em NTSC a opcao e inerte. */
		case TITLE_DEBUG_H240:
			return !gRegionIsPal ? "240 NA" : (gScreen240 ? "240 ON" : "240 OFF");
		default:                   return "BACK";
	}
}

static const char *title_main_label(u8 item)
{
	return (item == TITLE_MAIN_START) ? "START" : "OPTION";
}

/* Desenha a fatia da lista que contem o cursor.  O titulo carrega o numero da
   pagina porque sem ele nao ha como saber que existe mais coisa abaixo. */
static void title_render_paged(const char *titulo, u8 count, const char *(*label)(u8))
{
	u8 page = (u8)(titleCursor / TITLE_ITEMS_PER_PAGE);
	u8 first = (u8)(page * TITLE_ITEMS_PER_PAGE);
	u8 pages = (u8)((count + TITLE_ITEMS_PER_PAGE - 1) / TITLE_ITEMS_PER_PAGE);
	u8 i;

	title_map_fill();
	if(pages > 1)
	{
		sprintf(gStr, "%s %u", titulo, (u16)(page + 1));
		title_put_centered(gStr, 0);
	}
	else
	{
		title_put_centered(titulo, 0);
	}

	for(i = 0; i < TITLE_ITEMS_PER_PAGE && (u8)(first + i) < count; i++)
	{
		title_put_centered(label((u8)(first + i)), (u8)(2 + (i * 2)));
	}
	title_put_cursor((u8)(2 + ((titleCursor - first) * 2)), TRUE);
	title_commit_map();
}

static void title_render_main(void)
{
	title_render_paged("MAIN MENU", 2, title_main_label);
}

static void title_render_options(void)
{
	title_render_paged("OPTIONS", (u8)(TITLE_OPTION_BACK + 1), title_options_label);
}

static void title_render_debug(void)
{
	title_render_paged("DEBUG", (u8)(TITLE_DEBUG_BACK + 1), title_debug_label);
}

/* Todas as paginas tem a mesma geometria agora, mas a arte e redesenhada
   assim mesmo: o painel anterior pode ter deixado tiles opacos onde a nova
   pagina tem menos itens. */
static void title_goto_page(u8 page, u8 cursor)
{
	titlePage = page;
	titleCursor = cursor;
	sTitlePageInputLock = 2;
	sPanelY = TITLE_PANEL_Y;
	sPanelH = TITLE_PANEL_H;
	title_menu_sfx();
	title_restore_artwork();
	if(page == TITLE_PAGE_MAIN){ title_render_main(); }
	else if(page == TITLE_PAGE_OPTIONS){ title_render_options(); }
	else { title_render_debug(); }
}

static void title_menu_sfx(void)
{
	if(gConfig.audioSfx)
	{
		XGM_setPCM(INGAME_SFX, snd_confirm, sizeof(snd_confirm));
		XGM_startPlayPCM(INGAME_SFX, 1, SOUND_PCM_CH3);
	}
}

static void title_start_game(void)
{
	title_menu_sfx();
	/* A troca de cena nao pode acontecer no mesmo tick que inicia o fade:
	   CLEAR_VDP e a carga do seletor sobrescreveriam a composicao enquanto a
	   paleta ainda esta sendo reduzida, produzindo um corte visivel.  O estado
	   FADE_OUT deixa a cena atual dona do VDP ate PAL_isDoingFade() terminar. */
	sTitlePhase = TITLE_PHASE_FADE_OUT;
	sTitleFadeTicks = 0;
	sTitlePageInputLock = 0xFF;
	if(gConfig.useFade){ PAL_fadeOutAll(8, TRUE); }
}

void FUNCAO_TITLE_INIT(void)
{
	if((TITLE_SCENE_TILE_BASE + title_scene.tileset->numTile) >= TITLE_FONT_TILE_BASE)
	{
		SYS_die("Title font overlaps title artwork");
		return;
	}
	titlePage = TITLE_PAGE_MAIN;
	titleCursor = TITLE_MAIN_START;
	sMainSelectionLatched = TITLE_MAIN_START;
	sTitlePageInputLock = 0;
	/* A pagina de debug usa um painel maior; reentrar no titulo tem de voltar
	   a geometria do menu, senao o primeiro commit desenha no lugar errado. */
	sPanelY = TITLE_PANEL_Y;
	sPanelH = TITLE_PANEL_H;
	sTitlePhase = TITLE_PHASE_LOADING;
	sTitleDirty = TRUE;
	sTitleInitialCommit = TRUE;
	sTitleFadeTicks = 0;
}

void FUNCAO_TITLE_UPDATE(void)
{
	if(sTitlePhase == TITLE_PHASE_LOADING)
	{
		title_load_composition();
		/* O fade e sobre as 64 cores, entao palette[] precisa conter TODAS as
		   quatro paletas de destino.  Deixar PAL1 zerada aqui fazia o fade
		   levar a paleta do texto para preto DEPOIS de ela ter sido carregada:
		   o painel aparecia preenchido e sem letra nenhuma.  Medido no
		   BlastEm: p02_t4/t7/t12 antes desta correcao. */
		copy_title_palette(&palette[0], title_scene.palette);
		copy_title_palette(&palette[16], spr_hud_energy_y.palette);
		memset(&palette[32], 0, 16 * sizeof(u16));
		if(gConfig.useFade){ PAL_fadeIn(0, (4 * 16) - 1, palette, TITLE_FADE_IN_TICKS, TRUE); }
		else { PAL_setColors(0, palette, 64, CPU); }
		sTitlePhase = TITLE_PHASE_FADE_IN;
		sTitleFadeTicks = 0;
		return;
	}
	if(sTitlePhase == TITLE_PHASE_FADE_IN)
	{
		/* Nenhum input e lido durante o fade: a borda que pulou a abertura nao
		   pode virar confirmacao aqui. */
		sTitleFadeTicks++;
		if(!gConfig.useFade || (sTitleFadeTicks >= TITLE_FADE_IN_TICKS && !PAL_isDoingFade()))
		{
			sTitlePhase = TITLE_PHASE_ACTIVE;
		}
		return;
	}
	if(sTitlePhase == TITLE_PHASE_FADE_OUT)
	{
		sTitleFadeTicks++;
		if(!gConfig.useFade || (sTitleFadeTicks >= 8u && !PAL_isDoingFade()))
		{
			/* O fade terminou; so agora o seletor recebe o VDP e a borda de
			   START deixa de existir para a nova cena. */
			P[1].key_JOY_A_status = KEY_FREE;
			P[1].key_JOY_START_status = KEY_FREE;
			P[1].key_JOY_B_status = KEY_FREE;
			FUNCAO_TITLE_EXIT();
			CLEAR_VDP();
			SCENE_request(SCENE_SELECT);
		}
		return;
	}
	if(!sTitleReady){ return; }
	/* A borda que abriu uma página pertence somente à página anterior. Dois
	   ticks de guarda cobrem a atualização de tilemap e impedem A/B/START
	   mantidos ou duplicados de atravessarem a transição. */
	if(sTitlePageInputLock > 0){ sTitlePageInputLock--; return; }
	if(titlePage == TITLE_PAGE_MAIN)
	{
		if(P[1].key_JOY_UP_status == KEY_PRESSED || P[1].key_JOY_DOWN_status == KEY_PRESSED)
		{
			titleCursor = (titleCursor == TITLE_MAIN_START) ? TITLE_MAIN_OPTION : TITLE_MAIN_START;
			sMainSelectionLatched = titleCursor;
			title_menu_sfx();
			title_render_main();
		}
		if(P[1].key_JOY_A_status == KEY_PRESSED || P[1].key_JOY_START_status == KEY_PRESSED)
		{
			/* A seleção é latched na borda de UP/DOWN. Assim a confirmação não
			   depende de uma segunda leitura do cursor depois de SFX/DMA. */
			if(sMainSelectionLatched == TITLE_MAIN_START){ title_start_game(); }
			else
			{
				/* Tem de passar por title_goto_page: e ela que ajusta a
				   geometria do painel.  Trocar titlePage a mao deixava OPTIONS
				   com a altura do menu principal, e o painel cortava em 5
				   itens -- medido em out/emulator_evidence/p03_options. */
				title_goto_page(TITLE_PAGE_OPTIONS, TITLE_OPTION_SFX);
			}
		}
		return;
	}

	if(titlePage == TITLE_PAGE_OPTIONS)
	{
		bool confirm = (P[1].key_JOY_A_status == KEY_PRESSED || P[1].key_JOY_START_status == KEY_PRESSED);
		bool adjust = (P[1].key_JOY_LEFT_status == KEY_PRESSED || P[1].key_JOY_RIGHT_status == KEY_PRESSED);

		if(P[1].key_JOY_UP_status == KEY_PRESSED && titleCursor > TITLE_OPTION_SFX){ titleCursor--; title_menu_sfx(); title_render_options(); }
		if(P[1].key_JOY_DOWN_status == KEY_PRESSED && titleCursor < TITLE_OPTION_BACK){ titleCursor++; title_menu_sfx(); title_render_options(); }

		if(titleCursor == TITLE_OPTION_DEBUG && confirm)
		{
			title_goto_page(TITLE_PAGE_DEBUG, TITLE_DEBUG_BBOX);
			return;
		}
		if(titleCursor == TITLE_OPTION_BACK && confirm)
		{
			title_goto_page(TITLE_PAGE_MAIN, TITLE_MAIN_OPTION);
			return;
		}
		if(P[1].key_JOY_B_status == KEY_PRESSED)
		{
			title_goto_page(TITLE_PAGE_MAIN, TITLE_MAIN_OPTION);
			return;
		}
		if(titleCursor == TITLE_OPTION_DEFAULTS && confirm)
		{
			/* DEFAULTS e ACAO, nao toggle: restaura os valores e limpa estados
			   de ferramenta que nao deveriam sobreviver a um reset. */
			CONFIG_setDefaults();
			gDebugFlags = DBG_DEFAULT;
			gDebug = 0;
			gFreeStepArmed = FALSE;
			gFreeStepAdvance = FALSE;
			gTimingProfile = TIMING_PROFILE_NORMAL;
			gLogicRate = LOGIC_RATE_60;
			gScreen240 = FALSE;
			title_menu_sfx();
			title_render_options();
			return;
		}

		/* Um pressionamento gera UMA acao.  DEBUG, DEFAULTS e BACK ja
		   retornaram acima, entao nao caem aqui. */
		if(adjust || (confirm && titleCursor < TITLE_OPTION_DEBUG))
		{
				switch(titleCursor)
			{
				case TITLE_OPTION_SFX:     gConfig.audioSfx   = !gConfig.audioSfx;   break;
				case TITLE_OPTION_MUSIC:   gConfig.audioMusic = !gConfig.audioMusic; break;
				case TITLE_OPTION_LIFEBAR: gConfig.hudLifeBar = !gConfig.hudLifeBar; break;
				case TITLE_OPTION_TIMER:   gConfig.hudTimer   = !gConfig.hudTimer;   break;
				case TITLE_OPTION_TIMERBG: gConfig.hudTimerBg = !gConfig.hudTimerBg; break;
				case TITLE_OPTION_TIMELIM:
					/* 99 -> 60 -> OFF -> 99 */
					if(gConfig.timeLimit == CONFIG_TIME_99){ gConfig.timeLimit = CONFIG_TIME_60; }
					else if(gConfig.timeLimit == CONFIG_TIME_60){ gConfig.timeLimit = CONFIG_TIME_OFF; }
					else { gConfig.timeLimit = CONFIG_TIME_99; }
					break;
				case TITLE_OPTION_SPECIALBAR: gConfig.hudSpecialBar = !gConfig.hudSpecialBar; break;
				case TITLE_OPTION_HITCOUNT: gConfig.hudHitCount = !gConfig.hudHitCount; break;
				case TITLE_OPTION_SPECIALRULES: gConfig.specialRules = !gConfig.specialRules; break;
				case TITLE_OPTION_STAGE2: gConfig.stage2Enabled = !gConfig.stage2Enabled; if(!gConfig.stage2Enabled){ gBG_Choice = 1; } break;
				case TITLE_OPTION_OPENING: gConfig.showOpening = !gConfig.showOpening; break;
				case TITLE_OPTION_FADE: gConfig.useFade = !gConfig.useFade; break;
				default: break;
			}
			CONFIG_validate();
			title_menu_sfx();
			title_render_options();
		}
		return;
	}

	/* --- PAGINA DEBUG --- */
	{
		bool confirm = (P[1].key_JOY_A_status == KEY_PRESSED || P[1].key_JOY_START_status == KEY_PRESSED);
		bool adjust = (P[1].key_JOY_LEFT_status == KEY_PRESSED || P[1].key_JOY_RIGHT_status == KEY_PRESSED);

		if(P[1].key_JOY_UP_status == KEY_PRESSED && titleCursor > TITLE_DEBUG_BBOX){ titleCursor--; title_menu_sfx(); title_render_debug(); }
		if(P[1].key_JOY_DOWN_status == KEY_PRESSED && titleCursor < TITLE_DEBUG_BACK){ titleCursor++; title_menu_sfx(); title_render_debug(); }

		if(P[1].key_JOY_B_status == KEY_PRESSED ||
			(confirm && titleCursor == TITLE_DEBUG_BACK))
		{
			title_goto_page(TITLE_PAGE_OPTIONS, TITLE_OPTION_DEBUG);
			return;
		}

		if(adjust || (confirm && titleCursor < TITLE_DEBUG_BACK))
		{
			switch(titleCursor)
			{
				case TITLE_DEBUG_BBOX:     gDebugFlags ^= DBG_BBOX; break;
				case TITLE_DEBUG_HBOX:     gDebugFlags ^= DBG_HBOX; break;
				case TITLE_DEBUG_TEXT:     gDebugFlags ^= DBG_TEXT; break;
				case TITLE_DEBUG_PERF:     gDebugFlags ^= DBG_PERF; break;
				case TITLE_DEBUG_FRAMEADV: gDebugFlags ^= DBG_FRAMEADV; break;
				case TITLE_DEBUG_FREESTEP:
					gFreeStepArmed = !gFreeStepArmed;
					gFreeStepAdvance = FALSE;
					break;
				case TITLE_DEBUG_TICK:
					/* NORM -> L60 -> L50 -> NORM.  NORM e a politica de
					   entrega (60 ticks/s nas duas regioes); os dois LEGACY
					   existem para comparar com o comportamento antigo e sao
					   diagnostico, nao opcao de jogo. */
					if(gTimingProfile == TIMING_PROFILE_NORMAL)
					{
						gTimingProfile = TIMING_PROFILE_LEGACY;
						gLogicRate = LOGIC_RATE_60;
					}
					else if(gLogicRate == LOGIC_RATE_60){ gLogicRate = LOGIC_RATE_50; }
					else { gTimingProfile = TIMING_PROFILE_NORMAL; gLogicRate = LOGIC_RATE_60; }
					break;
				case TITLE_DEBUG_H240:
					/* Inerte em NTSC: 240 linhas so existem no timing PAL.
					   A altura NAO e aplicada aqui: o proprio menu de titulo
					   desenha um tilemap de 28 linhas e mostraria lixo na
					   faixa extra. Quem aplica e FUNCAO_SCREEN_HEIGHT_APPLY,
					   ja dentro da luta e so se o cenario for alto o bastante. */
					if(gRegionIsPal){ gScreen240 = !gScreen240; }
					break;
				default: break;
			}
			DEBUG_syncMaster();
			title_menu_sfx();
			title_render_debug();
		}
	}
}

void FUNCAO_TITLE_EXIT(void)
{
	sTitleDirty = FALSE;
	/* The caller tears the title down with CLEAR_VDP, which hands the whole
	   tile range to the next scene.  Drop the "already uploaded" latch so a
	   later return to gRoom 1 re-uploads the font, cursor and black tile
	   instead of drawing the menu with whatever now lives at those indices. */
	sTitleReady = FALSE;
}
