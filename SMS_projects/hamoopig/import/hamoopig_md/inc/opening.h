#ifndef OPENING_H
#define OPENING_H

#include "globals.h"

/* --- ABERTURA -------------------------------------------------------------
   Cena propria, separada do titulo.  Antes as duas viviam em fases de
   gRoom==1 e o menu era desenhado por cima da arte da abertura, o que
   escondia os creditos atras do painel.

   Maquina de estados:
     FADE_IN (0,3 s) -> HOLD (2 s) -> FADE_OUT (0,25 s) -> pede SCENE_TITLE

   As duracoes estao em TICKS LOGICOS, e por isso nao precisam de conversao
   por regiao: depois do P01 o tick vale 1/60 s em NTSC e em PAL.  Antes disto
   a mesma constante daria 2,4 s em PAL e 2 s em NTSC.

   A/START durante o HOLD pede antecipacao do fade-out.  O pedido NAO vira
   confirmacao no titulo: a borda e consumida aqui, e o titulo so passa a
   aceitar input depois do proprio fade-in.
   ------------------------------------------------------------------------- */

#define OPENING_FADE_IN_TICKS   18u  /* 0,30 s */
#define OPENING_HOLD_TICKS     120u  /* 2,00 s, contados APOS o fade-in */
#define OPENING_FADE_OUT_TICKS  15u  /* 0,25 s */

void FUNCAO_OPENING_INIT(void);
void FUNCAO_OPENING_UPDATE(void);

/* Estado interno exposto para teste e para o overlay de debug. */
u8  OPENING_phase(void);
u16 OPENING_phaseTicks(void);

#define OPENING_PHASE_FADE_IN  0u
#define OPENING_PHASE_HOLD     1u
#define OPENING_PHASE_FADE_OUT 2u
#define OPENING_PHASE_DONE     3u

#endif // OPENING_H
