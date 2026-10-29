import type { APIRoute } from 'astro';
import { AUTORE, pagineInOrdine, url } from '../lib/pagine';

// Tutto il testo del corso in un file, nell'ordine di lettura. Gli import MDX e i tag dei
// componenti interattivi (<Prova>, <Tabs>…) vengono tolti: resta il testo e il codice.
const pulisci = (mdx: string) => mdx
  .replace(/^import .*$/gm, '')
  .replace(/^\s*<\/?[A-Z].*>\s*$/gm, '')
  .replace(/\n{3,}/g, '\n\n')
  .trim();

export const GET: APIRoute = async () => {
  const pagine = (await pagineInOrdine()).flatMap((g) => g.pagine).filter((p) => p.id !== 'index');
  const testo = [
    `# Corso JSON & API — testo integrale`, '',
    `Autore: ${AUTORE.firma} (${AUTORE.url}). Licenza dei testi: CC BY 4.0; codice: MIT.`, '',
    ...pagine.map((p) => `\n---\n\n# ${p.data.title}\n\nURL: ${url(p.id)}\n\n${pulisci(p.body ?? '')}\n`),
  ].join('\n');
  return new Response(testo, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
