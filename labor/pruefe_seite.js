// Laborseite im echten Browser: laden, drei Fälle über PRUEFSTAND stellen, rechnen, beide Wege vergleichen, Bilder sichern.
const { chromium } = require('/tmp/node_modules/playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1360, height: 900 } });
  const fehler = []; pg.on('pageerror', e => fehler.push(String(e))); pg.on('console', m => { if (m.type() === 'error') fehler.push(m.text()); });
  await pg.goto('file:///workspace/Telegraphengleichung/Telegraphen_Labor_1.4.html');
  console.log('Titel:', await pg.title());
  const aus = {};
  for (const [name, o, schritte] of [['Leerlauf, Ri=0', { art: 'leerlauf', Ri: 0 }, 900], ['Ri=120, Za=1000', { art: 'wert', Za: 1000, Ri: 120 }, 1100], ['Gauss, Anpassung', { form: 'gauss', art: 'anpassung', Ri: 0, T: 1.5 }, 700]]) {
    await pg.evaluate(o => window.PRUEFSTAND.stellen(o), o);
    const r = await pg.evaluate(k => window.PRUEFSTAND.rechne(k), schritte);
    aus[name] = r; console.log(name.padEnd(18), `t = ${r.t_ns.toFixed(2)} ns  max|Weg1-Weg2| = ${r.max_abw_V.toExponential(2)} V  u(l) W1 ${r.u_ende_w1.toFixed(4)} W2 ${r.u_ende_w2.toFixed(4)}`);
    await pg.screenshot({ path: `/workspace/Telegraphengleichung/bilder/labor_${name.replace(/[^a-z0-9]/gi, '_')}.png` });
  }
  // Fassung 1.2: Wellenwiderstand sichtbar, Knöpfe „übernehmen", Impulslänge
  const vorher = await pg.evaluate(() => ({ zw: document.getElementById('zwAnzeige').textContent, il: document.getElementById('impulslaenge').textContent, za: document.getElementById('zaAnzeige').textContent }));
  await pg.click('text=R_i und Z_a = Z_w (beide anpassen)'); await pg.waitForTimeout(200);
  const nachher = await pg.evaluate(() => ({ Ri: +document.getElementById('Ri').value, Za: +document.getElementById('Za').value, art: document.getElementById('art').value, Zw: window.PRUEFSTAND.parameter().Zw,
      ra: window.PRUEFSTAND.stand().ra, za: document.getElementById('zaAnzeige').textContent }));
  const knoepfe = { zw_text: vorher.zw, impulslaenge: vorher.il, nach_knopf: nachher,
      richtig: Math.abs(nachher.Ri - nachher.Zw) < 0.01 && Math.abs(nachher.Za - nachher.Zw) < 0.01 && nachher.art === 'wert' && Math.abs(nachher.ra) < 1e-4 && /Z_w = \d+\.\d+ Ω/.test(vorher.zw) && /Impulslänge v·T = 0\.\d+ m/.test(vorher.il) };
  console.log('Knöpfe 1.2:', JSON.stringify(knoepfe)); aus['knoepfe_1_2'] = knoepfe;
  await pg.evaluate(() => { document.getElementById('T').value = 12; document.getElementById('T').dispatchEvent(new Event('change')); });
  console.log('T = 12 ns:', await pg.evaluate(() => document.getElementById('impulslaenge').textContent));
  // Reiter Verzweigung (1.2): Einstellungen von der Hauptseite, R optimal und frei, eigener Start
  await pg.evaluate(o => window.PRUEFSTAND.stellen(o), { form: 'rechteck', art: 'wert', Za: 3 * 359.24, Ri: 359.24 / 3, T: 2 });
  for (const [name, o, schritte] of [['Stern R opt', { rart: 'opt' }, 700], ['Stern R=0', { rart: 'frei', R: 0 }, 700], ['Stern R=Zw', { rart: 'frei', R: 359.24 }, 500]]) {
    const s = await pg.evaluate(o => window.PRUEFSTAND.stern.stellen(o), o);
    const r = await pg.evaluate(k => window.PRUEFSTAND.stern.rechne(k), schritte);
    aus[name] = { ...s, ...r }; console.log(name.padEnd(18), `R = ${s.R.toFixed(2)} r = ${s.r.toFixed(4)} t = ${s.t.toFixed(4)}  t = ${r.t_ns.toFixed(2)} ns  max|Weg1-Weg2| = ${r.max_abw_V.toExponential(2)} V  u2(l) W1 ${r.u2_ende_w1.toFixed(4)} W2 ${r.u2_ende_w2.toFixed(4)}  u_S ${r.uS.toFixed(4)}  ${r.strahlen} Strahlen`);
    await pg.screenshot({ path: `/workspace/Telegraphengleichung/bilder/labor_${name.replace(/[^a-z0-9]/gi, '_')}.png` });
  }
  const sternKnopf = await pg.evaluate(() => { sternNeu(); sternStart(); return document.getElementById('kStart2').textContent; });
  await pg.waitForTimeout(1500); const sternLaeuft = await pg.evaluate(() => window.PRUEFSTAND.stern.stand());
  console.log('Start-Knopf Verzweigung:', sternKnopf, JSON.stringify(sternLaeuft)); aus['stern_start'] = { knopf: sternKnopf, ...sternLaeuft };
  await pg.evaluate(() => sternHalt());
  // Reiter Rechenweg (1.4): jeder Schritt nennt seine Gleichung, und jede genannte Gleichung ist CAS-geprüft
  const weg = await pg.evaluate(() => window.PRUEFSTAND.rechenweg());
  const einmalig = [...new Set(weg.gleichungen)];
  console.log('Rechenweg:', weg.schritte, 'Schritte,', einmalig.length, 'verschiedene Gleichungen:', einmalig.join(' '));
  aus['rechenweg'] = { schritte: weg.schritte, gleichungen: einmalig };
  await pg.screenshot({ path: '/workspace/Telegraphengleichung/bilder/labor_rechenweg.png', fullPage: true });
  await pg.click('#r-doku'); await pg.waitForTimeout(300);
  const dokuSichtbar = await pg.evaluate(() => ({ sichtbar: document.getElementById('ansicht-doku').offsetHeight > 500, mathml: document.querySelectorAll('#ansicht-doku math').length, bilder: document.querySelectorAll('#ansicht-doku img').length }));
  console.log('Manuskript-Reiter:', JSON.stringify(dokuSichtbar)); await pg.screenshot({ path: '/workspace/Telegraphengleichung/bilder/labor_manuskript.png' });
  console.log('Seitenfehler:', fehler.length, fehler.slice(0, 2));
  require('fs').writeFileSync('/workspace/Telegraphengleichung/labor/pruefe_seite.json', JSON.stringify({ aus, dokuSichtbar, fehler }));
  await b.close();
})();
