// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

const cap = (dir, n, titolo, en) => ({ label: `${n}. ${titolo}`, translations: { en: `${n}. ${en}` }, slug: `${dir}/${String(n).padStart(2, '0')}-${titolo.toLowerCase().replace(/[àáâ]/g, 'a').replace(/[èéê]/g, 'e').replace(/[ìí]/g, 'i').replace(/[òó]/g, 'o').replace(/[ùú]/g, 'u').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}` });

// https://astro.build/config
export default defineConfig({
	site: 'https://corso-api-json.giuseppebosi.com',
	trailingSlash: 'always',
	integrations: [
		starlight({
			title: { it: 'Corso JSON & API', en: 'JSON & API Course' },
			description: 'Da 0 a esperto: JSON in Python e TypeScript, poi interrogare database tramite API. Con server di prova.',
			defaultLocale: 'root',
			locales: { root: { label: 'Italiano', lang: 'it' }, en: { label: 'English', lang: 'en' } },
			customCss: ['./src/styles/custom.css'],
			head: [
				{
					tag: 'script',
					attrs: { type: 'application/ld+json' },
					content: JSON.stringify({
						'@context': 'https://schema.org',
						'@type': 'Course',
						name: 'Corso JSON & API: da 0 a esperto',
						description: 'Corso gratuito su JSON in Python e TypeScript/JavaScript e sull\'interrogazione di database tramite API HTTP, con un server di prova pubblico. In italiano e in inglese.',
						url: 'https://corso-api-json.giuseppebosi.com/',
						inLanguage: ['it', 'en'],
						workExample: [
							{ '@type': 'CreativeWork', inLanguage: 'it', url: 'https://corso-api-json.giuseppebosi.com/' },
							{ '@type': 'CreativeWork', inLanguage: 'en', name: 'JSON & API Course: from zero to expert', url: 'https://corso-api-json.giuseppebosi.com/en/' },
						],
						isAccessibleForFree: true,
						license: 'https://creativecommons.org/licenses/by/4.0/',
						author: { '@type': 'Person', name: 'Giuseppe Bosi', honorificPrefix: 'Prof.', url: 'https://www.giuseppebosi.com', sameAs: ['https://www.linkedin.com/in/giuseppebosi'] },
						provider: { '@type': 'Person', name: 'Giuseppe Bosi', url: 'https://www.giuseppebosi.com' },
					}),
				},
			],
			lastUpdated: true,
			pagination: true,
			sidebar: [
				{ label: 'Inizia qui', translations: { en: 'Start here' }, items: [
					{ label: 'Presentazione', translations: { en: 'About the course' }, slug: 'presentazione' },
					{ label: 'Prerequisiti e setup', translations: { en: 'Prerequisites and setup' }, slug: 'prerequisiti' },
				] },
				{ label: 'Sezione 1 · JSON da 0 a esperto', translations: { en: 'Section 1 · JSON from zero to expert' }, items: [
					cap('json', 1, 'Cos è JSON', 'What is JSON'), cap('json', 2, 'Sintassi e tipi', 'Syntax and types'), cap('json', 3, 'Limiti e trappole', 'Limits and pitfalls'),
					cap('json', 4, 'Python: json base', 'Python: json basics'), cap('json', 5, 'Python: json avanzato', 'Python: advanced json'), cap('json', 6, 'JavaScript: parse e stringify', 'JavaScript: parse and stringify'),
					cap('json', 7, 'TypeScript: tipi e validazione', 'TypeScript: types and validation'), cap('json', 8, 'Python: dataclass, TypedDict, pydantic', 'Python: dataclass, TypedDict, pydantic'),
					cap('json', 9, 'JSON Schema', 'JSON Schema'), cap('json', 10, 'JSON annidati e navigazione', 'Nested JSON and navigation'), cap('json', 11, 'File grandi e streaming', 'Large files and streaming'),
					cap('json', 12, 'Performance', 'Performance'), cap('json', 13, 'JSON nei database', 'JSON in databases'), cap('json', 14, 'JSON e HTTP', 'JSON and HTTP'),
					cap('json', 15, 'Progetto finale', 'Final project'),
				] },
				{ label: 'Sezione 2 · Database tramite API', translations: { en: 'Section 2 · Databases through APIs' }, items: [
					cap('db-api', 1, 'HTTP e REST', 'HTTP and REST'), cap('db-api', 2, 'curl dalla A alla Z', 'curl from A to Z'), cap('db-api', 3, 'Primo GET in Python e TypeScript', 'First GET in Python and TypeScript'),
					cap('db-api', 4, 'Filtri, ordinamento, paginazione', 'Filtering, sorting, pagination'), cap('db-api', 5, 'Relazioni e chiavi esterne', 'Relations and foreign keys'),
					cap('db-api', 6, 'Sandbox e scritture', 'Sandbox and writes'), cap('db-api', 7, 'Errori e status code', 'Errors and status codes'), cap('db-api', 8, 'Autenticazione', 'Authentication'),
					cap('db-api', 9, 'Ricerca full-text', 'Full-text search'), cap('db-api', 10, 'Aggregazioni e statistiche', 'Aggregations and statistics'), cap('db-api', 11, 'Query strutturate', 'Structured queries'),
					cap('db-api', 12, 'SQL via API e JOIN', 'SQL over the API and JOINs'), cap('db-api', 13, 'Transazioni e integrità', 'Transactions and integrity'), cap('db-api', 14, 'Performance, cache, rate limit', 'Performance, caching, rate limits'),
					cap('db-api', 15, 'Sicurezza', 'Security'), cap('db-api', 16, 'Client robusti', 'Robust clients'), cap('db-api', 17, 'Progetto finale', 'Final project'),
				] },
				{ label: 'Riferimento', translations: { en: 'Reference' }, items: [
					{ label: 'Il dataset (Libreria Aurora)', translations: { en: 'The dataset (Aurora Bookshop)' }, slug: 'riferimento/dataset' },
					{ label: 'Tutti gli endpoint', translations: { en: 'All endpoints' }, slug: 'riferimento/endpoint' },
					{ label: 'Cheatsheet curl', translations: { en: 'curl cheatsheet' }, slug: 'riferimento/curl' },
					{ label: 'Glossario', translations: { en: 'Glossary' }, slug: 'riferimento/glossario' },
					{ label: 'Crediti e licenze', translations: { en: 'Credits and licenses' }, slug: 'crediti' },
					{ label: 'Privacy', translations: { en: 'Privacy' }, slug: 'privacy' },
					{ label: "Attiva l'API di prova", translations: { en: 'Switch on the test API' }, slug: 'api-attiva' },
					{ label: 'Swagger UI (/api/docs)', translations: { en: 'Swagger UI (/api/docs)' }, link: 'https://corso-api-json.giuseppebosi.com/api/docs', attrs: { target: '_blank' } },
				] },
			],
			components: { PageTitle: './src/components/PageTitle.astro', Footer: './src/components/Footer.astro', SiteTitle: './src/components/SiteTitle.astro' },
		}),
	],
});
