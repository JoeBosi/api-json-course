# Revisione del corso come opera di divulgazione pubblica

Fatta il 27/10/2026, prima dell'apertura al pubblico. Solo lettura: **non ho cambiato niente**
nel sito, nell'API o nella configurazione.

---

## 1. Giudizio in breve

Il corso è **buono e pubblicabile**, con alcune correzioni mirate prima di aprirlo.

- 38 pagine, 32 capitoli completi: ognuno ha obiettivi, teoria, curl spiegato, esempi Python e
  TypeScript affiancati, esercizio **con soluzione**, errori comuni. **Nessun capitolo abbozzato,
  nessun "TODO", nessun esercizio senza risposta, nessun link interno rotto.**
- Gli esempi sono veri: ho fatto rieseguire decine di chiamate contro l'API e gli output scritti
  nelle pagine coincidono cifra per cifra (titoli, prezzi, id, SQL generato, messaggi d'errore).
  È la cosa più difficile da ottenere in un corso ed è fatta bene.
- I difetti sono pochi e concentrati: **9 errori veri** (elencati sotto), un po' di invecchiamento
  normale (versioni di Node, zod, `node:sqlite`) e la rifinitura del glossario.
- Quello che manca davvero non sono i contenuti ma **le diciture**: oggi il sito non dice chi è
  l'autore, da quando è aggiornato, con che licenza si può usare, né che è stato scritto con
  l'aiuto dell'IA. Per un'opera citata nel CV questa è la lacuna più visibile.

Stima: **circa una giornata di lavoro** per correzioni + diciture.

---

## 2. Errori da correggere nei contenuti (in ordine di importanza)

### Gravi — dicono cose false

| # | Dove | Cosa non va | Correzione |
|---|---|---|---|
| 1 | `json/02` r.54, `json/03` r.48 e r.142-143, `json/04` r.49 e r.167 | Le sequenze `è` e la coppia surrogata dell'emoji **sono andate perse dal sorgente**: resta scritto «`è` = `è`» e «`😀` è `😀`». Sono proprio le righe che spiegano l'Unicode, quindi non spiegano più nulla. Verificato da me sui byte del file | Rimettere la forma con la barra rovescia (`è`, `😀`) |
| 2 | `db-api/10` r.163 | **La soluzione dell'esercizio è sbagliata**: dice narrativa 35 ordini e cucina 39 copie; l'API dà saggistica prima sia per incasso (1489,55 €) sia per copie vendute (82) | Riscrivere la soluzione con i dati veri |
| 3 | `db-api/12` r.163-165 | Dice che `WITH RECURSIVE` è **bloccata** su `/sql`: falso, il codice la permette (`sql_guard.py` r.12) e la query gira | Dire che è permessa e invitare a provarla |
| 4 | `db-api/14` r.40, 96, 230 | Tre volte: «la compressione la fa solo Caddy, in locale non la vedi». Falso: l'API comprime da sé (`GZipMiddleware`), in locale 29.504 → 4.126 byte | Dire che comprime l'API; in produzione Caddy può usare zstd |
| 5 | `db-api/02` r.73 e `riferimento/curl` r.14 | Insegnano `curl -I`, ma su `/api/v1/*` ogni HEAD risponde **405**: l'esempio promesso non funziona | Dire che su questa API HEAD dà 405 e usare `-D - -o /dev/null`; `-I` va sulle pagine del sito |
| 6 | `json/01` r.89 | Il testo dice `{"w": 14, "h": 21}`, il JSON sopra e l'API dicono `{"w": 15, "h": 19}` | Correggere in 15/19 |
| 7 | `json/09` r.159-160, 183-185 | L'esempio con **ajv** quasi certamente non parte: `import Ajv from "ajv"` in TypeScript dà "Ajv is not a constructor", e la classe predefinita è draft-07 mentre lo schema è 2020-12 | Usare `ajv/dist/2020.js`; da provare davvero |
| 8 | `db-api/09` r.64-68 | Gli `score` mostrati come output di `jq` sono **arrotondati a mano** (`-3.125` invece di `-3.1252954…`). Le regole del progetto vietano output ritoccati | Mettere i valori veri o arrotondare con `jq` |
| 9 | `db-api/14` r.36, `db-api/07` r.42 e r.113, `db-api/02` r.271 | Quattro dettagli sbagliati: `public, max-age=60` vale solo per `GET /books/{id}`; i metodi non previsti danno 404 **ma HEAD dà 405**; il carattere 14 è la graffa, non la virgola; il codice d'errore è `validation_error`, non `json_invalid` | Allineare le quattro frasi al comportamento vero |

### Invecchiamento (il corso è di settembre 2026, oggi è ottobre)

- `json/13` r.171: `node:sqlite` è dato per **sperimentale con flag**; non lo è più da Node 24.
- `prerequisiti` r.284 e **tutti** i capitoli TypeScript: il commento `node --experimental-strip-types`
  ormai non serve. Da uniformare a `node file.ts`, con una nota per chi ha Node 22.
- `json/07` e `json/15`: mescolano **zod v3 e v4** (`z.string().datetime()` e `z.string().email()`
  sono deprecati in v4). Da scegliere una versione e dichiararla.
- `prerequisiti` r.273 e 288: l'elenco dei pacchetti da installare è incompleto (mancano
  `jsonpath-ng`, `referencing`, `ajv-formats`, `jsonpath-plus`, `stream-json`): chi segue le
  istruzioni alla lettera si blocca ai capitoli 9-11.

### Rifiniture (fastidiose ma non gravi)

- `riferimento/glossario`: copre quasi solo la sezione 2. Mancano termini spiegati nel corso
  (reviver/replacer, `toJSON`, round-trip, coppia surrogata, `Decimal`, zod, TypedDict, jq,
  JSONPath, orjson…) e due voci rimandano al capitolo sbagliato.
- `json/01` dice «sei tipi», `json/02` dice «sette»: incoerenza fra i due capitoli d'apertura.
- `json/10` r.56: titolo «jq in otto mosse», i comandi sono sette.
- `json/06` r.142: la soluzione non fa quello che chiede l'esercizio (e la nota lo ammette).
- `json/08` r.108: `libro_td: BookTD = grezzo` segnalato come errore dal type checker, proprio nel
  capitolo che spiega il type checking; serve `cast`.
- `json/15` r.113: `dict(Counter(...))` non ordina per frequenza, ma il report mostrato è ordinato.
- `json/13` r.93, `json/08` r.60, `riferimento/endpoint` r.36 e r.69, `db-api/15` r.149 e r.274,
  `db-api/13` r.256, `db-api/17` r.244: piccoli disallineamenti fra testo e realtà.
- `db-api/13` e `17`: due widget «Prova» usano id (`/orders/121`, `customer_id: 41`) che esistono
  solo se il lettore ha già eseguito i widget precedenti; altrimenti dà 404. Va avvisato.

---

## 3. Diciture che mancano (nessuna c'è oggi)

Il sito **non contiene nessuna dicitura**: niente autore, niente contatti, niente licenza, niente
privacy. Il piè di pagina è quello standard di Starlight ("Built with Starlight").

| Cosa | Perché serve | Dove metterla |
|---|---|---|
| **Autore e contatto** | È un'opera citata nel CV: chi la legge deve sapere di chi è e come scrivere | piè di pagina + pagina di presentazione; contatto: `info@giuseppebosi.com` |
| **Data di ultimo aggiornamento** | Un corso tecnico senza data non è valutabile. Starlight ce l'ha ma è **spento** (`lastUpdated: false`) e **il progetto non ha nemmeno un commit git**, quindi oggi la data sarebbe vuota | prima fare il primo commit, poi `lastUpdated: true` |
| **Licenza dei contenuti** | Senza licenza nessuno può riusare il materiale, e "gratuito" non vuol dire "libero" | `LICENSE` in radice + riga nel piè di pagina. Consiglio: **CC BY 4.0** per i testi, **MIT** per il codice degli esempi |
| **"Prodotto con l'aiuto dell'IA e rivisto dall'autore"** | Onestà verso il lettore, e ti protegge se qualcuno lo scopre da sé | presentazione + piè di pagina |
| **"Non affiliato / non approvato da"** | Il corso cita molti marchi altrui | pagina "Crediti e licenze". Da nominare almeno: Python (PSF), JavaScript (Oracle), TypeScript e VS Code (Microsoft), Node.js (OpenJS), curl, jq, SQLite, FastAPI, Pydantic, Astro/Starlight, GitHub, npm |
| **Licenze delle dipendenze** | Obbligo delle licenze MIT/Apache usate | stessa pagina crediti |
| **Privacy** | Vedi sotto: serve, ma è semplice | pagina `privacy`, link nel piè di pagina |
| **Avviso sull'audio** | Le voci sono sintetiche, va detto | sotto il lettore audio |

### Privacy: la situazione è buona

- **Nessun cookie, nessun analytics, nessun font o script esterno, ricerca interna al sito.**
  Quindi **non serve nessun banner dei cookie**.
- Nel browser del visitatore si salvano solo preferenze tecniche (voce, velocità, posizione di
  lettura) e il token della sandbox: dati che non arrivano mai al server. Basta dichiararlo.
- Lato server: Caddy non tiene log di accesso, ma l'indirizzo IP è usato per il limite di
  richieste e compare nel journal del servizio. Va scritto in una riga.
- **Unica eccezione da sistemare:** la pagina `/api/docs` carica Swagger da una CDN esterna
  (jsDelivr), quindi l'IP del visitatore finisce a un terzo. O lo si dichiara nella privacy, o si
  servono quei due file dal sito (meglio).

### Link esterni: tutti funzionanti

Solo 4 link esterni in tutto il corso, tutti rispondono 200. I due RFC rimandano alla pagina
"info" dello stesso documento: si possono puntare direttamente lì.

---

## 4. Rischi dell'apertura al pubblico e cosa sistemare prima

### Da fare prima di aprire

1. **La password `basic_auth` è debole e scritta in chiaro.** La password attuale è una data, e il
   suo hash sta in `deploy/Caddyfile.snippet` dentro il progetto: un hash bcrypt di una data si
   rompe offline in pochi secondi. Inoltre la stessa password è scritta **in chiaro** in
   `/root/Developer/VPS_Controller/ARCHITETTURA.md`. Se è una password che Giuseppe usa anche
   altrove, va **cambiata lì dove la usa**, e tolta da quei due file. (Il blocco `basic_auth` lo
   rimuove il Controller: io non l'ho toccato.)
2. **L'API di prova resterebbe aperta a chiunque.** È il rischio più concreto: chiunque potrebbe
   usarla come servizio gratuito proprio (le origini CORS sono aperte a tutti). *In corso: sto
   realizzando l'interruttore richiesto dal Controller — API spenta di norma, accesa dal sito con
   password e spegnimento dopo 60 minuti di inattività.*
3. **Esaurimento delle sandbox.** Oggi il limite è 500 sandbox e ognuno può crearne quante vuole:
   con 120 richieste al minuto si riempiono in 5 minuti e gli altri lettori ricevono "troppe
   sandbox attive". Serve un tetto **per indirizzo IP** (es. 3 sandbox a testa), oltre al limite
   totale che il Controller porta a 100.
4. **Il servizio gira come `root`.** Un'applicazione esposta al pubblico non dovrebbe: una falla
   diventerebbe subito un problema di tutta la macchina. Da far girare con un utente dedicato
   (`User=` nell'unit systemd, o `DynamicUser=yes` con la cartella dati in `StateDirectory`).
   Richiede una modifica systemd, quindi la decide il Controller.

### Rischi minori, da tenere d'occhio

- **Nessun log di accesso** (Caddy ha `log { output discard }`): è ottimo per la privacy, ma se
  qualcuno abusa del sito non te ne accorgi e non puoi contare i visitatori. Valutare un log
  minimo, senza IP, oppure accettarlo consapevolmente.
- **Traffico**: il corso pesa 111 MB, di cui **105 MB di audio**. Un visitatore che ascolta tutto
  scarica circa 100 MB. Con pochi visitatori è irrilevante, ma è la voce che può crescere.
- **Endpoint `/echo`**: rimanda indietro qualsiasi cosa riceve. Innocuo, ma è il tipo di endpoint
  che qualcuno usa per fare prove con il tuo dominio. Con l'interruttore acceso solo quando serve,
  il problema si riduce da sé.
- **`/api/v1/sql`**: è ben protetto (solo SELECT, 2 secondi, 200 righe, database in sola lettura,
  tabelle interne vietate). Nessuna modifica necessaria.
- **Disco**: 190 GB liberi, una sandbox pesa 184 KB. Nessun rischio.

### Rischi che **non** ci sono

- **Costi: zero.** Nessuna chiave API nel progetto (il file `.env` non esiste), nessun servizio a
  pagamento collegato, l'audio è già generato e servito come file statici. Aprire al pubblico non
  fa spendere niente.
- **Dati personali: nessuno.** Il dataset è inventato (clienti con nomi finti e indirizzi
  `@example.com`, che è un dominio riservato proprio per gli esempi). Le sandbox sono copie
  private che si cancellano da sole.
- **Codice su GitHub: nessuno.** Il progetto non ha nemmeno un commit e nessun repository remoto,
  quindi niente è stato pubblicato per sbaglio.

### Una cosa da decidere

L'audio del corso usa oggi la voce **Piper**, quella che avevi giudicato inascoltabile. Il lettore
di default usa la voce del browser dove c'è, ma su alcuni dispositivi parte Piper. Prima di aprire
conviene decidere: generare la voce buona (OpenAI, ~2,57 $ una tantum) oppure togliere Piper e
lasciare solo la voce del browser.

---

## 5. Cosa ho verificato e cosa no

**Verificato davvero:** tutti i 32 capitoli letti; decine di esempi rieseguiti contro l'API vera
con curl (conteggi, filtri, ricerca, statistiche, SQL, errori, ETag, CORS, export, compressione);
i byte dei file dove segnalavo caratteri persi; i 4 link esterni; i test del progetto (14 test API
verdi, test del browser verdi); la configurazione di Caddy e di systemd; l'assenza di chiavi,
cookie, script esterni e commit git; lo spazio su disco; il sito pubblico che risponde.

**Non verificato:** il comportamento del server pubblico dietro Caddy per alcuni dettagli citati
nel corso (redirect da HTTP, codice del redirect verso le URL con barra finale, limite di 1 MB sul
corpo); il reale comportamento sotto carico; gli esempi TypeScript dei capitoli 9-11 non sono stati
eseguiti (servirebbe installare zod, ajv e le altre librerie), quindi il punto 7 resta "molto
probabilmente rotto" e va provato.
