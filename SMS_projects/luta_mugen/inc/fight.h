/* fight.h — motor de luta interpretado por tabelas (Plano 2, Task 4).
 *
 * O estado do jogo vive em `Fighter` (luta.h); as tabelas de animacao,
 * fisica e colisao sao dados destilados do fixture sintetico (mini.air /
 * mini.cns) + blobs gerados pelo mugen2sms (inc/gen/mini_art.h). Nenhum
 * CNS-em-runtime: o interpretador e fixo, os dados sao gerados.
 */
#ifndef FIGHT_H
#define FIGHT_H

#include "luta.h"

/* Bits de input ja na convencao do motor (Task 5 liga SMS_getKeysHeld a
 * estes bits via padroes do CMD; aqui vem de roteiro deterministico). */
#define K_UP     0x01
#define K_DOWN   0x02
#define K_LEFT   0x04
#define K_RIGHT  0x08
#define K_LP     0x10            /* soco fraco  -> state 200 */
#define K_HP     0x20            /* soco forte  -> state 201 */
#define K_GUARD  0x40            /* guarda      -> state 120 */

extern Fighter fighters[2];
volatile extern unsigned char dbg_frame;   /* contador do loop p/ HUD */

void fight_init(void);                     /* carrega pool de poses + paleta */
void fight_reset(Fighter *p, unsigned char slot);
void fight_step(Fighter *p, unsigned int keys, unsigned int opp_keys);
void fight_draw(void);

#endif /* FIGHT_H */
