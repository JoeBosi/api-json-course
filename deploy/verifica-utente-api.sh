#!/usr/bin/env bash
# Controlla che l'API giri davvero con l'utente dedicato e che sia chiusa dove deve esserlo.
# Da lanciare DOPO deploy/installa-utente-api.sh, come root:
#     cd /root/Developer/corso-api-json && sudo deploy/verifica-utente-api.sh
# Non cambia niente: solo letture e chiamate all'API.
set -uo pipefail

UTENTE=corso-api
DEST=/opt/corso-api-json
DATI=/var/lib/corso-api-json
PORTA=8795
B="http://127.0.0.1:$PORTA"
ok=0; ko=0

si() { printf '  \033[32mok\033[0m   %s\n' "$1"; ok=$((ok+1)); }
no() { printf '  \033[31mKO\033[0m   %s\n' "$1"; ko=$((ko+1)); }
prova() { if eval "$2" >/dev/null 2>&1; then si "$1"; else no "$1"; fi; }
nega()  { if eval "$2" >/dev/null 2>&1; then no "$1 (invece è riuscito!)"; else si "$1"; fi; }

echo "== 1. Chi fa girare il servizio =="
PID=$(systemctl show corso-api-json -p MainPID --value 2>/dev/null)
U=$(ps -o user= -p "${PID:-0}" 2>/dev/null | tr -d ' ')
[[ $U == "$UTENTE" ]] && si "gira come $UTENTE (pid $PID)" || no "gira come '${U:-nessuno}', atteso $UTENTE"
prova "l'utente non ha shell di login" "getent passwd $UTENTE | grep -qE '(nologin|/bin/false)$'"
prova "non appartiene a gruppi privilegiati" "! id -nG $UTENTE | tr ' ' '\n' | grep -qxE 'sudo|root|adm|docker|wheel'"

echo "== 2. Cosa può leggere e scrivere =="
nega  "NON legge /root"                       "sudo -u $UTENTE test -r /root/Developer"
nega  "NON legge il sorgente in /root"        "sudo -u $UTENTE cat /root/Developer/corso-api-json/CLAUDE.md"
prova "legge il codice in $DEST"              "sudo -u $UTENTE test -r $DEST/api/app/main.py"
nega  "NON scrive nel codice in $DEST"        "sudo -u $UTENTE touch $DEST/prova-scrittura"
prova "legge il .env (per l'hash)"            "sudo -u $UTENTE test -r $DEST/.env"
prova "scrive nei dati in $DATI"              "sudo -u $UTENTE touch $DATI/.prova && sudo -u $UTENTE rm -f $DATI/.prova"
nega  "NON scrive in /etc"                    "sudo -u $UTENTE touch /etc/prova-corso-api"
nega  "NON scrive in /var/lib fuori dai dati" "sudo -u $UTENTE touch /var/lib/prova-corso-api"

echo "== 3. Test automatici del progetto =="
if ( cd "$(dirname "$0")/../api" && uv run pytest -q >/tmp/pytest-corso.log 2>&1 ); then
    si "pytest: $(tail -1 /tmp/pytest-corso.log)"
else
    no "pytest fallito, vedi /tmp/pytest-corso.log"
fi

echo "== 4. API spenta (stato normale) =="
S=$(curl -s -o /dev/null -w '%{http_code}' "$B/api/v1/books")
[[ $S == 503 ]] && si "/api/v1/books risponde 503" || no "/api/v1/books risponde $S, atteso 503"
curl -s "$B/api/v1/books" | grep -q api_spenta && si "il messaggio dice dove accenderla" || no "manca il codice api_spenta"
prova "lo stato si legge sempre"   "curl -fsS $B/api/v1/interruttore"
prova "il sito risponde"           "curl -fsS -o /dev/null $B/"
prova "la pagina /api-attiva c'è"  "curl -fsS -o /dev/null $B/api-attiva/"

echo "== 5. Accensione e uso (serve la password) =="
read -rsp "  Password dell'API (invio per saltare questa parte): " PW; echo
if [[ -z $PW ]]; then
    echo "  -- saltata"
else
    R=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$B/api/v1/interruttore/accendi" \
        -H 'Content-Type: application/json' -d "{\"password\":$(printf '%s' "$PW" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}")
    [[ $R == 200 ]] && si "password giusta: API accesa" || no "accensione fallita (HTTP $R)"
    prova "ora /api/v1/books risponde" "curl -fsS -o /dev/null $B/api/v1/books"
    T=$(curl -s -X POST "$B/api/v1/sandbox" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))' 2>/dev/null)
    [[ -n $T ]] && si "sandbox creata (${T:0:6}…)" || no "sandbox non creata"
    if [[ -n $T ]]; then
        C=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$B/api/v1/books" -H "Authorization: Bearer $T" \
            -H 'Content-Type: application/json' \
            -d '{"title":"Verifica","author_id":1,"category_id":1,"price":9.9,"format":"tascabile","pages":80,"published_year":2021,"isbn":"9780000000777","stock":1}')
        [[ $C == 201 ]] && si "scrittura in sandbox (201)" || no "scrittura in sandbox: $C"
        curl -s -o /dev/null -X DELETE "$B/api/v1/sandbox" -H "Authorization: Bearer $T"
        D=$(curl -s -o /dev/null -w '%{http_code}' "$B/api/v1/books" -H "Authorization: Bearer $T")
        [[ $D == 401 ]] && si "token cancellato: 401" || no "token cancellato ma risponde $D"
    fi
    echo "  40 chiamate di fila (limite 30 al minuto):"
    for _ in $(seq 40); do curl -s -o /dev/null -w '%{http_code}\n' "$B/api/v1/books?limit=1"; done | sort | uniq -c | sed 's/^/    /'
    echo "  (atteso: circa 30 risposte 200 e il resto 429)"
fi

echo
echo "Riepilogo: $ok controlli superati, $ko falliti."
[[ $ko -eq 0 ]] || exit 1
