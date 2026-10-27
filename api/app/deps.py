"""Dipendenze condivise: connessione DB (pubblica o sandbox), paginazione, token."""
from __future__ import annotations

from typing import Annotated, Iterator
import sqlite3

from fastapi import Depends, Header, Query, Request
from pydantic import BaseModel

from . import config, db, sandbox
from .errors import ApiError


def _token(request: Request, authorization: str | None, x_sandbox_token: str | None) -> str | None:
    if authorization:
        schema, _, valore = authorization.partition(" ")
        if schema.lower() != "bearer" or not valore:
            raise ApiError(401, "bad_authorization", "Usa l'intestazione: Authorization: Bearer <token>")
        return valore.strip()
    if x_sandbox_token:
        return x_sandbox_token.strip()
    return request.query_params.get("token")   # comodo per provare dal browser


def sandbox_corrente(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_sandbox_token: Annotated[str | None, Header()] = None,
) -> sandbox.Sandbox | None:
    return sandbox.valida(_token(request, authorization, x_sandbox_token))


SandboxDep = Annotated[sandbox.Sandbox | None, Depends(sandbox_corrente)]


def connessione_lettura(sb: SandboxDep) -> Iterator[sqlite3.Connection]:
    """Sandbox se c'è il token, altrimenti il dataset pubblico in sola lettura."""
    path, ro = (sb.path, False) if sb else (config.SEED_DB, True)
    with db.connessione(path, readonly=ro) as con:
        yield con


def connessione_scrittura(sb: SandboxDep) -> Iterator[sqlite3.Connection]:
    """Le scritture richiedono una sandbox: il dataset pubblico non si tocca."""
    if sb is None:
        raise ApiError(401, "sandbox_required",
                       "Le scritture richiedono un token sandbox: POST /api/v1/sandbox, poi Authorization: Bearer <token>")
    with db.connessione(sb.path, readonly=False) as con:
        yield con


ReadDB = Annotated[sqlite3.Connection, Depends(connessione_lettura)]
WriteDB = Annotated[sqlite3.Connection, Depends(connessione_scrittura)]


class Paginazione(BaseModel):
    page: int
    limit: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def paginazione(
    page: Annotated[int, Query(ge=1, description="Pagina (parte da 1)")] = 1,
    limit: Annotated[int, Query(ge=1, le=config.PAGE_MAX, description="Elementi per pagina")] = 20,
) -> Paginazione:
    return Paginazione(page=page, limit=limit)


PageDep = Annotated[Paginazione, Depends(paginazione)]


def pagina(items: list, total: int, p: Paginazione, request: Request) -> dict:
    """Busta standard delle liste: items + meta (+ link next/prev)."""
    pages = max(1, -(-total // p.limit))

    def link(n: int | None):
        if n is None:
            return None
        return str(request.url.include_query_params(page=n, limit=p.limit))

    return {
        "items": items,
        "meta": {"page": p.page, "limit": p.limit, "total": total, "pages": pages},
        "links": {"self": link(p.page), "next": link(p.page + 1) if p.page < pages else None,
                  "prev": link(p.page - 1) if p.page > 1 else None},
    }


def o_404(row, cosa: str, id_):
    if row is None:
        raise ApiError(404, "not_found", f"{cosa} {id_} non trovato")
    return row
