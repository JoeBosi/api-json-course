"""Ricerca full-text, statistiche, query strutturate, SQL read-only, export CSV/NDJSON."""
from __future__ import annotations

import csv
import io
import json
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from .. import config, sql_guard
from ..db import riga, righe
from ..deps import ReadDB, SandboxDep
from ..errors import ApiError
from ..querybuilder import costruisci
from ..schemas import QueryIn, SqlIn

router = APIRouter(tags=["advanced"])


@router.get("/search", summary="Ricerca full-text (FTS5) su titoli e descrizioni, con ranking e snippet")
def cerca(con: ReadDB, q: Annotated[str, Query(min_length=2, max_length=100)], limit: int = 10) -> dict:
    try:
        rows = con.execute(
            "SELECT b.id, b.title, b.price, b.author_id, bm25(books_fts) AS score, "
            "snippet(books_fts, 1, '<b>', '</b>', '…', 12) AS snippet "
            "FROM books_fts JOIN books b ON b.id = books_fts.rowid WHERE books_fts MATCH ? ORDER BY score LIMIT ?",
            (q, min(limit, 50))).fetchall()
    except Exception as e:  # sintassi FTS non valida (es. virgolette sbilanciate)
        raise ApiError(400, "bad_query", "Sintassi di ricerca non valida", {"sqlite": str(e)})
    return {"query": q, "items": righe(rows)}


@router.get("/stats", summary="Aggregazioni: conteggi, prezzi medi, libri per categoria, top autori")
def stats(con: ReadDB) -> dict:
    return {
        "totals": riga(con.execute(
            "SELECT (SELECT COUNT(*) FROM books) AS books, (SELECT COUNT(*) FROM authors) AS authors, "
            "(SELECT COUNT(*) FROM customers) AS customers, (SELECT COUNT(*) FROM orders) AS orders, "
            "(SELECT COUNT(*) FROM reviews) AS reviews").fetchone()),
        "prices": riga(con.execute("SELECT ROUND(MIN(price),2) AS min, ROUND(AVG(price),2) AS avg, ROUND(MAX(price),2) AS max FROM books").fetchone()),
        "books_by_category": righe(con.execute(
            "SELECT c.slug, c.name, COUNT(b.id) AS books, ROUND(AVG(b.price),2) AS avg_price FROM categories c "
            "LEFT JOIN books b ON b.category_id=c.id GROUP BY c.id HAVING books > 0 ORDER BY books DESC")),
        "top_authors": righe(con.execute(
            "SELECT a.id, a.name, COUNT(b.id) AS books, ROUND(AVG(s.avg_rating),2) AS avg_rating FROM authors a "
            "JOIN books b ON b.author_id=a.id LEFT JOIN book_stats s ON s.book_id=b.id GROUP BY a.id ORDER BY books DESC, a.name LIMIT 5")),
        "orders_by_status": righe(con.execute("SELECT status, COUNT(*) AS orders, ROUND(SUM(total),2) AS revenue FROM orders GROUP BY status")),
    }


@router.get("/stats/sales", summary="Vendite raggruppate per mese, categoria o autore")
def vendite(con: ReadDB, group_by: Annotated[str, Query(pattern="^(month|category|author|city)$")] = "month",
            date_from: Annotated[str | None, Query(alias="from")] = None, date_to: Annotated[str | None, Query(alias="to")] = None) -> dict:
    where, params = ["o.status != 'cancelled'"], []
    if date_from:
        where.append("o.created_at >= ?"); params.append(date_from)
    if date_to:
        where.append("o.created_at < ?"); params.append(date_to)
    w = " AND ".join(where)
    chiavi = {
        "month": ("substr(o.created_at,1,7) AS month", "month", ""),
        "category": ("c.slug AS category", "c.slug", "JOIN categories c ON c.id=b.category_id"),
        "author": ("a.name AS author", "a.id", "JOIN authors a ON a.id=b.author_id"),
        "city": ("cu.city AS city", "cu.city", "JOIN customers cu ON cu.id=o.customer_id"),
    }
    sel, grp, join = chiavi[group_by]
    rows = righe(con.execute(
        f"SELECT {sel}, COUNT(DISTINCT o.id) AS orders, SUM(oi.quantity) AS books_sold, "
        f"ROUND(SUM(oi.quantity*oi.unit_price),2) AS revenue FROM orders o JOIN order_items oi ON oi.order_id=o.id "
        f"JOIN books b ON b.id=oi.book_id {join} WHERE {w} GROUP BY {grp} ORDER BY 1", params))
    return {"group_by": group_by, "items": rows}


@router.post("/query", summary="Query strutturata in JSON → SQL (allow-list di tabelle e campi)")
def query(dati: QueryIn, con: ReadDB) -> dict:
    sql, params = costruisci(dati)
    rows = righe(con.execute(sql, params).fetchall())
    return {"items": rows, "meta": {"sql": sql, "params": params, "count": len(rows)}}


@router.post("/sql", summary="SQL in sola lettura: solo SELECT, max 200 righe, 2 secondi")
def sql(dati: SqlIn, sb: SandboxDep) -> dict:
    path = sb.path if sb else config.SEED_DB
    return sql_guard.esegui(path, dati.sql, dati.params, dati.explain)


@router.get("/export/books.{fmt}", summary="Export in streaming: csv o ndjson")
def export_libri(fmt: str, con: ReadDB):
    if fmt not in ("csv", "ndjson"):
        raise ApiError(404, "not_found", "Formati disponibili: csv, ndjson")
    cur = con.execute("SELECT b.*, a.name AS author_name, c.slug AS category FROM books b "
                      "JOIN authors a ON a.id=b.author_id JOIN categories c ON c.id=b.category_id ORDER BY b.id")
    colonne = [d[0] for d in cur.description]
    rows = cur.fetchall()   # la connessione si chiude a fine richiesta: leggiamo prima di uscire

    def gen_csv():
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(colonne)
        yield buf.getvalue(); buf.seek(0); buf.truncate()
        for r in rows:
            w.writerow(list(r))
            yield buf.getvalue(); buf.seek(0); buf.truncate()

    def gen_ndjson():
        for r in rows:
            yield json.dumps(riga(r), ensure_ascii=False) + "\n"

    media = "text/csv; charset=utf-8" if fmt == "csv" else "application/x-ndjson"
    return StreamingResponse(gen_csv() if fmt == "csv" else gen_ndjson(), media_type=media,
                             headers={"Content-Disposition": f'attachment; filename="books.{fmt}"'})
