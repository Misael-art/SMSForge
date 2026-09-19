#ifndef SCENE_H
#define SCENE_H

#include "globals.h"

/* --- GERENCIADOR DE CENAS -------------------------------------------------
   Antes desta tarefa a troca de cena era `gRoom = N; gFrames = 0 ou 1`, e a
   escolha entre 0 e 1 dependia da POSICAO TEXTUAL do bloco alvo na cadeia de
   `if(gRoom==N)`: alvo depois do bloco atual usava 1, para cair nele na mesma
   iteracao; alvo antes usava 0.  Reordenar os blocos quebrava as transicoes.

   Agora a troca e sempre um PEDIDO.  O commit acontece num unico ponto, no
   fim do tick, e sempre zera gFrames -- o tick seguinte incrementa para 1 e a
   cena inicializa.  Uniforme, sem dependencia de ordem.

   Consequencia intencional: transicoes que antes rodavam o bloco alvo na
   MESMA iteracao agora custam 1 tick a mais.  A 60Hz sao 16,7 ms, invisiveis,
   e em troca some a armadilha de ordenacao.

   Os IDs preservam os valores de gRoom porque a sonda HPRB exporta a cena no
   bloco de SRAM; mudar os numeros invalidaria as capturas historicas.
   ------------------------------------------------------------------------- */

#define SCENE_NONE          255u
#define SCENE_OPENING         0u  /* novo: abertura, antes embutida no titulo */
#define SCENE_TITLE           1u
#define SCENE_SELECT          2u
#define SCENE_DECOMPRESSION   9u
#define SCENE_FIGHT          10u
#define SCENE_AFTER_MATCH    11u
#define SCENE_ROUND_RESET    12u

/* Agenda a troca. Chamar duas vezes no mesmo tick e erro de chamador: vence o
   primeiro pedido, e o segundo e ignorado para que nunca haja duas saidas
   concorrentes de uma mesma cena. */
void SCENE_request(u8 sceneId);

/* TRUE se ha troca agendada; usado por quem precisa parar de mexer na cena
   velha depois que ela ja entregou o controle. */
bool SCENE_pending(void);

/* Efetiva a troca. Chamado UMA vez por tick, no fim do dispatch. */
void SCENE_commit(void);

#endif // SCENE_H
