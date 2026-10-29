import type { APIRoute } from 'astro';
import { ALTRI_CORSI, AUTORE, SITO, pagineInOrdine, url } from '../lib/pagine';

// Formato https://llmstxt.org: titolo, riassunto, sezioni con link e una riga di descrizione.
export const GET: APIRoute = async () => {
  const gruppi = await pagineInOrdine();
  const testo = [
    '# Corso JSON & API',
    '',
    '> Corso gratuito in italiano, da 0 a esperto: JSON in Python e TypeScript/JavaScript, poi ' +
      'interrogare database tramite API HTTP (curl spiegato opzione per opzione, filtri, ' +
      'paginazione, relazioni, sandbox, errori, autenticazione, full-text, SQL con JOIN via API). ' +
      `Ogni esempio gira contro un server di prova pubblico (${SITO}/api/v1). ` +
      `Autore: ${AUTORE.firma} (${AUTORE.url}). Testi CC BY 4.0, codice MIT.`,
    '',
    `Versione integrale in un solo file: ${SITO}/llms-full.txt`,
    '',
    ...gruppi.flatMap((g) => [
      `## ${g.titolo}`, '',
      ...g.pagine.map((p) => `- [${p.data.title}](${url(p.id)}): ${p.data.description ?? ''}`.trimEnd()),
      '',
    ]),
    '## Optional', '',
    `- [Documentazione interattiva dell'API (Swagger UI)](${SITO}/api/docs): tutti gli endpoint del server di prova`,
    `- [Sito dell'autore](${AUTORE.url}): ${AUTORE.firma}`,
    ...ALTRI_CORSI.map((c) => `- [${c.titolo}](${c.url}): un altro corso dello stesso autore`),
    '',
  ].join('\n');
  return new Response(testo, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
