# Diario delle decisioni

Formato: `data — cosa — decisione/esito`.

- 2026-09-18 — avvio progetto — ambiente agentico costruito da zero (niente agent-kit, per scelta di Giuseppe): CLAUDE.md, `cerca-skill`, `bootstrap.sh`, `skills-lock.json` via `npx skills`.
- 2026-09-18 — skill installate — `fastapi` (fastapi/fastapi, ufficiale), `astro` (oakoss/agent-skills, da docs.astro.build), `find-skills` (vercel-labs/skills). Scartata `curl-md`: repo non raggiungibile.
- 2026-09-18 — stack — Astro Starlight per il sito, FastAPI + SQLite per l'API; un solo servizio systemd (porta 8795) serve `/api/*` e `site/dist` (Caddy non legge sotto /root).
- 2026-09-18 — sandbox — un token = una copia del seed in `api/data/sandboxes/`; TTL 6h rinnovato a ogni uso; senza token lettura del dataset pubblico. Rate limit 120/min per IP (slowapi).
- 2026-09-18 — `/sql` — read-only vero: authorizer SQLite (solo SELECT/READ/FUNCTION), `mode=ro`, 2 s, 200 righe.
- 2026-09-18 — corso scritto — 32 capitoli + 4 pagine di riferimento (39 pagine), tutti gli output presi dall'API locale; `/sql` ora ammette `WITH RECURSIVE`. Verifica e2e con Chromium headless: widget Prova, pannello Sandbox, POST 201, ricerca Pagefind.
- 2026-09-18 — pubblicazione — `deploy/pubblica.sh` ok (build + 14 test). `deploy/attiva-caddy.sh` va lanciato da Giuseppe (auto-mode blocca i deploy in produzione).
- 2026-09-19 — online — `deploy/attiva-caddy.sh` eseguito: servizio `corso-api-json` attivo, blocco Caddy aggiunto (backup `Caddyfile.bak.20260919-074048`), https 200. Attesa avvio negli script portata a 30 s (uvicorn parte in ~6 s). Aggiunto `GZipMiddleware` all'API: Caddy non comprimeva le risposte in streaming (export NDJSON 34 KB → 5,7 KB). `encode` di Caddy con match esplicito dei content-type. ARCHITETTURA.md e MEMORIA.md di VPS_Controller aggiornati.
- 2026-09-19 — accesso — basic_auth Caddy (utente giuseppe) su tutto il dominio, API compresa, su richiesta di Giuseppe.
- 2026-09-19 — audio — pianificata la lettura vocale dei capitoli (Piper in build + fallback browser): docs/PIANO-AUDIO.md. Non implementata.
- 2026-09-19 — audio implementato — estrai.py (1882 paragrafi, 220k caratteri, 1575 unici), genera.py con Piper paola-medium, player Lettura.astro via override PageTitle, e2e in site/tests/e2e.mjs (Playwright devDependency del sito). Nessuna skill adatta trovata (find: solo TTS cloud/training).
- 2026-09-19 — audio online — 1625 mp3 (221 min, 105 MB) pubblicati con deploy/pubblica.sh; e2e OK (99,7% paragrafi associati).
- 2026-09-19 — audio v2 — su richiesta di Giuseppe (voce Piper «inascoltabile», parole inglesi lette all'italiana, manca la pausa): player ridotto a pulsante 🔊, pausa/stop veri, disattivazione su tutto il sito (riattivabile da Presentazione), selettore voce con le voci del browser (default la migliore italiana) + «Prova voce», «Segui il testo». Le riscritture fonetiche restano solo per Piper; le voci del browser ricevono il testo con l'inglese in inglese. Voce di qualità (cloud) in attesa di decisione.
- 2026-09-19 — Player pronto per la voce Azure («Voce del corso», predefinita se nel manifest ci sono MP3 `audio/az/`); estrai.py conserva gli hash Azure; in attesa della chiave in .env.
- 2026-09-24 — Azure scartato da Giuseppe. Voce del corso con OpenAI `gpt-4o-mini-tts` (`audio/genera_openai.py`): niente SSML, la pronuncia dell'inglese si guida con `instructions`. Stima per tutto il corso: ~257 min, ~$2,57. Manifest e player resi generici (`cloud: {voce, dir}`, campi `hc`/`dc`), `audio/genera_azure.py` rimosso.
- 2026-10-27 — Apertura al pubblico (richieste del Controller per Giuseppe). (1) Revisione divulgativa in `REVISIONE-DIVULGAZIONE.md`: 9 errori da correggere, diciture tutte mancanti, rischi dell'apertura. (2) Interruttore dell'API: spenta di norma, si accende da `/api-attiva` con password (hash scrypt in `.env`, mai in chiaro), si rispegne dopo 60 min di inattività, 5 tentativi per IP ogni 15 min; `/api/v1/interruttore` risponde sempre. (3) L'API non gira più come root: utente `corso-api`, codice in `/opt/corso-api-json`, dati in `/var/lib/corso-api-json`, unit blindata; installazione con `deploy/installa-utente-api.sh` (idempotente, con ritorno indietro) e controllo con `deploy/verifica-utente-api.sh`. Riavvio e creazione utente li lancia Giuseppe via SSH.
- 2026-10-28 — Applicate le 9 correzioni approvate (sequenze `\uXXXX` in 5 punti, soluzione dell'esercizio db-api/10 verificata con l'API, `WITH RECURSIVE` permessa, compressione fatta dall'API, `-I`/HEAD che dà 405, dimensioni del libro 1, esempio ajv con `ajv/dist/2020.js` + `strict:false` **provato davvero**, punteggi BM25 ora arrotondati dentro il comando `jq` invece che a mano, quattro dettagli su Cache-Control/405/codici d'errore). Una segnalazione della revisione era sbagliata e NON è stata applicata: in JavaScript `JSON.stringify` non escapa i caratteri non ASCII, quindi l'output di json/03 era già corretto.
- 2026-10-28 — Diciture: piè di pagina proprio (`site/src/components/Footer.astro`) con autore, contatto, licenze e avviso IA; `lastUpdated: true`; `LICENSE` (MIT, codice) e `LICENSE-CONTENUTI` (CC BY 4.0, testi); pagine `crediti` e `privacy`; nota "voce sintetica" nel lettore. Swagger UI servito da `site/public/swagger/` (5.34.0): `/api/docs` non contatta più jsDelivr, con test che lo verifica.
- 2026-10-28 — Voce audio: scelta la **voce del browser** (Web Speech), Piper rimosso dal lettore e da `pubblica.sh` (`genera.py --solo-manifest`); i 1627 MP3 di Piper sono rimasti su disco in attesa dell'ok di Giuseppe per cancellarli. Dove il browser non ha voci italiane il lettore lo dice invece di leggere male.
- 2026-10-28 — Primo commit locale (nessun remoto). `attiva-caddy.sh` non installa più la unit: ora lo fa `installa-utente-api.sh`.
- 2026-10-28 — Su ok di Giuseppe, i 1627 MP3 di Piper (105 MB) spostati nel Cestino con `gio trash` (`~/.local/share/Trash`, lo svuota lui). Il sito passa da 111 MB a 8,6 MB; test rifatti dopo la rimozione: 21 pytest verdi, build 43 pagine, E2E OK, lettura audio che avvisa quando il browser non ha voci italiane. Aggiunto `deploy/cambia-password-sito.sh`: chiede la nuova password del sito senza mostrarla, calcola l'hash bcrypt con `caddy hash-password`, lo salva in `/root/.config/corso-api-json/basic-auth.hash` (600) e aggiorna `deploy/Caddyfile.snippet`; NON tocca `/etc/caddy/Caddyfile` né ricarica Caddy (lo fa il Controller).

## 28/10/2026 — Via le frasi di avvertenza sull'IA
Richiesta di Giuseppe (via Controller): in un corso ogni frase deve insegnare qualcosa, quindi
niente diciture "scritto con l'aiuto dell'IA", "riletto dall'autore", "esempi non inventati",
né marche di verifica. Tolte dal piè di pagina, dalla Presentazione e dai Crediti; nelle
Informazioni restano autore, licenza, crediti e privacy. Le due note su `node:sqlite` che
dicevano "verificato con Node 22.23" / "sperimentale" sono diventate contenuto normale con il
link alla documentazione ufficiale di Node. Corretta anche la frase della Presentazione che
offriva ancora "la voce generata sul server" (Piper non c'è più).

## 28/10/2026 — Sito aperto al pubblico
Giuseppe ha deciso di aprire il corso senza password (i link sono nel CV letto dalla commissione
del Comune); il Controller ha tolto `basic_auth` dal Caddyfile. Regola scritta in CLAUDE.md:
non rimetterla, non toccare Caddy nelle pubblicazioni, e dopo ogni pubblicazione verificare con
curl che le pagine rispondano 200 senza credenziali. La password resta solo per accendere l'API.

## 28/10/2026 — "Prof. Giuseppe Bosi" nella barra in alto
Richiesta di Giuseppe: il nome dell'autore sempre visibile nell'header, con link alla sua home.
Fatto con un override di `SiteTitle` di Starlight (`site/src/components/SiteTitle.astro`): il
nome sta sotto il titolo del corso, dentro la barra, che Starlight tiene fissa in cima. Sotto i
480 px titolo e nome rimpiccioliscono per entrare nei 390 px.
Pubblicazione: il servizio serve `/opt/corso-api-json/site/dist`, quindi per il solo sito basta
l'rsync di `dist` (niente riavvio, niente Caddy). Verifica con `site/tests/probe-autore.mjs`.

## 29/10/2026 — Visibilità per motori di ricerca e IA
Piano approvato da Giuseppe. Nessun noindex c'era (né meta né header in Caddy): Caddy non toccato.
Aggiunti come pagine Astro generate dai contenuti (`site/src/pages/`, elenco comune in
`site/src/lib/pagine.ts`): `robots.txt` (tutto permesso, anche GPTBot, ClaudeBot, PerplexityBot,
Google-Extended), `sitemap.xml` (41 pagine + home), `llms.txt` (formato llmstxt.org) e
`llms-full.txt` (testo integrale; i tag dei componenti interattivi tolti, i blocchi `<Curl>`
lasciati perché contengono il comando e la spiegazione delle opzioni). Title, description,
canonical e Open Graph li genera già Starlight su ogni pagina. JSON-LD `Course` in `head` con
autore Prof. Giuseppe Bosi e link a www.giuseppebosi.com; LinkedIn non messo finché la chat
Curriculum non comunica l'indirizzo definitivo. Piè di pagina: nome dell'autore cliccabile e
link agli altri corsi pubblici (corso-rag, corso-llamacpp).

## 29/10/2026 — LinkedIn dell autore
Indirizzo definitivo https://www.linkedin.com/in/giuseppebosi (dal Controller): nel piè di pagina, in JSON-LD (`sameAs`) e in llms.txt. Il vecchio indirizzo non era mai stato usato qui.

## 29/10/2026 — Corso bilingue (italiano + inglese sotto /en/)
Richiesta di Giuseppe. i18n nativo di Starlight: `root` = italiano (URL invariati), `en` in
`site/src/content/docs/en/` con gli stessi slug (`/en/json/01-cos-e-json/`), così hreflang e
selettore di lingua collegano le pagine gemelle. Glossario in `docs/glossary-en.md`. Traduzione
fatta in chat; codice, comandi e output sono copiati identici dalle pagine italiane dallo script
`site/scripts/traduci.py` (si ferma se un blocco manca o è in più). Componenti bilingui tramite
`site/src/lib/i18n.ts`; nella barra un link IT/EN sempre visibile, anche su telefono. La lettura
audio resta solo in italiano (`estrai.py` salta `docs/en/`, il lettore non compare sulle pagine
inglesi). SEO: hreflang it/en/x-default (Starlight), `sitemap.xml` con le due lingue e le
alternative, `llms.txt` con sezione inglese, `llms-full-en.txt`. Controllo link:
`site/tests/link-en.py`. Durante la revisione corretti in italiano: limite pubblico 30/min (non
120), esempio del 429 rifatto davvero con il limite reale, link morto a ReDoc, due frasi "è stato
eseguito". Link a GitHub nel piè di pagina pronto ma spento (`GITHUB_PUBBLICO=false`) finché il
repo è privato.
- 30/10/2026: cambio lingua con bandierina SVG (regola di Giuseppe per i siti bilingui), tolto il menu lingua di Starlight.
