/* stream.h -- pose streaming over one shared pool of 128 TALL pair slots.
 *
 * Measured sizing (memory bank 2026-09-29): fixed ping-pong halves need 130
 * of 128 pairs; current + next pose of both fighters, worst allowed
 * idle/guard/punch transition, needs 125. So every pose target (pose +
 * facing) gets whatever slots are free; nothing is resident.
 *
 * Per fighter: SHOWN (in the SAT the VDP displays) and NEXT (being
 * uploaded). A target is presented only when all of its pairs are resident;
 * a request for another target drops the pending upload (its slots are
 * freed, nothing partial is ever shown); slots of the old SHOWN target are
 * freed only after the SAT with the new one was copied.
 */
#ifndef STREAM_H
#define STREAM_H

#include "pose_table.h"

/* Still declared by the generated scene header (versus_poses); the pool
 * streams from PoseTiles instead, which carries the P2 blob for Ryu. */
typedef struct { unsigned char bank;
                 unsigned int off;
                 unsigned int size; } PoseRef;

#define STREAM_SLOTS 128u
#define STREAM_LIMIT_DEFAULT 0x70u
extern unsigned char sa_limit;

void stream_init(void);
/* Blocking load at boot (display off). */
void stream_load_now(unsigned char who, const PoseTiles *pt, unsigned char facing,
                     unsigned char pose);
/* Idempotent: the target the logic wants shown next. */
void stream_request(unsigned char who, const PoseTiles *pt, unsigned char facing,
                    unsigned char pose);
/* Uploads pending pairs of both fighters (assembly loop, VCounter-bound). */
void stream_step(void);
/* Choose what the SAT being built shows; returns the pose number and fills
 * the metasprite source, the pair->slot map and the facing. */
unsigned char stream_display(unsigned char who, const PoseTiles *want, unsigned char want_facing,
                             const unsigned char **meta, const unsigned char **map,
                             unsigned char *facing, const unsigned char **rows);
/* 1 when the target is the one in the displayed SAT. */
unsigned char stream_shows(unsigned char who, const PoseTiles *pt, unsigned char facing);
/* Call right after the SAT copy (index swap only). */
void stream_sat_copied(void);
/* Release the previous SHOWN target; call after stream_step, before
 * fight_draw (the next request). */
void stream_reclaim(void);

/* Telemetry for the probe. */
extern unsigned char stream_slots_used, stream_slots_peak;
extern unsigned char stream_alloc_fail, stream_dropped;

#endif
