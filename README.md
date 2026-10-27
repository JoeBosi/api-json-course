# Corso JSON & API — da 0 a esperto

Sito del corso + server API di prova. Online: https://corso-api-json.giuseppebosi.com

- **Sezione 1** — JSON in Python e TypeScript/JavaScript (15 capitoli).
- **Sezione 2** — Interrogare database tramite API, da un GET semplice a JOIN su più tabelle (17 capitoli).
- Ogni esempio è mostrato in **curl (spiegato opzione per opzione)**, **Python** e **TypeScript**, e si può
  eseguire dalla pagina contro il server di prova. Con una **sandbox** personale si può anche scrivere.
- Ogni capitolo si può **ascoltare**: voce neurale (Piper, generata in build) con paragrafo evidenziato e pausa
  davanti ai widget; se manca l'audio, voce del browser.

## Struttura
```
site/    Astro Starlight — i capitoli in src/content/docs/{json,db-api,riferimento}
api/     FastAPI + SQLite — app/routers/*.py, dataset in app/seed.py, test in tests/
deploy/  systemd + Caddy + script di pubblicazione
.claude/ skill locali per Claude Code (cerca-skill, fastapi, astro, find-skills)
audio/   estrai.py (testo parlato), genera.py (Piper → MP3), pronuncia.json, manifest.json
docs/    JOURNAL.md (decisioni), GUIDA-CAPITOLI.md (come scrivere un capitolo), PIANO-AUDIO.md
```

## Farlo girare in locale
```bash
./bootstrap.sh                                  # skill + dipendenze (node 22, uv)
cd site && npm run build && cd ..               # sito in site/dist
cd api && uv run fastapi dev app/main.py --port 8795   # http://127.0.0.1:8795 (sito + /api/docs)
cd api && uv run pytest -q                      # test
```
Il sito in sviluppo (`cd site && npm run dev`) chiama l'API tramite `PUBLIC_API_BASE` in `site/.env`
(es. `PUBLIC_API_BASE=http://127.0.0.1:8795`).
