// Testi dell'interfaccia dei componenti del corso, in italiano e in inglese.
// La lingua è quella della pagina (Starlight: Astro.locals.starlightRoute.lang).
export type Lingua = 'it' | 'en';
export const lingua = (lang?: string): Lingua => (lang?.startsWith('en') ? 'en' : 'it');
/** Prefisso dei link interni: '' per l'italiano, '/en' per l'inglese. */
export const pre = (l: Lingua) => (l === 'en' ? '/en' : '');

export const T = {
  it: {
    autore: 'Prof. Giuseppe Bosi',
    sitoAutore: 'https://www.giuseppebosi.com',
    terminale: 'terminale',
    prova: {
      body: 'Body (JSON, puoi modificarlo)', esegui: '▶ Esegui', copia: 'Copia come curl', copiato: 'Copiato!',
      serveToken: 'Serve un token sandbox: crealo dal pannello', pannello: 'La tua sandbox', ancora: '/db-api/06-sandbox-e-scritture/#la-tua-sandbox',
      salvato: '(viene salvato nel browser).', headerRisposta: 'Header della risposta',
      vuota: '(risposta vuota)', byte: 'byte', nessuno: '(nessuno esposto)', erroreRete: 'errore di rete',
      locale: "Se stai leggendo il corso in locale, avvia l'API (cd api && uv run fastapi dev app/main.py --port 8795).",
    },
    sandbox: {
      titolo: 'La tua sandbox', nessuna: 'Nessuna sandbox attiva in questo browser.', crea: 'Crea sandbox', creaNuova: 'Crea una nuova sandbox',
      reset: 'Azzera i dati', elimina: 'Elimina', copia: 'Copia token', resetOk: 'Dati riportati allo stato iniziale.',
      errore: 'Errore: ', scaduto: 'token scaduto? Creane una nuova.', creata: 'Sandbox creata. Scade il {data} (si rinnova a ogni uso).', locale: 'it-IT',
    },
    attiva: {
      controllo: "Controllo lo stato dell'API…", password: 'Password', placeholder: "password dell'API di prova", accendi: "Accendi l'API",
      nota: "Finché resta accesa puoi eseguire tutti gli esempi del corso. Dopo un'ora senza chiamate si spegne da sola e questa pagina te lo dirà.",
      nonContatto: 'Non riesco a contattare il server. Riprova più tardi.', nonConfigurata: 'L’interruttore non è ancora configurato sul server.',
      accesa: 'L’API di prova è accesa.', spegneTra: 'Si spegne fra circa {min} minuti se nessuno la usa.',
      spenta: 'L’API di prova è spenta.', inserisci: 'Inserisci la password per accenderla.',
      nonRiuscito: 'Non è stato possibile accendere l’API.', nonServer: 'Non riesco a contattare il server.',
    },
    footer: {
      di: 'di', opera: 'opera di divulgazione gratuita.', scrivi: 'Scrivi a', testi: 'Testi', codice: 'codice degli esempi',
      crediti: 'Crediti e licenze', privacy: 'Privacy', github: 'Codice sorgente su GitHub', altri: 'Altri corsi dello stesso autore:',
    },
  },
  en: {
    autore: 'by Prof. Giuseppe Bosi',
    sitoAutore: 'https://www.giuseppebosi.com/en/',
    terminale: 'terminal',
    prova: {
      body: 'Body (JSON, you can edit it)', esegui: '▶ Run', copia: 'Copy as curl', copiato: 'Copied!',
      serveToken: 'This needs a sandbox token: create one in the panel', pannello: 'Your sandbox', ancora: '/en/db-api/06-sandbox-e-scritture/#your-sandbox',
      salvato: '(it is saved in your browser).', headerRisposta: 'Response headers',
      vuota: '(empty response)', byte: 'bytes', nessuno: '(none exposed)', erroreRete: 'network error',
      locale: 'If you are reading the course locally, start the API (cd api && uv run fastapi dev app/main.py --port 8795).',
    },
    sandbox: {
      titolo: 'Your sandbox', nessuna: 'No active sandbox in this browser.', crea: 'Create sandbox', creaNuova: 'Create a new sandbox',
      reset: 'Reset data', elimina: 'Delete', copia: 'Copy token', resetOk: 'Data reset to the initial state.',
      errore: 'Error: ', scaduto: 'token expired? Create a new one.', creata: 'Sandbox created. It expires on {data} (renewed on every use).', locale: 'en-US',
    },
    attiva: {
      controllo: 'Checking the API status…', password: 'Password', placeholder: 'test API password', accendi: 'Switch the API on',
      nota: 'While it is on you can run every example in the course. After an hour without calls it switches itself off, and this page will tell you.',
      nonContatto: 'Cannot reach the server. Please try again later.', nonConfigurata: 'The switch is not configured on the server yet.',
      accesa: 'The test API is on.', spegneTra: 'It switches off in about {min} minutes if nobody uses it.',
      spenta: 'The test API is off.', inserisci: 'Enter the password to switch it on.',
      nonRiuscito: 'The API could not be switched on.', nonServer: 'Cannot reach the server.',
    },
    footer: {
      di: 'by', opera: 'a free educational work.', scrivi: 'Write to', testi: 'Texts', codice: 'example code',
      crediti: 'Credits and licenses', privacy: 'Privacy', github: 'Source code on GitHub', altri: 'Other courses by the same author:',
    },
  },
} as const;

/** Il repo su GitHub è ancora privato: il link compare solo quando diventa pubblico. */
export const GITHUB_PUBBLICO = false;
export const GITHUB = 'https://github.com/JoeBosi/api-json-course';
