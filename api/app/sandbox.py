"""Sandbox per lettore: un token = una copia privata del database.

POST /api/v1/sandbox crea `data/sandboxes/<token>.db` copiando il seed. Il token va poi
inviato con `Authorization: Bearer <token>` (o `X-Sandbox-Token`). Senza token si legge il
dataset pubblico in sola lettura. Le sandbox scadono dopo SANDBOX_TTL_HOURS e vengono
cancellate alla prima occasione utile.
"""
from __future__ import annotations

import secrets
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from . import config
from .errors import ApiError

_PREFIX = "sb_"


@dataclass
class Sandbox:
    token: str
    path: Path
    created_at: float
    expires_at: float


def _path(token: str) -> Path:
    return config.SANDBOX_DIR / f"{token}.db"


def pulisci_scadute() -> int:
    """Rimuove i file scaduti; ritorna quante sandbox ha cancellato."""
    ora, tolte = time.time(), 0
    ttl = config.SANDBOX_TTL_HOURS * 3600
    for f in config.SANDBOX_DIR.glob(f"{_PREFIX}*.db*"):
        try:
            if ora - f.stat().st_mtime > ttl:
                f.unlink()
                tolte += 1
        except FileNotFoundError:
            pass
    return tolte


def crea() -> Sandbox:
    pulisci_scadute()
    vive = len(list(config.SANDBOX_DIR.glob(f"{_PREFIX}*.db")))
    if vive >= config.SANDBOX_MAX:
        raise ApiError(503, "sandbox_full", "Troppe sandbox attive in questo momento: riprova tra qualche minuto.")
    token = _PREFIX + secrets.token_urlsafe(18)
    shutil.copyfile(config.SEED_DB, _path(token))
    return info(token)


def info(token: str) -> Sandbox:
    p = _path(token)
    st = p.stat()
    return Sandbox(token, p, st.st_mtime, st.st_mtime + config.SANDBOX_TTL_HOURS * 3600)


def valida(token: str | None) -> Sandbox | None:
    """None se non c'è token; errore 401 se il token non esiste o è scaduto."""
    if not token:
        return None
    if not token.startswith(_PREFIX) or "/" in token or ".." in token or not _path(token).exists():
        raise ApiError(401, "invalid_token", "Token sandbox sconosciuto o scaduto: creane uno con POST /api/v1/sandbox")
    sb = info(token)
    if sb.expires_at < time.time():
        _path(token).unlink(missing_ok=True)
        raise ApiError(401, "expired_token", "Token sandbox scaduto: creane uno con POST /api/v1/sandbox")
    _path(token).touch()   # ogni uso rinnova la scadenza
    return sb


def azzera(token: str) -> None:
    shutil.copyfile(config.SEED_DB, _path(token))


def elimina(token: str) -> None:
    for f in config.SANDBOX_DIR.glob(f"{token}.db*"):
        f.unlink(missing_ok=True)
