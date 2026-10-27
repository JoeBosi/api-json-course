"""Endpoint di servizio: indice, health, echo, schema del database (PK/FK)."""
from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Request

from .. import config
from ..deps import ReadDB

router = APIRouter(tags=["meta"])


@router.get("/", summary="Indice dell'API con i link principali")
def indice(request: Request) -> dict:
    base = str(request.base_url).rstrip("/") + "/api/v1"
    return {
        "name": "Corso JSON & API — server di prova",
        "version": "1",
        "docs": f"{request.base_url}api/docs",
        "links": {k: f"{base}/{k}" for k in ["health", "schema", "books", "authors", "categories",
                                              "customers", "orders", "reviews", "search", "stats", "sandbox"]},
        "sandbox": "POST /api/v1/sandbox → token; poi Authorization: Bearer <token>",
    }


@router.get("/health", summary="Stato del servizio")
def health() -> dict:
    return {"status": "ok", "public_dataset": config.SEED_DB.exists()}


@router.get("/echo", summary="Rimanda ciò che ricevi (metodo, query, header)")
@router.post("/echo")
@router.put("/echo")
async def echo(request: Request) -> dict[str, Any]:
    corpo: Any = None
    raw = await request.body()
    if raw:
        try:
            corpo = await request.json()
        except Exception:
            corpo = {"_raw": raw.decode("utf-8", "replace")[:2000], "_note": "il body non è JSON valido"}
    return {
        "method": request.method,
        "path": request.url.path,
        "query": dict(request.query_params),
        "headers": {k: v for k, v in request.headers.items() if k.lower() not in ("cookie",)},
        "json": corpo,
    }


@router.get("/schema", summary="Tabelle, colonne, chiavi primarie ed esterne del database")
def schema(con: ReadDB) -> dict:
    tabelle = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'books_fts%' ORDER BY name")]
    out = {}
    for t in tabelle:
        cols = [{"name": c["name"], "type": c["type"], "primary_key": bool(c["pk"]), "nullable": not c["notnull"]}
                for c in con.execute(f"PRAGMA table_info({t})")]
        fks = [{"column": f["from"], "references": {"table": f["table"], "column": f["to"]}}
               for f in con.execute(f"PRAGMA foreign_key_list({t})")]
        out[t] = {"columns": cols, "primary_key": [c["name"] for c in cols if c["primary_key"]],
                  "foreign_keys": fks, "rows": con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]}
    return {"tables": out, "views": ["book_stats"], "full_text": ["books_fts"]}
