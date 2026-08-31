#!/usr/bin/env bash
# run.sh — abre a ROM no emulador gate. Sem ROM = falha honesta.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME="$(basename "$DIR")"
ROM="$DIR/out/rom/$NAME.sms"
EMU_JSON="$DIR/../../tools/emuladores/emulators.json"
[ -f "$ROM" ] || { echo "[FAIL] ROM ausente: rode ./build.sh primeiro"; exit 1; }
EMU=$(python3 - "$EMU_JSON" <<'EOF'
import json,sys,shutil
try:
    p=json.load(open(sys.argv[1])).get("default_emulator")
except Exception:
    p=None
print(p or shutil.which("openmsx") or shutil.which("emulicious") or "")
EOF
)
[ -n "$EMU" ] || { echo "[FAIL_AMBIENTE] nenhum emulador configurado (tools/emuladores/)"; exit 2; }
exec "$EMU" "$ROM"
