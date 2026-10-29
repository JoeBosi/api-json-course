// Elenco delle pagine del corso nell'ordine di lettura, condiviso da sitemap.xml, llms.txt e
// llms-full.txt (così i tre file non vanno mai fuori sincrono con i contenuti).
import { getCollection, type CollectionEntry } from 'astro:content';

export const SITO = 'https://corso-api-json.giuseppebosi.com';
export const AUTORE = { nome: 'Giuseppe Bosi', firma: 'Prof. Giuseppe Bosi', url: 'https://www.giuseppebosi.com', urlEn: 'https://www.giuseppebosi.com/en/', linkedin: 'https://www.linkedin.com/in/giuseppebosi' };
export const ALTRI_CORSI = [
  { titolo: 'Costruisci la tua memoria AI', url: 'https://corso-rag.giuseppebosi.com/' },
  { titolo: 'Corso pratico di llama.cpp', url: 'https://corso-llamacpp.giuseppebosi.com/' },
];

export type Lingua = 'it' | 'en';

const GRUPPI: [Record<Lingua, string>, (id: string) => boolean][] = [
  [{ it: 'Inizia qui', en: 'Start here' }, (id) => ['index', 'presentazione', 'prerequisiti'].includes(id)],
  [{ it: 'Sezione 1 · JSON da 0 a esperto', en: 'Section 1 · JSON from zero to expert' }, (id) => id.startsWith('json/')],
  [{ it: 'Sezione 2 · Database tramite API', en: 'Section 2 · Databases through APIs' }, (id) => id.startsWith('db-api/')],
  [{ it: 'Riferimento', en: 'Reference' }, (id) => id.startsWith('riferimento/')],
  [{ it: 'Informazioni', en: 'About' }, (id) => ['crediti', 'privacy', 'api-attiva'].includes(id)],
];

/** id della pagina senza il prefisso di lingua: 'en/json/01-…' → 'json/01-…', 'en' → 'index' */
export const base = (id: string) => (id === 'en' || id === 'en/index' ? 'index' : id.replace(/^en\//, ''));
export const lingua = (id: string): Lingua => (id === 'en' || id.startsWith('en/') ? 'en' : 'it');
/** URL pubblico di una pagina, dato l'id senza prefisso e la lingua */
export const url = (id: string, l: Lingua = 'it') =>
  `${SITO}/${l === 'en' ? 'en/' : ''}${id === 'index' ? '' : id + '/'}`;

export async function pagineInOrdine(l: Lingua = 'it') {
  const tutte = (await getCollection('docs')).filter((e) => lingua(e.id) === l);
  const ordine = ['index', 'presentazione', 'prerequisiti'];
  const chiave = (e: CollectionEntry<'docs'>) => (ordine.includes(base(e.id)) ? String(ordine.indexOf(base(e.id))) : base(e.id));
  return GRUPPI.map(([titolo, appartiene]) => ({
    titolo: titolo[l],
    pagine: tutte.filter((e) => appartiene(base(e.id))).sort((a, b) => chiave(a).localeCompare(chiave(b))),
  }));
}
