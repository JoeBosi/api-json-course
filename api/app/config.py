"""Configurazione letta dalle variabili d'ambiente e da ../.env (vedi ../.env.example)."""
from pathlib import Path
import os


def _carica_env() -> None:
    """Legge ../.env senza dipendenze: le variabili già nell'ambiente vincono."""
    f = Path(__file__).resolve().parent.parent.parent / ".env"
    try:
        righe = f.read_text().splitlines()
    except OSError:
        return
    for riga in righe:
        riga = riga.strip()
        if not riga or riga.startswith("#") or "=" not in riga:
            continue
        chiave, _, valore = riga.partition("=")
        os.environ.setdefault(chiave.strip(), valore.strip().strip("'\""))


_carica_env()

BASE_DIR = Path(__file__).resolve().parent.parent          # api/
DATA_DIR = Path(os.environ.get("CORSO_DATA_DIR", BASE_DIR / "data"))
SEED_DB = DATA_DIR / "seed.db"
SANDBOX_DIR = DATA_DIR / "sandboxes"
SITE_DIST = Path(os.environ.get("CORSO_SITE_DIST", BASE_DIR.parent / "site" / "dist"))

SANDBOX_TTL_HOURS = int(os.environ.get("CORSO_SANDBOX_TTL_HOURS", "6"))
SANDBOX_MAX = int(os.environ.get("CORSO_SANDBOX_MAX", "500"))      # limite di sandbox vive
RATE_LIMIT = os.environ.get("CORSO_RATE_LIMIT", "120/minute")
SQL_MAX_ROWS = 200
PAGE_MAX = 100
PUBLIC_URL = os.environ.get("CORSO_PUBLIC_URL", "https://corso-api-json.giuseppebosi.com")

# Interruttore dell'API di prova: spenta di norma, si accende dal sito con la password.
STATO_FILE = DATA_DIR / "api_stato.json"
API_IDLE_MIN = int(os.environ.get("CORSO_API_IDLE_MIN", "60"))          # spegnimento dopo inattività
API_PASSWORD_HASH = os.environ.get("CORSO_API_PASSWORD_HASH", "")       # scrypt, mai la password
API_TENTATIVI_MAX = int(os.environ.get("CORSO_API_TENTATIVI_MAX", "5"))
API_TENTATIVI_FINESTRA_MIN = int(os.environ.get("CORSO_API_TENTATIVI_FINESTRA_MIN", "15"))
PAGINA_ATTIVA = os.environ.get("CORSO_PAGINA_ATTIVA", "/api-attiva/")   # dove si accende
