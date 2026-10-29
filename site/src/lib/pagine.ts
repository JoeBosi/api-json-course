// Elenco delle pagine del corso nell'ordine di lettura, condiviso da sitemap.xml, llms.txt e
// llms-full.txt (così i tre file non vanno mai fuori sincrono con i contenuti).
import { getCollection, type CollectionEntry } from 'astro:content';

export const SITO = 'https://corso-api-json.giuseppebosi.com';
export const AUTORE = { nome: 'Giuseppe Bosi', firma: 'Prof. Giuseppe Bosi', url: 'https://www.giuseppebosi.com' };
export const ALTRI_CORSI = [
  { titolo: 'Costruisci la tua memoria AI', url: 'https://corso-rag.giuseppebosi.com/' },
  { titolo: 'Corso pratico di llama.cpp', url: 'https://corso-llamacpp.giuseppebosi.com/' },
];

const GRUPPI: [string, (id: string) => boolean][] = [
  ['Inizia qui', (id) => ['index', 'presentazione', 'prerequisiti'].includes(id)],
  ['Sezione 1 · JSON da 0 a esperto', (id) => id.startsWith('json/')],
  ['Sezione 2 · Database tramite API', (id) => id.startsWith('db-api/')],
  ['Riferimento', (id) => id.startsWith('riferimento/')],
  ['Informazioni', (id) => ['crediti', 'privacy', 'api-attiva'].includes(id)],
];

export const url = (id: string) => `${SITO}/${id === 'index' ? '' : id + '/'}`;

export async function pagineInOrdine() {
  const tutte = await getCollection('docs');
  const ordine = ['index', 'presentazione', 'prerequisiti'];
  const chiave = (e: CollectionEntry<'docs'>) => (ordine.includes(e.id) ? String(ordine.indexOf(e.id)) : e.id);
  return GRUPPI.map(([titolo, appartiene]) => ({
    titolo,
    pagine: tutte.filter((e) => appartiene(e.id)).sort((a, b) => chiave(a).localeCompare(chiave(b))),
  }));
}
