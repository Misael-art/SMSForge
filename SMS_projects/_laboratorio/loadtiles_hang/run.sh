#!/usr/bin/env bash
# run.sh — abre a ROM no emulador gate. Sem ROM = falha honesta.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAME="$(basename "$DIR")"
ROM="$DIR/out/rom/$NAME.sms"
# Localiza a RAIZ do workspace subindo os diretorios ate achar tools/sms_wrapper.
# Profundidade fixa (../../) quebrava probes de laboratorio, que vivem um nivel
# mais fundo (SMS_projects/_laboratorio/<probe>/) — exatamente o que o runbook
# laboratory-mode.md manda criar.
ROOT="$DIR"
while [ "$ROOT" != "/" ] && [ ! -d "$ROOT/tools/sms_wrapper" ]; do
  ROOT="$(dirname "$ROOT")"
done
[ -d "$ROOT/tools/sms_wrapper" ] || { echo "[FAIL] raiz do SMSForge nao encontrada acima de $DIR"; exit 2; }
EMU_JSON="$ROOT/tools/emuladores/emulators.json"
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
