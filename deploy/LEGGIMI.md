# Pubblicazione di corso-api-json

Dominio: `corso-api-json.giuseppebosi.com` (DNS già puntato al VPS).
Un solo servizio systemd, `corso-api-json`, avvia uvicorn dal `.venv` del progetto su
`127.0.0.1:8795`: serve `/api/*` (FastAPI) e `site/dist` (sito Starlight compilato). Caddy fa
reverse proxy con HTTPS e `basic_auth` (utente `giuseppe`; la password NON è in questo repo: l'hash sta nel
snippet, la password la conosce Giuseppe). Vale anche per `/api/*`: negli script e in curl serve `-u giuseppe:<password>`.
Nessun file esce dalla cartella del progetto.

## Aggiornare il sito o l'API
```bash
deploy/pubblica.sh      # build sito + test API + riavvio servizio + controllo Caddy
```

## Prima installazione (o ripristino)
```bash
deploy/pubblica.sh
deploy/attiva-caddy.sh  # unit systemd + blocco in fondo a /etc/caddy/Caddyfile (backup, validate, reload, rollback)
```
Tocca configurazione condivisa (systemd, Caddy): va lanciato con consapevolezza.

## Stato e diagnosi
```bash
systemctl status corso-api-json
journalctl -u corso-api-json -n 50
curl -s http://127.0.0.1:8795/api/v1/health
curl -s -o /dev/null -w '%{http_code}\n' https://corso-api-json.giuseppebosi.com/
ls api/data/sandboxes | wc -l          # sandbox vive
```

## Tornare indietro
```bash
systemctl disable --now corso-api-json && rm /etc/systemd/system/corso-api-json.service && systemctl daemon-reload
cp -p /etc/caddy/Caddyfile.bak.<data> /etc/caddy/Caddyfile
caddy validate --adapter caddyfile --config /etc/caddy/Caddyfile && systemctl reload caddy
```

## Variabili (unit systemd)
`CORSO_RATE_LIMIT` (120/minute), `CORSO_SANDBOX_TTL_HOURS` (6), `CORSO_SANDBOX_MAX` (500),
`CORSO_DATA_DIR` (api/data), `CORSO_SITE_DIST` (site/dist).
