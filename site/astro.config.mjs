// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

const cap = (dir, n, titolo) => ({ label: `${n}. ${titolo}`, slug: `${dir}/${String(n).padStart(2, '0')}-${titolo.toLowerCase().replace(/[àáâ]/g, 'a').replace(/[èéê]/g, 'e').replace(/[ìí]/g, 'i').replace(/[òó]/g, 'o').replace(/[ùú]/g, 'u').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}` });

// https://astro.build/config
export default defineConfig({
	site: 'https://corso-api-json.giuseppebosi.com',
	trailingSlash: 'always',
	integrations: [
		starlight({
			title: 'Corso JSON & API',
			description: 'Da 0 a esperto: JSON in Python e TypeScript, poi interrogare database tramite API. Con server di prova.',
			defaultLocale: 'root',
			locales: { root: { label: 'Italiano', lang: 'it' } },
			customCss: ['./src/styles/custom.css'],
			lastUpdated: true,
			pagination: true,
			sidebar: [
				{ label: 'Inizia qui', items: [
					{ label: 'Presentazione', slug: 'presentazione' },
					{ label: 'Prerequisiti e setup', slug: 'prerequisiti' },
				] },
				{ label: 'Sezione 1 · JSON da 0 a esperto', items: [
					cap('json', 1, 'Cos è JSON'), cap('json', 2, 'Sintassi e tipi'), cap('json', 3, 'Limiti e trappole'),
					cap('json', 4, 'Python: json base'), cap('json', 5, 'Python: json avanzato'), cap('json', 6, 'JavaScript: parse e stringify'),
					cap('json', 7, 'TypeScript: tipi e validazione'), cap('json', 8, 'Python: dataclass, TypedDict, pydantic'),
					cap('json', 9, 'JSON Schema'), cap('json', 10, 'JSON annidati e navigazione'), cap('json', 11, 'File grandi e streaming'),
					cap('json', 12, 'Performance'), cap('json', 13, 'JSON nei database'), cap('json', 14, 'JSON e HTTP'),
					cap('json', 15, 'Progetto finale'),
				] },
				{ label: 'Sezione 2 · Database tramite API', items: [
					cap('db-api', 1, 'HTTP e REST'), cap('db-api', 2, 'curl dalla A alla Z'), cap('db-api', 3, 'Primo GET in Python e TypeScript'),
					cap('db-api', 4, 'Filtri, ordinamento, paginazione'), cap('db-api', 5, 'Relazioni e chiavi esterne'),
					cap('db-api', 6, 'Sandbox e scritture'), cap('db-api', 7, 'Errori e status code'), cap('db-api', 8, 'Autenticazione'),
					cap('db-api', 9, 'Ricerca full-text'), cap('db-api', 10, 'Aggregazioni e statistiche'), cap('db-api', 11, 'Query strutturate'),
					cap('db-api', 12, 'SQL via API e JOIN'), cap('db-api', 13, 'Transazioni e integrità'), cap('db-api', 14, 'Performance, cache, rate limit'),
					cap('db-api', 15, 'Sicurezza'), cap('db-api', 16, 'Client robusti'), cap('db-api', 17, 'Progetto finale'),
				] },
				{ label: 'Riferimento', items: [
					{ label: 'Il dataset (Libreria Aurora)', slug: 'riferimento/dataset' },
					{ label: 'Tutti gli endpoint', slug: 'riferimento/endpoint' },
					{ label: 'Cheatsheet curl', slug: 'riferimento/curl' },
					{ label: 'Glossario', slug: 'riferimento/glossario' },
					{ label: 'Crediti e licenze', slug: 'crediti' },
					{ label: 'Privacy', slug: 'privacy' },
					{ label: "Attiva l'API di prova", slug: 'api-attiva' },
					{ label: 'Swagger UI (/api/docs)', link: '/api/docs', attrs: { target: '_blank' } },
				] },
			],
			components: { PageTitle: './src/components/PageTitle.astro', Footer: './src/components/Footer.astro' },
		}),
	],
});
