// Verifica end-to-end nel browser headless: widget Prova, pannello Sandbox, ricerca, player audio
// (associazione paragrafi ↔ pagina su TUTTE le pagine, soglia 95%).
// Uso: BASE=http://127.0.0.1:8795 node tests/e2e.mjs   (serve l'API attiva che serve site/dist)
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const BASE = process.env.BASE ?? 'http://127.0.0.1:8795';
const b = await chromium.launch(); const p = await b.newPage();
const errs = []; p.on('pageerror', e => errs.push(String(e)));
let ko = 0;
const ok = (c, msg) => { console.log(`  ${c ? 'ok ' : 'KO '} ${msg}`); if (!c) ko++; };

console.log('Widget Prova');
await p.goto(`${BASE}/json/01-cos-e-json/`, { waitUntil: 'networkidle' });
await p.locator('prova-api [data-esegui]').first().click();
await p.waitForFunction(() => /\d{3}/.test(document.querySelector('prova-api [data-stato]')?.textContent ?? ''));
ok((await p.locator('prova-api [data-stato]').first().innerText()).startsWith('200'), 'GET /books/1 → 200 dalla pagina');

console.log('Sandbox + POST');
await p.goto(`${BASE}/db-api/06-sandbox-e-scritture/`, { waitUntil: 'networkidle' });
await p.locator('sandbox-pannello [data-crea]').click();
await p.waitForFunction(() => document.querySelector('sandbox-pannello [data-token]')?.textContent?.includes('sb_'));
const post = p.locator('prova-api[data-method="POST"][data-sandbox="1"]').first();
await post.locator('[data-esegui]').click();
await p.waitForFunction(() => [...document.querySelectorAll('prova-api[data-method="POST"] [data-stato]')].some(e => /\d{3}/.test(e.textContent)));
ok((await post.locator('[data-stato]').innerText()).startsWith('201'), 'POST in sandbox → 201');
await p.evaluate(() => fetch('/api/v1/sandbox', { method: 'DELETE', headers: { Authorization: 'Bearer ' + localStorage.getItem('corso-api-json.sandbox') } }));

console.log('Ricerca');
await p.goto(`${BASE}/`, { waitUntil: 'networkidle' });
await p.locator('site-search button').first().click(); await p.locator('site-search input').fill('sandbox'); await p.waitForTimeout(1500);
ok((await p.locator('site-search .pagefind-ui__result').count()) > 0, 'Pagefind trova "sandbox"');

console.log('Player audio: associazione paragrafi su tutte le pagine');
const pronto = () => document.querySelector('lettura-audio') && !document.querySelector('lettura-audio').hidden && document.querySelector('lettura-audio').pars.length > 0;
const manifest = JSON.parse(readFileSync(new URL('../public/audio/manifest.json', import.meta.url)));
let totP = 0, totA = 0;
for (const slug of Object.keys(manifest.pagine)) {
  await p.goto(`${BASE}/${slug}/`, { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(pronto, null, { timeout: 15000 });
  const r = await p.evaluate(() => { const l = document.querySelector('lettura-audio'); return { t: l.pars.length, a: l.el.filter(Boolean).length, miss: l.pars.filter((x, k) => !l.el[k]).slice(0, 2).map(x => x.t.slice(0, 40)) }; });
  totP += r.t; totA += r.a;
  if (r.a / r.t < 0.95) ok(false, `${slug}: ${r.a}/${r.t} — es. ${JSON.stringify(r.miss)}`);
}
ok(totA / totP >= 0.95, `paragrafi associati ${totA}/${totP} (${(100 * totA / totP).toFixed(1)}%)`);

console.log('Player audio: comandi');
await p.evaluate(() => localStorage.removeItem('corso-api-json.lettura'));
await p.goto(`${BASE}/json/01-cos-e-json/`, { waitUntil: 'networkidle' });
await p.waitForFunction(pronto);
ok(await p.locator('lettura-audio [data-barra]').isHidden(), 'di default solo il pulsante 🔊 (barra chiusa, niente autoplay)');
await p.locator('lettura-audio [data-apri]').click();
ok(await p.locator('lettura-audio [data-barra]').isVisible(), 'clic su 🔊 apre la barra');
const voci = await p.locator('lettura-audio [data-voce] option').allInnerTexts();
ok(!voci.some(v => v.includes('Piper')), `nessuna voce Piper nel selettore (${voci.length} opzioni)`);
// Chromium headless non ha voci italiane: in quel caso il lettore deve dirlo, non restare muto
const nota = (await p.locator('lettura-audio [data-nota]').textContent()) ?? '';
ok(voci.length > 0 || /non ha voci italiane/.test(nota),
   voci.length > 0 ? `${voci.length} voci del browser disponibili` : 'senza voci italiane il lettore avvisa');
await p.locator('lettura-audio [data-play]').click(); await p.waitForSelector('.in-lettura');
ok((await p.locator('lettura-audio [data-play]').innerText()).includes('Pausa'), 'play → il pulsante diventa ⏸ Pausa');
await p.locator('lettura-audio [data-play]').click();
const i1 = await p.evaluate(() => document.querySelector('lettura-audio').i);
await p.waitForTimeout(2500);
const i2 = await p.evaluate(() => document.querySelector('lettura-audio').i);
ok(i1 === i2 && (await p.evaluate(() => document.querySelector('lettura-audio').audio.paused)), 'pausa → audio fermo, non avanza');
await p.locator('lettura-audio [data-stop]').click();
ok((await p.locator('.in-lettura').count()) === 0 && (await p.locator('lettura-audio [data-play]').innerText()).includes('Ascolta'), 'stop → evidenziazione tolta, si riparte dall\'inizio');
await p.locator('lettura-audio [data-chiudi]').click();
ok(await p.locator('lettura-audio [data-apri]').isVisible(), '✕ chiude la barra');
await p.locator('lettura-audio [data-apri]').click();
await p.locator('lettura-audio [data-disattiva]').click();
await p.goto(`${BASE}/json/02-sintassi-e-tipi/`, { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
ok(await p.locator('lettura-audio').isHidden(), '"Non mostrare più" → nascosto anche nelle altre pagine');
await p.goto(`${BASE}/presentazione/`, { waitUntil: 'networkidle' });
await p.locator('lettura-impostazioni [data-toggle]').click();
await p.goto(`${BASE}/json/02-sintassi-e-tipi/`, { waitUntil: 'networkidle' });
await p.waitForFunction(pronto);
ok(await p.locator('lettura-audio [data-apri]').isVisible(), 'riattivata dalla Presentazione');
// Nota (28/10/2026): aprendo la ricerca, Pagefind lancia una volta "Unexpected end of input"
// durante la propria inizializzazione, PRIMA di qualunque query e anche servendo dist/ con un
// server statico qualsiasi: è suo, non nostro, e la ricerca funziona (vedi il controllo sopra).
// Resta elencato qui sotto: se cambia o se ne aggiungono altri, il test lo fa vedere.
const NOTI = ['Unexpected end of input'];
const nostri = errs.filter((e) => !NOTI.some((n) => e.includes(n)));
if (errs.length !== nostri.length) console.log(`  --  ignorato errore noto di Pagefind (${errs.length - nostri.length}x)`);
ok(nostri.length === 0, `nessun errore JavaScript nostro ${nostri.length ? JSON.stringify(nostri) : ''}`);
await b.close();
console.log(ko ? `\nE2E KO (${ko})` : '\nE2E OK'); process.exit(ko ? 1 : 0);
