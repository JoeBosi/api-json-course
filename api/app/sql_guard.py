"""Esegue SQL in sola lettura: authorizer di SQLite (solo SELECT/READ/FUNCTION), connessione
`mode=ro`, interruzione dopo 2 secondi, massimo SQL_MAX_ROWS righe.
"""
from __future__ import annotations

import sqlite3
import time

from . import config
from .errors import ApiError

_PERMESSE = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE}
_TIMEOUT_S = 2.0


def _authorizer(action, arg1, arg2, dbname, source):
    if action in _PERMESSE:
        # tabelle interne di SQLite escluse
        if action == sqlite3.SQLITE_READ and arg1 and arg1.startswith("sqlite_"):
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def esegui(path, sql: str, params: list, explain: bool = False) -> dict:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    con.set_authorizer(_authorizer)
    scadenza = time.monotonic() + _TIMEOUT_S
    con.set_progress_handler(lambda: 1 if time.monotonic() > scadenza else 0, 5000)
    inizio = time.perf_counter()
    try:
        if explain:
            sql = "EXPLAIN QUERY PLAN " + sql
        cur = con.execute(sql, params)
        colonne = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(config.SQL_MAX_ROWS + 1)
    except sqlite3.DatabaseError as e:
        msg = str(e)
        if "not authorized" in msg:
            raise ApiError(403, "sql_not_allowed", "Solo SELECT: questa istruzione non è permessa", {"sqlite": msg})
        if "interrupted" in msg:
            raise ApiError(408, "sql_timeout", f"Query interrotta: superati {_TIMEOUT_S:.0f} secondi")
        raise ApiError(400, "sql_error", "SQL non valido", {"sqlite": msg})
    finally:
        con.close()
    troncato = len(rows) > config.SQL_MAX_ROWS
    rows = rows[: config.SQL_MAX_ROWS]
    return {
        "columns": colonne,
        "rows": [list(r) for r in rows],
        "row_count": len(rows),
        "truncated": troncato,
        "elapsed_ms": round((time.perf_counter() - inizio) * 1000, 2),
    }
