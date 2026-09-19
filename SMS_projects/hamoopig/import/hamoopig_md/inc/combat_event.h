#ifndef COMBAT_EVENT_H
#define COMBAT_EVENT_H

#include <genesis.h>

#define COMBAT_EVENT_CAPACITY 8
#define COMBAT_METER_HIT_ATTACKER_GAIN 4
#define COMBAT_METER_HIT_DEFENDER_GAIN 2
#define COMBAT_METER_GUARD_ATTACKER_GAIN 1
#define COMBAT_EVENT_ATTACH_NONE 0
#define COMBAT_EVENT_ATTACH_ACCEPTED 1
#define COMBAT_EVENT_ATTACH_DUPLICATE 2
#define COMBAT_EVENT_RESULT_NONE 0
#define COMBAT_EVENT_RESULT_HIT 1
#define COMBAT_EVENT_RESULT_KO 2

typedef enum
{
	COMBAT_EVENT_HIT = 0,
	COMBAT_EVENT_GUARD = 1,
	COMBAT_EVENT_THROW = 2
} CombatEventKind;

typedef enum
{
	COMBAT_EVENT_SOURCE_BODY = 0,
	COMBAT_EVENT_SOURCE_PROJECTILE = 1,
	COMBAT_EVENT_SOURCE_THROW = 2,
	COMBAT_EVENT_SOURCE_DOUBLE = 3
} CombatEventSource;

typedef struct
{
	u8 attacker;
	u8 defender;
	u16 attackState;
	u8 kind;
	u8 source;
	u8 sourceInstance;
	u8 hitIndex;
	s8 meterAttackerDelta;
	s8 meterDefenderDelta;
	s8 legacyDefenderDelta;
	s8 healthDelta;
	u8 healthAttached;
	u8 result;
	u16 tick;
} CombatEvent;

void COMBAT_EVENTS_BEGIN_TICK(u16 tick);
void COMBAT_EVENTS_RESET(void);
void COMBAT_EVENTS_RESET_ROUND(void);
bool COMBAT_EVENTS_EMIT(u8 attacker, u8 defender, u16 attackState, u8 kind);
bool COMBAT_EVENTS_EMIT_SOURCE(u8 attacker, u8 defender, u16 attackState, u8 kind, u8 source, u8 sourceInstance);
bool COMBAT_EVENTS_ATTACH_METER_DELTA(u8 defender, s8 delta);
u8 COMBAT_EVENTS_ATTACH_HEALTH_DELTA(u8 defender, s8 delta);
bool COMBAT_EVENTS_CLAIM_CONSUMPTION(void);
u8 COMBAT_EVENTS_COUNT(void);
const CombatEvent *COMBAT_EVENTS_AT(u8 index);
void COMBAT_EVENTS_SET_RESULT(u8 index, u8 result);

#endif
