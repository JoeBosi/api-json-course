import { chromium } from 'playwright';
const BASE = process.env.BASE ?? 'https://corso-api-json.giuseppebosi.com';
const b = await chromium.launch();
const S = '/tmp/claude-0/-root-Developer-corso-api-json/19ca438c-da98-46d0-9809-24d127a04eaf/scratchpad';
for (const [nome, vp] of [['desktop', { width: 1280, height: 800 }], ['telefono', { width: 390, height: 844 }]]) {
  const p = await b.newPage({ viewport: vp, deviceScaleFactor: 2 });
  await p.goto(BASE + '/json/01-cos-e-json/', { waitUntil: 'load' });
  const a = p.locator('header a.autore');
  const st = await a.evaluate(e => { const c = getComputedStyle(e); const t = getComputedStyle(e.previousElementSibling);
    return { bg: c.backgroundColor, bordo: c.borderStyle + ' ' + c.borderWidth, raggio: c.borderRadius, ombra: c.boxShadow,
             pad: c.padding, deco: c.textDecorationLine, size: c.fontSize, titoloSize: t.fontSize,
             sottoIlTitolo: e.getBoundingClientRect().top >= e.previousElementSibling.getBoundingClientRect().bottom - 1 }; });
  console.log(nome, JSON.stringify(st));
  await a.hover(); await p.waitForTimeout(200);
  console.log(nome, 'hover →', await a.evaluate(e => getComputedStyle(e).textDecorationLine));
  await p.mouse.move(0, 400);
  const box = await p.locator('header').boundingBox();
  await p.screenshot({ path: `${S}/firma-${nome}.png`, clip: { x: 0, y: 0, width: Math.min(vp.width, 520), height: Math.ceil(box.height) + 8 } });
  await p.close();
}
await b.close();
