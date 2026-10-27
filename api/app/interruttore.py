"""Interruttore dell'API di prova: di norma spenta, si accende dal sito con una password.

Perché: il sito del corso è pubblico e senza password, ma l'API di prova (scritture in sandbox,
SQL, export) non deve restare esposta a chiunque 24 ore su 24. Chi vuole fare gli esercizi la
accende dalla pagina /api-attiva; dopo CORSO_API_IDLE_MIN minuti senza chiamate si spegne da sola.

Niente password in chiaro da nessuna parte: in .env sta solo l'hash scrypt, scritto da
deploy/imposta-password-api.py. Lo stato (ultima chiamata) sta in data/api_stato.json, così
sopravvive al riavvio del servizio.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from . import config
from .errors import ApiError

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2**14, 8, 1

# stato in memoria: scriviamo su disco al massimo una volta al minuto (una richiesta = un touch)
_ultima: float = 0.0
_ultima_salvata: float = 0.0
_tentativi: dict[str, list[float]] = {}


# --- password -------------------------------------------------------------------------------

def genera_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32)
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N, _SCRYPT_R, _SCRYPT_P,
        base64.b64encode(salt).decode(), base64.b64encode(dk).decode())


def verifica_password(password: str, memorizzato: str) -> bool:
    try:
        algo, n, r, p, salt_b64, hash_b64 = memorizzato.split("$")
        if algo != "scrypt":
            return False
        dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64),
                            n=int(n), r=int(r), p=int(p), dklen=len(base64.b64decode(hash_b64)))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk, base64.b64decode(hash_b64))


# --- stato ----------------------------------------------------------------------------------

def _carica() -> float:
    global _ultima
    if _ultima:
        return _ultima
    try:
        _ultima = float(json.loads(config.STATO_FILE.read_text()).get("ultima", 0))
    except (OSError, ValueError, AttributeError):
        _ultima = 0.0
    return _ultima


def _salva(forza: bool = False) -> None:
    global _ultima_salvata
    if not forza and time.time() - _ultima_salvata < 60:
        return
    try:
        config.STATO_FILE.parent.mkdir(parents=True, exist_ok=True)
        config.STATO_FILE.write_text(json.dumps({"ultima": _ultima}))
        _ultima_salvata = time.time()
    except OSError:
        pass


def secondi_rimasti() -> float:
    return max(0.0, _carica() + config.API_IDLE_MIN * 60 - time.time())


def accesa() -> bool:
    return secondi_rimasti() > 0


def tocca() -> None:
    """Ogni chiamata all'API rimanda in avanti lo spegnimento automatico."""
    global _ultima
    _ultima = time.time()
    _salva()


def accendi() -> None:
    global _ultima
    _ultima = time.time()
    _salva(forza=True)


def spegni() -> None:
    global _ultima
    _ultima = 0.0
    _salva(forza=True)


def stato() -> dict:
    rimasti = int(secondi_rimasti())
    return {"attiva": rimasti > 0, "spegnimento_tra_s": rimasti,
            "minuti_di_inattivita": config.API_IDLE_MIN,
            "configurata": bool(config.API_PASSWORD_HASH)}


# --- accensione con password ------------------------------------------------------------------

def _controlla_tentativi(ip: str) -> None:
    ora = time.time()
    finestra = config.API_TENTATIVI_FINESTRA_MIN * 60
    recenti = [t for t in _tentativi.get(ip, []) if ora - t < finestra]
    _tentativi[ip] = recenti
    if len(recenti) >= config.API_TENTATIVI_MAX:
        attesa = int(finestra - (ora - recenti[0]))
        raise ApiError(429, "troppi_tentativi",
                       f"Troppi tentativi di password: riprova tra {attesa // 60 + 1} minuti.",
                       headers={"Retry-After": str(attesa)})


def prova_password(password: str, ip: str) -> dict:
    """Accende l'API se la password è giusta. Conta i tentativi per IP."""
    if not config.API_PASSWORD_HASH:
        raise ApiError(503, "password_non_configurata",
                       "L'interruttore non è ancora configurato: manca la password sul server.")
    _controlla_tentativi(ip)
    if not verifica_password(password, config.API_PASSWORD_HASH):
        _tentativi.setdefault(ip, []).append(time.time())
        rimasti = config.API_TENTATIVI_MAX - len(_tentativi[ip])
        raise ApiError(401, "password_errata",
                       f"Password sbagliata. Tentativi rimasti: {max(0, rimasti)}.")
    _tentativi.pop(ip, None)
    accendi()
    return stato()
