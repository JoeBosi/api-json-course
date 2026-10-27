#!/usr/bin/env bash
# Cambia la password con cui si entra nel sito del corso (basic_auth di Caddy).
#
# Cosa fa:
#   1. chiede la nuova password due volte, senza mostrarla a schermo;
#   2. calcola l'hash bcrypt con `caddy hash-password` (la password non finisce da nessuna parte:
#      né in un file, né nella cronologia della shell, né in questo script);
#   3. salva SOLO l'hash in /root/.config/corso-api-json/basic-auth.hash (permessi 600) e lo
#      stampa, perché è quello che va messo nel blocco Caddy;
#   4. aggiorna il blocco di esempio deploy/Caddyfile.snippet (con copia di sicurezza), così il
#      file del progetto non contiene più l'hash vecchio.
#
# NON tocca /etc/caddy/Caddyfile e NON ricarica Caddy: quello lo fa il Controller.
#
# Uso (via SSH, sul VPS):
#     cd /root/Developer/corso-api-json && sudo deploy/cambia-password-sito.sh [utente]
# L'utente predefinito è `giuseppe`.
set -euo pipefail

UTENTE="${1:-giuseppe}"
PROGETTO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SNIPPET="$PROGETTO/deploy/Caddyfile.snippet"
DEST_DIR=/root/.config/corso-api-json
DEST="$DEST_DIR/basic-auth.hash"

errore() { printf '\033[31mERRORE: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || errore "serve root: usa sudo."
command -v caddy >/dev/null || errore "il comando caddy non c'è."
[[ -t 0 ]] || errore "serve un terminale: lancialo via SSH, non da uno script."

echo "Nuova password per entrare nel sito (utente: $UTENTE)."
echo "Non verrà mostrata, né salvata in chiaro da nessuna parte."
echo

for tentativo in 1 2 3; do
    read -rsp "Nuova password: " p1; echo
    if [[ ${#p1} -lt 12 ]]; then
        echo "  Troppo corta: almeno 12 caratteri. Evita date e nomi."; echo; continue
    fi
    read -rsp "Ripetila: " p2; echo
    if [[ "$p1" != "$p2" ]]; then
        echo "  Le due password non coincidono."; echo; continue
    fi
    break
done
[[ -n "${p1:-}" && "${p1:-}" == "${p2:-}" && ${#p1} -ge 12 ]] || errore "password non impostata."

# l'hash lo calcola caddy; la password passa solo sullo stdin del comando
# nota: caddy legge una RIGA dallo stdin, quindi il \n ci vuole (senza, risponde "EOF")
HASH=$(printf '%s\n' "$p1" | caddy hash-password) || errore "caddy hash-password è fallito."
unset p1 p2
[[ $HASH == '$2a$'* || $HASH == '$2b$'* ]] || errore "hash inatteso: $HASH"

install -d -m 700 "$DEST_DIR"
umask 077
printf '# Hash bcrypt della password del sito corso-api-json (basic_auth di Caddy)\n# utente: %s — generato il %s da deploy/cambia-password-sito.sh\n%s\n' \
       "$UTENTE" "$(date '+%F %H:%M')" "$HASH" > "$DEST"
chmod 600 "$DEST"

# il blocco di esempio nel progetto non deve restare con l'hash vecchio
if [[ -f $SNIPPET ]]; then
    cp -a "$SNIPPET" "$SNIPPET.bak-$(date +%F-%H%M%S)"
    python3 - "$SNIPPET" "$UTENTE" "$HASH" <<'PY'
import re, sys
percorso, utente, hash_ = sys.argv[1:4]
testo = open(percorso, encoding='utf-8').read()
nuovo, n = re.subn(r'(basic_auth \{\s*\n\s*)\S+\s+\$2[ab]\$\S+',
                   lambda m: f'{m.group(1)}{utente} {hash_}', testo, count=1)
open(percorso, 'w', encoding='utf-8').write(nuovo)
print(f"   snippet aggiornato ({n} blocco)" if n else "   ATTENZIONE: nel blocco non ho trovato basic_auth da aggiornare")
PY
fi

cat <<FINE

Fatto. La password non è stata salvata: esiste solo nella tua testa.

Hash da mettere nel blocco Caddy (utente $UTENTE):

    basic_auth {
        $UTENTE $HASH
    }

Copia dell'hash (solo root): $DEST

Ora passa l'hash al Controller: Caddy e il reload NON li ho toccati.
Ricorda di aggiornare dove la password è scritta a mano (es. ARCHITETTURA.md) e di non
riusarla altrove.
FINE
