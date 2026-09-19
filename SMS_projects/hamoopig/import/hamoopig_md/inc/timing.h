#ifndef TIMING_H
#define TIMING_H

#include "globals.h"

/* --- CONTRATO DE TEMPO ----------------------------------------------------
   Tres relogios distintos, que o codigo antigo tratava como um so:

     - VIDEO: o refresh do console. 60Hz em NTSC, 50Hz em PAL. Nao e
       configuravel; e propriedade do hardware.
     - LOGICA: a unidade de simulacao. TIMING_LOGIC_HZ ticks por segundo em
       QUALQUER regiao. Um frame de video pode rodar 1 ou 2 ticks.
     - APRESENTACAO: quantos frames de video passaram. Menus e fades contam
       isto, nao ticks, para nao acelerarem junto com slow-motion ou
       free-step da luta.

   Antes desta tarefa a logica era 1 tick por VBlank, entao o jogo inteiro
   rodava 17% mais lento em PAL -- e o modo "TICK 50" descartava 1 de cada 6
   frames em NTSC para imitar esse defeito, oferecendo-o como opcao.

   No perfil NORMAL o acumulador inteiro emite 60 ticks por segundo nas duas
   regioes: em PAL o padrao e 1,1,1,1,2 (6 ticks a cada 5 frames).  O perfil
   LEGACY preserva o comportamento antigo, e ferramenta de comparacao, nao
   default de entrega.
   ------------------------------------------------------------------------- */

#define TIMING_LOGIC_HZ 60u

/* Teto de ticks por frame de video.  PAL normal pede no maximo 2; o limite
   existe para que um acumulador corrompido nao produza um loop longo dentro
   de um unico frame. */
#define TIMING_MAX_TICKS_PER_FRAME 2u

#define TIMING_PROFILE_NORMAL 0u
#define TIMING_PROFILE_LEGACY 1u

/* Relogio de round.  60 ticks = 1 segundo real no perfil NORMAL.  O valor
   arcade herdado (ROUND_CLOCK_TICKS) nao representa um segundo e fica so no
   perfil de comparacao. */
void TIMING_init(void);

/* Quantos ticks logicos este frame de video deve executar. */
u8 TIMING_ticksForThisFrame(void);

/* Ticks que o mostrador do relogio espera entre dois decrementos. */
u8 TIMING_roundClockTicks(void);

/* Estado interno, para teste e para o overlay de debug. */
u16 TIMING_accumulator(void);
u16 TIMING_videoHz(void);

#endif // TIMING_H
