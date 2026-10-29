// Laborseite im echten Browser: laden, drei Fälle über PRUEFSTAND stellen, rechnen, beide Wege vergleichen, Bilder sichern.
const { chromium } = require('/tmp/node_modules/playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1360, height: 900 } });
  const fehler = []; pg.on('pageerror', e => fehler.push(String(e))); pg.on('console', m => { if (m.type() === 'error') fehler.push(m.text()); });
  await pg.goto('file:///workspace/Telegraphengleichung/Telegraphen_Labor_1.8.html');
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
  // --- Abnahme: die Seite muss RECHNEN, nicht nur laden. Harte Sollwerte, sonst Rückgabe 1. ---
  const soll = [];
  const pruef = (gut, text) => { soll.push((gut ? 'ok     ' : 'FEHLER ') + text); if (!gut) fehler.push('Abnahme: ' + text); };
  await pg.evaluate(() => window.PRUEFSTAND.stellen({ d: 10, r0: 0.5, epsr: 1, l: 3, E0: 1, T: 2, Ri: 0, art: 'leerlauf', form: 'rechteck' }));
  const a1 = await pg.evaluate(() => window.PRUEFSTAND.rechne(800));
  pruef(a1.t_ns > 10, `die Zeit läuft: nach 800 Schritten t = ${a1.t_ns.toFixed(2)} ns (soll > 10)`);
  pruef(a1.max_abw_V < 1e-9, `beide Wege decken sich: ${a1.max_abw_V.toExponential(2)} V (soll < 1e-9)`);
  const a2 = await pg.evaluate(() => { const v0 = window.PRUEFSTAND.stand().t_ns; window.PRUEFSTAND.rechne(200); return { v0, v1: window.PRUEFSTAND.stand().t_ns }; });
  pruef(a2.v1 > a2.v0, `weitere Schritte bringen die Zeit voran: ${a2.v0.toFixed(2)} → ${a2.v1.toFixed(2)} ns`);
  const a3 = await pg.evaluate(async () => { const t0 = window.PRUEFSTAND.stand().t_ns; start();
      await new Promise(r => setTimeout(r, 1200)); const t1 = window.PRUEFSTAND.stand().t_ns; halt(); return { t0, t1 }; });
  pruef(a3.t1 > a3.t0, `der Start-Knopf treibt die Simulation: ${a3.t0.toFixed(2)} → ${a3.t1.toFixed(2)} ns`);
  const a4 = await pg.evaluate(async () => { window.PRUEFSTAND.stern.stellen({ rart: 'opt' }); const t0 = window.PRUEFSTAND.stern.stand().t_ns;
      sternStart(); await new Promise(r => setTimeout(r, 1200)); const t1 = window.PRUEFSTAND.stern.stand().t_ns; sternHalt();
      const r = window.PRUEFSTAND.stern.rechne(300); return { t0, t1, abw: r.max_abw_V }; });
  pruef(a4.t1 > a4.t0, `der Start-Knopf der Verzweigung läuft: ${a4.t0.toFixed(2)} → ${a4.t1.toFixed(2)} ns`);
  pruef(a4.abw < 1e-9, `Verzweigung: beide Wege decken sich: ${a4.abw.toExponential(2)} V`);
  const a5 = await pg.evaluate(() => window.PRUEFSTAND.rechenweg());
  pruef(a5.schritte === 16, `Reiter Rechenweg zeigt ${a5.schritte} Schritte (soll 16)`);
  console.log('Abnahme:\n  ' + soll.join('\n  '));
  console.log('Seitenfehler:', fehler.length, fehler.slice(0, 3));
  require('fs').writeFileSync('/workspace/Telegraphengleichung/labor/pruefe_seite.json', JSON.stringify({ aus, dokuSichtbar, fehler }));
  await b.close();
  process.exit(fehler.length ? 1 : 0);      // die Prüfung endet mit Fehler, wenn die Seite nicht rechnet
})();
