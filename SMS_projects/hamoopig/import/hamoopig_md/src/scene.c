#include <genesis.h>
#include "scene.h"
#include "globals.h"
#include "stage.h"

static u8 sPending = SCENE_NONE;

void SCENE_request(u8 sceneId)
{
	/* Primeiro pedido vence.  Se uma cena pede saida e, no mesmo tick, algo
	   dentro dela pede outra, a segunda e engolida -- caso contrario a cena
	   teria duas saidas concorrentes e a ultima a executar decidiria por
	   acidente de ordem, que e exatamente o que este modulo existe para
	   eliminar. */
	if(sPending == SCENE_NONE){ sPending = sceneId; }
}

bool SCENE_pending(void)
{
	return (sPending != SCENE_NONE) ? TRUE : FALSE;
}

void SCENE_commit(void)
{
	if(sPending == SCENE_NONE){ return; }
	STAGE_ambient_off();
	gRoom = sPending;
	/* Sempre 0: o gFrames++ do topo do proximo tick leva a 1, e e esse 1 que
	   toda cena usa como "inicialize agora".  Nenhum chamador escolhe mais
	   entre 0 e 1. */
	gFrames = 0;
	sPending = SCENE_NONE;
}
