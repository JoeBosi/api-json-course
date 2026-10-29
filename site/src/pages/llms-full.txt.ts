import type { APIRoute } from 'astro';
import { AUTORE, base, pagineInOrdine, url, type Lingua } from '../lib/pagine';

// Tutto il testo del corso in un file, nell'ordine di lettura. Gli import MDX e i tag dei
// componenti interattivi (<Prova>, <Tabs>…) vengono tolti: resta il testo e il codice.
const pulisci = (mdx: string) => mdx
  .replace(/^import .*$/gm, '')
  .replace(/^\s*<\/?[A-Z].*>\s*$/gm, '')
  .replace(/\n{3,}/g, '\n\n')
  .trim();

const INTESTAZIONE: Record<Lingua, string[]> = {
  it: ['# Corso JSON & API — testo integrale', '', `Autore: ${AUTORE.firma} (${AUTORE.url}). Licenza dei testi: CC BY 4.0; codice: MIT.`],
  en: ['# JSON & API Course — full text', '', `Author: ${AUTORE.firma} (${AUTORE.urlEn}). Texts licensed CC BY 4.0; code MIT.`],
};

/** Testo integrale del corso in una lingua: usato da /llms-full.txt e /llms-full-en.txt. */
export async function testoIntegrale(l: Lingua) {
  const pagine = (await pagineInOrdine(l)).flatMap((g) => g.pagine).filter((p) => base(p.id) !== 'index');
  const testo = [
    ...INTESTAZIONE[l], '',
    ...pagine.map((p) => `\n---\n\n# ${p.data.title}\n\nURL: ${url(base(p.id), l)}\n\n${pulisci(p.body ?? '')}\n`),
  ].join('\n');
  return new Response(testo, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}

export const GET: APIRoute = () => testoIntegrale('it');
