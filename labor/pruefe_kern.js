// Prüft labor_kern.js in Node gegen die Zahlen von pruefung/impuls_auf_leitung.py: beide Wege, sechs Rechteck-Fälle und der Gaußimpuls (7.1).
const K = require('./labor_kern.js');
const b = K.belaege(10, 0.5, 1); const l = 3.0; let max = 0;
console.log(`Zw ${b.Zw.toFixed(2)} Ohm  v ${(b.v / 1e8).toFixed(4)}e8 m/s`);
for (const [name, Ri, Za, form] of [['Anpassung', 0, b.Zw], ['Leerlauf', 0, Infinity], ['Kurzschluss', 0, 0], ['Ri=Zw/3,Za=3Zw', b.Zw / 3, 3 * b.Zw], ['Ri=Zw,Leerlauf', b.Zw, Infinity], ['Ri=2Zw,Za=Zw/2', 2 * b.Zw, b.Zw / 2], ['Gauss,Ri=Zw/3,Za=3Zw', b.Zw / 3, 3 * b.Zw, 'gauss']]) {
  const p = { ...b, l, Ri, Za, e: K.quelle(form || 'rechteck', 1.0, 2e-9) }; const N = 1500; const z = K.zeitschritt(p, N); let d = 0;
  const nt = Math.round(6 * l / b.v / z.dt);
  for (let n = 0; n < nt; n++) { const t = z.t; z.schritt(); d = Math.max(d, Math.abs(z.u[N / 2] - K.geschlossen(p, l / 2, t)), Math.abs(z.u[N] - K.geschlossen(p, l, t))); }
  max = Math.max(max, d); console.log(`${name.padEnd(16)} max|Weg2 - Weg1| = ${d.toExponential(2)} V`);
}
// Verzweigung: Sternpunkt 1 auf 2, Weg 1 (Strahlensumme) gegen Weg 2 (Leapfrog mit Sternknoten), und gegen die Python-Zahlen
const py = JSON.parse(require('fs').readFileSync(__dirname + '/../pruefung/impuls_ergebnis.json', 'utf8'));
for (const [name, R, Ri, Za, pyName] of [['Stern R opt', b.Zw / 3, b.Zw / 3, 3 * b.Zw, 'Stern R opt, Ri=Zw/3, Za=3Zw'], ['Stern R=0', 0, 0, Infinity, 'Stern R=0, Ri=0, Leerlauf'], ['Stern R=Zw', b.Zw, b.Zw, b.Zw, 'Stern R=Zw, Ri=Zw, Za=Zw']]) {
  const p = { ...b, l, Ri, Za, e: K.quelle('rechteck', 1.0, 2e-9) }; const N = 1500; const tEnd = 6 * l / b.v;
  const st = K.verzweigungStrahlen(p, R, tEnd); const z = K.verzweigungZeitschritt(p, R, N); let d = 0, u2max = 0;
  const nt = Math.round(tEnd / z.dt);
  for (let n = 0; n < nt; n++) { const t = z.t; z.schritt(); u2max = Math.max(u2max, z.u[1][N]);
    d = Math.max(d, Math.abs(z.u[0][N / 2] - K.verzweigungGeschlossen(p, st, 0, l / 2, t)), Math.abs(z.u[1][N / 2] - K.verzweigungGeschlossen(p, st, 1, l / 2, t)), Math.abs(z.u[1][N] - K.verzweigungGeschlossen(p, st, 1, l, t))); }
  const s = K.stern(p, R); const dpy = Math.abs(u2max - py[pyName].u2_ende_max) + Math.abs(s.r - py[pyName].r_stern);
  max = Math.max(max, d, dpy); console.log(`${name.padEnd(16)} r = ${s.r.toFixed(4)} t = ${s.t.toFixed(4)}  max|Weg2 - Weg1| = ${d.toExponential(2)} V  u2_ende max ${u2max.toFixed(4)} (Python ${py[pyName].u2_ende_max.toFixed(4)}), Abstand zu Python ${dpy.toExponential(2)}`);
}
console.log(max < 1e-9 ? 'KERN RICHTIG' : 'KERN FALSCH');
