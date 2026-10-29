import type { APIRoute } from 'astro';
import { SITO } from '../lib/pagine';

// Tutti i crawler sono benvenuti, compresi quelli dei motori di ricerca basati su IA.
export const GET: APIRoute = () => new Response(
  ['User-agent: *', 'Allow: /', '',
   ...['GPTBot', 'ClaudeBot', 'PerplexityBot', 'Google-Extended'].flatMap((b) => [`User-agent: ${b}`, 'Allow: /', '']),
   `Sitemap: ${SITO}/sitemap.xml`, ''].join('\n'),
  { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
