"""Sandbox: crea, mostra, azzera, elimina la copia privata del database."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Response

from .. import sandbox
from ..deps import SandboxDep
from ..errors import ApiError

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rappresenta(sb: sandbox.Sandbox) -> dict:
    return {"token": sb.token, "created_at": _iso(sb.created_at), "expires_at": _iso(sb.expires_at),
            "how_to_use": {"header": f"Authorization: Bearer {sb.token}", "alt_header": f"X-Sandbox-Token: {sb.token}"}}


@router.post("", status_code=201, summary="Crea una sandbox: una copia privata del database")
def crea() -> dict:
    return _rappresenta(sandbox.crea())


@router.get("", summary="Informazioni sulla sandbox del token inviato")
def info(sb: SandboxDep) -> dict:
    if sb is None:
        raise ApiError(401, "sandbox_required", "Invia il token con Authorization: Bearer <token>")
    return _rappresenta(sb)


@router.post("/reset", summary="Riporta la sandbox ai dati iniziali")
def reset(sb: SandboxDep) -> dict:
    if sb is None:
        raise ApiError(401, "sandbox_required", "Invia il token con Authorization: Bearer <token>")
    sandbox.azzera(sb.token)
    return {"status": "reset", **_rappresenta(sandbox.info(sb.token))}


@router.delete("", status_code=204, summary="Elimina la sandbox")
def elimina(sb: SandboxDep) -> Response:
    if sb is None:
        raise ApiError(401, "sandbox_required", "Invia il token con Authorization: Bearer <token>")
    sandbox.elimina(sb.token)
    return Response(status_code=204)


@router.get("/me", summary="Chi sono? (200 con token valido, 401 senza)", tags=["auth"])
def me(sb: SandboxDep) -> dict:
    if sb is None:
        raise ApiError(401, "unauthorized", "Nessun token: aggiungi Authorization: Bearer <token>")
    return {"authenticated": True, "token_prefix": sb.token[:8] + "…", "expires_at": _iso(sb.expires_at)}
