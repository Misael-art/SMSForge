#!/usr/bin/env bash
# new_project.sh <nome> — instancia o modelo em SMS_projects/<nome>/
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$HERE/../.."
NAME="${1:-}"
[ -n "$NAME" ] || { echo "uso: new_project.sh <nome-slug>"; exit 3; }
[[ "$NAME" =~ ^[a-z0-9_]+$ ]] || { echo "[FAIL] nome deve ser slug [a-z0-9_]"; exit 3; }
DEST="$ROOT/SMS_projects/$NAME"
[ -e "$DEST" ] && { echo "[FAIL] $DEST ja existe"; exit 1; }
cp -r "$HERE/modelo" "$DEST"
find "$DEST" -name "*.sh" -exec chmod +x {} \;
grep -rl "__PROJECT_NAME__" "$DEST" | while read -r f; do
  sed -i "s/__PROJECT_NAME__/$NAME/g" "$f"
done
mkdir -p "$DEST/rascunho" "$DEST/data" "$DEST/inc" "$DEST/out" "$DEST/.agent"
cat > "$DEST/.agent/README.md" <<EOF
.agent local de $NAME — MATERIALIZACAO.
Fonte canonica: tools/sms_wrapper/.agent/ (regras sempre ativas).
Politica: arquivo local existente NAO e sobrescrito pelo bootstrap.
EOF
echo "[OK] projeto instanciado: $DEST"
echo "proximo passo: preencher $DEST/doc/11-gdd.md e rodar $NAME/build.sh"
