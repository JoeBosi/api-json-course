import { chromium } from 'playwright';
const BASE = process.env.BASE ?? 'http://127.0.0.1:8893';
const S = process.env.SHOTS ?? '.';
const b = await chromium.launch();
for (const [nome, vp] of [['desktop', { width: 1280, height: 800 }], ['telefono', { width: 390, height: 844 }]]) {
  const p = await b.newPage({ viewport: vp });
  const errs = []; p.on('pageerror', e => errs.push(String(e)));
  for (const u of ['/en/', '/en/json/01-cos-e-json/']) {
    await p.goto(BASE + u, { waitUntil: 'networkidle' });
    const info = await p.evaluate(() => ({
      lang: document.documentElement.lang,
      autore: document.querySelector('header a.autore')?.textContent, autoreHref: document.querySelector('header a.autore')?.getAttribute('href'),
      lingua: document.querySelector('header a.lingua')?.textContent, linguaHref: document.querySelector('header a.lingua')?.getAttribute('href'),
      linguaVisibile: !!document.querySelector('header a.lingua')?.getBoundingClientRect().width,
      bottone: document.querySelector('prova-api [data-esegui]')?.textContent,
      sidebar: document.querySelector('nav.sidebar a[aria-current="page"]')?.textContent?.trim(),
      footer: document.querySelector('.corso-footer p')?.textContent?.replace(/\s+/g, ' ').trim().slice(0, 90),
      audio: !document.querySelector('lettura-audio')?.hidden,
    }));
    console.log(nome, u, JSON.stringify(info));
    await p.screenshot({ path: `${S}/en-${nome}-${u.replaceAll('/', '_')}.png` });
  }
  if (nome === 'desktop') {
    await p.locator('prova-api [data-esegui]').first().click();
    await p.waitForFunction(() => /\d{3}/.test(document.querySelector('prova-api [data-stato]')?.textContent ?? ''));
    console.log('Run →', await p.locator('prova-api [data-stato]').first().innerText());
  }
  console.log(nome, 'errori JS:', errs.length ? errs : 'nessuno');
  await p.close();
}
await b.close();
