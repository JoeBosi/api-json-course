import { chromium } from 'playwright';
const BASE = process.env.BASE ?? 'https://corso-api-json.giuseppebosi.com';
const b = await chromium.launch();
let ko = 0;
const ok = (c, m) => { console.log(`  ${c ? 'ok ' : 'KO '} ${m}`); if (!c) ko++; };
for (const [nome, vp] of [['desktop 1280', { width: 1280, height: 800 }], ['telefono 390', { width: 390, height: 844 }]]) {
  const p = await b.newPage({ viewport: vp });
  for (const u of ['/', '/presentazione/', '/json/01-cos-e-json/', '/db-api/17-progetto-finale/', '/crediti/', '/api-attiva/']) {
    await p.goto(BASE + u, { waitUntil: 'load' });
    const a = p.locator('header a.autore');
    const vis = await a.isVisible();
    const box = await a.boundingBox();
    const href = await a.getAttribute('href');
    const testo = (await a.innerText()).trim();
    // visibile anche dopo aver scorso la pagina
    await p.evaluate(() => window.scrollTo(0, 3000));
    await p.waitForTimeout(250);
    const box2 = await a.boundingBox();
    const dentro = box2 && box2.y >= 0 && box2.y < vp.height && box2.width > 20;
    ok(vis && testo === 'Prof. Giuseppe Bosi' && href === 'https://www.giuseppebosi.com' && box.width > 20 && dentro,
       `${nome} ${u} — "${testo}" ${box ? Math.round(box.width) + 'px' : 'nessun box'} ${dentro ? 'fissa dopo scroll' : 'NON visibile dopo scroll'}`);
  }
  // il link funziona
  await p.close();
}
const p = await b.newPage({ viewport: { width: 390, height: 844 } });
await p.goto(BASE + '/json/01-cos-e-json/', { waitUntil: 'load' });
const r = await p.evaluate(() => { const a = document.querySelector('header a.autore'); const h = document.querySelector('header'); return { ar: a.getBoundingClientRect(), hr: h.getBoundingClientRect(), overflow: a.scrollWidth > a.clientWidth + 1 }; });
ok(!r.overflow, `telefono 390: la scritta non è tagliata (scrollWidth ${r.overflow ? 'maggiore' : 'ok'})`);
ok(r.ar.right <= r.hr.right + 1, 'telefono 390: la scritta sta dentro la barra');
await p.screenshot({ path: '/tmp/claude-0/-root-Developer-corso-api-json/19ca438c-da98-46d0-9809-24d127a04eaf/scratchpad/telefono-390.png' });
await p.setViewportSize({ width: 1280, height: 800 });
await p.screenshot({ path: '/tmp/claude-0/-root-Developer-corso-api-json/19ca438c-da98-46d0-9809-24d127a04eaf/scratchpad/desktop-1280.png' });
await b.close();
console.log(ko ? `\nKO (${ko})` : '\nTUTTO OK'); process.exit(ko ? 1 : 0);
