#!/usr/bin/env bash
# Ripristina le skill elencate in skills-lock.json (copiate nel progetto) e controlla che
# l'ambiente sia portabile. Uso: ./bootstrap.sh [--check]
set -euo pipefail
cd "$(dirname "$0")"
CHECK=${1:-}
FAIL=0
ok(){ printf '  ok  %s\n' "$1"; }
ko(){ printf '  KO  %s\n' "$1"; FAIL=1; }

if [ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ] && ! command -v node >/dev/null; then
  . "${NVM_DIR:-$HOME/.nvm}/nvm.sh"; nvm use 22 >/dev/null 2>&1 || true
fi
command -v node >/dev/null && ok "node $(node -v)" || ko "manca node (serve a npx skills)"
command -v uv   >/dev/null && ok "uv $(uv --version | awk '{print $2}')" || ko "manca uv (https://docs.astral.sh/uv/)"

echo "Skill"
if [ -f skills-lock.json ]; then
  while read -r NAME SRC; do
    [ -z "$NAME" ] && continue
    if [ -f ".claude/skills/$NAME/SKILL.md" ]; then ok "$NAME"
    elif [ "$CHECK" = "--check" ]; then ko "$NAME manca (lancia ./bootstrap.sh)"
    else
      echo "  ..  reinstallo $NAME da $SRC"
      # </dev/null: altrimenti npx si mangia lo stdin del ciclo e ripristina solo la prima skill
      npx -y skills@latest add "$SRC" --skill "$NAME" -a claude-code --copy -y </dev/null >/dev/null 2>&1 \
        && ok "$NAME" || ko "ripristino di $NAME fallito"
    fi
  done < <(node -e 'const l=require("./skills-lock.json").skills||{};for(const [n,v] of Object.entries(l)) console.log(n, v.source||"")')
fi
for d in .claude/skills/*/; do [ -f "$d/SKILL.md" ] || ko "$(basename "$d") senza SKILL.md"; done

echo "Portabilità"
[ -z "$(find .claude -type l 2>/dev/null)" ] && ok "nessun symlink" || ko "symlink sotto .claude: reinstalla con --copy"
ASSOLUTI=$(grep -rlIE --include='*.md' --include='*.sh' --include='*.json' --include='*.py' --include='*.mjs' --include='*.ts' \
  --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=dist --exclude-dir=.astro --exclude-dir=.git \
  --exclude-dir=.claude --exclude-dir=docs --exclude=bootstrap.sh \
  -e '(^|[[:space:]"'"'"'`(=:,])/(root|home|Users)/' . 2>/dev/null || true)
[ -z "$ASSOLUTI" ] && ok "nessun path assoluto" || ko "path assoluti in: $(echo "$ASSOLUTI" | tr '\n' ' ')"
[ -f .env ] && ! grep -q '^\.env$' .gitignore && ko ".env non è in .gitignore" || ok "nessun segreto tracciato"

echo "Dipendenze"
if [ "$CHECK" != "--check" ]; then
  ( cd api && uv sync -q ) && ok "api/.venv" || ko "uv sync fallito"
  ( cd site && npm ci --no-audit --no-fund >/dev/null 2>&1 ) && ok "site/node_modules" || ko "npm ci fallito"
fi
echo
[ "$FAIL" -eq 0 ] && echo "Ambiente pronto." || { echo "Ambiente incompleto: vedi KO."; exit 1; }
