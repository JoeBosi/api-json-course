# Guida per scrivere un capitolo

Modello di riferimento: `site/src/content/docs/json/01-cos-e-json.mdx`. Ogni capitolo è un file
`.mdx` in `site/src/content/docs/<json|db-api>/NN-slug.mdx` (gli slug sono già creati come stub:
NON rinominarli, la sidebar in `site/astro.config.mjs` li elenca).

## Struttura obbligatoria
```
---
title: "N. Titolo"            (come nella sidebar)
description: "una frase"
---
import { Tabs, TabItem, Aside, Steps } from '@astrojs/starlight/components';
import Prova from '../../../components/Prova.astro';
import Curl from '../../../components/Curl.astro';
(import Sandbox from '../../../components/Sandbox.astro'; solo dove serve il pannello)

## Obiettivi          (3-5 punti)
## Teoria             (chiara, con tabelle/esempi; 400-900 parole; sottosezioni ## libere)
## curl, spiegato     (<Curl cmd=... spiega=[[token, spiegazione html], ...] />: OGNI opzione usata va spiegata,
                       anche la sintassi dell'URL/query string, gli header, il body, le virgolette della shell)
                       Poi il blocco ```json con la risposta VERA (ottenuta da http://127.0.0.1:8795, abbreviata con … se lunga)
## Python e TypeScript (<Tabs syncKey="lang"> con <TabItem label="Python"> e <TabItem label="TypeScript">,
                       codice completo ed eseguibile: Python con httpx (o json stdlib), TS con fetch nativo,
                       commento in testa con come lanciarlo)
## Prova subito       (<Prova path="/api/v1/..." method="POST" body={{...}} sandbox titolo="..." />: uno o più)
## Esercizio          (+ <details><summary>Soluzione</summary> ... </details>)
## Errori comuni      (3-5 punti)
## In sintesi         (2-4 righe + rimando al capitolo successivo)
```

## Regole
- Italiano; codice, nomi di campi, termini tecnici in inglese. Tono diretto, niente fuffa.
- URL negli esempi: `https://corso-api-json.giuseppebosi.com/api/v1/...`. Nei `<Prova>` il path è RELATIVO (`/api/v1/...`).
- Le risposte mostrate devono essere VERE: eseguile con curl su `http://127.0.0.1:8795` (API locale identica alla pubblica) e incollale (abbreviando con `…` se lunghe). Niente output inventati.
- Le scritture (POST/PUT/PATCH/DELETE) richiedono la sandbox: in curl mostra `-H 'Authorization: Bearer $TOKEN'` dopo aver spiegato come ottenere il token (`curl -s -X POST .../api/v1/sandbox`), nei `<Prova>` usa `sandbox`.
- Errori dell'API hanno sempre la forma `{"error":{"code","message","details?"}}`.
- Dentro MDX: le graffe `{}` nel testo vanno in codice inline o escapate; niente `<` nudi nel testo (usa `&lt;` o codice). Attributi JSX per `body`: `body={{"title": "x"}}` oppure stringa.
- Non usare `<Curl spiega>` con apostrofi non escapati dentro stringhe con apici singoli: usa doppi apici o `&#39;`.
- Non lanciare `npm run build` (lo fa il coordinatore); controlla però che l'MDX sia ben formato.
- Endpoint disponibili: vedi `api/app/routers/*.py` o `curl -s http://127.0.0.1:8795/api/openapi.json`.
- Dataset: "Libreria Aurora" — tabelle authors, categories (albero), books (attributes JSON, tags N-N), customers, orders (shipping_address JSON), order_items, reviews; vista book_stats; FTS books_fts. `GET /api/v1/schema` mostra PK e FK.
- Ogni capitolo della Sezione 2 deve far vedere almeno un curl con spiegazione completa della sintassi.

## Lettura audio (dal 2026-09-19)
Ogni pagina ha il player "Ascolta il capitolo": `audio/estrai.py` estrae il testo parlato per paragrafo
(titoli, paragrafi, liste, tabelle, Aside, spiegazioni dei `<Curl>`; MAI il codice), `audio/genera.py`
sintetizza con Piper un MP3 per paragrafo. Conseguenze per chi scrive:
- I concetti vanno nel testo, non solo nel codice: chi ascolta il codice non lo sente.
- Le spiegazioni dei `<Curl>` vengono lette: scrivile come frasi complete.
- Il paragrafo prima di un `<Prova>` viene letto e poi la lettura si ferma ("ora premi Esegui"): chiudi quel paragrafo con un invito a provare.
- Termini tecnici con pronuncia strana → aggiungi una regola in `audio/pronuncia.json`.
- Controllo: `python3 audio/estrai.py --pagina <slug> --stampa` mostra cosa verrà letto.
