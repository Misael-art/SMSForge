#!/usr/bin/env bash
# build_proto.sh — compila um protótipo que usa a CorridorEngine.
# uso: build_proto.sh <prog.c> [nome]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SMSFORGE="$(cd "$HERE/../.." && pwd)"
D="$SMSFORGE/sdk/devkitSMS"
S="$SMSFORGE/sdk/sdcc-portable/bin/sdcc"
PROJ="$SMSFORGE/SMS_projects/laboratorio_01"
PROG="${1:-example_proto.c}"
NAME="${2:-proto}"
OUT="$HERE/build"
mkdir -p "$OUT"
echo "[proto] compilando engine.c + $PROG"
"$S" -c -mz80 -o "$OUT/engine.rel" -I"$HERE" -I"$D/SMSlib" -I"$D/PSGlib" "$HERE/engine.c"
"$S" -c -mz80 -o "$OUT/$NAME.rel" -I"$HERE" -I"$D/SMSlib" -I"$D/PSGlib" -I"$PROJ/inc" "$HERE/$PROG"
"$S" -o "$OUT/$NAME.ihx" -mz80 --no-std-crt0 --data-loc 0xC000 \
    "$D/crt0/crt0_sms.rel" "$OUT/engine.rel" "$OUT/$NAME.rel" \
    "$D/SMSlib/SMSlib.lib" "$D/PSGlib/PSGlib.lib"
"$D/tools/makesms" "$OUT/$NAME.ihx" "$OUT/$NAME.sms"
echo "[proto] OK -> $OUT/$NAME.sms"
