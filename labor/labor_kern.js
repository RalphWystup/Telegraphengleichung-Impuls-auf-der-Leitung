/* labor_kern.js — der Rechenkern der Laborseite „Telegraphengleichung“. Zwei Wege aus DEMSELBEN Manuskript:
   Weg 1 (geschlossen, Gl. 3.24; Reflexionsfaktoren Gl. 3.21 und Gl. 3.23): u(x,t) = Zw/(Ri+Zw) · Σ (rq ra)^n [ e(t - (2nl+x)/v) + ra · e(t - (2(n+1)l - x)/v) ]
          mit rq = (Ri-Zw)/(Ri+Zw), ra = (Za-Zw)/(Za+Zw), v = 1/sqrt(L'C'), Zw = sqrt(L'/C').
   Weg 2 (Zeitschritt, Gl. 2.3 und Gl. 2.6): Leapfrog mit dt = dx/v, Randknoten als halbe Zellen mit Trapezregel
          (Quelle: u0' = [(Ri-Zw)u0 + Zw(e(t)+e(t-dt)) - 2 Ri Zw i] / (Ri+Zw); Last: uN' = [(Za-Zw)uN + 2 Za Zw i] / (Za+Zw)).
   Beide Wege sind in pruefung/impuls_auf_leitung.py gegeneinander geprüft (Abstand 1e-13 V). Keine weiteren Annahmen. */
const LABOR = (() => {
  const MU0 = 4e-7 * Math.PI, EPS0 = 8.8541878128e-12;
  function belaege(d_mm, r0_mm, eps_r) {          // Gl. 5.3 und Gl. 5.5 (Doppelleitung, d >> r0), daraus Gl. 5.6 (Z_w) und Gl. 5.7 (v)
    const q = Math.log(d_mm / r0_mm);
    const C1 = Math.PI * EPS0 * eps_r / q, L1 = MU0 / Math.PI * q;
    return { C1, L1, Zw: Math.sqrt(L1 / C1), v: 1 / Math.sqrt(L1 * C1) };
  }
  function quelle(form, E0, T) {                   // e(t): Rechteck oder Gauß (Breite T = volle Breite bei halber Höhe)
    if (form === 'gauss') { const s = T / (2 * Math.sqrt(2 * Math.LN2)); return t => (t >= 0) ? E0 * Math.exp(-0.5 * ((t - 2 * T) / s) ** 2) : 0; }   // Gl. 7.1, mit sigma(t); Impulslaenge dazu Gl. 7.2
    return t => (t >= 0 && t < T) ? E0 : 0;
  }
  function geschlossen(p, x, t, nmax = 12) {      // Gl. 3.24
    const { Zw, v, l, Ri, Za, e } = p;
    const ra = (Za === Infinity) ? 1 : (Za - Zw) / (Za + Zw), rq = (Ri - Zw) / (Ri + Zw);
    let u = 0, g = 1;
    for (let n = 0; n <= nmax; n++) { u += g * (e(t - (2 * n * l + x) / v) + ra * e(t - (2 * (n + 1) * l - x) / v)); g *= rq * ra; if (Math.abs(g) < 1e-12) break; }
    return Zw / (Ri + Zw) * u;
  }
  function zeitschritt(p, N) {                     // Weg 2: Zustand, Schritt für Schritt
    const { Zw, v, l, Ri, Za, e, L1, C1 } = p; const dx = l / N, dt = dx / v;
    const u = new Float64Array(N + 1), i = new Float64Array(N); let n = 0;
    return {
      dt, dx, u, i, get t() { return n * dt; },
      schritt() {
        const t = n * dt;
        for (let k = 0; k < N; k++) i[k] -= dt / L1 * (u[k + 1] - u[k]) / dx;
        for (let k = 1; k < N; k++) u[k] -= dt / C1 * (i[k] - i[k - 1]) / dx;
        if (Ri === 0) u[0] = e(t); else u[0] = ((Ri - Zw) * u[0] + Zw * (e(t) + e(t - dt)) - 2 * Ri * Zw * i[0]) / (Ri + Zw);
        if (Za === Infinity) u[N] = u[N] + 2 * Zw * i[N - 1]; else if (Za === 0) u[N] = 0; else u[N] = ((Za - Zw) * u[N] + 2 * Za * Zw * i[N - 1]) / (Za + Zw);
        n++;
      }
    };
  }
  // ---- Verzweigung: Sternpunkt 1 auf 2 mit Widerstand R in jedem Zweig (Abschnitt 6: Gl. 6.12 und Gl. 6.13, Durchlass aus Gl. 6.16; Zeitschritt Gl. 7.3a, Gl. 7.3b, Gl. 7.4, Gl. 7.5) ----
  function stern(p, R, n = 3) {                    // Z_ein (6.12), r (6.13), Durchlass je Zweig t = (1 - r)/(n - 1)
    const Zein = R + (R + p.Zw) / (n - 1), r = (Zein - p.Zw) / (Zein + p.Zw);
    return { Zein, r, t: (1 - r) / (n - 1), Ropt: (n - 2) / n * p.Zw };
  }
  function verzweigungStrahlen(p, R, tEnd, eps = 1e-7) {   // Weg 1: Verschiebungssatz Glied fuer Glied; jede Welle ein verzoegerter, skalierter Impuls
    const { Zw, v, l, Ri, Za } = p; const tau = l / v; const { r, t } = stern(p, R);
    const ra = (Za === Infinity) ? 1 : (Za - Zw) / (Za + Zw), rq = (Ri - Zw) / (Ri + Zw);
    const aus = []; const offen = [{ k: 0, d: +1, A: Zw / (Ri + Zw), t0: 0 }];      // Leitung 0: Quelle (x=0) -> Stern (x=l); Leitung 1,2: Stern (x=0) -> Abschluss (x=l)
    while (offen.length) {
      const q = offen.pop(); if (Math.abs(q.A) < eps || q.t0 > tEnd) continue; aus.push(q);
      const t1 = q.t0 + tau;
      if (q.k === 0) {
        if (q.d > 0) { offen.push({ k: 0, d: -1, A: q.A * r, t0: t1 }); offen.push({ k: 1, d: +1, A: q.A * t, t0: t1 }); offen.push({ k: 2, d: +1, A: q.A * t, t0: t1 }); }
        else offen.push({ k: 0, d: +1, A: q.A * rq, t0: t1 });                          // am Generator mit r_q (3.23)
      } else {
        if (q.d > 0) offen.push({ k: q.k, d: -1, A: q.A * ra, t0: t1 });                   // am Abschluss mit r_a (3.21)
        else { offen.push({ k: q.k, d: +1, A: q.A * r, t0: t1 }); offen.push({ k: 0, d: -1, A: q.A * t, t0: t1 }); offen.push({ k: 3 - q.k, d: +1, A: q.A * t, t0: t1 }); }
      }
    }
    return aus;
  }
  function verzweigungGeschlossen(p, strahlen, k, x, t) {   // Argument auf 1e-6 tau0 gerundet: an der Impulsflanke entscheidet sonst Gleitkomma-Rest das Vorzeichen
    const { v, l, e } = p; const raster = 1e-6 * l / v; let u = 0;
    for (const q of strahlen) { if (q.k !== k) continue; const arg = q.d > 0 ? t - q.t0 - x / v : t - q.t0 - (l - x) / v; u += q.A * e(Math.round(arg / raster) * raster); }
    return u;
  }
  function verzweigungZeitschritt(p, R, N, n = 3) {   // Weg 2: Leapfrog auf drei Leitungen, Sternknoten als drei halbe Zellen mit Trapezregel (7.3-7.5)
    const { Zw, Ri, Za, e, L1, C1, l, v } = p; const dx = l / N, dt = dx / v;
    const u = [0, 1, 2].map(() => new Float64Array(N + 1)), i = [0, 1, 2].map(() => new Float64Array(N)); let m = 0, uS = 0;
    return {
      dt, dx, u, i, get t() { return m * dt; }, get uS() { return uS; },
      schritt() {
        const t = m * dt;
        for (let k = 0; k < 3; k++) {
          for (let j = 0; j < N; j++) i[k][j] -= dt / L1 * (u[k][j + 1] - u[k][j]) / dx;
          for (let j = 1; j < N; j++) u[k][j] -= dt / C1 * (i[k][j] - i[k][j - 1]) / dx;
        }
        if (Ri === 0) u[0][0] = e(t); else u[0][0] = ((Ri - Zw) * u[0][0] + Zw * (e(t) + e(t - dt)) - 2 * Ri * Zw * i[0][0]) / (Ri + Zw);
        for (const k of [1, 2]) { if (Za === Infinity) u[k][N] = u[k][N] + 2 * Zw * i[k][N - 1]; else if (Za === 0) u[k][N] = 0; else u[k][N] = ((Za - Zw) * u[k][N] + 2 * Za * Zw * i[k][N - 1]) / (Za + Zw); }
        const ue = [u[0][N], u[1][0], u[2][0]], ie = [i[0][N - 1], -i[1][0], -i[2][0]];   // Stroeme in den jeweiligen Endknoten hinein
        if (R === 0) { const g = ue[0] + 2 * Zw * (ie[0] + ie[1] + ie[2]) / n; u[0][N] = u[1][0] = u[2][0] = g; uS = g; }   // (7.5): ein Knoten aus drei halben Zellen
        else {
          const a = 1 / Zw + 1 / R; const rhs = ue.map((uk, k) => 2 * ie[k] + uk * (1 / Zw - 1 / R) + uS / R);        // (7.3)
          const uSn = Zw * (rhs[0] + rhs[1] + rhs[2]) / n;                                                              // (7.4)
          u[0][N] = (rhs[0] + uSn / R) / a; u[1][0] = (rhs[1] + uSn / R) / a; u[2][0] = (rhs[2] + uSn / R) / a; uS = uSn;
        }
        m++;
      }
    };
  }
  return { belaege, quelle, geschlossen, zeitschritt, stern, verzweigungStrahlen, verzweigungGeschlossen, verzweigungZeitschritt };
})();
if (typeof module !== 'undefined') module.exports = LABOR;
