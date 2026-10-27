"""Dataset di esempio: la libreria online "Libreria Aurora" (dati inventati, deterministici).

Serve al corso: relazioni 1-N (autore -> libri, cliente -> ordini), N-N (libri <-> tag,
ordini <-> libri), gerarchia (categorie annidate), una colonna JSON (`books.attributes`) e
un indice full-text (FTS5) sui libri. `random.seed(42)`: rigenerare produce sempre gli stessi dati.
"""
from __future__ import annotations

import json
import random
import sqlite3
from datetime import datetime, timedelta

SCHEMA = """
CREATE TABLE authors (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL, born_year INTEGER,
  bio TEXT
);
CREATE TABLE categories (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE,
  parent_id INTEGER REFERENCES categories(id)
);
CREATE TABLE books (
  id INTEGER PRIMARY KEY, title TEXT NOT NULL, isbn TEXT NOT NULL UNIQUE,
  author_id INTEGER NOT NULL REFERENCES authors(id),
  category_id INTEGER NOT NULL REFERENCES categories(id),
  price REAL NOT NULL CHECK(price >= 0), pages INTEGER, published_year INTEGER,
  language TEXT NOT NULL DEFAULT 'it', in_stock INTEGER NOT NULL DEFAULT 1,
  attributes TEXT NOT NULL DEFAULT '{}',   -- JSON: formato, copertina, premi, ecc.
  created_at TEXT NOT NULL
);
CREATE TABLE tags (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE book_tags (
  book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (book_id, tag_id)
);
CREATE TABLE customers (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, city TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE orders (
  id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id),
  status TEXT NOT NULL CHECK(status IN ('pending','paid','shipped','delivered','cancelled')),
  shipping_address TEXT NOT NULL,         -- JSON: {street, city, zip, country}
  total REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE order_items (
  id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  book_id INTEGER NOT NULL REFERENCES books(id), quantity INTEGER NOT NULL CHECK(quantity > 0),
  unit_price REAL NOT NULL
);
CREATE TABLE reviews (
  id INTEGER PRIMARY KEY, book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), comment TEXT, created_at TEXT NOT NULL
);
CREATE INDEX idx_books_author ON books(author_id);
CREATE INDEX idx_books_category ON books(category_id);
CREATE INDEX idx_books_price ON books(price);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE VIRTUAL TABLE books_fts USING fts5(title, description);
CREATE VIEW book_stats AS
  SELECT b.id AS book_id, COUNT(r.id) AS reviews_count, ROUND(AVG(r.rating), 2) AS avg_rating
  FROM books b LEFT JOIN reviews r ON r.book_id = b.id GROUP BY b.id;
"""

AUTORI = [
    ("Elena Marchetti", "IT", 1971), ("Marco Ferrante", "IT", 1965), ("Giulia Serra", "IT", 1984),
    ("Tomás Aldana", "ES", 1958), ("Ingrid Halvorsen", "NO", 1979), ("Samuel Okafor", "NG", 1988),
    ("Chiara Bellini", "IT", 1992), ("Lorenzo Vitali", "IT", 1949), ("Amélie Roux", "FR", 1975),
    ("Hiro Tanaka", "JP", 1968), ("Beatrice Colombo", "IT", 1980), ("Davide Moretti", "IT", 1977),
    ("Nadia Karim", "MA", 1986), ("Pietro Galli", "IT", 1955), ("Sofia Lindqvist", "SE", 1990),
    ("Riccardo Fontana", "IT", 1963), ("Anna Kowalski", "PL", 1982), ("Matteo Rinaldi", "IT", 1995),
    ("Laura Esposito", "IT", 1970), ("Kwame Mensah", "GH", 1983),
]

CATEGORIE = [  # (slug, nome, parent_slug)
    ("narrativa", "Narrativa", None), ("gialli", "Gialli e thriller", "narrativa"),
    ("fantascienza", "Fantascienza", "narrativa"), ("storici", "Romanzi storici", "narrativa"),
    ("saggistica", "Saggistica", None), ("storia", "Storia", "saggistica"),
    ("scienza", "Scienza e tecnologia", "saggistica"), ("cucina", "Cucina", None),
    ("informatica", "Informatica", "saggistica"), ("ragazzi", "Ragazzi", None),
]

TAG = ["bestseller", "novità", "premio", "classico", "illustrato", "serie", "esordio",
       "tascabile", "audiolibro", "tradotto"]

TITOLI = {
    "gialli": ["Il silenzio di {}", "L'ultimo treno per {}", "Delitto a {}", "La casa sul {}", "Nebbia su {}", "Tre giorni a {}"],
    "fantascienza": ["Le stelle di {}", "Orbita {}", "Il pianeta {}", "Oltre {}", "Codice {}", "I giardini di {}"],
    "storici": ["La contessa di {}", "1848: {}", "Le mura di {}", "Il mercante di {}", "Ritorno a {}"],
    "narrativa": ["Quello che resta di {}", "Le estati a {}", "Il giardino di {}", "Una vita a {}", "Le voci di {}"],
    "storia": ["Storia di {}", "{} e il Novecento", "La caduta di {}", "Vite di {}"],
    "scienza": ["Il cervello e {}", "L'universo in {}", "Numeri e {}", "La fisica di {}"],
    "cucina": ["La cucina di {}", "Pane e {}", "Le ricette di {}", "Dolci di {}"],
    "informatica": ["JSON e {}", "API per {}", "Python a {}", "TypeScript e {}", "Database di {}"],
    "ragazzi": ["Le avventure di {}", "Il drago di {}", "Un'estate a {}", "Il mistero di {}"],
    "saggistica": ["Pensare {}", "Il valore di {}", "Contro {}"],
}
LUOGHI = ["Trieste", "Montecarvo", "Valdera", "Sorano", "Ravello", "Porto Vecchio", "Lucignano",
          "Ferrara", "Alba", "Bassano", "Mantova", "Levanto", "Norcia", "Orvieto", "Camogli",
          "Bergamo", "Lecce", "Matera", "Asti", "Aosta", "Andromeda", "Kepler-7", "Tarvisio",
          "Ustica", "Cividale", "Volterra", "Brisighella", "Vieste", "Otranto", "Sestri"]
FORMATI = ["brossura", "rilegato", "tascabile"]
CITTA = ["Milano", "Roma", "Torino", "Bologna", "Firenze", "Napoli", "Genova", "Verona", "Padova", "Bari"]
NOMI = ["Alessandro", "Francesca", "Giovanni", "Martina", "Luca", "Sara", "Andrea", "Valentina",
        "Federico", "Silvia", "Simone", "Elisa", "Nicola", "Roberta", "Fabio", "Claudia"]
COGNOMI = ["Rossi", "Russo", "Bianchi", "Romano", "Gallo", "Costa", "Conti", "Greco", "Bruno",
           "Ricci", "Marino", "Longo", "Leone", "Ferri", "Sala", "Villa"]
COMMENTI = {5: ["Bellissimo, letto in due giorni.", "Da regalare a tutti.", "Il migliore dell'autore."],
            4: ["Molto buono, qualche lungaggine.", "Consigliato.", "Scritto bene, finale un po' rapido."],
            3: ["Nella media.", "Carino ma dimenticabile.", "Mi aspettavo di più."],
            2: ["Non mi ha convinto.", "Trama confusa."], 1: ["Abbandonato a metà.", "Non fa per me."]}


def _iso(d: datetime) -> str:
    return d.replace(microsecond=0).isoformat() + "Z"


def popola(con: sqlite3.Connection) -> None:
    rnd = random.Random(42)
    base = datetime(2024, 1, 1)

    for i, (n, c, y) in enumerate(AUTORI, 1):
        con.execute("INSERT INTO authors VALUES (?,?,?,?,?)", (i, n, c, y, f"{n} è nata/o nel {y}. Scrive dal {y + 25}."))

    ids = {}
    for i, (slug, nome, parent) in enumerate(CATEGORIE, 1):
        ids[slug] = i
        con.execute("INSERT INTO categories VALUES (?,?,?,?)", (i, nome, slug, ids.get(parent)))

    for i, t in enumerate(TAG, 1):
        con.execute("INSERT INTO tags VALUES (?,?)", (i, t))

    # 80 libri, titoli unici
    book_id, usati, cat_slugs = 0, set(), [c[0] for c in CATEGORIE]
    fts = []
    while book_id < 80:
        slug = rnd.choice(cat_slugs)
        titolo = rnd.choice(TITOLI[slug]).format(rnd.choice(LUOGHI))
        if titolo in usati:
            continue
        usati.add(titolo)
        book_id += 1
        anno = rnd.randint(1985, 2026)
        attrs = {"format": rnd.choice(FORMATI), "cover": rnd.choice(["morbida", "rigida"]),
                 "awards": rnd.sample(["Strega", "Campiello", "Bancarella", "Viareggio"], rnd.choice([0, 0, 0, 1, 2])),
                 "dimensions_cm": {"w": rnd.choice([12, 14, 15]), "h": rnd.choice([19, 21, 23])},
                 "ebook": rnd.random() < 0.6}
        if slug == "informatica":
            attrs["edition"] = rnd.randint(1, 4)
        con.execute(
            "INSERT INTO books VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (book_id, titolo, f"978-88-{rnd.randint(10000, 99999)}-{book_id:03d}-{rnd.randint(0, 9)}",
             rnd.randint(1, len(AUTORI)), ids[slug], round(rnd.uniform(6.9, 34.9), 2),
             rnd.randint(90, 720), anno, rnd.choice(["it", "it", "it", "en", "es"]),
             1 if rnd.random() < 0.85 else 0, json.dumps(attrs, ensure_ascii=False),
             _iso(base + timedelta(days=rnd.randint(0, 600)))))
        for tag_id in rnd.sample(range(1, len(TAG) + 1), rnd.randint(0, 3)):
            con.execute("INSERT INTO book_tags VALUES (?,?)", (book_id, tag_id))
        fts.append((book_id, titolo, f"{titolo}. Un libro di {CATEGORIE[ids[slug] - 1][1].lower()} ambientato tra {rnd.choice(LUOGHI)} e {rnd.choice(LUOGHI)}."))
    con.executemany("INSERT INTO books_fts(rowid, title, description) VALUES (?,?,?)", fts)

    for i in range(1, 41):
        nome = f"{rnd.choice(NOMI)} {rnd.choice(COGNOMI)}"
        con.execute("INSERT INTO customers VALUES (?,?,?,?,?)",
                    (i, nome, f"{nome.lower().replace(' ', '.')}{i}@example.com", rnd.choice(CITTA),
                     _iso(base + timedelta(days=rnd.randint(0, 500)))))

    stati = ["pending", "paid", "paid", "shipped", "delivered", "delivered", "delivered", "cancelled"]
    item_id = 0
    for oid in range(1, 121):
        cid = rnd.randint(1, 40)
        citta = con.execute("SELECT city FROM customers WHERE id=?", (cid,)).fetchone()[0]
        quando = base + timedelta(days=rnd.randint(30, 620), hours=rnd.randint(8, 22))
        indirizzo = {"street": f"Via {rnd.choice(LUOGHI)} {rnd.randint(1, 120)}", "city": citta,
                     "zip": f"{rnd.randint(10000, 98000):05d}", "country": "IT"}
        totale = 0.0
        righe = []
        for bid in rnd.sample(range(1, 81), rnd.randint(1, 4)):
            prezzo = con.execute("SELECT price FROM books WHERE id=?", (bid,)).fetchone()[0]
            q = rnd.choice([1, 1, 1, 2, 3])
            righe.append((bid, q, prezzo))
            totale += q * prezzo
        con.execute("INSERT INTO orders VALUES (?,?,?,?,?,?)",
                    (oid, cid, rnd.choice(stati), json.dumps(indirizzo, ensure_ascii=False), round(totale, 2), _iso(quando)))
        for bid, q, prezzo in righe:
            item_id += 1
            con.execute("INSERT INTO order_items VALUES (?,?,?,?,?)", (item_id, oid, bid, q, prezzo))

    rid = 0
    for bid in range(1, 81):
        for cid in rnd.sample(range(1, 41), rnd.randint(0, 6)):
            rid += 1
            voto = rnd.choices([1, 2, 3, 4, 5], weights=[1, 2, 4, 8, 9])[0]
            con.execute("INSERT INTO reviews VALUES (?,?,?,?,?,?)",
                        (rid, bid, cid, voto, rnd.choice(COMMENTI[voto]), _iso(base + timedelta(days=rnd.randint(100, 640)))))
