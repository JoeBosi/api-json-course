"""Libri: lista con filtri/ordinamento/paginazione, dettaglio con expand ed ETag, CRUD in sandbox."""
from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request, Response

from .. import config
from ..db import riga, righe
from ..deps import PageDep, ReadDB, WriteDB, o_404, pagina
from ..errors import ApiError
from ..schemas import BookIn, BookPatch

router = APIRouter(prefix="/books", tags=["books"])

ORDINAMENTI = {"title": "b.title", "price": "b.price", "year": "b.published_year", "pages": "b.pages",
               "created_at": "b.created_at", "id": "b.id", "rating": "s.avg_rating"}
EXPAND = {"author", "category", "tags", "stats", "reviews"}

SELECT = """SELECT b.*, s.reviews_count, s.avg_rating FROM books b
            LEFT JOIN book_stats s ON s.book_id = b.id"""


def _espandi(con, libro: dict, expand: set[str]) -> dict:
    if "author" in expand:
        libro["author"] = riga(con.execute("SELECT * FROM authors WHERE id=?", (libro["author_id"],)).fetchone())
    if "category" in expand:
        libro["category"] = riga(con.execute("SELECT * FROM categories WHERE id=?", (libro["category_id"],)).fetchone())
    if "tags" in expand:
        libro["tags"] = [r[0] for r in con.execute(
            "SELECT t.name FROM tags t JOIN book_tags bt ON bt.tag_id=t.id WHERE bt.book_id=? ORDER BY t.name", (libro["id"],))]
    if "reviews" in expand:
        libro["reviews"] = righe(con.execute(
            "SELECT r.id, r.rating, r.comment, r.created_at, c.name AS customer_name FROM reviews r "
            "JOIN customers c ON c.id=r.customer_id WHERE r.book_id=? ORDER BY r.created_at DESC", (libro["id"],)))
    return libro


def _parse_expand(expand: str | None) -> set[str]:
    if not expand:
        return set()
    voci = {e.strip() for e in expand.split(",") if e.strip()}
    sconosciute = voci - EXPAND
    if sconosciute:
        raise ApiError(400, "bad_expand", f"expand non valido: {', '.join(sorted(sconosciute))}", {"allowed": sorted(EXPAND)})
    return voci


@router.get("", summary="Elenco libri con filtri, ordinamento e paginazione")
def lista(
    con: ReadDB, p: PageDep, request: Request,
    q: Annotated[str | None, Query(description="Testo cercato nel titolo (LIKE)")] = None,
    author_id: int | None = None,
    category: Annotated[str | None, Query(description="slug della categoria (include le sottocategorie)")] = None,
    tag: str | None = None,
    min_price: float | None = None, max_price: float | None = None,
    year_from: int | None = None, year_to: int | None = None,
    language: str | None = None,
    in_stock: bool | None = None,
    format: Annotated[str | None, Query(description="filtra attributes.format (colonna JSON)")] = None,
    sort: Annotated[str, Query(description="campo, con '-' per discendente: es. -price, title, rating")] = "id",
    expand: Annotated[str | None, Query(description="author,category,tags")] = None,
) -> dict:
    where, params = ["1=1"], []
    if q:
        where.append("b.title LIKE ?"); params.append(f"%{q}%")
    if author_id is not None:
        where.append("b.author_id = ?"); params.append(author_id)
    if category:
        where.append("""b.category_id IN (WITH RECURSIVE sub(id) AS (
            SELECT id FROM categories WHERE slug = ? UNION ALL
            SELECT c.id FROM categories c JOIN sub ON c.parent_id = sub.id) SELECT id FROM sub)""")
        params.append(category)
    if tag:
        where.append("b.id IN (SELECT bt.book_id FROM book_tags bt JOIN tags t ON t.id=bt.tag_id WHERE t.name = ?)"); params.append(tag)
    if min_price is not None:
        where.append("b.price >= ?"); params.append(min_price)
    if max_price is not None:
        where.append("b.price <= ?"); params.append(max_price)
    if year_from is not None:
        where.append("b.published_year >= ?"); params.append(year_from)
    if year_to is not None:
        where.append("b.published_year <= ?"); params.append(year_to)
    if language:
        where.append("b.language = ?"); params.append(language)
    if in_stock is not None:
        where.append("b.in_stock = ?"); params.append(int(in_stock))
    if format:
        where.append("json_extract(b.attributes, '$.format') = ?"); params.append(format)

    desc = sort.startswith("-")
    campo = sort.lstrip("-+")
    if campo not in ORDINAMENTI:
        raise ApiError(400, "bad_sort", f"sort non valido: {sort}", {"allowed": sorted(ORDINAMENTI)})
    order = f"{ORDINAMENTI[campo]} {'DESC' if desc else 'ASC'}, b.id ASC"

    w = " AND ".join(where)
    total = con.execute(f"SELECT COUNT(*) FROM books b LEFT JOIN book_stats s ON s.book_id=b.id WHERE {w}", params).fetchone()[0]
    rows = righe(con.execute(f"{SELECT} WHERE {w} ORDER BY {order} LIMIT ? OFFSET ?", [*params, p.limit, p.offset]))
    exp = _parse_expand(expand) - {"reviews"}
    items = [_espandi(con, r, exp) for r in rows] if exp else rows
    return pagina(items, total, p, request)


@router.get("/{book_id}", summary="Dettaglio di un libro (con ETag e expand)")
def dettaglio(book_id: int, con: ReadDB, request: Request, response: Response,
              expand: Annotated[str | None, Query(description="author,category,tags,reviews")] = None) -> dict:
    libro = o_404(riga(con.execute(f"{SELECT} WHERE b.id=?", (book_id,)).fetchone()), "Libro", book_id)
    libro = _espandi(con, libro, _parse_expand(expand))
    etag = '"' + hashlib.sha1(json.dumps(libro, sort_keys=True, default=str).encode()).hexdigest()[:16] + '"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})  # type: ignore[return-value]
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=60" if request.headers.get("authorization") is None else "no-store"
    return libro


def _controlla_fk(con, author_id: int | None, category_id: int | None):
    if author_id is not None and con.execute("SELECT 1 FROM authors WHERE id=?", (author_id,)).fetchone() is None:
        raise ApiError(422, "unknown_author", f"author_id {author_id} non esiste (chiave esterna)")
    if category_id is not None and con.execute("SELECT 1 FROM categories WHERE id=?", (category_id,)).fetchone() is None:
        raise ApiError(422, "unknown_category", f"category_id {category_id} non esiste (chiave esterna)")


def _salva_tag(con, book_id: int, tags: list[str]):
    con.execute("DELETE FROM book_tags WHERE book_id=?", (book_id,))
    for t in tags:
        con.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (t,))
        tid = con.execute("SELECT id FROM tags WHERE name=?", (t,)).fetchone()[0]
        con.execute("INSERT OR IGNORE INTO book_tags VALUES (?,?)", (book_id, tid))


@router.post("", status_code=201, summary="Crea un libro (serve la sandbox)")
def crea(dati: BookIn, con: WriteDB, request: Request, response: Response) -> dict:
    _controlla_fk(con, dati.author_id, dati.category_id)
    isbn = dati.isbn or f"978-88-sandbox-{con.execute('SELECT COALESCE(MAX(id),0)+1 FROM books').fetchone()[0]}"
    if con.execute("SELECT 1 FROM books WHERE isbn=?", (isbn,)).fetchone():
        raise ApiError(409, "duplicate_isbn", f"Esiste già un libro con ISBN {isbn}")
    from datetime import datetime, timezone
    cur = con.execute(
        "INSERT INTO books(title,isbn,author_id,category_id,price,pages,published_year,language,in_stock,attributes,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (dati.title, isbn, dati.author_id, dati.category_id, dati.price, dati.pages, dati.published_year, dati.language,
         int(dati.in_stock), json.dumps(dati.attributes, ensure_ascii=False),
         datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")))
    book_id = cur.lastrowid
    _salva_tag(con, book_id, dati.tags)
    con.execute("INSERT INTO books_fts(rowid, title, description) VALUES (?,?,?)", (book_id, dati.title, dati.title))
    response.headers["Location"] = f"{request.base_url}api/v1/books/{book_id}"
    return _espandi(con, riga(con.execute(f"{SELECT} WHERE b.id=?", (book_id,)).fetchone()), {"tags"})


@router.put("/{book_id}", summary="Sostituisce un libro per intero (serve la sandbox)")
def sostituisci(book_id: int, dati: BookIn, con: WriteDB) -> dict:
    o_404(con.execute("SELECT 1 FROM books WHERE id=?", (book_id,)).fetchone(), "Libro", book_id)
    _controlla_fk(con, dati.author_id, dati.category_id)
    con.execute("UPDATE books SET title=?,author_id=?,category_id=?,price=?,pages=?,published_year=?,language=?,in_stock=?,attributes=? WHERE id=?",
                (dati.title, dati.author_id, dati.category_id, dati.price, dati.pages, dati.published_year, dati.language,
                 int(dati.in_stock), json.dumps(dati.attributes, ensure_ascii=False), book_id))
    _salva_tag(con, book_id, dati.tags)
    return _espandi(con, riga(con.execute(f"{SELECT} WHERE b.id=?", (book_id,)).fetchone()), {"tags"})


@router.patch("/{book_id}", summary="Modifica solo i campi inviati (serve la sandbox)")
def modifica(book_id: int, dati: BookPatch, con: WriteDB) -> dict:
    o_404(con.execute("SELECT 1 FROM books WHERE id=?", (book_id,)).fetchone(), "Libro", book_id)
    campi = dati.model_dump(exclude_unset=True)
    if not campi:
        raise ApiError(422, "empty_patch", "Nessun campo da modificare")
    _controlla_fk(con, campi.get("author_id"), campi.get("category_id"))
    tags = campi.pop("tags", None)
    if "attributes" in campi:
        campi["attributes"] = json.dumps(campi["attributes"], ensure_ascii=False)
    if "in_stock" in campi:
        campi["in_stock"] = int(campi["in_stock"])
    if campi:
        set_ = ", ".join(f"{k}=?" for k in campi)
        con.execute(f"UPDATE books SET {set_} WHERE id=?", [*campi.values(), book_id])
    if tags is not None:
        _salva_tag(con, book_id, tags)
    return _espandi(con, riga(con.execute(f"{SELECT} WHERE b.id=?", (book_id,)).fetchone()), {"tags"})


@router.delete("/{book_id}", status_code=204, summary="Elimina un libro (serve la sandbox)")
def elimina(book_id: int, con: WriteDB) -> Response:
    o_404(con.execute("SELECT 1 FROM books WHERE id=?", (book_id,)).fetchone(), "Libro", book_id)
    if con.execute("SELECT 1 FROM order_items WHERE book_id=? LIMIT 1", (book_id,)).fetchone():
        raise ApiError(409, "book_in_orders", "Il libro compare in ordini esistenti: la chiave esterna impedisce di cancellarlo")
    con.execute("DELETE FROM books WHERE id=?", (book_id,))
    con.execute("DELETE FROM books_fts WHERE rowid=?", (book_id,))
    return Response(status_code=204)
