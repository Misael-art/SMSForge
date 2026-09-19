#ifndef CONFIG_H
#define CONFIG_H

#include "globals.h"

/* --- CONFIGURACAO ---------------------------------------------------------
   Um lugar so para preferencias, com defaults unicos e validacao.  Antes elas
   eram globais soltas (gAudioSfxEnabled, gAudioMusicEnabled) sem faixa
   declarada e sem como restaurar.

   Duas classes, e a diferenca importa:

     IMEDIATA  -- apresentacao.  Vale no mesmo instante em que o menu muda.
                  Esconder a barra de vida nao altera regra nenhuma: o dano e
                  o KO continuam funcionando.
     REGRA     -- muda o resultado da partida.  E congelada em MatchRules no
                  inicio da luta, para que mexer no menu entre rounds nao
                  troque a regra no meio da partida.

   Preferencias duram a SESSAO.  SRAM e fase posterior; nao ha persistencia.

   REGRA DE ESCOPO desta tarefa (plano, secao 3, linha 167): "nao adicionar
   botao inativo sem destino implementado".  Por isso cada item presente possui
   um caminho real; TIMER BG usa uma moldura compacta e STAGE2 controla o pool.
   ------------------------------------------------------------------------- */

/* TIME LIMIT.  OFF desliga o time-over; o mostrador some junto porque nao ha
   contagem a exibir. */
#define CONFIG_TIME_OFF 0u
#define CONFIG_TIME_60  60u
#define CONFIG_TIME_99  99u

typedef struct
{
	/* imediatas */
	bool audioSfx;
	bool audioMusic;
	bool hudLifeBar;
	bool hudTimer;
	bool hudTimerBg;
	bool hudSpecialBar;
	bool hudHitCount;
	bool specialRules;
	bool stage2Enabled;
	bool showOpening;
	bool useFade;
	/* regra */
	u8   timeLimit;
} GameConfig;

/* Copia congelada no inicio da partida.  A luta le daqui, nunca de gConfig. */
typedef struct
{
	u8 timeLimit;
} MatchRules;

extern GameConfig gConfig;
extern MatchRules gMatchRules;

void CONFIG_setDefaults(void);

/* Corrige valores fora de faixa e devolve TRUE se precisou corrigir.  Existe
   porque um valor invalido tem de virar erro visivel, nao comportamento
   silencioso. */
bool CONFIG_validate(void);

/* Chamada uma vez por partida, em FUNCAO_INICIALIZACAO. */
void CONFIG_freezeMatchRules(void);

#endif // CONFIG_H
