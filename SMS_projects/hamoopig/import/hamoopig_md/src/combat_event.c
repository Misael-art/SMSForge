#include <genesis.h>
#include "combat_event.h"

static CombatEvent sEvents[COMBAT_EVENT_CAPACITY];
static u8 sEventCount;
static u16 sEventTick;
static bool sConsumptionClaimed;
static bool sLastEventAttachable;
static u8 sLastEventIndex;
/* Contact is allowed once per attack lifecycle, not once per video tick. */
static bool sGateValid[3][3][4];
static u16 sGateAttackState[3][3][4];
static u8 sGateSourceInstance[3][3][4];

static bool combat_event_is_confirmed(u8 kind)
{
	return (kind == COMBAT_EVENT_HIT || kind == COMBAT_EVENT_THROW);
}

void COMBAT_EVENTS_RESET(void)
{
	sEventCount = 0;
	sConsumptionClaimed = FALSE;
	sLastEventAttachable = FALSE;
	sLastEventIndex = 0;
}

void COMBAT_EVENTS_RESET_ROUND(void)
{
	u8 attacker;
	u8 defender;
	u8 source;
	COMBAT_EVENTS_RESET();
	for(attacker = 0; attacker < 3; attacker++)
	{
		for(defender = 0; defender < 3; defender++)
		{
			for(source = 0; source < 4; source++)
			{
				sGateValid[attacker][defender][source] = FALSE;
			}
		}
	}
}

void COMBAT_EVENTS_BEGIN_TICK(u16 tick)
{
	sEventTick = tick;
	COMBAT_EVENTS_RESET();
}

bool COMBAT_EVENTS_EMIT_SOURCE(u8 attacker, u8 defender, u16 attackState, u8 kind, u8 source, u8 sourceInstance)
{
	CombatEvent *event;
	u8 index;
	sLastEventAttachable = FALSE;
	if(attacker < 1 || attacker > 2 || defender < 1 || defender > 2 || attacker == defender){ return FALSE; }
	/* Uma mesma hitbox pode ser observada por mais de um caminho da FSM no
	   mesmo tick. O evento é a unidade de feedback, portanto a segunda
	   observação não pode criar outro combo/ganho de medidor. Mantemos o
	   índice para que o delta legado dessa chamada continue sendo auditável. */
	for(index = 0; index < sEventCount; index++)
	{
		event = &sEvents[index];
		if(event->attacker == attacker && event->defender == defender &&
			event->attackState == attackState &&
			event->source == source && event->sourceInstance == sourceInstance &&
			event->tick == sEventTick)
		{
			sLastEventIndex = index;
			sLastEventAttachable = TRUE;
			return FALSE;
		}
	}
	if(sEventCount >= COMBAT_EVENT_CAPACITY){ return FALSE; }
	if(sGateValid[attacker][defender][source] &&
		sGateAttackState[attacker][defender][source] == attackState &&
		sGateSourceInstance[attacker][defender][source] == sourceInstance)
	{
		/* The same hitbox is still touching the same victim. */
		return FALSE;
	}
	event = &sEvents[sEventCount];
	event->attacker = attacker;
	event->defender = defender;
	event->attackState = attackState;
	event->kind = kind;
	event->source = source;
	event->sourceInstance = sourceInstance;
	event->hitIndex = sEventCount;
	event->meterAttackerDelta = combat_event_is_confirmed(kind) ? COMBAT_METER_HIT_ATTACKER_GAIN : COMBAT_METER_GUARD_ATTACKER_GAIN;
	event->meterDefenderDelta = combat_event_is_confirmed(kind) ? COMBAT_METER_HIT_DEFENDER_GAIN : 0;
	event->legacyDefenderDelta = 0;
	event->healthDelta = 0;
	event->healthAttached = FALSE;
	event->result = COMBAT_EVENT_RESULT_NONE;
	event->tick = sEventTick;
	sLastEventIndex = sEventCount;
	sEventCount++;
	sLastEventAttachable = TRUE;
	sGateValid[attacker][defender][source] = TRUE;
	sGateAttackState[attacker][defender][source] = attackState;
	sGateSourceInstance[attacker][defender][source] = sourceInstance;
	return TRUE;
}

bool COMBAT_EVENTS_EMIT(u8 attacker, u8 defender, u16 attackState, u8 kind)
{
	return COMBAT_EVENTS_EMIT_SOURCE(attacker, defender, attackState, kind,
		COMBAT_EVENT_SOURCE_BODY, 0);
}

u8 COMBAT_EVENTS_ATTACH_HEALTH_DELTA(u8 defender, s8 delta)
{
	CombatEvent *event;
	u8 index;
	if(!sLastEventAttachable || sEventCount == 0){ return COMBAT_EVENT_ATTACH_NONE; }
	for(index = sEventCount; index > 0; index--)
	{
		event = &sEvents[index - 1];
		if(event->defender != defender){ continue; }
		sLastEventIndex = index - 1;
		if(event->healthAttached){ return COMBAT_EVENT_ATTACH_DUPLICATE; }
		event->healthDelta = delta;
		event->healthAttached = TRUE;
		return COMBAT_EVENT_ATTACH_ACCEPTED;
	}
	return COMBAT_EVENT_ATTACH_NONE;
}

bool COMBAT_EVENTS_ATTACH_METER_DELTA(u8 defender, s8 delta)
{
	CombatEvent *event;
	u8 index;
	s16 total;
	if(!sLastEventAttachable || sEventCount == 0){ return FALSE; }
	for(index = sEventCount; index > 0; index--)
	{
		event = &sEvents[index - 1];
		if(!combat_event_is_confirmed(event->kind) || event->defender != defender){ continue; }
		total = (s16)event->legacyDefenderDelta + (s16)delta;
		if(total < -127){ total = -127; }
		if(total > 127){ total = 127; }
		event->legacyDefenderDelta = (s8)total;
		sLastEventIndex = index - 1;
		return TRUE;
	}
	return FALSE;
}

bool COMBAT_EVENTS_CLAIM_CONSUMPTION(void)
{
	if(sConsumptionClaimed){ return FALSE; }
	sConsumptionClaimed = TRUE;
	return TRUE;
}

u8 COMBAT_EVENTS_COUNT(void){ return sEventCount; }

const CombatEvent *COMBAT_EVENTS_AT(u8 index)
{
	if(index >= sEventCount){ return NULL; }
	return &sEvents[index];
}

void COMBAT_EVENTS_SET_RESULT(u8 index, u8 result)
{
	if(index >= sEventCount){ return; }
	sEvents[index].result = result;
}
