import type { APIRoute } from 'astro';
import { base, pagineInOrdine, url } from '../lib/pagine';

// Una voce per pagina e per lingua, con le alternative hreflang (it, en, x-default = italiano)
// come raccomanda Google per i siti multilingue.
export const GET: APIRoute = async () => {
  const it = (await pagineInOrdine('it')).flatMap((g) => g.pagine).map((p) => base(p.id));
  const en = new Set((await pagineInOrdine('en')).flatMap((g) => g.pagine).map((p) => base(p.id)));
  const alternative = (id: string) => [
    `<xhtml:link rel="alternate" hreflang="it" href="${url(id, 'it')}"/>`,
    ...(en.has(id) ? [`<xhtml:link rel="alternate" hreflang="en" href="${url(id, 'en')}"/>`] : []),
    `<xhtml:link rel="alternate" hreflang="x-default" href="${url(id, 'it')}"/>`,
  ].join('');
  const voci = it.flatMap((id) => [
    `  <url><loc>${url(id, 'it')}</loc>${alternative(id)}</url>`,
    ...(en.has(id) ? [`  <url><loc>${url(id, 'en')}</loc>${alternative(id)}</url>`] : []),
  ]);
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n${voci.join('\n')}\n</urlset>\n`,
    { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
