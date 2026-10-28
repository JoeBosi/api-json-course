# corso-api-json — istruzioni per l'agente

Corso web "JSON e API: da 0 a esperto" (Python + TypeScript/JavaScript) con server API di
prova. Tutto vive in questa cartella: `site/` (Astro Starlight), `api/` (FastAPI + SQLite),
`deploy/` (systemd + Caddy), `.claude/skills/` (skill locali). Pubblico:
https://corso-api-json.giuseppebosi.com — l'API di prova risponde su `/api/v1`, Swagger su `/api/docs`.

**Il sito è aperto a tutti, senza password** (decisione di Giuseppe del 28/10/2026: i link sono
nel CV letto dalla commissione del Comune). Il `basic_auth` è stato tolto dal Caddyfile dal
Controller: **non rimetterlo**. Nelle pubblicazioni non si tocca Caddy, e **dopo ogni
pubblicazione si verifica che le pagine rispondano 200 senza password**:
`for u in / /presentazione/ /json/01-cos-e-json/ /crediti/; do curl -s -o /dev/null -w "%{http_code} $u\n" https://corso-api-json.giuseppebosi.com$u; done`
La password resta solo per **accendere l'API di prova** dalla pagina `/api-attiva/`.

## Regole (valgono sempre)

1. **Prima cerca una skill.** Locali in `.claude/skills/`; poi online con
   `npx -y skills@latest find "<parola>"`. Leggi il `SKILL.md` **prima** di installare (gira con
   i permessi dell'agente). Installa solo così, mai globale, mai symlink:
   `npx -y skills@latest add <owner/repo> --skill <nome> -a claude-code --copy -y`.
   Procedura completa: `.claude/skills/cerca-skill/SKILL.md`. Le skill installate stanno in
   `skills-lock.json` e si ripristinano con `./bootstrap.sh`.
2. **Lavoro tecnico = documentazione ufficiale attuale**, non memoria. Le note utili vanno in
   `docs/research/AAAA-MM-GG-<slug>.md`.
3. **Verifica prima di dire "fatto"**: `cd api && uv run pytest -q`, `cd site && npm run build`,
   `curl` sull'endpoint. Se non puoi verificare, dillo.
4. **Portabile**: niente path assoluti nei file del progetto, venv/node_modules dentro la cartella,
   nessun file fuori da qui (Caddy fa reverse proxy verso il servizio che sta qui dentro).
5. **Niente segreti** in file, log o chat. `.env` è ignorato; `.env.example` è il registro.
6. **Caddy, systemd, firewall**: solo con conferma esplicita di Giuseppe (script pronti in `deploy/`).
7. **Niente scorciatoie nascoste** (dati finti, workaround): avvisare prima.
8. Decisioni non banali → una riga in `docs/JOURNAL.md`.

## Regole del corso

- Testo in italiano, codice e termini tecnici in inglese. Lettore: sa le basi di Python e/o JS.
- Ogni capitolo: obiettivi → teoria breve → esempio **curl spiegato opzione per opzione** →
  stesso esempio in Python e TypeScript affiancati (`<Tabs syncKey="lang">`) → widget
  `<Prova>` che esegue la richiesta dalla pagina → esercizio con soluzione → errori comuni.
- Gli esempi devono girare davvero contro l'API (locale o pubblica): niente output inventati.
- Dataset fittizio "Libreria Aurora" (`api/app/seed.py`), nessun dato personale reale.

## Comandi

```bash
cd api && uv run fastapi dev app/main.py --port 8795   # API in sviluppo (http://127.0.0.1:8795/api/docs)
cd api && uv run pytest -q                              # test API
cd site && npm run dev                                  # sito in sviluppo (http://localhost:4321)
cd site && npm run build                                # build in site/dist (servita da FastAPI)
cd api && uv run python ../audio/estrai.py            # testo parlato → audio/manifest.json (--pagina X --stampa)
cd api && uv run python ../audio/genera.py            # MP3 con Piper (solo i paragrafi cambiati)
cd api && uv run python ../audio/genera_openai.py --stima   # voce del corso (OpenAI TTS): costo, poi --campioni / --voce X
cd site && npm run test:e2e                             # verifica nel browser (serve l'API attiva)
deploy/pubblica.sh                                      # audio + build sito + test + riavvio servizio
deploy/attiva-caddy.sh                                  # prima installazione (unit systemd + blocco Caddy)
python3 deploy/imposta-password-api.py                  # password che accende l'API (salva solo l'hash in .env)
sudo deploy/installa-utente-api.sh                      # fa girare l'API come utente corso-api da /opt
sudo deploy/verifica-utente-api.sh                      # controlla utente, permessi, API ON/OFF, limiti
./bootstrap.sh                                          # ripristina le skill dal lock e controlla l'ambiente
```

## Quando → usa

| Quando | Usa |
|---|---|
| serve una capacità nuova (libreria, tool, formato) | skill `cerca-skill` (+ `find-skills`) |
| codice FastAPI, Pydantic, dipendenze, risposte | skill `fastapi` |
| pagine, componenti, config del sito | skill `astro` |
| pubblicare un aggiornamento | `deploy/pubblica.sh` |
| capire l'API | `api/app/routers/*.py`, `/api/docs` |
| API di prova spenta/accesa, password, pagina di attivazione | `api/app/interruttore.py`, `site/src/components/AttivaApi.astro`, `site/src/content/docs/api-attiva.mdx` |
| utente di sistema, permessi, deploy in /opt | `deploy/installa-utente-api.sh`, `deploy/corso-api-json.service` |
| lettura audio (testo parlato, pronunce, player) | `audio/estrai.py`, `audio/pronuncia.json`, `site/src/components/Lettura.astro`, `audio/genera_openai.py`, `docs/PIANO-AUDIO.md` |
