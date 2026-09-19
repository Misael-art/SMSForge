#include <genesis.h>
#include "timing.h"
#include "globals.h"
#include "game_types.h"

static u16 sAccumulator;
static u16 sVideoHz;

void TIMING_init(void)
{
	/* gRegionIsPal e lido do flag de status do VDP no boot (main.c). */
	sVideoHz = gRegionIsPal ? 50u : 60u;
	sAccumulator = 0;
}

u8 TIMING_ticksForThisFrame(void)
{
	u8 ticks = 0;

	if(gTimingProfile == TIMING_PROFILE_LEGACY)
	{
		/* Comportamento historico, preservado so para comparacao: 1 tick por
		   VBlank, e o modo 50 descarta 1 de cada 6 frames em NTSC. */
		static u8 legacyAccum = 0;
		if(gLogicRate == LOGIC_RATE_50 && !gRegionIsPal)
		{
			legacyAccum++;
			if(legacyAccum >= 6){ legacyAccum = 0; return 0; }
		}
		return 1;
	}

	/* Acumulador inteiro: soma a taxa logica, desconta a taxa de video.
	   NTSC 60/60 -> sempre 1.  PAL 60/50 -> 1,1,1,1,2 repetindo, ou seja 6
	   ticks a cada 5 frames, exatamente 60 por segundo. */
	sAccumulator += TIMING_LOGIC_HZ;
	while(sAccumulator >= sVideoHz && ticks < TIMING_MAX_TICKS_PER_FRAME)
	{
		sAccumulator -= sVideoHz;
		ticks++;
	}
	return ticks;
}

u8 TIMING_roundClockTicks(void)
{
	/* No perfil NORMAL um decremento do mostrador e um segundo real.  O 38
	   herdado e ritmo arcade: a partida inteira termina mais cedo do que o
	   numero exibido sugere. */
	return (gTimingProfile == TIMING_PROFILE_LEGACY)
		? (u8)ROUND_CLOCK_TICKS : (u8)TIMING_LOGIC_HZ;
}

u16 TIMING_accumulator(void) { return sAccumulator; }
u16 TIMING_videoHz(void) { return sVideoHz; }
