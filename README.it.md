[English](README.md) · **Italiano**

# Corso JSON & API — da 0 a esperto

Corso gratuito su **JSON** (Python e TypeScript/JavaScript) e sull'**interrogazione di database
tramite API HTTP**, insieme al **server API di prova** su cui girano tutti gli esempi.

**Sito:** https://corso-api-json.giuseppebosi.com
(API di prova su `/api/v1`, documentazione interattiva su `/api/docs`; quando nessuno la usa è
spenta e si accende dalla pagina `/api-attiva/`)

## Cosa contiene

- **Sezione 1 — JSON** (15 capitoli): sintassi e tipi, trappole, `json` in Python, `JSON.parse` /
  `JSON.stringify`, tipi e validazione in TypeScript (zod), pydantic, JSON Schema, dati annidati,
  file grandi in streaming, performance, JSON nei database.
- **Sezione 2 — Database tramite API** (17 capitoli): HTTP e REST, curl spiegato opzione per
  opzione, filtri e paginazione, relazioni e chiavi esterne, scritture in sandbox, errori e status
  code, autenticazione, ricerca full-text, aggregazioni, SQL con JOIN via API, transazioni, cache e
  rate limit, sicurezza, client robusti.
- Ogni esempio è in **curl, Python e TypeScript affiancati** e si esegue dalla pagina contro
  l'API di prova. Con una **sandbox** personale (copia privata del database) si può anche scrivere.
- Le pagine si possono **ascoltare** con la sintesi vocale del browser, con il paragrafo evidenziato.
- Per motori di ricerca e assistenti IA: [`/llms.txt`](https://corso-api-json.giuseppebosi.com/llms.txt),
  [`/llms-full.txt`](https://corso-api-json.giuseppebosi.com/llms-full.txt),
  [`/sitemap.xml`](https://corso-api-json.giuseppebosi.com/sitemap.xml).

Il dataset ("Libreria Aurora", una libreria immaginaria) è inventato: nessun dato di persone reali.

## Farlo girare in locale

Servono Node 22+ e [uv](https://docs.astral.sh/uv/) (Python 3.12+).

```bash
./bootstrap.sh                                   # skill locali e controllo degli strumenti
cd site && npm install && npm run build && cd .. # sito statico in site/dist
cd api && uv run pytest -q                       # test dell'API
api/.venv/bin/python deploy/imposta-password-api.py   # password che accende l'API (in .env va solo l'hash scrypt)
cd api && uv run fastapi dev app/main.py --port 8795  # sito + API su http://127.0.0.1:8795
```

Poi apri http://127.0.0.1:8795/api-attiva/ e accendi l'API con la password.
Per lavorare sul sito con il ricaricamento automatico: `cd site && npm run dev`, con
`PUBLIC_API_BASE=http://127.0.0.1:8795` in `site/.env`.

## Struttura

```
site/     Astro + Starlight: capitoli in src/content/docs/{json,db-api,riferimento}, componenti in src/components
api/      FastAPI + SQLite: router in app/routers, dataset in app/seed.py, interruttore in app/interruttore.py, test in tests/
audio/    estrazione del testo per la lettura ad alta voce (estrai.py, pronuncia.json, manifest.json)
deploy/   unit systemd (utente dedicato senza privilegi), blocco Caddy, script di installazione e pubblicazione
docs/     guida alla scrittura dei capitoli, piano audio, note di ricerca
.claude/  skill locali per Claude Code, usate per costruire il corso
```

## Licenza

- **Testi** (capitoli, spiegazioni, esercizi): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.it) — file `LICENSE-CONTENUTI`.
- **Codice** (esempi, server di prova, sito): [MIT](LICENSE).

## Autore

**Giuseppe Bosi** — https://www.giuseppebosi.com · [LinkedIn](https://www.linkedin.com/in/giuseppebosi)

Il progetto non è affiliato né approvato dalle organizzazioni che curano gli strumenti di cui
parla (Python, TypeScript, Node.js, curl, SQLite, FastAPI, Astro e altri); nomi e marchi
appartengono ai rispettivi titolari.
