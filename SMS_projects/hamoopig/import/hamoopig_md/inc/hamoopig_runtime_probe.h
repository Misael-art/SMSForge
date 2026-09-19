#ifndef HAMOOPIG_RUNTIME_PROBE_H
#define HAMOOPIG_RUNTIME_PROBE_H
#include <genesis.h>
void HAMOOPIG_probeInit(void);
/* Marks the fight-entry initialization and the following rolling CPU window
   as load-time work, separate from sustained gameplay. */
void HAMOOPIG_probeFightInit(void);
void HAMOOPIG_probeVramReset(void);
void HAMOOPIG_probeVramRange(u16 start, u16 count);
void HAMOOPIG_probeSpriteDma(u16 dmaBeforeSpriteUpdate);
void HAMOOPIG_probeStageDma(u8 stage, u16 dmaBeforeStage);
/* Consolida os eventos produzidos/consumidos no tick atual. Deve ser chamado
   depois de FUNCAO_CONSUME_COMBAT_EVENTS(), enquanto o ledger ainda existe. */
void HAMOOPIG_probeCombatEvents(void);
void HAMOOPIG_probeTick(u8 scene);
/* Leitura dos mesmos picos que o probe ja exporta para a SRAM.  O overlay de
   debug le daqui em vez de recalcular, para nao divergir da evidencia. */
u16 HAMOOPIG_probePeakDma(void);
u16 HAMOOPIG_probePeakActiveSprites(void);
u16 HAMOOPIG_probePeakScanlineSprites(void);
u16 HAMOOPIG_probePeakVdpSprites(void);
#endif
