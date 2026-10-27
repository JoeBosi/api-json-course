"""Traduce il JSON di POST /query in SQL con allow-list di tabelle e campi.

I campi `attributes.x` diventano `json_extract(attributes, '$.x')`: così il lettore vede
come una query "strutturata" diventa SQL vero (la risposta include `meta.sql`).
"""
from __future__ import annotations

import re

from .errors import ApiError
from .schemas import Condition, Group, QueryIn

CAMPI = {
    "books": ["id", "title", "isbn", "author_id", "category_id", "price", "pages", "published_year",
              "language", "in_stock", "attributes", "created_at"],
    "authors": ["id", "name", "country", "born_year"],
    "customers": ["id", "name", "email", "city", "created_at"],
    "orders": ["id", "customer_id", "status", "shipping_address", "total", "created_at"],
    "reviews": ["id", "book_id", "customer_id", "rating", "comment", "created_at"],
}
JSON_COLS = {"books": "attributes", "orders": "shipping_address"}
_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _colonna(tabella: str, campo: str) -> str:
    base, _, sotto = campo.partition(".")
    if base not in CAMPI[tabella]:
        raise ApiError(400, "unknown_field", f"Campo '{campo}' non ammesso per {tabella}", {"allowed": CAMPI[tabella]})
    if sotto:
        if base != JSON_COLS.get(tabella):
            raise ApiError(400, "unknown_field", f"'{base}' non è una colonna JSON: niente sottocampi")
        parti = sotto.split(".")
        if not all(_KEY.match(p) for p in parti):
            raise ApiError(400, "unknown_field", f"Percorso JSON non valido: {campo}")
        return f"json_extract({base}, '$.{sotto}')"
    return base


def _cond(tabella: str, c: Condition, params: list) -> str:
    col = _colonna(tabella, c.field)
    op = c.op
    if op == "is_null":
        return f"{col} IS {'NULL' if c.value in (None, True) else 'NOT NULL'}"
    if op == "in":
        if not isinstance(c.value, list) or not c.value or len(c.value) > 100:
            raise ApiError(400, "bad_condition", "'in' richiede una lista (1-100 valori)")
        params.extend(c.value)
        return f"{col} IN ({','.join('?' * len(c.value))})"
    simboli = {"eq": "=", "ne": "!=", "lt": "<", "lte": "<=", "gt": ">", "gte": ">=", "like": "LIKE"}
    if isinstance(c.value, (dict, list)):
        raise ApiError(400, "bad_condition", f"Valore non scalare per '{c.field}'")
    params.append(1 if c.value is True else 0 if c.value is False else c.value)
    return f"{col} {simboli[op]} ?"


def _where(tabella: str, nodo, params: list, profondita=0) -> str:
    if profondita > 5:
        raise ApiError(400, "bad_condition", "Filtro troppo annidato (max 5 livelli)")
    if isinstance(nodo, Condition):
        return _cond(tabella, nodo, params)
    if nodo.and_ and nodo.or_:
        raise ApiError(400, "bad_condition", "Un gruppo ha o 'and' o 'or', non entrambi")
    figli, glue = (nodo.and_, " AND ") if nodo.and_ else (nodo.or_, " OR ")
    if not figli:
        raise ApiError(400, "bad_condition", "Gruppo vuoto")
    return "(" + glue.join(_where(tabella, f, params, profondita + 1) for f in figli) + ")"


def costruisci(q: QueryIn) -> tuple[str, list]:
    t = q.from_
    params: list = []
    select = ", ".join(_colonna(t, c) + (f' AS "{c}"' if "." in c else "") for c in q.select) if q.select else "*"
    sql = f"SELECT {select} FROM {t}"
    if q.where is not None:
        sql += " WHERE " + _where(t, q.where, params)
    if q.order_by:
        parti = []
        for o in q.order_by:
            desc = o.startswith("-")
            parti.append(_colonna(t, o.lstrip("-+")) + (" DESC" if desc else " ASC"))
        sql += " ORDER BY " + ", ".join(parti)
    sql += f" LIMIT {q.limit} OFFSET {q.offset}"
    return sql, params
