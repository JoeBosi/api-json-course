**English** · [Italiano](README.it.md)

# JSON & API Course — from zero to expert

A free, Italian-language course on **JSON** (Python and TypeScript/JavaScript) and on **querying
databases through HTTP APIs**, together with the **live test API** every example runs against.

**Live demo:** https://corso-api-json.giuseppebosi.com
(the test API is at `/api/v1`, interactive docs at `/api/docs`; it sleeps when unused and is
switched on from the `/api-attiva/` page)

## What it does

- **Section 1 — JSON** (15 chapters): syntax and types, pitfalls, `json` in Python, `JSON.parse` /
  `JSON.stringify`, TypeScript types and validation (zod), pydantic, JSON Schema, nested data,
  streaming large files, performance, JSON in databases.
- **Section 2 — Databases through APIs** (17 chapters): HTTP and REST, curl explained option by
  option, filtering and pagination, relations and foreign keys, writes in a private sandbox,
  errors and status codes, authentication, full-text search, aggregations, SQL with JOINs over
  the API, transactions, caching and rate limits, security, robust clients.
- Every example is shown in **curl, Python and TypeScript side by side** and can be run from the
  page against the test API. A personal **sandbox** (a private copy of the database) lets readers
  create, update and delete data without affecting anyone else.
- Pages can be **read aloud** with the browser's speech synthesis, highlighting the current
  paragraph.
- Machine-readable entry points: [`/llms.txt`](https://corso-api-json.giuseppebosi.com/llms.txt),
  [`/llms-full.txt`](https://corso-api-json.giuseppebosi.com/llms-full.txt),
  [`/sitemap.xml`](https://corso-api-json.giuseppebosi.com/sitemap.xml).

The dataset ("Libreria Aurora", a fictional bookshop) is entirely made up: no real people's data.

## Run it locally

Requirements: Node 22+, [uv](https://docs.astral.sh/uv/) (Python 3.12+).

```bash
./bootstrap.sh                                   # restore local agent skills, check the toolchain
cd site && npm install && npm run build && cd .. # static site into site/dist
cd api && uv run pytest -q                       # API tests
api/.venv/bin/python deploy/imposta-password-api.py   # choose the password that switches the API on (only a scrypt hash is stored in .env)
cd api && uv run fastapi dev app/main.py --port 8795  # site + API on http://127.0.0.1:8795
```

Then open http://127.0.0.1:8795/api-attiva/ and switch the API on with your password.
For live-reload work on the site, run `cd site && npm run dev` with `PUBLIC_API_BASE=http://127.0.0.1:8795`
in `site/.env`.

## Project layout

```
site/     Astro + Starlight: chapters in src/content/docs/{json,db-api,riferimento}, components in src/components
api/      FastAPI + SQLite: routers in app/routers, dataset in app/seed.py, on/off switch in app/interruttore.py, tests in tests/
audio/    text extraction for the read-aloud player (estrai.py, pronuncia.json, manifest.json)
deploy/   systemd unit (dedicated unprivileged user, hardened), Caddy block, install and publish scripts
docs/     chapter-writing guide, audio plan, research notes
.claude/  local skills for Claude Code, used while building the course
```

Security notes: the SQL endpoint is read-only (SQLite authorizer, `mode=ro`, time and row limits);
writes only happen in per-reader sandboxes that expire; requests are rate-limited per IP; the
service runs as a dedicated system user with an empty capability set.

## License

- **Texts** (chapters, explanations, exercises): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — see `LICENSE-CONTENUTI`.
- **Code** (examples, test server, site): [MIT](LICENSE).

## Author

**Giuseppe Bosi** — https://www.giuseppebosi.com · [LinkedIn](https://www.linkedin.com/in/giuseppebosi)

This project is not affiliated with or endorsed by the organisations behind the tools it
covers (Python, TypeScript, Node.js, curl, SQLite, FastAPI, Astro and others); their names and
trademarks belong to their respective owners.
