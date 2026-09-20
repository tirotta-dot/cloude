// Verifica visiva locale del Second Brain: serve split/ via HTTP, stubba window.claude (sola lettura), fotografa le schede.
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const base = process.env.SB_URL || 'http://127.0.0.1:8765/index.html';
  const out = process.env.SB_OUT || path.join(__dirname, 'shots'); fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await browser.newContext({ viewport: { width: 1380, height: 900 }, locale: 'it-IT' });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('response', r => { if (r.status() >= 400 && !/favicon\.ico$/.test(r.url())) errors.push('http ' + r.status() + ': ' + r.url()); });
  page.on('console', m => { if (m.type() === 'error' && !/CERT_AUTHORITY|favicon|Failed to load resource/.test(m.text())) errors.push('console: ' + m.text()); });
  await page.addInitScript(() => { window.claude = { use: () => new Promise(r => setTimeout(() => r(null), 30)) }; try { localStorage.clear(); } catch (e) {} });
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  await page.addStyleTag({ content: 'html{scroll-behavior:auto!important}' }); // gli screenshot di elemento leggono il box a scroll finito
  const report = {};
  // screenshot di un elemento alto: si allarga la finestra all'altezza del blocco prima di misurarlo, così non scatta il fullPage interno (che ridisegna la pagina e sposta il ritaglio)
  const shotEl = async (sel, name) => { const el = page.locator(sel).first(); if (!(await el.count())) { errors.push('non trovato per screenshot: ' + sel); return; }
    const h0 = await el.evaluate(e => Math.ceil(e.getBoundingClientRect().height));
    await page.setViewportSize({ width: 1380, height: Math.min(Math.max(900, h0 + 160), 9000) }); await page.waitForTimeout(500);
    await el.scrollIntoViewIfNeeded(); await page.waitForTimeout(300);
    const r = await el.evaluate(e => { const b = e.getBoundingClientRect(); return { top: b.top, height: b.height, vh: window.innerHeight }; });
    if (r.height + 20 > r.vh) await page.setViewportSize({ width: 1380, height: Math.min(Math.ceil(r.height) + 160, 9000) }), await page.waitForTimeout(400), await el.scrollIntoViewIfNeeded(), await page.waitForTimeout(300);
    await el.screenshot({ path: path.join(out, name + '.png') }).catch(e => errors.push('screenshot ' + name + ': ' + e.message));
    report['shot_' + name] = { altezzaBlocco: Math.round(r.height), viewport: r.vh };
    await page.setViewportSize({ width: 1380, height: 900 }); await page.waitForTimeout(400); };
  const shot = async (name) => { await page.waitForTimeout(400); await page.screenshot({ path: path.join(out, name + '.png'), fullPage: false }); };
  report.title = await page.title();
  await shot('01-oggi');
  const click = async (sel, name) => { const b = page.locator(sel).first(); if (await b.count()) { await b.click().catch(e => errors.push('click ' + name + ': ' + e.message)); await shot(name); return true; } errors.push('non trovato: ' + sel); return false; };
  await click('#v-dash', '02-commesse');
  report.commessePicker = await page.evaluate(() => Array.from(document.querySelectorAll('.picker .pk b')).map(b => b.textContent));
  await click('#cm-ord', '03-ordini');
  report.ordiniKpi = await page.evaluate(() => Array.from(document.querySelectorAll('.cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()).slice(0, 4));
  await click('#cm-cash', '04-cashflow-tutte');
  report.cashTutteHead = await page.evaluate(() => Array.from(document.querySelectorAll('.cf thead th')).map(t => t.textContent).slice(0, 8));
  await click('.picker .pk[data-code="SBC-15-26"]', '05-sel-sbc15');
  await click('#cm-cash', '06-cashflow-sbc15');
  report.cashSbc15 = await page.evaluate(() => Array.from(document.querySelectorAll('.cf tbody tr')).map(r => Array.from(r.children).map(td => td.textContent).join(' | ')));
  report.fornSbc15 = await page.evaluate(() => Array.from(document.querySelectorAll('.cfforn tbody tr')).slice(0, 6).map(r => r.textContent.replace(/\s+/g, ' ').trim()));
  await click('#cm-scad', '07-scadenze');
  report.scadRows = await page.evaluate(() => Array.from(document.querySelectorAll('.otab tbody tr')).slice(0, 8).map(r => r.textContent.replace(/\s+/g, ' ').trim()));
  await click('#c-none', '08-none');
  await click('#cm-scad', '09-scadenze-tutte');
  report.scadKpi = await page.evaluate(() => Array.from(document.querySelectorAll('.cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()).slice(0, 3));
  await click('#cm-cli', '09b-clienti');
  report.clienti = await page.evaluate(() => Array.from(document.querySelectorAll('.pcard > b')).slice(0, 5).map(b => b.textContent.replace(/\s+/g, ' ').trim()));
  await click('#cm-ctr', '09c-contratti');
  report.contrattiRows = await page.evaluate(() => document.querySelectorAll('.otab tbody tr').length);
  await click('#cm-bdg', '09d-budget-tutte');
  await page.waitForTimeout(1600);
  report.bdgFiles = await page.evaluate(() => Array.from(document.querySelectorAll('[data-bdgfile]')).map(a => a.getAttribute('href')));
  if (report.bdgFiles.length < 5) errors.push('Budget: attesi almeno 5 link ai file pubblicati, trovati ' + report.bdgFiles.length);
  for (const u of report.bdgFiles) { const r = await page.request.get(base.replace(/index\.html$/, '') + u); if (!r.ok()) errors.push('file pubblicato non raggiungibile: ' + u + ' (' + r.status() + ')'); }
  report.bdgRiep = await page.evaluate(() => ({ righe: document.querySelectorAll('.bdgt tbody tr').length, kpi: Array.from(document.querySelectorAll('.bdgk .cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()).slice(0, 5), btn: (document.getElementById('cm-bdg') || {}).textContent }));
  await click('.picker .pk[data-code="SBC-15-26"]', '09e-sel-sbc15');
  await click('#cm-bdg', '09f-budget-sbc15');
  await page.waitForTimeout(1600);
  await shotEl('#bdg-SBC-15-26', '09f-budget-blocco');
  report.bdgSbc15 = await page.evaluate(() => ({ righe: Array.from(document.querySelectorAll('#bdg-SBC-15-26 .bdgt tbody tr')).map(r => r.textContent.replace(/\s+/g, ' ').trim().slice(0, 140)), kpi: Array.from(document.querySelectorAll('#bdg-SBC-15-26 .bdgk .cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()), proposta: !!document.querySelector('#bdg-SBC-15-26 .bdgprop'), editorRighe: document.querySelectorAll('#bdged-SBC-15-26 tbody tr').length }));
  report.bdgProp = await page.evaluate(() => { const p = document.querySelector('#bdg-SBC-15-26 .bdgprop'); return p ? { txt: p.textContent.replace(/\s+/g, ' ').trim().slice(0, 420), opts: Array.from(p.querySelectorAll('option')).map(o => o.textContent), extProposti: Array.from(document.querySelectorAll('#bdged-SBC-15-26 input[data-f="ext"]')).map(i => i.value).slice(0, 8) } : null; });
  { const s = page.locator('[data-bdgrif="SBC-15-26"]'); if (await s.count()) { const v = await s.evaluate(el => el.options.length > 1 ? el.options[1].value : null); if (v) { await s.selectOption(v); await page.waitForTimeout(1600); report.bdgRifSingola = await page.evaluate(() => ({ kpi: (document.querySelector('#bdg-SBC-15-26 .bdgk .cm-kpi:nth-child(2)') || {}).textContent, banner: (document.querySelector('#bdg-SBC-15-26 .bdgprop') || {}).textContent.replace(/\s+/g, ' ').slice(0, 200) })); await s.selectOption('media'); await page.waitForTimeout(1600); } } }
  await click('[data-bdgv="listino"]', '09g-budget-listino');
  report.bdgListino = await page.evaluate(() => ({ head: Array.from(document.querySelectorAll('#bdg-SBC-15-26 .bdgt thead th')).map(t => t.textContent), prima: (document.querySelector('#bdg-SBC-15-26 .bdgt tbody tr') || {}).textContent }));
  await page.evaluate(() => { const ed = document.getElementById('bdged-SBC-15-26'); if (ed) ed.open = true; const inp = ed && ed.querySelector('input[data-f="ext"]'); if (inp) inp.value = '150000'; });
  await click('[data-bdgsave="SBC-15-26"]', '09h-budget-salvato');
  await page.waitForTimeout(1600);
  report.bdgDopoSalva = await page.evaluate(() => ({ kpi: Array.from(document.querySelectorAll('#bdg-SBC-15-26 .bdgk .cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()).slice(1, 5), prima: (document.querySelector('#bdg-SBC-15-26 .bdgt tbody tr') || {}).textContent, status: (document.querySelector('.status') || {}).textContent }));
  { const hu = page.locator('#bdg-hu-SBC-15-26'); if (await hu.count()) { await page.evaluate(() => { const ed = document.getElementById('bdged-SBC-15-26'); if (ed) ed.open = true; }); await hu.fill('120'); await click('[data-bdgsave="SBC-15-26"]', '09h2-budget-ore-commessa'); await page.waitForTimeout(1600); } else errors.push('non trovato: #bdg-hu-SBC-15-26'); }
  report.bdgOreCm = await page.evaluate(() => ({ huInput: (document.getElementById('bdg-hu-SBC-15-26') || {}).value, summary: (document.querySelector('#bdg-SBC-15-26 .cfforn summary') || {}).textContent, ore: Array.from(document.querySelectorAll('#bdg-SBC-15-26 .cfforn tbody tr')).map(r => r.textContent.replace(/\s+/g, ' ').trim().slice(0, 200)), utile: Array.from(document.querySelectorAll('#bdg-SBC-15-26 .bdgk .cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()).filter(t => /utile/.test(t)), kpiBudget: (document.querySelector('#bdg-SBC-15-26 .bdgk .cm-kpi:nth-child(2)') || {}).textContent, status: (document.querySelector('.status') || {}).textContent }));
  await click('#c-none', '09i-none');
  await click('#cv-ev', '09j-evase');
  report.evase = await page.evaluate(() => ({ n: document.querySelectorAll('.picker .pk').length, btn: (document.getElementById('cv-ev') || {}).textContent }));
  await click('#cm-bdg', '09k-budget-evase-tutte');
  await page.waitForTimeout(1600);
  report.bdgRiepEvase = await page.evaluate(() => ({ righe: document.querySelectorAll('.bdgt tbody tr').length, kpi: Array.from(document.querySelectorAll('.bdgk .cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()).slice(0, 5), prime: Array.from(document.querySelectorAll('.bdgt tbody tr')).slice(0, 4).map(r => r.textContent.replace(/\s+/g, ' ').trim().slice(0, 160)) }));
  await shotEl('.bdgk', '09k2-riepilogo-evase-kpi'); // tabella dell'utile consuntivo delle commesse chiuse: KPI e prime righe
  { const t = page.locator('.bdgt').first(); if (await t.count()) { await t.evaluate(e => e.scrollIntoView({ block: 'start' })); await page.waitForTimeout(300); await shot('09k3-riepilogo-evase-tab'); } }
  await click('.picker .pk[data-code="SBC-14-24"]', '09l-sel-sbc14');
  await click('#cm-bdg', '09m-budget-sbc14');
  await page.waitForTimeout(1600);
  await shotEl('#bdg-SBC-14-24', '09m-budget-evasa-blocco');
  report.bdgSbc14Prezzo = await page.evaluate(() => ({ kpi: (document.querySelector('#bdg-SBC-14-24 .bdgk .cm-kpi') || {}).textContent, prz: !!document.getElementById('bdg-prz-SBC-14-24') }));
  // R26: evasa con prezzo del gestionale incompleto → niente utile e avviso; il prezzo di vendita si scrive dall'editor
  await click('.picker .pk[data-code="FC-14-17"]', '09n-sel-fc14');
  await click('#cm-bdg', '09n-budget-fc14');
  await page.waitForTimeout(1600);
  report.bdgDubbio = await page.evaluate(() => ({ kpi: Array.from(document.querySelectorAll('#bdg-FC-14-17 .bdgk .cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()), prz: !!document.getElementById('bdg-prz-FC-14-17') }));
  if (!/incompleto/.test((report.bdgDubbio.kpi || []).join(' '))) errors.push('FC-14-17: manca l\'avviso di prezzo incompleto');
  if (!report.bdgDubbio.prz) errors.push('FC-14-17: manca il campo prezzo di vendita nell\'editor');
  await page.evaluate(() => { const ed = document.getElementById('bdged-FC-14-17'); if (ed) ed.open = true; const i = document.getElementById('bdg-prz-FC-14-17'); if (i) i.value = '1500000'; });
  await click('[data-bdgsave="FC-14-17"]', '09n2-prezzo-salvato');
  await page.waitForTimeout(1600);
  report.bdgDubbioDopo = await page.evaluate(() => ({ kpi: Array.from(document.querySelectorAll('#bdg-FC-14-17 .bdgk .cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()).filter(t => /prezzo|utile/.test(t)) }));
  if (!/1\.500\.000/.test((report.bdgDubbioDopo.kpi || []).join(' '))) errors.push('FC-14-17: il prezzo scritto nell\'editor non è stato salvato');
  report.bdgEvasa = await page.evaluate(() => ({ kpi: Array.from(document.querySelectorAll('#bdg-SBC-14-24 .bdgk .cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()), banner: !!document.querySelector('#bdg-SBC-14-24 .bdgprop'), righe: Array.from(document.querySelectorAll('#bdg-SBC-14-24 .bdgt tbody tr')).slice(0, 5).map(r => r.textContent.replace(/\s+/g, ' ').trim().slice(0, 120)), editorOpen: (document.getElementById('bdged-SBC-14-24') || {}).open }));
  await click('#c-none', '09n-none');
  { const e0 = errors.length; await click('#cm-schede', '09n2-schede-evase'); await page.waitForTimeout(800);
    report.schedeEvase = await page.evaluate(() => ({ cmcSenzaSelezione: document.querySelectorAll('.cmc').length, pk: document.querySelectorAll('.picker .pk').length, apri: (document.getElementById('c-all') || {}).textContent || null, cview: (document.getElementById('cv-ev') || {}).getAttribute ? document.getElementById('cv-ev').getAttribute('aria-pressed') : null, kpi: Array.from(document.querySelectorAll('.cm-kpis .cm-kpi')).map(k => k.textContent.replace(/\s+/g, ' ').trim()).slice(0, 5) }));
    await click('#c-all', '09n3-schede-evase-aperte'); await page.waitForTimeout(1200); // apre tutte le schede evase (anche quelle importate dal gestionale, con campi sparsi)
    Object.assign(report.schedeEvase, await page.evaluate(() => ({ cmc: document.querySelectorAll('.cmc').length, prime: Array.from(document.querySelectorAll('.cmc')).slice(0, 3).map(c => c.textContent.replace(/\s+/g, ' ').trim().slice(0, 160)), gest: Array.from(document.querySelectorAll('.cmc')).filter(c => /A-02-14|2013-001/.test(c.textContent)).slice(0, 2).map(c => c.textContent.replace(/\s+/g, ' ').trim().slice(0, 200)) })));
    report.schedeEvase.errors = errors.slice(e0);
    await click('#c-none', '09n4-none'); }
  await click('#cv-att', '09o-attive');
  await click('#cm-schede', '09p-schede');
  for (const [sel, name] of [['#v-board', '10-task'], ['#v-bill', '11-denaro'], ['#v-cal', '12-calendario'], ['#v-pers', '13-persone'], ['#v-trip', '14-viaggi']]) await click(sel, name);
  report.cassaHead = await page.evaluate(() => { const el = document.querySelector('#v-bill'); return null; });
  await click('#v-bill', '11b-denaro');
  report.cassaInQuadro = await page.evaluate(() => document.querySelectorAll('.cf tbody tr').length);
  await click('[data-den="flusso"]', '11c-denaro-flusso');
  report.cassa = await page.evaluate(() => Array.from(document.querySelectorAll('.cf tbody tr')).map(r => r.children[0].textContent + ' | ' + Array.from(r.children).slice(1, 5).map(td => td.textContent).join(' | ')));
  report.bozzePronte = await page.evaluate(() => document.querySelectorAll('a.gml.bz').length);
  await click('#v-pers', '13-persone');
  await click('[data-per="forn"]', '13b-fornitori');
  report.fornitori = await page.evaluate(() => ({ n: document.querySelectorAll('.pcard').length, first: Array.from(document.querySelectorAll('.pcard')).slice(0, 3).map(c => c.textContent.replace(/\s+/g, ' ').trim().slice(0, 160)) }));
  await click('[data-solf]:not([disabled])', '13c-sollecito');
  report.solf = await page.evaluate(() => Array.from(document.querySelectorAll('[data-solf]')).slice(0, 3).map(b => b.textContent));
  await click('[data-ordf]', '13d-ordini-fornitore');
  report.ordQ = await page.evaluate(() => (document.querySelector('.fbar') || {}).textContent || null);
  await click('#v-pers', '13-persone');
  await click('[data-per="capi"]', '13e-capi');
  report.deleghe = await page.evaluate(() => Array.from(document.querySelectorAll('.otab tbody tr')).slice(0, 5).map(r => r.textContent.replace(/\s+/g, ' ').trim()));
  await click('#v-trip', '14-viaggi');
  report.viaggiForm = await page.evaluate(() => !!document.getElementById('vr-go'));
  report.chiediHidden = await page.evaluate(() => { const c = document.getElementById('chiedi'); return c ? c.hidden : 'missing'; });
  report.errors = errors;
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report, null, 1));
  await browser.close();
})().catch(e => { console.error('FATAL', e); process.exit(1); });
