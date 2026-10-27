# Piano: lettura audio dei capitoli ("ascolta e guarda")

Stato: **implementato** il 2026-09-19 (voce Paola, MP3 64 kbps, codice mai letto, soluzioni lette solo se aperte). Un MP3 per paragrafo, nome = hash del testo; associazione ai paragrafi della pagina per testo normalizzato (`Lettura.astro`), verificata da `site/tests/e2e.mjs`.

## Obiettivo
In ogni pagina del corso il lettore può far leggere il testo, sezione per sezione, mentre la
pagina evidenzia il paragrafo in lettura e scorre. La lettura si ferma da sola davanti a un
widget `Prova` ("ora esegui e guarda la risposta") e riprende al clic. Voce neurale generata
**in fase di build** con Piper sul VPS (gratis, offline); se per una sezione manca l'audio, si usa
la voce del browser (`speechSynthesis`) come ripiego.

## Fatti verificati (2026-09-19)
- `piper-tts` 1.8.0 si installa con `uv` su Python 3.12.
- Voci italiane su `rhasspy/piper-voices`: `paola` (medium), `riccardo` (x_low), `serena` (medium, high).
  Prova con `paola-medium`: 8 s di audio in 7,4 s (primo avvio, modello incluso); modello 63 MB.
- `ffmpeg` presente in `/usr/bin/ffmpeg` (per convertire WAV → MP3/Opus).
- VPS: 6 vCPU, 7 GB RAM liberi, 37 GB disco liberi. Stima corso: ~250.000 caratteri → ~5 ore
  di audio → ~150 MB in MP3 64 kbps (o ~80 MB in Opus 32 kbps). Generazione completa: ~20-40 min
  di CPU, ma incrementale (si rigenera solo ciò che cambia).

## Architettura

```
site/src/content/docs/**/*.mdx
        │  (1) estrazione del testo parlato, per sezione (## …) e per paragrafo
        ▼
audio/estrai.py  →  audio/manifest.json   { pagina → sezioni → paragrafi { id, hash, testo_parlato } }
        │  (2) sintesi solo dei paragrafi con hash nuovo
        ▼
audio/genera.py (Piper + ffmpeg)  →  site/public/audio/<pagina>/<hash>.mp3   (+ durata nel manifest)
        │  (3) build normale di Astro: i file finiscono in site/dist/audio/
        ▼
componente <Lettura />  (player per pagina)  ← legge audio/manifest.json (pubblicato come /audio/manifest.json)
```

Un file audio **per paragrafo** (non per pagina): così l'evidenziazione è naturale (un paragrafo =
un file = un `<p>` da illuminare), i file sono piccoli e la rigenerazione è chirurgica.

### 1. Estrazione del "testo parlato" (`audio/estrai.py`, Python)
- Parsa gli `.mdx` con `markdown-it-py` (o regex robuste): prende `#`/`##`/`###`, paragrafi, liste,
  tabelle (lette come "colonna: valore"), `Aside` (letti con il titolo: "Suggerimento: …").
- **Cosa non si legge**: blocchi di codice (` ``` `), `import`, frontmatter, `<Prova>`, `<Sandbox>`.
- **Cosa si parafrasa**:
  - `<Curl cmd=… spiega=[[opzione, testo], …]>` → "Il comando curl. Opzione -s: …; opzione -X: …"
    (le spiegazioni ci sono già, scritte per questo).
  - `<Tabs syncKey="lang">` → si legge solo il testo che precede/segue; il codice no. Si aggiunge la
    frase "Qui trovi lo stesso esempio in Python e in TypeScript: scegli la scheda."
  - inline code `` `x` `` → letto com'è ma con le sostituzioni fonetiche (tabella `audio/pronuncia.json`:
    `JSON`→"gèison", `API`→"a pi ai", `curl`→"curl", `httpx`→"http-x", `-H`→"meno acca", `->>`→"freccia doppia",
    `null`→"null", `true`/`false`, `{}`→"graffe", ecc.).
  - link → solo il testo; `<details>` (soluzioni) → letti solo se il lettore li apre (paragrafi con flag `nascosto`).
- Ogni paragrafo riceve un `id` stabile (`p-<indice>`) e un `hash` sha1 del testo parlato.
- Il paragrafo che precede un `<Prova>` riceve `pausa: true` → il player si ferma lì e dice
  "Premi Esegui e guarda la risposta, poi riprendi".
- Ogni paragrafo estratto deve corrispondere a un elemento nel DOM: `estrai.py` aggiunge al file
  `.mdx` nulla; l'associazione avviene a runtime per **ordine dei blocchi di testo** dentro
  `.sl-markdown-content` (stesso algoritmo di estrazione applicato al DOM: p, li, h2, h3, td…).
  Verifica in build: numero di paragrafi estratti = numero trovati nel DOM della pagina compilata
  (script Playwright già usato per gli e2e); se non coincidono la build **fallisce** (R3 verifica).

### 2. Sintesi (`audio/genera.py`)
- `uv run --with piper-tts --with markdown-it-py python audio/genera.py [--voce paola] [--pagina json/01-cos-e-json]`
- Per ogni paragrafo con hash non presente su disco: Piper (modello caricato una sola volta, processo
  unico, `--sentence-silence 0.4`) → WAV → `ffmpeg -i x.wav -c:a libmp3lame -b:a 64k` → MP3 (compatibile
  ovunque; Opus rimandato). Scrive `durata_s` nel manifest.
- File orfani (hash non più nel manifest) cancellati.
- Modello ONNX in `audio/voci/` (gitignorato, ~63 MB; scaricato dallo script se manca, URL nel codice).
- Parallelismo: 3 processi (6 vCPU): ~5 ore di audio in ~15 min.
- `deploy/pubblica.sh` chiama `audio/genera.py` prima di `npm run build` (passo "1b. Audio").

### 3. Player (`site/src/components/Lettura.astro`, custom element `<lettura-audio>`)
- Inserito una volta per pagina via override del componente Starlight `PageTitle` (o `Hero`):
  barra compatta sotto il titolo: **▶ Ascolta il capitolo** · velocità 1×/1.25×/1.5× · voce
  "Paola (audio)" / "Voce del browser" · ⏮ sezione ⏭ · tempo.
- Legge `/audio/manifest.json` (una fetch, cache 1 giorno), prende la voce della pagina corrente.
- **Sincronizzazione**: un `<audio>` alla volta; a `ended` passa al paragrafo successivo. Il paragrafo
  in lettura riceve la classe `.in-lettura` (sfondo leggero, bordo accento) e
  `scrollIntoView({block:'center', behavior:'smooth'})`; clic su un paragrafo = "leggi da qui".
- **Pausa sui widget**: al paragrafo con `pausa` il player si ferma, evidenzia il `<Prova>` seguente e
  mostra "Riprendi" (ripresa automatica quando il widget riceve una risposta: evento custom
  `corso:prova-eseguita` lanciato da `Prova.astro`).
- **Fallback**: se `manifest` manca la pagina o il fetch dell'MP3 fallisce → `speechSynthesis` con voce
  `it-IT` (scelta migliore disponibile), stesso testo parlato (il manifest contiene il testo, quindi
  il fallback legge esattamente le stesse frasi con le stesse pronunce corrette). Evidenziazione con
  `onboundary`/`onend`.
- **Memoria**: posizione (pagina + paragrafo), velocità e modalità in `localStorage`
  (`corso-api-json.lettura`); "Continua da dove eri" al ritorno.
- **Accessibilità**: il player è un `region` con `aria-label`; niente autoplay; pulsanti con etichette;
  chi usa screen reader non viene disturbato (l'audio parte solo su azione).
- Preload del paragrafo successivo (`new Audio(...).preload='auto'`) per evitare buchi tra un file e l'altro.

### 4. Integrazione nel progetto
```
audio/                estrai.py, genera.py, pronuncia.json, manifest.json (versionato), voci/ (ignorato)
site/public/audio/    <pagina>/<hash>.mp3 + manifest.json (generati; ignorati in git? → NO: ~150 MB,
                      meglio ignorati e rigenerati in build sul VPS; il manifest sì versionato)
site/src/components/Lettura.astro, site/src/styles/custom.css (.in-lettura, barra)
site/astro.config.mjs  components: { PageTitle: './src/components/PageTitleConLettura.astro' }
deploy/pubblica.sh     passo audio prima della build
docs/GUIDA-CAPITOLI.md aggiunta: "scrivi paragrafi leggibili a voce; non mettere concetti solo nel codice"
```
- Skill da cercare prima (R1): `npx skills find "piper tts"`, `"text to speech"`, `"web speech api"`.
- Nota ricerca (R2): `docs/research/2026-09-19-piper-tts.md` (versioni, voci, parametri).

## Fasi e verifiche
| Fase | Lavoro | Verifica |
|---|---|---|
| A | `estrai.py` + `pronuncia.json` su 3 pagine pilota (json/01, db-api/02, db-api/06) | stampa del testo parlato letto da Giuseppe; conteggio paragrafi = DOM |
| B | `genera.py` con Piper, MP3 per le 3 pagine | ascolto di 2-3 file; durata totale/pagina nel manifest |
| C | `Lettura.astro`: play, evidenziazione, scroll, pausa sui widget, fallback browser | e2e Playwright: avvia, cambia paragrafo, si ferma al `Prova`, riprende; con manifest vuoto usa speechSynthesis |
| D | scelta voce (Paola vs Serena: due campioni a Giuseppe), generazione completa, `pubblica.sh` | tempo di generazione, dimensione `dist/audio`, tutte le pagine con audio |
| E | rifinitura pronunce (ascolto a campione di 10 paragrafi tecnici), guida capitoli aggiornata | lista correzioni in `pronuncia.json` |

## Decisioni da prendere con Giuseppe
1. **Voce**: Paola (medium) o Serena (high, più pesante e lenta da generare). Preparo due campioni.
2. **Formato**: MP3 64 kbps (compatibilità) — consigliato; Opus dimezza il peso ma Safari vecchi no.
3. **Soluzioni degli esercizi**: lette solo se aperte (consigliato) o sempre.
4. **Codice**: mai letto (consigliato); alternativa: letto "a parole" solo per i comandi curl brevi.
5. Audio in git: no (rigenerato in build); solo `manifest.json`.

## Rischi
- Pronuncia di termini tecnici: gestita con `pronuncia.json`, ma richiederà qualche iterazione di ascolto.
- Allineamento paragrafi ↔ DOM se Starlight cambia il markup: coperto dal test in build.
- Tempo di build più lungo la prima volta (~15-40 min): incrementale poi.
- Con `basic_auth` attivo gli MP3 sono protetti come il resto: nessun problema, stessa origine.
