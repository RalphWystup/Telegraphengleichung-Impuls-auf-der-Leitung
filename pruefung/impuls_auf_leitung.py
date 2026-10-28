#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Numerische Gegenprobe: ein Impuls auf der Leitung, gerechnet im Zeitbereich aus den Leitungsgleichungen
(4.27)/(4.30) mit einem Leapfrog-Verfahren (Spannung und Strom versetzt, wie FDTD), gegen die geschlossene
Loesung des Manuskripts: u(x,t) = e(t - sqrt(L'C') x) bei Anpassung (Verschiebungssatz), bei Fehlanpassung die
Summe der verzoegerten, mit r multiplizierten Impulse. Schreibt Bilder und impuls_ergebnis.json."""
import json, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

L1, C1 = 1.1983e-6, 9.285e-12          # Doppelleitung Luft d = 10 mm, r0 = 0,5 mm (aus dem CAS-Skript)
Zw = np.sqrt(L1/C1); v = 1/np.sqrt(L1*C1); l = 3.0                       # 3 m Leitung
tau0 = l/v; print(f"Zw = {Zw:.2f} Ohm, v = {v/1e8:.4f}e8 m/s, Laufzeit tau0 = {tau0*1e9:.3f} ns")
N = 1500; dx = l/N; dt = dx/v                      # magischer Zeitschritt: Leapfrog exakt (Courant = 1)
T_puls = 2e-9; E0 = 1.0
def e_quelle(t):                                   # Rechteckimpuls 1 V, 2 ns
    return E0*((np.asarray(t) >= 0) & (np.asarray(t) < T_puls)).astype(float)
SIG = T_puls/(2*np.sqrt(2*np.log(2)))                 # Gaussimpuls (7.1): T = Halbwertsbreite, Scheitel bei 2T
def e_gauss(t):                                    # mit sigma(t): e = 0 fuer t < 0 (Voraussetzung der Laplace-Transformation, Gl. 3.13/3.18)
    t = np.asarray(t, dtype=float)
    return E0*np.exp(-0.5*((t - 2*T_puls)/SIG)**2)*(t >= 0)
def lauf(Za, t_end=5*tau0, Ri=0.0, e_quelle=e_quelle):
    u = np.zeros(N + 1); i = np.zeros(N)           # u an Knoten 0..N, i auf halben Zellen
    nt = int(t_end/dt); aufz = {}; merk_t = [0.15*tau0, 0.35*tau0, 0.55*tau0, 0.75*tau0]   # vier Momentaufnahmen INNERHALB der ersten Laufzeit: der Impuls wandert sichtbar (28.10.2026 nachgebessert)
    u_ende = np.zeros(nt); u_mitte = np.zeros(nt); zeit = np.arange(nt)*dt
    for n in range(nt):
        t = n*dt
        i -= dt/L1*(u[1:] - u[:-1])/dx             # di/dt = -(1/L') du/dx
        u[1:-1] -= dt/C1*(i[1:] - i[:-1])/dx       # du/dt = -(1/C') di/dx
        # Randknoten als HALBE Zellen (C' dx/2) mit Trapezregel fuer den Widerstandszweig; bei dt = dx/v ist dt/(C' dx) = Zw.
        # Quelle:  u0' = [(Ri - Zw) u0 + Zw (e(t) + e(t - dt)) - 2 Ri Zw i_{1/2}] / (Ri + Zw)   (Ri = 0: u0 = e(t))
        # Last:    uN' = [(Za - Zw) uN + 2 Za Zw i_{N-1/2}] / (Za + Zw);  Leerlauf uN' = uN + 2 Zw i;  Kurzschluss uN = 0
        # Gemessen 28.10.2026: explizite Fassungen und die Quelle ohne Mittelung der Quellspannung (e(t) statt (e(t)+e(t-dt))/2)
        # weichen um 0,25 bis 1 V ab (Zeitlage um einen halben Schritt), diese Fassung liegt bei 1e-13 V in allen Faellen.
        if Ri == 0: u[0] = e_quelle(t)
        else: u[0] = ((Ri - Zw)*u[0] + Zw*(e_quelle(t) + e_quelle(t - dt)) - 2*Ri*Zw*i[0])/(Ri + Zw)
        if Za == np.inf: u[-1] = u[-1] + 2*Zw*i[-1]
        elif Za == 0: u[-1] = 0.0
        else: u[-1] = ((Za - Zw)*u[-1] + 2*Za*Zw*i[-1])/(Za + Zw)
        u_ende[n] = u[-1]; u_mitte[n] = u[N//2]
        for tm in merk_t:
            if abs(t - tm) < dt/2: aufz[tm] = u.copy()
    return zeit, u_ende, u_mitte, aufz
def geschlossen(t, x, Za, nmax=8, Ri=0.0, e_quelle=e_quelle):
    """Gl. (3.24): Eingangsteiler Zw/(Ri+Zw), Reflexion am Ende r_a, am Generator r_q, geometrische Reihe der Mehrfachreflexionen."""
    ra = 1.0 if Za == np.inf else (Za - Zw)/(Za + Zw); rq = (Ri - Zw)/(Ri + Zw)
    u = np.zeros_like(t)
    for n in range(0, nmax + 1):
        u += (rq*ra)**n*(e_quelle(t - (2*n*l + x)/v) + ra*e_quelle(t - (2*(n + 1)*l - x)/v))
    return Zw/(Ri + Zw)*u
erg = {}
fig, ax = plt.subplots(3, 1, figsize=(8, 8.5), sharex=True)
for k, (name, Za) in enumerate((("Anpassung Z_a = Z_w", Zw), ("Leerlauf", np.inf), ("Kurzschluss", 0.0))):
    zeit, u_ende, u_mitte, aufz = lauf(Za)
    ug = geschlossen(zeit, l/2, Za)
    d = np.abs(u_mitte - ug).max()
    erg[name] = {"Za": (None if Za == np.inf else Za), "max_abw_mitte_V": float(d), "u_ende_max": float(u_ende.max()), "u_ende_min": float(u_ende.min())}
    ax[k].plot(zeit*1e9, u_mitte, label="Leapfrog, Mitte der Leitung"); ax[k].plot(zeit*1e9, ug, "--", label="geschlossen (Verschiebungssatz, Reflexionen)")
    ax[k].plot(zeit*1e9, u_ende, ":", label="Leapfrog, Leitungsende"); ax[k].set_ylabel("u / V"); ax[k].set_title(f"{name}: größte Abweichung in der Mitte {d:.2e} V"); ax[k].legend(fontsize=8); ax[k].grid(alpha=.3)
    print(f"{name:22s} max|Leapfrog - geschlossen| (Mitte) = {d:.2e} V; u_ende max {u_ende.max():.3f} V")
ax[-1].set_xlabel("t / ns"); fig.tight_layout(); fig.savefig("/workspace/Telegraphengleichung/bilder/impuls_leitung.png", dpi=130)
# Bild 2: Momentaufnahmen des Impulses laengs der Leitung (Anpassung)
zeit, u_ende, u_mitte, aufz = lauf(Zw)
fig, ax = plt.subplots(figsize=(8, 3.6)); xs = np.linspace(0, l, N + 1)
for tm, uu in sorted(aufz.items()): ax.plot(xs, uu, label=f"t = {tm*1e9:.2f} ns")
ax.set_xlabel("x / m"); ax.set_ylabel("u / V"); ax.set_title("Rechteckimpuls 1 V, 2 ns auf der angepassten Leitung: unverzerrt mit v = 1/sqrt(L'C')"); ax.legend(fontsize=8); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig("/workspace/Telegraphengleichung/bilder/impuls_momentaufnahmen.png", dpi=130)
# Quelle mit Innenwiderstand: R_i = Zw/3, Z_a = 3 Zw (beide fehlangepasst) und R_i = Zw (Anpassung am Generator)
for name, Ri, Za in (("Ri = Zw/3, Za = 3 Zw", Zw/3, 3*Zw), ("Ri = Zw, Leerlauf", Zw, np.inf), ("Ri = 2 Zw, Za = Zw/2", 2*Zw, Zw/2)):
    zeit, u_ende, u_mitte, aufz = lauf(Za, Ri=Ri); ug = geschlossen(zeit, l/2, Za, Ri=Ri); d = np.abs(u_mitte - ug).max()
    erg[name] = {"max_abw_mitte_V": float(d), "u_ende_max": float(u_ende.max())}
    print(f"{name:22s} max|Leapfrog - geschlossen| (Mitte) = {d:.2e} V; u_ende max {u_ende.max():.3f} V")
# Siebter Fall: Gaussimpuls (7.1) mit Quellen- und Lastfehlanpassung, beide Wege gegeneinander
zeit, u_ende, u_mitte, aufz = lauf(3*Zw, Ri=Zw/3, e_quelle=e_gauss); ug = geschlossen(zeit, l/2, 3*Zw, Ri=Zw/3, e_quelle=e_gauss); d = np.abs(u_mitte - ug).max()
erg["Gauss, Ri = Zw/3, Za = 3 Zw"] = {"max_abw_mitte_V": float(d), "u_ende_max": float(u_ende.max()), "e_bei_0": float(e_gauss(0.0)), "halbwert": float(e_gauss(2*T_puls + T_puls/2))}
print(f"{'Gauss, Ri=Zw/3, Za=3Zw':22s} max|Leapfrog - geschlossen| (Mitte) = {d:.2e} V; u_ende max {u_ende.max():.3f} V; e(0) = {e_gauss(0.0):.2e} V, e(t0+T/2) = {e_gauss(2*T_puls + T_puls/2):.4f} V")
# ---- Verzweigung: Sternpunkt 1 auf 2 mit R je Zweig (Gl. 6.12/6.13/6.16, Zeitschritt 7.3-7.5); Weg 1 = Strahlensumme, Weg 2 = Leapfrog ----
def stern(R, n=3):
    Zein = R + (R + Zw)/(n - 1); r = (Zein - Zw)/(Zein + Zw); return Zein, r, (1 - r)/(n - 1)
def strahlen(R, Ri, Za, t_end, eps=1e-7):
    _, r, tt = stern(R); ra = 1.0 if Za == np.inf else (Za - Zw)/(Za + Zw); rq = (Ri - Zw)/(Ri + Zw)
    aus = []; offen = [(0, +1, Zw/(Ri + Zw), 0.0)]
    while offen:
        k, d, A, t0 = offen.pop()
        if abs(A) < eps or t0 > t_end: continue
        aus.append((k, d, A, t0)); t1 = t0 + tau0
        if k == 0:
            if d > 0: offen += [(0, -1, A*r, t1), (1, +1, A*tt, t1), (2, +1, A*tt, t1)]
            else: offen.append((0, +1, A*rq, t1))
        else:
            if d > 0: offen.append((k, -1, A*ra, t1))
            else: offen += [(k, +1, A*r, t1), (0, -1, A*tt, t1), (3 - k, +1, A*tt, t1)]
    return aus
def strahl_u(st, k, x, t, e_quelle=e_quelle):
    """Summe der Strahlen an der Stelle x der Leitung k. Das Argument wird auf 1e-6 tau0 gerundet: 1,5 tau0 - tau0 - 0,5 tau0 ist in
    Gleitkommazahlen nicht exakt null, und an der Impulsflanke entscheidet das Vorzeichen (gemessen 28.10.2026: ein Abtastwert 0,375 V)."""
    u = np.zeros_like(t); raster = 1e-6*tau0
    for kk, d, A, t0 in st:
        if kk != k: continue
        arg = t - t0 - x/v if d > 0 else t - t0 - (l - x)/v
        u += A*e_quelle(np.round(arg/raster)*raster)
    return u
def lauf_stern(R, Ri, Za, t_end, n=3, e_quelle=e_quelle):
    u = [np.zeros(N + 1) for _ in range(3)]; i = [np.zeros(N) for _ in range(3)]; uS = 0.0
    nt = int(t_end/dt); zeit = np.arange(nt)*dt; auf = {"u1_ende": np.zeros(nt), "u2_mitte": np.zeros(nt), "u2_ende": np.zeros(nt), "uS": np.zeros(nt), "u1_mitte": np.zeros(nt)}
    for m in range(nt):
        t = m*dt
        for k in range(3):
            i[k] -= dt/L1*(u[k][1:] - u[k][:-1])/dx; u[k][1:-1] -= dt/C1*(i[k][1:] - i[k][:-1])/dx
        if Ri == 0: u[0][0] = e_quelle(t)
        else: u[0][0] = ((Ri - Zw)*u[0][0] + Zw*(e_quelle(t) + e_quelle(t - dt)) - 2*Ri*Zw*i[0][0])/(Ri + Zw)
        for k in (1, 2):
            if Za == np.inf: u[k][-1] = u[k][-1] + 2*Zw*i[k][-1]
            elif Za == 0: u[k][-1] = 0.0
            else: u[k][-1] = ((Za - Zw)*u[k][-1] + 2*Za*Zw*i[k][-1])/(Za + Zw)
        ue = np.array([u[0][-1], u[1][0], u[2][0]]); ie = np.array([i[0][-1], -i[1][0], -i[2][0]])
        if R == 0:
            g = ue[0] + 2*Zw*ie.sum()/n; u[0][-1] = u[1][0] = u[2][0] = g; uS = g                       # (7.5)
        else:
            a = 1/Zw + 1/R; rhs = 2*ie + ue*(1/Zw - 1/R) + uS/R                                            # (7.3)
            uSn = Zw*rhs.sum()/n; neu = (rhs + uSn/R)/a; u[0][-1], u[1][0], u[2][0] = neu; uS = uSn       # (7.4)
        auf["u1_ende"][m] = u[0][-1]; auf["u1_mitte"][m] = u[0][N//2]; auf["u2_mitte"][m] = u[1][N//2]; auf["u2_ende"][m] = u[1][-1]; auf["uS"][m] = uS
    return zeit, auf
for name, R, Ri, Za in (("Stern R opt, Ri=Zw/3, Za=3Zw", Zw/3, Zw/3, 3*Zw), ("Stern R=0, Ri=0, Leerlauf", 0.0, 0.0, np.inf), ("Stern R=Zw, Ri=Zw, Za=Zw", Zw, Zw, Zw)):
    zeit, auf = lauf_stern(R, Ri, Za, 6*tau0); st = strahlen(R, Ri, Za, 6*tau0)
    d1 = np.abs(auf["u1_mitte"] - strahl_u(st, 0, l/2, zeit)).max(); d2 = np.abs(auf["u2_mitte"] - strahl_u(st, 1, l/2, zeit)).max(); d3 = np.abs(auf["u2_ende"] - strahl_u(st, 1, l, zeit)).max()
    Zein, r, tt = stern(R)
    erg[name] = {"R": float(R), "Zein": float(Zein), "r_stern": float(r), "t_stern": float(tt), "max_abw_V": float(max(d1, d2, d3)), "u2_ende_max": float(auf["u2_ende"].max()), "uS_max": float(auf["uS"].max()), "strahlen": len(st)}
    print(f"{name:28s} Zein = {Zein:.2f}, r = {r:+.4f}, t = {tt:.4f}; max|Leapfrog - Strahlen| = {max(d1, d2, d3):.2e} V; u2_ende max {auf['u2_ende'].max():.4f} V; {len(st)} Strahlen")
erg["Zw_Ohm"] = float(Zw); erg["v_m_s"] = float(v); erg["tau0_ns"] = float(tau0*1e9)
json.dump(erg, open("impuls_ergebnis.json", "w"), indent=1); print("Bilder geschrieben")
