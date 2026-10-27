"""Test end-to-end dell'API di prova (pytest + TestClient)."""


def test_indice_e_health(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"
    assert "books" in client.get("/api/v1/").json()["links"]


def test_schema_espone_pk_e_fk(client):
    s = client.get("/api/v1/schema").json()["tables"]
    assert s["books"]["primary_key"] == ["id"]
    fk = {f["column"]: f["references"]["table"] for f in s["books"]["foreign_keys"]}
    assert fk == {"author_id": "authors", "category_id": "categories"}
    assert s["order_items"]["rows"] > 100


def test_lista_filtri_ordinamento_paginazione(client):
    r = client.get("/api/v1/books", params={"sort": "-price", "limit": 5, "page": 2, "min_price": 10}).json()
    assert r["meta"]["limit"] == 5 and r["meta"]["page"] == 2
    prezzi = [b["price"] for b in r["items"]]
    assert prezzi == sorted(prezzi, reverse=True) and all(p >= 10 for p in prezzi)
    assert "page=3" in r["links"]["next"] and "page=1" in r["links"]["prev"]
    assert client.get("/api/v1/books", params={"sort": "boh"}).status_code == 400
    assert client.get("/api/v1/books", params={"limit": 500}).status_code == 422


def test_filtro_json_e_categoria_ricorsiva(client):
    r = client.get("/api/v1/books", params={"format": "tascabile", "limit": 100}).json()
    assert r["meta"]["total"] > 0 and all(b["attributes"]["format"] == "tascabile" for b in r["items"])
    narrativa = client.get("/api/v1/books", params={"category": "narrativa", "limit": 1}).json()["meta"]["total"]
    gialli = client.get("/api/v1/books", params={"category": "gialli", "limit": 1}).json()["meta"]["total"]
    assert narrativa > gialli > 0


def test_expand_e_relazioni(client):
    b = client.get("/api/v1/books/1", params={"expand": "author,category,tags,reviews"}).json()
    assert b["author"]["id"] == b["author_id"] and b["category"]["id"] == b["category_id"]
    assert isinstance(b["tags"], list) and isinstance(b["reviews"], list)
    o = client.get("/api/v1/orders/1", params={"expand": "items.book,customer"}).json()
    assert o["customer"]["id"] == o["customer_id"]
    assert o["items"][0]["book"]["author_name"]
    assert client.get("/api/v1/authors/1/books").json()["meta"]["total"] >= 1
    assert client.get("/api/v1/categories", params={"tree": "true"}).json()["items"][0]["children"]
    assert client.get("/api/v1/books/1", params={"expand": "boh"}).status_code == 400


def test_errori_hanno_formato_unico(client):
    for url, code in [("/api/v1/books/9999", 404), ("/api/nope", 404), ("/api/v1/books/abc", 422)]:
        r = client.get(url)
        assert r.status_code == code and set(r.json()["error"]) >= {"code", "message"}


def test_etag_e_304(client):
    r = client.get("/api/v1/books/2")
    et = r.headers["etag"]
    assert client.get("/api/v1/books/2", headers={"If-None-Match": et}).status_code == 304


def test_scritture_senza_token_negate(client):
    r = client.post("/api/v1/books", json={"title": "x", "author_id": 1, "category_id": 1, "price": 1})
    assert r.status_code == 401 and r.json()["error"]["code"] == "sandbox_required"
    assert client.get("/api/v1/sandbox/me").status_code == 401
    assert client.get("/api/v1/sandbox/me", headers={"Authorization": "Bearer sb_finto"}).status_code == 401


def test_crud_in_sandbox(client, sandbox):
    r = client.post("/api/v1/books", json={"title": "Prova", "author_id": 1, "category_id": 2, "price": 9.5, "tags": ["novità"]}, headers=sandbox)
    assert r.status_code == 201 and r.headers["location"].endswith(f"/api/v1/books/{r.json()['id']}")
    bid = r.json()["id"]
    assert client.patch(f"/api/v1/books/{bid}", json={"price": 12}, headers=sandbox).json()["price"] == 12
    assert client.put(f"/api/v1/books/{bid}", json={"title": "Prova 2", "author_id": 2, "category_id": 2, "price": 3}, headers=sandbox).json()["title"] == "Prova 2"
    assert client.post("/api/v1/books", json={"title": "x", "author_id": 999, "category_id": 1, "price": 1}, headers=sandbox).json()["error"]["code"] == "unknown_author"
    # il dataset pubblico non cambia
    assert client.get("/api/v1/books", params={"q": "Prova 2"}).json()["meta"]["total"] == 0
    assert client.get("/api/v1/books", params={"q": "Prova 2"}, headers=sandbox).json()["meta"]["total"] == 1
    assert client.delete(f"/api/v1/books/{bid}", headers=sandbox).status_code == 204
    assert client.get(f"/api/v1/books/{bid}", headers=sandbox).status_code == 404


def test_ordine_transazione_e_stati(client, sandbox):
    body = {"customer_id": 1, "items": [{"book_id": 1, "quantity": 2}, {"book_id": 2, "quantity": 1}],
            "shipping_address": {"street": "Via Roma 1", "city": "Milano", "zip": "20100"}}
    r = client.post("/api/v1/orders", json=body, headers=sandbox)
    assert r.status_code == 201 and len(r.json()["items"]) == 2 and r.json()["status"] == "pending"
    oid = r.json()["id"]
    assert client.patch(f"/api/v1/orders/{oid}", json={"status": "shipped"}, headers=sandbox).status_code == 409
    assert client.patch(f"/api/v1/orders/{oid}", json={"status": "paid"}, headers=sandbox).json()["status"] == "paid"
    assert client.delete("/api/v1/books/1", headers=sandbox).status_code == 409   # FK: libro in un ordine
    assert client.delete(f"/api/v1/orders/{oid}", headers=sandbox).status_code == 204
    bad = dict(body, shipping_address={"street": "x", "city": "y", "zip": "1"})
    assert client.post("/api/v1/orders", json=bad, headers=sandbox).status_code == 422


def test_sandbox_reset(client, sandbox):
    client.post("/api/v1/books/1/reviews", json={"customer_id": 1, "rating": 5}, headers=sandbox)
    prima = client.get("/api/v1/books/1/reviews", headers=sandbox).json()["meta"]["total"]
    client.post("/api/v1/sandbox/reset", headers=sandbox)
    assert client.get("/api/v1/books/1/reviews", headers=sandbox).json()["meta"]["total"] == prima - 1


def test_ricerca_stats_query_sql_export(client):
    s = client.get("/api/v1/search", params={"q": "trieste"}).json()
    assert s["items"] and "<b>" in (s["items"][0]["snippet"] or "")
    assert client.get("/api/v1/stats").json()["totals"]["books"] == 80
    assert client.get("/api/v1/stats/sales", params={"group_by": "month"}).json()["items"]
    q = client.post("/api/v1/query", json={"from": "books", "select": ["id", "title", "attributes.format"],
                                           "where": {"or": [{"field": "price", "op": "lt", "value": 8}, {"field": "attributes.ebook", "op": "eq", "value": True}]},
                                           "order_by": ["-price"], "limit": 5}).json()
    assert q["meta"]["sql"].startswith("SELECT") and "json_extract" in q["meta"]["sql"] and q["items"]
    assert client.post("/api/v1/query", json={"from": "books", "where": {"field": "password", "op": "eq", "value": 1}}).status_code == 400
    ok = client.post("/api/v1/sql", json={"sql": "SELECT c.name, COUNT(*) AS n FROM books b JOIN categories c ON c.id=b.category_id GROUP BY c.id"}).json()
    assert ok["columns"] == ["name", "n"] and ok["row_count"] > 0
    for cattivo in ["DELETE FROM books", "DROP TABLE books", "ATTACH DATABASE 'x' AS y", "PRAGMA table_info(books)", "SELECT * FROM sqlite_master"]:
        assert client.post("/api/v1/sql", json={"sql": cattivo}).status_code in (403, 400), cattivo
    assert client.post("/api/v1/sql", json={"sql": "SELECT * FROM order_items"}).json()["truncated"] is True
    assert client.post("/api/v1/sql", json={"sql": "SELECT 1", "explain": True}).json()["columns"][0] == "id"
    csv = client.get("/api/v1/export/books.csv")
    assert csv.headers["content-type"].startswith("text/csv") and csv.text.count("\n") == 81
    nd = client.get("/api/v1/export/books.ndjson").text.strip().split("\n")
    assert len(nd) == 80


def test_echo(client):
    r = client.post("/api/v1/echo?x=1", json={"a": [1, 2]}, headers={"X-Demo": "ciao"}).json()
    assert r["json"] == {"a": [1, 2]} and r["query"] == {"x": "1"} and r["headers"]["x-demo"] == "ciao"


def test_sql_cte_ricorsiva_permessa(client):
    sql = ("WITH RECURSIVE sub(id, name, depth) AS (SELECT id, name, 0 FROM categories WHERE parent_id IS NULL "
           "UNION ALL SELECT c.id, c.name, sub.depth+1 FROM categories c JOIN sub ON c.parent_id = sub.id) "
           "SELECT name, depth FROM sub ORDER BY depth, name")
    r = client.post("/api/v1/sql", json={"sql": sql})
    assert r.status_code == 200 and r.json()["row_count"] == 10

def test_swagger_servito_dal_sito_non_da_cdn(client):
    """La pagina /api/docs non deve contattare CDN esterne (vedi la pagina Privacy)."""
    r = client.get("/api/docs")
    assert r.status_code == 200
    html = r.text
    assert "/swagger/swagger-ui-bundle.js" in html
    assert "/swagger/swagger-ui.css" in html
    for terzo in ("jsdelivr", "unpkg", "cdnjs", "cloudflare"):
        assert terzo not in html.lower(), f"la pagina carica ancora da {terzo}"

