// Vollständiger Durchlauf: jeder Reiter, jeder Knopf, jede Eingabe — mit Zeitmessung (Einfrieren = Fehler).
const { chromium } = require('/tmp/node_modules/playwright');
const datei = process.argv[2] || '/workspace/Telegraphengleichung/Telegraphen_Labor_1.8.html';
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1360, height: 950 } });
  const f = []; pg.on('pageerror', e => f.push('pageerror: ' + e.message));
  pg.on('console', m => { if (m.type() === 'error') f.push('console: ' + m.text()); });
  let schritte = 0, langsamste = ['—', 0];
  const tu = async (was, fn) => {
    const t0 = Date.now();
    try { await fn(); } catch (e) { f.push(`${was}: ${e.message.split('\n')[0]}`); }
    const dt = Date.now() - t0; schritte++;
    if (dt > langsamste[1]) langsamste = [was, dt];
    if (dt > 4000) f.push(`LANGSAM ${was}: ${dt} ms — Verdacht auf Endlosschleife`);
  };
  await pg.goto('file://' + datei, { timeout: 20000 });
  // 1 alle Reiter in beide Richtungen
  for (const r of ['r-stern', 'r-weg', 'r-doku', 'r-labor', 'r-weg', 'r-stern', 'r-labor'])
    await tu('Reiter ' + r, async () => { await pg.click('#' + r); await pg.waitForTimeout(120); });
  // 2 jeder Knopf im Labor-Reiter
  await pg.click('#r-labor');
  for (const t of ['R_i = 0 (ideale Quelle)', 'R_i = Z_w übernehmen', 'Z_a = Z_w übernehmen', 'R_i und Z_a = Z_w (beide anpassen)'])
    await tu('Knopf ' + t, async () => { await pg.click(`text=${t}`); await pg.waitForTimeout(100); });
  await tu('Start', async () => { await pg.click('#kStart'); await pg.waitForTimeout(900); });
  await tu('Halt', async () => { await pg.click('text=Halt >> nth=0'); });
  await tu('Schritt', async () => { await pg.click('text=Schritt >> nth=0'); });
  // 3 jede Eingabe, auch an den Rändern
  const faelle = [['d','3'],['d','50'],['d','10'],['r0','0.05'],['r0','2'],['r0','0.5'],['epsr','1'],['epsr','9'],
                  ['l','0.2'],['l','50'],['l','3'],['E0','0.001'],['E0','10'],['E0','-1'],['E0','1'],
                  ['T','0.1'],['T','40'],['T','2'],['Ri','0'],['Ri','5000'],['Ri','120'],['Za','0'],['Za','10000'],['Za','100']];
  for (const [id, v] of faelle)
    await tu(`Eingabe ${id}=${v}`, async () => {
      await pg.evaluate(([i, w]) => { const e = document.getElementById(i); e.value = w; e.dispatchEvent(new Event('change')); }, [id, v]);
      await pg.waitForTimeout(90);
    });
  for (const art of ['leerlauf', 'kurzschluss', 'wert', 'anpassung'])
    await tu('Abschluss ' + art, async () => { await pg.selectOption('#art', art); await pg.waitForTimeout(90); });
  for (const form of ['gauss', 'rechteck'])
    await tu('Form ' + form, async () => { await pg.selectOption('#form', form); await pg.waitForTimeout(90); });
  await tu('Zeitlupe', async () => { await pg.fill('#zl', '20'); await pg.evaluate(() => document.getElementById('zl').dispatchEvent(new Event('input'))); });
  // 4 Verzweigung: jeder Knopf, beide Arten, Start
  await pg.click('#r-stern');
  for (const t of ['R = 0 (nackte Verzweigung)', 'R = Z_w'])
    await tu('Stern-Knopf ' + t, async () => { await pg.click(`text=${t}`); await pg.waitForTimeout(150); });
  await tu('Stern R optimal', async () => { await pg.check('input[name=rart][value=opt]'); await pg.waitForTimeout(150); });
  await tu('Stern R frei 42', async () => { await pg.check('input[name=rart][value=frei]'); await pg.fill('#Rfrei', '42'); await pg.evaluate(() => document.getElementById('Rfrei').dispatchEvent(new Event('change'))); await pg.waitForTimeout(150); });
  await tu('Stern Start', async () => { await pg.click('#kStart2'); await pg.waitForTimeout(900); });
  await tu('Stern Halt', async () => { await pg.evaluate(() => sternHalt()); });
  await tu('Stern Schritt', async () => { await pg.evaluate(() => sternSchritt(5)); });
  await tu('Stern zurück', async () => { await pg.evaluate(() => sternNeu()); });
  // 5 Rechenweg nach allen Änderungen
  await tu('Rechenweg', async () => { await pg.click('#r-weg'); await pg.waitForTimeout(200); });
  const weg = await pg.evaluate(() => ({ schritte: document.querySelectorAll('#ansicht-weg .schritt').length,
                                         leer: [...document.querySelectorAll('#ansicht-weg .zahlen')].filter(e => !e.textContent.trim()).length }));
  // 6 Manuskript
  await tu('Manuskript', async () => { await pg.click('#r-doku'); await pg.waitForTimeout(250); });
  const doku = await pg.evaluate(() => ({ hoehe: document.getElementById('ansicht-doku').offsetHeight,
                                          bilder: document.querySelectorAll('#ansicht-doku img').length }));
  // 7 Ergebnis prüfen: rechnen beide Wege noch übereinander?
  await pg.click('#r-labor');
  const r = await pg.evaluate(() => { window.PRUEFSTAND.stellen({ d:10, r0:0.5, epsr:1, l:3, E0:1, T:2, Ri:0, art:'leerlauf' }); return window.PRUEFSTAND.rechne(800); });
  console.log(`Schritte durchgespielt: ${schritte}; langsamster: ${langsamste[0]} ${langsamste[1]} ms`);
  console.log(`Rechenweg: ${weg.schritte} Schritte, ${weg.leer} ohne Zahlen | Manuskript: ${doku.hoehe} px, ${doku.bilder} Bilder`);
  console.log(`Schlussrechnung: t = ${r.t_ns.toFixed(2)} ns, max|Weg1-Weg2| = ${r.max_abw_V.toExponential(2)} V`);
  console.log(f.length ? `FEHLER (${f.length}):\n  ` + f.slice(0, 10).join('\n  ') : 'KEIN FEHLER');
  await pg.screenshot({ path: '/tmp/claude-1000/-workspace/028f65c7-3766-4b0d-ac9e-8be9434f4e1a/scratchpad/vollprobe.png' });
  await b.close();
  process.exit(f.length ? 1 : 0);
})();
