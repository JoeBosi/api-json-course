#!/usr/bin/env bash
# Compila il sito, esegue i test dell'API e riavvia il servizio (se installato).
# Non tocca Caddy né il DNS. Uso: deploy/pubblica.sh
set -euo pipefail
cd "$(dirname "$0")/.."
DOMINIO=corso-api-json.giuseppebosi.com
PORTA=8795

if ! command -v node >/dev/null && [ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]; then
  . "${NVM_DIR:-$HOME/.nvm}/nvm.sh"; nvm use 22 >/dev/null
fi

echo "1. Testo parlato dei capitoli (Piper, solo i paragrafi cambiati)"
( cd api && uv sync -q && uv run python ../audio/estrai.py >/dev/null && uv run python ../audio/genera.py --solo-manifest 2>/dev/null | tail -1 ) \
  || { echo "   KO: generazione audio fallita (cd api && uv run python ../audio/genera.py)" >&2; exit 1; }
echo "   ok  (manifest del testo parlato; la lettura usa la voce del browser)"

echo "2. Sito: dipendenze e build"
( cd site && npm ci --no-audit --no-fund >/dev/null 2>&1 && npm run build >/dev/null 2>&1 ) || { echo "   KO: build fallita (cd site && npm run build)" >&2; exit 1; }
[ -s site/dist/index.html ] && [ -s site/dist/404.html ] || { echo "   KO: manca site/dist/index.html o 404.html" >&2; exit 1; }
echo "   ok  ($(du -sh site/dist | cut -f1), $(find site/dist -name index.html | wc -l) pagine)"

echo "3. API: dipendenze e test"
( cd api && uv sync -q && uv run pytest -q >/dev/null 2>&1 ) || { echo "   KO: test falliti (cd api && uv run pytest)" >&2; exit 1; }
echo "   ok"

echo "4. Copia in /opt/corso-api-json (il servizio gira da lì, con l'utente corso-api)"
DEST=/opt/corso-api-json
if [ -d "$DEST" ]; then
  rsync -a --delete --exclude '.git/' --exclude '.venv/' --exclude 'node_modules/' \
        --exclude '__pycache__/' --exclude '.pytest_cache/' --exclude '.ruff_cache/' \
        --exclude 'api/data/' --exclude '.env' api/ "$DEST/api/"
  rsync -a --delete site/dist/ "$DEST/site/dist/"
  install -o root -g corso-api -m 640 .env "$DEST/.env" 2>/dev/null || true
  ( cd "$DEST/api" && uv sync -q ) || { echo "   KO: uv sync in $DEST" >&2; exit 1; }
  chown -R root:corso-api "$DEST"; chmod -R u=rwX,g=rX,o= "$DEST"; chmod 640 "$DEST/.env" 2>/dev/null || true
  echo "   ok  (codice e sito copiati)"
else
  echo "   --  $DEST assente: prima deploy/installa-utente-api.sh"
fi

echo "5. Servizio corso-api-json"
if systemctl is-active --quiet corso-api-json 2>/dev/null; then
  systemctl restart corso-api-json
  # l'API di prova nasce spenta: l'interruttore è l'endpoint che risponde sempre
  for _ in $(seq 1 15); do curl -sf -o /dev/null "http://127.0.0.1:$PORTA/api/v1/interruttore" && break; sleep 2; done
  curl -sf -o /dev/null "http://127.0.0.1:$PORTA/api/v1/interruttore" && curl -sf -o /dev/null "http://127.0.0.1:$PORTA/" \
    && echo "   ok  (riavviato, risponde su 127.0.0.1:$PORTA; API di prova spenta finché non la accendono)" \
    || { echo "   KO: il servizio non risponde: journalctl -u corso-api-json -n 30" >&2; exit 1; }
else
  echo "   --  servizio non installato: deploy/installa-utente-api.sh"
fi

echo "6. Caddy"
if grep -q "^$DOMINIO {" /etc/caddy/Caddyfile 2>/dev/null; then
  caddy validate --adapter caddyfile --config /etc/caddy/Caddyfile >/dev/null 2>&1 \
    && echo "   ok  (blocco presente, configurazione valida)" || { echo "   KO: caddy validate fallisce" >&2; exit 1; }
  echo; echo "Pubblicato: https://$DOMINIO"
else
  echo "   --  blocco assente: deploy/attiva-caddy.sh"; echo; echo "Build pronta. Per metterla online: deploy/attiva-caddy.sh"
fi
