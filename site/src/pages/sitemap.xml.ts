import type { APIRoute } from 'astro';
import { pagineInOrdine, url } from '../lib/pagine';

export const GET: APIRoute = async () => {
  const righe = (await pagineInOrdine()).flatMap((g) => g.pagine).map((p) => `  <url><loc>${url(p.id)}</loc></url>`);
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${righe.join('\n')}\n</urlset>\n`,
    { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
