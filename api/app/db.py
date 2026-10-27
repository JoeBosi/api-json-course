"""Accesso a SQLite. Il seed (dataset pubblico) è un file `data/seed.db` rigenerato se manca.

Ogni sandbox è una copia di quel file. Le connessioni sono per-richiesta: SQLite è
leggero e questo evita problemi di thread.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config
from .seed import SCHEMA, popola


def _connect(path: Path, readonly: bool = False) -> sqlite3.Connection:
    if readonly:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    else:
        con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 3000")
    return con


def assicura_seed() -> Path:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    if not config.SEED_DB.exists():
        tmp = config.SEED_DB.with_suffix(".tmp")
        tmp.unlink(missing_ok=True)
        con = sqlite3.connect(tmp)
        con.execute("PRAGMA journal_mode = WAL")
        con.executescript(SCHEMA)
        popola(con)
        con.commit()
        con.close()
        tmp.rename(config.SEED_DB)
    return config.SEED_DB


@contextmanager
def connessione(path: Path, readonly: bool):
    con = _connect(path, readonly)
    try:
        yield con
        if not readonly:
            con.commit()
    finally:
        con.close()


# --- helper di conversione riga -> dict ---------------------------------------------------

JSON_COLS = {"attributes", "shipping_address", "metadata"}


def riga(r: sqlite3.Row | None) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in JSON_COLS:
        if k in d and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except ValueError:
                pass
    for k in ("in_stock",):
        if k in d and d[k] is not None:
            d[k] = bool(d[k])
    return d


def righe(rows) -> list[dict]:
    return [riga(r) for r in rows]
