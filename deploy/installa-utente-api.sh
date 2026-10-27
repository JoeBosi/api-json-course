#!/usr/bin/env bash
# Fa girare l'API con un utente dedicato invece che come root.
#
#   utente   : corso-api (di sistema, senza shell, senza home di login, nessun gruppo in più)
#   codice   : /opt/corso-api-json        root:corso-api, il servizio lo legge e basta
#   dati     : /var/lib/corso-api-json    unica cartella scrivibile dal servizio
#   segreti  : /opt/corso-api-json/.env   640 root:corso-api (solo l'hash della password)
#
# Si può rilanciare quante volte si vuole: rifà solo ciò che manca o è cambiato.
# Da lanciare come root via SSH:
#     cd /root/Developer/corso-api-json && sudo deploy/installa-utente-api.sh
#
# PRIMA va impostata la password dell'API, altrimenti lo script si ferma:
#     cd /root/Developer/corso-api-json && python3 deploy/imposta-password-api.py
set -euo pipefail

UTENTE=corso-api
SORGENTE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST=/opt/corso-api-json
DATI=/var/lib/corso-api-json
UNIT=/etc/systemd/system/corso-api-json.service
DROPIN_DIR=/etc/systemd/system/corso-api-json.service.d
PORTA=8795

info() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
errore() { printf '\033[31mERRORE: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || errore "serve root: usa sudo."
[[ -f "$SORGENTE/api/pyproject.toml" ]] || errore "non trovo il sorgente in $SORGENTE."

# --- 1. la password deve esserci, altrimenti l'API nasce spenta e non si può accendere -------
info "Controllo la password dell'API"
if ! grep -qs '^CORSO_API_PASSWORD_HASH=.\+' "$SORGENTE/.env"; then
    errore "manca CORSO_API_PASSWORD_HASH in $SORGENTE/.env.
  Senza, l'API resta spenta e nessuno può accenderla dal sito. Prima lancia:
      cd $SORGENTE && python3 deploy/imposta-password-api.py"
fi
echo "   c'è (nel file sta solo l'hash)."

# --- 2. utente di sistema --------------------------------------------------------------------
info "Utente $UTENTE"
if id -u "$UTENTE" >/dev/null 2>&1; then
    echo "   esiste già."
else
    useradd --system --no-create-home --home-dir /nonexistent \
            --shell /usr/sbin/nologin --comment "corso-api-json (API di prova del corso)" "$UTENTE"
    echo "   creato."
fi
# nessun gruppo oltre al proprio
usermod -G "$UTENTE" "$UTENTE"

# --- 3. codice in /opt ------------------------------------------------------------------------
info "Copia del codice in $DEST"
mkdir -p "$DEST"
rsync -a --delete \
      --exclude '.git/' --exclude '.venv/' --exclude 'node_modules/' --exclude '__pycache__/' \
      --exclude '.pytest_cache/' --exclude '.ruff_cache/' --exclude 'site/.astro/' \
      --exclude 'api/data/' --exclude 'audio/voci/' --exclude '.env' \
      "$SORGENTE/api/" "$DEST/api/"
mkdir -p "$DEST/site"
[[ -d "$SORGENTE/site/dist" ]] || errore "manca $SORGENTE/site/dist: lancia prima 'cd site && npm run build'."
rsync -a --delete "$SORGENTE/site/dist/" "$DEST/site/dist/"
cp -f "$SORGENTE/CLAUDE.md" "$DEST/CLAUDE.md" 2>/dev/null || true

# --- 4. ambiente Python ricreato dentro /opt ---------------------------------------------------
info "Ambiente Python in $DEST/api/.venv"
if command -v uv >/dev/null 2>&1; then
    (cd "$DEST/api" && uv sync --quiet)
else
    python3 -m venv "$DEST/api/.venv"
    "$DEST/api/.venv/bin/pip" install --quiet --upgrade pip
    "$DEST/api/.venv/bin/pip" install --quiet "$DEST/api"
fi
"$DEST/api/.venv/bin/python" -c 'import fastapi, uvicorn, slowapi' \
    || errore "l'ambiente Python non è completo."
echo "   pronto."

# --- 5. segreti e permessi ----------------------------------------------------------------------
info "Permessi"
install -o root -g "$UTENTE" -m 640 "$SORGENTE/.env" "$DEST/.env"
chown -R root:"$UTENTE" "$DEST"
chmod -R u=rwX,g=rX,o= "$DEST"
chmod 640 "$DEST/.env"
install -d -o "$UTENTE" -g "$UTENTE" -m 750 "$DATI"
echo "   $DEST  root:$UTENTE (sola lettura per il servizio)"
echo "   $DATI  $UTENTE (unica cartella scrivibile)"

# --- 6. unit systemd ------------------------------------------------------------------------------
info "Servizio systemd"
BACKUP=""
if [[ -f $UNIT ]]; then
    BACKUP="$UNIT.bak-$(date +%F-%H%M%S)"
    cp -a "$UNIT" "$BACKUP"
    echo "   copia della unit vecchia: $BACKUP"
fi
# i limiti ora stanno nella unit: il vecchio drop-in non serve più
if [[ -f $DROPIN_DIR/limiti.conf ]]; then
    rm -f "$DROPIN_DIR/limiti.conf"
    rmdir "$DROPIN_DIR" 2>/dev/null || true
    echo "   rimosso il drop-in limiti.conf (i limiti sono nella unit)."
fi
install -m 644 "$SORGENTE/deploy/corso-api-json.service" "$UNIT"
systemctl daemon-reload

info "Riavvio e controllo"
systemctl enable --quiet corso-api-json
systemctl restart corso-api-json

# l'API nasce SPENTA: l'endpoint dell'interruttore è quello che risponde sempre
ok=0
for _ in $(seq 30); do
    if curl -fsS --max-time 2 "http://127.0.0.1:$PORTA/api/v1/interruttore" >/dev/null 2>&1; then
        ok=1; break
    fi
    sleep 1
done

if [[ $ok -eq 0 ]]; then
    printf '\033[31m\nIl servizio non risponde: torno indietro.\033[0m\n'
    journalctl -u corso-api-json -n 30 --no-pager || true
    if [[ -n $BACKUP ]]; then
        cp -a "$BACKUP" "$UNIT"
        systemctl daemon-reload
        systemctl restart corso-api-json || true
        echo "Unit precedente ripristinata da $BACKUP."
    fi
    errore "installazione annullata."
fi

UTENTE_VERO=$(ps -o user= -p "$(systemctl show corso-api-json -p MainPID --value)" | tr -d ' ')
echo "   servizio attivo, gira come: $UTENTE_VERO"
[[ $UTENTE_VERO == "$UTENTE" ]] || errore "gira come $UTENTE_VERO invece che $UTENTE."
curl -s "http://127.0.0.1:$PORTA/api/v1/interruttore"; echo

cat <<FINE

Fatto. L'API di prova è SPENTA, come deve essere: si accende da
    https://corso-api-json.giuseppebosi.com/api-attiva/
con la password impostata da deploy/imposta-password-api.py.

Da ora il sorgente resta in $SORGENTE, ma il servizio gira da $DEST.
Per pubblicare un aggiornamento: deploy/pubblica.sh
FINE
