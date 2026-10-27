#!/usr/bin/env bash
# Prima installazione (idempotente): 1) unit systemd che avvia uvicorn dal .venv del progetto
# su 127.0.0.1:8795; 2) blocco Caddy con reverse_proxy, in fondo a /etc/caddy/Caddyfile,
# con backup, validate, reload (mai restart) e rollback automatico se qualcosa fallisce.
# Uso: deploy/attiva-caddy.sh   (richiede root)
set -euo pipefail
cd "$(dirname "$0")/.."
PROGETTO=$(pwd)
DOMINIO=corso-api-json.giuseppebosi.com
PORTA=8795
UNIT=/etc/systemd/system/corso-api-json.service
CADDYFILE=/etc/caddy/Caddyfile

[ -s site/dist/index.html ] || { echo "Manca site/dist: lancia prima deploy/pubblica.sh" >&2; exit 1; }
[ -x api/.venv/bin/uvicorn ] || { echo "Manca api/.venv: cd api && uv sync" >&2; exit 1; }

echo "1. Servizio corso-api-json"
# Il servizio gira con l'utente corso-api da /opt: lo installa deploy/installa-utente-api.sh,
# che crea l'utente, copia il codice e mette la unit. Qui ci limitiamo a usarlo.
if ! id -u corso-api >/dev/null 2>&1 || [ ! -f "$UNIT" ]; then
  echo "   KO: prima va installato il servizio con l'utente dedicato:" >&2
  echo "       cd $PROGETTO && python3 deploy/imposta-password-api.py" >&2
  echo "       cd $PROGETTO && sudo deploy/installa-utente-api.sh" >&2
  exit 1
fi
systemctl restart corso-api-json
# l'API di prova nasce spenta: l'interruttore è l'endpoint che risponde sempre
for _ in $(seq 1 15); do curl -sf -o /dev/null "http://127.0.0.1:$PORTA/api/v1/interruttore" && break; sleep 2; done
curl -sf -o /dev/null "http://127.0.0.1:$PORTA/api/v1/interruttore" || { echo "   KO: il servizio non risponde (journalctl -u corso-api-json -n 30)" >&2; exit 1; }
echo "   ok  (attivo su 127.0.0.1:$PORTA, API di prova spenta)"

echo "2. Blocco Caddy"
if grep -q "^$DOMINIO {" "$CADDYFILE"; then
  echo "   --  già presente, non tocco il Caddyfile"
else
  BACKUP="$CADDYFILE.bak.$(date +%Y%m%d-%H%M%S)"
  cp -p "$CADDYFILE" "$BACKUP"
  echo "   backup: $BACKUP"
  { echo; cat deploy/Caddyfile.snippet; } >> "$CADDYFILE"
  ripristina() {
    echo "   KO: $1 — ripristino il Caddyfile precedente" >&2
    cp -p "$BACKUP" "$CADDYFILE"; systemctl reload caddy || true; exit 1
  }
  caddy validate --adapter caddyfile --config "$CADDYFILE" >/dev/null 2>&1 || ripristina "caddy validate fallisce"
  systemctl reload caddy || ripristina "reload fallito"
  sleep 3
  systemctl is-active --quiet caddy || ripristina "caddy non è attivo dopo il reload"
  echo "   ok  (blocco aggiunto, Caddy ricaricato)"
fi

echo "3. Verifica pubblica"
for _ in $(seq 1 20); do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "https://$DOMINIO/" || true)
  [ "$CODE" = "200" ] && break
  sleep 3
done
echo "   https://$DOMINIO → HTTP ${CODE:-nessuna risposta}"
[ "$CODE" = "200" ] || { echo "   Non risponde ancora 200: journalctl -u caddy -n 50" >&2; exit 1; }
curl -s "https://$DOMINIO/api/v1/health"; echo
echo; echo "Online: https://$DOMINIO"
