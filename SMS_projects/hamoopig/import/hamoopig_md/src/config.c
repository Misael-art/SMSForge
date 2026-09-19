#include <genesis.h>
#include "config.h"
#include "globals.h"

GameConfig gConfig;
MatchRules gMatchRules;

void CONFIG_setDefaults(void)
{
	gConfig.audioSfx    = TRUE;
	gConfig.audioMusic  = TRUE;
	gConfig.hudLifeBar  = TRUE;
	gConfig.hudTimer    = TRUE;
	gConfig.hudTimerBg  = FALSE;
	gConfig.hudSpecialBar = TRUE;
	gConfig.hudHitCount = TRUE;
	gConfig.specialRules = TRUE;
	gConfig.stage2Enabled = TRUE;
	gConfig.showOpening = TRUE;
	gConfig.useFade     = TRUE;
	gConfig.timeLimit   = CONFIG_TIME_99;
}

bool CONFIG_validate(void)
{
	bool corrigiu = FALSE;

	/* Os bool vem de toggles e nao tem como sair da faixa; o unico campo com
	   dominio proprio e timeLimit. */
	if(gConfig.timeLimit != CONFIG_TIME_OFF &&
	   gConfig.timeLimit != CONFIG_TIME_60 &&
	   gConfig.timeLimit != CONFIG_TIME_99)
	{
		gConfig.timeLimit = CONFIG_TIME_99;
		corrigiu = TRUE;
	}
	return corrigiu;
}

void CONFIG_freezeMatchRules(void)
{
	CONFIG_validate();
	gMatchRules.timeLimit = gConfig.timeLimit;
}
