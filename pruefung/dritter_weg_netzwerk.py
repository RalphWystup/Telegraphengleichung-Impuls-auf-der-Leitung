#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Dritter, unabhängiger Weg: die Leitung als echtes LC-Kettennetzwerk, ohne jeden Reflexionsfaktor.

Anlass 29.10.2026, sein Befund: „der rücklaufende Impuls wird an der Quelle falsch reflektiert."

Warum ein dritter Weg nötig ist: Die beiden Wege der Laborseite — die geschlossene Strahlensumme (Gl. 3.24)
und der Zeitschritt — benutzen BEIDE denselben Reflexionsfaktor r_q = (R_i − Z_w)/(R_i + Z_w). Wäre der
falsch, könnten sie einander nicht widerlegen: Sie zeigten übereinstimmend dasselbe Falsche. Ihr Vergleich
(Abstand 1e-15 V) ist deshalb KEIN Beweis für die Quellreflexion.

Dieser Weg kennt keine Wellen und keine Reflexionsfaktoren. Er schreibt nur die beiden Kirchhoffschen
Gesetze an einer Kette aus N Gliedern hin — Längsinduktivität L'·dx, Querkapazität C'·dx — und integriert
sie mit einem allgemeinen Verfahren aus scipy:

    L'·dx · di_k/dt = u_k − u_(k+1)                      k = 0 … N−1
    C'·dx · du_k/dt = i_(k−1) − i_k                      k = 1 … N−1   (volle Zelle)
    C'·dx/2 · du_0/dt = (e(t) − u_0)/R_i − i_0                          (halbe Zelle, Quelle mit R_i)
    C'·dx/2 · du_N/dt = i_(N−1) − u_N/Z_a                               (halbe Zelle, Abschluss)

Die Quelle ist eine wirkliche Schaltung: Spannungsquelle e(t) mit Reihenwiderstand R_i am ersten Knoten.
Ob daraus r_q = (R_i − Z_w)/(R_i + Z_w) folgt, muss sich ZEIGEN; es wird nicht hineingesteckt.

Zwei Entscheidungen, damit der Vergleich etwas aussagt:
  * Gaußimpuls statt Rechteck. Eine Kette aus N Gliedern bildet eine senkrechte Kante nicht ab — sie
    zerläuft und schwingt nach (Gitterdispersion). Das wäre ein Fehler des Prüfmittels, nicht der Sache.
    Ein glatter Impuls ist bandbegrenzt und kommt sauber durch.
  * Nur endliche R_i. Für R_i = 0 wäre die Quelle eine Zwangsbedingung statt einer Differentialgleichung;
    der Grenzfall folgt aus den endlichen Werten.

  python3 pruefung/dritter_weg_netzwerk.py
"""
from __future__ import annotations

import json, math, subprocess, sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

H = Path(__file__).resolve().parent
KERN = H.parent / "labor" / "labor_kern.js"
TMP = Path("/tmp/claude-1000")

JS = r"""
const K=require(process.argv[2]);
const d=JSON.parse(require('fs').readFileSync(process.argv[3],'utf8'));
const p={Zw:d.Zw,v:d.v,l:d.l,Ri:d.Ri,Za:(d.Za===null?Infinity:d.Za),L1:d.L1,C1:d.C1,
         e:K.quelle('gauss',1,d.T)};
const aus=[];
for(const t of d.t_aus){ const r=[]; for(const x of d.x_aus) r.push(K.geschlossen(p,x,t,60)); aus.push(r); }
console.log(JSON.stringify(aus));
"""


def belaege(d_mm, r0_mm, eps_r):
    MU0, EPS0 = 4e-7 * math.pi, 8.8541878128e-12
    q = math.log(d_mm / r0_mm)
    C1 = math.pi * EPS0 * eps_r / q
    L1 = MU0 / math.pi * q
    return C1, L1, math.sqrt(L1 / C1), 1.0 / math.sqrt(L1 * C1)


def gauss(E0, T):
    s = T / (2 * math.sqrt(2 * math.log(2)))
    return lambda t: (E0 * math.exp(-0.5 * ((t - 2 * T) / s) ** 2)) if t >= 0 else 0.0


def netzwerk(C1, L1, l, Ri, Za, e, N, t_aus):
    dx = l / N
    Lz, Cz = L1 * dx, C1 * dx
    halb = Cz / 2.0

    def f(t, y):
        u, i = y[: N + 1], y[N + 1:]
        du = np.empty(N + 1)
        di = (u[:-1] - u[1:]) / Lz
        du[1:N] = (i[:-1] - i[1:]) / Cz
        du[0] = ((e(t) - u[0]) / Ri - i[0]) / halb
        last = 0.0 if Za == math.inf else u[N] / Za
        du[N] = (i[N - 1] - last) / halb
        return np.concatenate([du, di])

    r = solve_ivp(f, (0.0, max(t_aus) * 1.001), np.zeros(2 * N + 1), method="DOP853",
                  rtol=1e-9, atol=1e-11, t_eval=list(t_aus), max_step=dx / 3e8)
    return [(t, r.y[: N + 1, k]) for k, t in enumerate(r.t)]


def main() -> int:
    C1, L1, Zw, v = belaege(10, 0.5, 1)
    l, N = 3.0, 160
    tau = l / v
    T = 0.22 * tau
    t_aus = [0.9 * tau, 1.5 * tau, 2.3 * tau, 3.1 * tau]
    x_aus = [0.0, 0.15 * l, 0.35 * l, 0.6 * l, 0.85 * l, l]
    faelle = [("R_i = Z_w/3, Ende offen", Zw / 3, math.inf),
              ("R_i = Z_w, Ende offen (Quelle angepasst)", Zw, math.inf),
              ("R_i = 3 Z_w, Ende offen", 3 * Zw, math.inf),
              ("R_i = Z_w/3, Z_a = 3 Z_w", Zw / 3, 3 * Zw),
              ("R_i = 2 Z_w, Z_a = Z_w/2", 2 * Zw, Zw / 2)]
    print(f"Z_w = {Zw:.3f} Ohm, tau = {tau*1e9:.3f} ns, Gaussimpuls T = {T*1e9:.3f} ns, "
          f"Kette mit N = {N} Gliedern\n")
    xg = np.linspace(0, l, N + 1)
    schlimm, wo = 0.0, ""
    for name, Ri, Za in faelle:
        e = gauss(1.0, T)
        netz = netzwerk(C1, L1, l, Ri, Za, e, N, t_aus)
        daten = dict(Zw=Zw, v=v, l=l, Ri=Ri, Za=(None if Za == math.inf else Za), L1=L1, C1=C1, T=T,
                     t_aus=[float(t) for t, _ in netz], x_aus=x_aus)
        (TMP / "dw.json").write_text(json.dumps(daten), encoding="utf-8")
        (TMP / "dw.js").write_text(JS, encoding="utf-8")
        r = subprocess.run(["node", str(TMP / "dw.js"), str(KERN), str(TMP / "dw.json")],
                           capture_output=True, text=True, timeout=900)
        if r.returncode:
            print(r.stdout + r.stderr); return 1
        strahl = json.loads(r.stdout.strip().splitlines()[-1])
        print(f"== {name}")
        print("   t/tau        " + "".join(f"{x/l:>10.2f}·l" for x in x_aus))
        for (t, u), sr in zip(netz, strahl):
            un = [float(np.interp(x, xg, u)) for x in x_aus]
            d = max(abs(a - b) for a, b in zip(un, sr))
            if d > schlimm:
                schlimm, wo = d, f"{name}, t = {t/tau:.2f} tau"
            print(f"   {t/tau:5.2f}  Netz " + "".join(f"{a:>11.4f}" for a in un))
            print(f"          Welle" + "".join(f"{b:>11.4f}" for b in sr) + f"    Abstand {d:.2e} V")
        print()
    print(f"Groesster Abstand Netzwerk gegen Wellenrechnung: {schlimm:.3e} V   ({wo})")
    gut = schlimm < 2e-2
    print("RICHTIG: Die Quellreflexion folgt aus der Schaltung selbst und deckt sich mit r_q = "
          "(R_i-Z_w)/(R_i+Z_w)." if gut else
          "FALSCH: Netzwerk und Wellenrechnung widersprechen sich — die Quellreflexion stimmt nicht.")
    return 0 if gut else 1


if __name__ == "__main__":
    sys.exit(main())
