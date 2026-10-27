"""Autori, categorie (albero), clienti, ordini (con righe e libri), recensioni: le relazioni
tra tabelle tramite chiavi primarie ed esterne, esposte come risorse annidate."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response

from ..db import riga, righe
from ..deps import PageDep, ReadDB, WriteDB, o_404, pagina
from ..errors import ApiError
from ..schemas import CustomerIn, OrderIn, OrderPatch, ReviewIn

router = APIRouter(tags=["relations"])


def _ora() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# --- autori ------------------------------------------------------------------------------

@router.get("/authors", summary="Elenco autori (con numero di libri)")
def autori(con: ReadDB, p: PageDep, request: Request, country: str | None = None) -> dict:
    w, params = ("WHERE a.country = ?", [country]) if country else ("", [])
    total = con.execute(f"SELECT COUNT(*) FROM authors a {w}", params).fetchone()[0]
    rows = righe(con.execute(
        f"SELECT a.*, COUNT(b.id) AS books_count FROM authors a LEFT JOIN books b ON b.author_id=a.id {w} "
        f"GROUP BY a.id ORDER BY a.name LIMIT ? OFFSET ?", [*params, p.limit, p.offset]))
    return pagina(rows, total, p, request)


@router.get("/authors/{author_id}", summary="Un autore")
def autore(author_id: int, con: ReadDB) -> dict:
    return o_404(riga(con.execute("SELECT * FROM authors WHERE id=?", (author_id,)).fetchone()), "Autore", author_id)


@router.get("/authors/{author_id}/books", summary="I libri di un autore (risorsa annidata: FK books.author_id)")
def libri_autore(author_id: int, con: ReadDB, p: PageDep, request: Request) -> dict:
    o_404(con.execute("SELECT 1 FROM authors WHERE id=?", (author_id,)).fetchone(), "Autore", author_id)
    total = con.execute("SELECT COUNT(*) FROM books WHERE author_id=?", (author_id,)).fetchone()[0]
    rows = righe(con.execute("SELECT * FROM books WHERE author_id=? ORDER BY published_year LIMIT ? OFFSET ?",
                             (author_id, p.limit, p.offset)))
    return pagina(rows, total, p, request)


# --- categorie ---------------------------------------------------------------------------

@router.get("/categories", summary="Categorie: piatte o ad albero (?tree=true)")
def categorie(con: ReadDB, tree: bool = False) -> dict:
    rows = righe(con.execute(
        "SELECT c.*, COUNT(b.id) AS books_count FROM categories c LEFT JOIN books b ON b.category_id=c.id GROUP BY c.id ORDER BY c.id"))
    if not tree:
        return {"items": rows}
    per_id = {r["id"]: {**r, "children": []} for r in rows}
    radici = []
    for r in per_id.values():
        (per_id[r["parent_id"]]["children"] if r["parent_id"] else radici).append(r)
    return {"items": radici}


@router.get("/categories/{slug}/books", summary="Libri di una categoria e delle sue sottocategorie (CTE ricorsiva)")
def libri_categoria(slug: str, con: ReadDB, p: PageDep, request: Request, deep: bool = True) -> dict:
    cat = o_404(riga(con.execute("SELECT * FROM categories WHERE slug=?", (slug,)).fetchone()), "Categoria", slug)
    if deep:
        sub = """WITH RECURSIVE sub(id) AS (SELECT ? UNION ALL SELECT c.id FROM categories c JOIN sub ON c.parent_id=sub.id)
                 SELECT id FROM sub"""
        w, params = f"category_id IN ({sub})", [cat["id"]]
    else:
        w, params = "category_id = ?", [cat["id"]]
    total = con.execute(f"SELECT COUNT(*) FROM books WHERE {w}", params).fetchone()[0]
    rows = righe(con.execute(f"SELECT * FROM books WHERE {w} ORDER BY title LIMIT ? OFFSET ?", [*params, p.limit, p.offset]))
    return {"category": cat, **pagina(rows, total, p, request)}


# --- clienti -----------------------------------------------------------------------------

@router.get("/customers", summary="Elenco clienti")
def clienti(con: ReadDB, p: PageDep, request: Request, city: str | None = None) -> dict:
    w, params = ("WHERE city = ?", [city]) if city else ("", [])
    total = con.execute(f"SELECT COUNT(*) FROM customers {w}", params).fetchone()[0]
    rows = righe(con.execute(f"SELECT * FROM customers {w} ORDER BY id LIMIT ? OFFSET ?", [*params, p.limit, p.offset]))
    return pagina(rows, total, p, request)


@router.get("/customers/{customer_id}", summary="Un cliente con il riepilogo dei suoi ordini")
def cliente(customer_id: int, con: ReadDB) -> dict:
    c = o_404(riga(con.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()), "Cliente", customer_id)
    c["orders_summary"] = riga(con.execute(
        "SELECT COUNT(*) AS orders_count, ROUND(COALESCE(SUM(total),0),2) AS total_spent, MAX(created_at) AS last_order_at "
        "FROM orders WHERE customer_id=? AND status != 'cancelled'", (customer_id,)).fetchone())
    return c


@router.post("/customers", status_code=201, summary="Crea un cliente (serve la sandbox)")
def crea_cliente(dati: CustomerIn, con: WriteDB) -> dict:
    if con.execute("SELECT 1 FROM customers WHERE email=?", (dati.email,)).fetchone():
        raise ApiError(409, "duplicate_email", f"Esiste già un cliente con email {dati.email}")
    cur = con.execute("INSERT INTO customers(name,email,city,created_at) VALUES (?,?,?,?)", (dati.name, dati.email, dati.city, _ora()))
    return riga(con.execute("SELECT * FROM customers WHERE id=?", (cur.lastrowid,)).fetchone())


@router.get("/customers/{customer_id}/orders", summary="Gli ordini di un cliente (FK orders.customer_id)")
def ordini_cliente(customer_id: int, con: ReadDB, p: PageDep, request: Request) -> dict:
    o_404(con.execute("SELECT 1 FROM customers WHERE id=?", (customer_id,)).fetchone(), "Cliente", customer_id)
    total = con.execute("SELECT COUNT(*) FROM orders WHERE customer_id=?", (customer_id,)).fetchone()[0]
    rows = righe(con.execute("SELECT * FROM orders WHERE customer_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                             (customer_id, p.limit, p.offset)))
    return pagina(rows, total, p, request)


# --- ordini ------------------------------------------------------------------------------

def _ordine_completo(con, order_id: int, expand: set[str]) -> dict:
    o = o_404(riga(con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()), "Ordine", order_id)
    if "customer" in expand:
        o["customer"] = riga(con.execute("SELECT * FROM customers WHERE id=?", (o["customer_id"],)).fetchone())
    if "items" in expand or "items.book" in expand:
        o["items"] = righe(con.execute("SELECT * FROM order_items WHERE order_id=? ORDER BY id", (order_id,)))
        if "items.book" in expand:   # tre tabelle: order_items -> books -> authors
            for it in o["items"]:
                it["book"] = riga(con.execute(
                    "SELECT b.id, b.title, b.price, b.author_id, a.name AS author_name FROM books b "
                    "JOIN authors a ON a.id=b.author_id WHERE b.id=?", (it["book_id"],)).fetchone())
    return o


@router.get("/orders", summary="Elenco ordini (filtri: status, customer_id, from, to)")
def ordini(con: ReadDB, p: PageDep, request: Request, status: str | None = None, customer_id: int | None = None,
           date_from: Annotated[str | None, Query(alias="from", description="ISO 8601, es. 2025-01-01")] = None,
           date_to: Annotated[str | None, Query(alias="to")] = None,
           sort: str = "-created_at") -> dict:
    where, params = ["1=1"], []
    if status:
        where.append("status=?"); params.append(status)
    if customer_id:
        where.append("customer_id=?"); params.append(customer_id)
    if date_from:
        where.append("created_at >= ?"); params.append(date_from)
    if date_to:
        where.append("created_at < ?"); params.append(date_to)
    campo = sort.lstrip("-")
    if campo not in {"created_at", "total", "id", "status"}:
        raise ApiError(400, "bad_sort", f"sort non valido: {sort}")
    order = f"{campo} {'DESC' if sort.startswith('-') else 'ASC'}"
    w = " AND ".join(where)
    total = con.execute(f"SELECT COUNT(*) FROM orders WHERE {w}", params).fetchone()[0]
    rows = righe(con.execute(f"SELECT * FROM orders WHERE {w} ORDER BY {order} LIMIT ? OFFSET ?", [*params, p.limit, p.offset]))
    return pagina(rows, total, p, request)


@router.get("/orders/{order_id}", summary="Un ordine; ?expand=items,items.book,customer per seguire le chiavi esterne")
def ordine(order_id: int, con: ReadDB, expand: Annotated[str | None, Query()] = "items") -> dict:
    voci = {e.strip() for e in (expand or "").split(",") if e.strip()}
    if voci - {"items", "items.book", "customer"}:
        raise ApiError(400, "bad_expand", "expand ammessi: items, items.book, customer")
    return _ordine_completo(con, order_id, voci)


@router.post("/orders", status_code=201, summary="Crea un ordine con le sue righe, in una transazione (serve la sandbox)")
def crea_ordine(dati: OrderIn, con: WriteDB, request: Request, response: Response) -> dict:
    o_404(con.execute("SELECT 1 FROM customers WHERE id=?", (dati.customer_id,)).fetchone(), "Cliente", dati.customer_id)
    righe_ordine, totale = [], 0.0
    for it in dati.items:
        b = con.execute("SELECT id, price, in_stock, title FROM books WHERE id=?", (it.book_id,)).fetchone()
        if b is None:
            raise ApiError(422, "unknown_book", f"book_id {it.book_id} non esiste")
        if not b["in_stock"]:
            raise ApiError(409, "out_of_stock", f"'{b['title']}' non è disponibile")
        righe_ordine.append((it.book_id, it.quantity, b["price"]))
        totale += it.quantity * b["price"]
    cur = con.execute("INSERT INTO orders(customer_id,status,shipping_address,total,created_at) VALUES (?,?,?,?,?)",
                      (dati.customer_id, "pending", dati.shipping_address.model_dump_json(), round(totale, 2), _ora()))
    oid = cur.lastrowid
    con.executemany("INSERT INTO order_items(order_id,book_id,quantity,unit_price) VALUES (?,?,?,?)",
                    [(oid, *r) for r in righe_ordine])
    response.headers["Location"] = f"{request.base_url}api/v1/orders/{oid}"
    return _ordine_completo(con, oid, {"items"})


TRANSIZIONI = {"pending": {"paid", "cancelled"}, "paid": {"shipped", "cancelled"}, "shipped": {"delivered"},
               "delivered": set(), "cancelled": set()}


@router.patch("/orders/{order_id}", summary="Cambia lo stato (macchina a stati: pending→paid→shipped→delivered)")
def stato_ordine(order_id: int, dati: OrderPatch, con: WriteDB) -> dict:
    o = o_404(riga(con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()), "Ordine", order_id)
    if dati.status not in TRANSIZIONI[o["status"]]:
        raise ApiError(409, "invalid_transition", f"Da '{o['status']}' non si può passare a '{dati.status}'",
                       {"allowed": sorted(TRANSIZIONI[o["status"]])})
    con.execute("UPDATE orders SET status=? WHERE id=?", (dati.status, order_id))
    return _ordine_completo(con, order_id, {"items"})


@router.delete("/orders/{order_id}", status_code=204, summary="Elimina un ordine e le sue righe (ON DELETE CASCADE)")
def elimina_ordine(order_id: int, con: WriteDB) -> Response:
    o_404(con.execute("SELECT 1 FROM orders WHERE id=?", (order_id,)).fetchone(), "Ordine", order_id)
    con.execute("DELETE FROM orders WHERE id=?", (order_id,))
    return Response(status_code=204)


# --- recensioni --------------------------------------------------------------------------

@router.get("/books/{book_id}/reviews", summary="Recensioni di un libro (JOIN con customers)")
def recensioni(book_id: int, con: ReadDB, p: PageDep, request: Request, min_rating: int | None = None) -> dict:
    o_404(con.execute("SELECT 1 FROM books WHERE id=?", (book_id,)).fetchone(), "Libro", book_id)
    w, params = ["r.book_id=?"], [book_id]
    if min_rating:
        w.append("r.rating >= ?"); params.append(min_rating)
    ww = " AND ".join(w)
    total = con.execute(f"SELECT COUNT(*) FROM reviews r WHERE {ww}", params).fetchone()[0]
    rows = righe(con.execute(
        f"SELECT r.*, c.name AS customer_name, c.city AS customer_city FROM reviews r JOIN customers c ON c.id=r.customer_id "
        f"WHERE {ww} ORDER BY r.created_at DESC LIMIT ? OFFSET ?", [*params, p.limit, p.offset]))
    return pagina(rows, total, p, request)


@router.post("/books/{book_id}/reviews", status_code=201, summary="Aggiunge una recensione (serve la sandbox)")
def crea_recensione(book_id: int, dati: ReviewIn, con: WriteDB) -> dict:
    o_404(con.execute("SELECT 1 FROM books WHERE id=?", (book_id,)).fetchone(), "Libro", book_id)
    o_404(con.execute("SELECT 1 FROM customers WHERE id=?", (dati.customer_id,)).fetchone(), "Cliente", dati.customer_id)
    cur = con.execute("INSERT INTO reviews(book_id,customer_id,rating,comment,created_at) VALUES (?,?,?,?,?)",
                      (book_id, dati.customer_id, dati.rating, dati.comment, _ora()))
    return riga(con.execute("SELECT * FROM reviews WHERE id=?", (cur.lastrowid,)).fetchone())


@router.delete("/reviews/{review_id}", status_code=204, summary="Elimina una recensione (serve la sandbox)")
def elimina_recensione(review_id: int, con: WriteDB) -> Response:
    o_404(con.execute("SELECT 1 FROM reviews WHERE id=?", (review_id,)).fetchone(), "Recensione", review_id)
    con.execute("DELETE FROM reviews WHERE id=?", (review_id,))
    return Response(status_code=204)
