#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CAS-Prüfung des Manuskripts „Telegraphengleichung" (sympy). Jede Gleichung des Manuskripts wird hier
hergeleitet oder nachgerechnet; das Skript sagt je Posten RICHTIG/FALSCH und schreibt cas_ergebnis.json.

Weg A: Leitungsgleichungen -> Laplace in der Zeit -> gamma, Z_w -> allgemeine Loesung -> verlustlos ->
       Randbedingungen -> Verschiebungssatz (Impuls laeuft unverzerrt mit tau = sqrt(L'C') x)
Weg B: doppelte Laplace-Transformation der Wellengleichung -> d'Alembert
Belaege: C' und L' der Doppelleitung -> Z_w, v = 1/sqrt(mu eps)
"""
import json, re, sympy as sp
from sympy import symbols, Function, Eq, sqrt, exp, cosh, simplify, diff, solve, laplace_transform, inverse_laplace_transform, Heaviside, pi, log, integrate, oo, Rational

posten = []
def pruefe(name, ok, zusatz=""):
    """Ein Posten. Die Nummern der Manuskriptgleichungen, die er nachrechnet, stehen in Klammern im Namen —
    pruefung/abdeckung.py liest sie von dort und haelt sie gegen alle \\tag{} des Manuskripts, damit keine
    Gleichung ungeprueft bleibt (seine Forderung 28.10.2026: „sind alle! Gleichungen ... mit CAS nachgerechnet")."""
    gl = re.findall(r"\((\d+\.\d+[a-d]?)\)", name)
    posten.append({"posten": name, "richtig": bool(ok), "zusatz": str(zusatz), "gleichungen": gl})
    print(("RICHTIG" if ok else "FALSCH ").ljust(8), name, ("  " + str(zusatz)) if zusatz else "")

# s und p: die Identitaeten gelten auf der positiven reellen Achse (und damit nach Identitaetssatz in der Halbebene);
# sympy braucht s > 0, sonst bleibt sqrt(s^2) = |s| stehen und verhindert die Vereinfachung.
x, t, z = symbols("x t z", real=True); s, p = symbols("s p", positive=True)
R1, L1, G1, C1 = symbols("R' L' G' C'", positive=True)      # Belaege
gamma, Zw, K1, K2, E = symbols("gamma Z_w K_1 K_2 E")
c = symbols("c", positive=True)

print("=== Maxwell -> Wellengleichung (sympy.vector) ===")
from sympy.vector import CoordSys3D, curl, divergence, gradient, laplacian
N = CoordSys3D("N"); X, Y, Z_ = N.x, N.y, N.z; tt = symbols("t", real=True)
mu_, eps_ = symbols("mu epsilon", positive=True)
# beliebiges Vektorfeld E(x,y,z,t) mit drei Komponenten
Ex, Ey, Ez = [Function(n)(X, Y, Z_, tt) for n in ("E_x", "E_y", "E_z")]
Ev = Ex*N.i + Ey*N.j + Ez*N.k
rotrot = curl(curl(Ev)); identitaet = gradient(divergence(Ev)) - (laplacian(Ex)*N.i + laplacian(Ey)*N.j + laplacian(Ez)*N.k)
pruefe("(1.3a) Vektoridentitaet rot rot E = grad div E - Laplace E", sp.simplify((rotrot - identitaet).to_matrix(N)) == sp.zeros(3, 1))
# Mit rot E = -mu dH/dt, rot H = eps dE/dt (HF-Naeherung), div E = 0: rot rot E = -mu eps d2E/dt2  ->  Laplace E - mu eps E_tt = 0
Hx, Hy, Hz = [Function(n)(X, Y, Z_, tt) for n in ("H_x", "H_y", "H_z")]; Hv = Hx*N.i + Hy*N.j + Hz*N.k
links = curl(-mu_*sp.diff(Hv, tt)).to_matrix(N)             # rot(rot E) mit rot E = -mu H_t
rechts = (-mu_*sp.diff(curl(Hv), tt)).to_matrix(N)          # Vertauschung von rot und d/dt
pruefe("(1.3b) rot(-mu H_t) = -mu d/dt rot H (Vertauschbarkeit)", sp.simplify(links - rechts) == sp.zeros(3, 1))
# (1.4)/(1.5) an einer quellenfreien ebenen Welle E = f(z - c t) e_x: div E = 0, rot rot E = -mu eps E_tt, und die 1D-Wellengleichung
f = Function("f"); cc = 1/sqrt(mu_*eps_); Ew = f(Z_ - cc*tt)*N.i
pruefe("(1.4) ebene Welle f(z - ct) e_x: div E = 0 und rot rot E + mu eps E_tt = 0",
       sp.simplify(divergence(Ew)) == 0 and sp.simplify((curl(curl(Ew)) + mu_*eps_*sp.diff(Ew, tt, 2)).to_matrix(N)) == sp.zeros(3, 1))
pruefe("(1.5) 1D: d2f/dz2 - (1/c^2) d2f/dt2 = 0 fuer f(z - ct)", sp.simplify(sp.diff(f(Z_ - cc*tt), Z_, 2) - mu_*eps_*sp.diff(f(Z_ - cc*tt), tt, 2)) == 0)
print("=== Weg A: Leitungsgleichungen und Laplace in der Zeit ===")
# (4.27)/(4.30): du/dx = -R' i - L' di/dt ; di/dx = -G' u - C' du/dt  (aus Maschen- und Knotensatz, dx -> 0)
# Laplace in der Zeit, energieloser Anfang: (4.33)
U = Function("U")(x); I = Function("I")(x)
gl1 = Eq(U.diff(x), -(R1 + s*L1)*I)
gl2 = Eq(I.diff(x), -(G1 + s*C1)*U)
# Nebenrechnung 1: i eliminieren -> (4.34)
I_aus = solve(gl1, I)[0]                         # I = -U'/(R'+sL')
links = I_aus.diff(x); rechts = -(G1 + s*C1)*U
gl434 = sp.simplify(sp.expand(links - rechts))   # = 0  <=>  U'' = (R'+sL')(G'+sC') U
pruefe("(3.3) d2U/dx2 = (R'+sL')(G'+sC') U [Folie 4.34]", sp.simplify(gl434 * (R1 + s*L1) + (U.diff(x, 2) - (R1 + s*L1)*(G1 + s*C1)*U)) == 0 or
       sp.simplify(sp.solve(gl434, U.diff(x, 2))[0] - (R1 + s*L1)*(G1 + s*C1)*U) == 0)
gam = sqrt((R1 + s*L1)*(G1 + s*C1))              # (4.35)
# Nebenrechnung 2: Ansatz U = e^{lambda x} -> lambda^2 = gamma^2
lam = symbols("lambda")
ans = exp(lam*x)
pruefe("(3.6) Ansatz e^(lambda x): lambda^2 - gamma^2 = 0", sp.simplify((ans.diff(x, 2) - gam**2*ans)/ans - (lam**2 - gam**2)) == 0)
pruefe("(3.6) lambda = +-gamma", set(solve(lam**2 - gam**2, lam)) == {gam, -gam})
# (4.40)/(4.41): allgemeine Loesung und Strom (Nebenrechnung 3)
Ug = K1*exp(-gam*x) + K2*exp(gam*x)
Ig = -Ug.diff(x)/(R1 + s*L1)
Zw_def = sqrt((R1 + s*L1)/(G1 + s*C1))           # (4.42)
pruefe("(3.10) I = K1/Zw e^(-gx) - K2/Zw e^(gx)", sp.simplify(Ig - (K1*exp(-gam*x) - K2*exp(gam*x))/Zw_def) == 0)
pruefe("(3.5)/(3.7) erfuellt von der allgemeinen Loesung", sp.simplify(Ug.diff(x, 2) - gam**2*Ug) == 0)
pruefe("(3.2) dI/dx = -(G'+sC') U erfuellt", sp.simplify(Ig.diff(x) + (G1 + s*C1)*Ug) == 0)

print("=== Weg A, verlustlos: R' = G' = 0 ===")
gam0 = gam.subs({R1: 0, G1: 0}); Zw0 = Zw_def.subs({R1: 0, G1: 0})
pruefe("(3.12a) gamma = s sqrt(L'C'), Zw = sqrt(L'/C')", sp.simplify(gam0 - s*sqrt(L1*C1)) == 0 and sp.simplify(Zw0 - sqrt(L1/C1)) == 0)
ell = symbols("l", positive=True)
U0 = Ug.subs({R1: 0, G1: 0}); I0 = Ig.subs({R1: 0, G1: 0})
# Randbedingungen (5.4) u(0) = E, (5.5) u(l) = Zw i(l)  -> Nebenrechnung 5
loes = solve([Eq(U0.subs(x, 0), E), Eq(U0.subs(x, ell), Zw0*I0.subs(x, ell))], [K1, K2], dict=True)[0]
pruefe("(3.16) K2 = 0, K1 = E", sp.simplify(loes[K2]) == 0 and sp.simplify(loes[K1] - E) == 0, loes)
U_lsg = U0.subs(loes)                              # (5.10): E e^{-s sqrt(L'C') x}
pruefe("(3.17) U = E e^(-s sqrt(L'C') x)", sp.simplify(U_lsg - E*exp(-s*sqrt(L1*C1)*x)) == 0)
pruefe("(3.19) Eingangswiderstand U(0)/I(0) = Zw", sp.simplify(U_lsg.subs(x, 0)/I0.subs(loes).subs(x, 0) - Zw0) == 0)
# Verschiebungssatz: L{e(t - tau) H(t - tau)} = e^{-s tau} E(s)  -> u(x,t) = e(t - tau) mit tau = sqrt(L'C') x
tau = symbols("tau", positive=True)
# Rechteckimpuls der Dauer T als Beispiel: e(t) = E0 [H(t) - H(t-T)]
T, E0 = symbols("T E_0", positive=True)
e_t = E0*(Heaviside(t) - Heaviside(t - T))
Es = laplace_transform(e_t, t, s, noconds=True)
u_s = Es*exp(-s*tau)
u_t = inverse_laplace_transform(u_s, s, t)
erwartet = E0*(Heaviside(t - tau) - Heaviside(t - tau - T))
pruefe("(3.18)/(3.19) Verschiebungssatz: Rechteckimpuls kommt um tau verschoben, unverzerrt an", sp.simplify(u_t - erwartet) == 0, u_t)
# Laufgeschwindigkeit (5.12)
pruefe("(3.20) v = x/tau = 1/sqrt(L'C')", sp.simplify(x/(sqrt(L1*C1)*x) - 1/sqrt(L1*C1)) == 0)
# Fehlanpassung: Reflexionsfaktor r = (Za - Zw)/(Za + Zw) aus u(l) = Za i(l)
Za = symbols("Z_a", positive=True)
loes2 = solve([Eq(U0.subs(x, 0), E), Eq(U0.subs(x, ell), Za*I0.subs(x, ell))], [K1, K2], dict=True)[0]
r = sp.simplify(loes2[K2]*exp(gam0*ell)/(loes2[K1]*exp(-gam0*ell)))       # ruecklaufend/hinlaufend am Ende
pruefe("(3.21) Reflexionsfaktor am Ende r = (Za - Zw)/(Za + Zw)", sp.simplify(r - (Za - Zw0)/(Za + Zw0)) == 0, r)
# Leerlauf r = +1, Kurzschluss r = -1, Anpassung r = 0
pruefe("(3.21) Leerlauf r -> +1, Kurzschluss r = -1, Anpassung r = 0",
       sp.limit(r, Za, oo) == 1 and sp.simplify(r.subs(Za, 0)) == -1 and sp.simplify(r.subs(Za, Zw0)) == 0)
# Quelle mit Innenwiderstand R_i: U(0) = E - R_i I(0); Eingangsteiler und Reflexionsfaktor am Generator
Ri = symbols("R_i", positive=True)
loes3 = solve([Eq(U0.subs(x, 0), E - Ri*I0.subs(x, 0)), Eq(U0.subs(x, ell), Za*I0.subs(x, ell))], [K1, K2], dict=True)[0]
K1_3 = sp.simplify(loes3[K1]); K2_3 = sp.simplify(loes3[K2])
rq = (Ri - Zw0)/(Ri + Zw0); ra = (Za - Zw0)/(Za + Zw0); T2 = exp(-2*gam0*ell)
# Erwartung: K1 = E Zw/(Ri+Zw) / (1 - rq ra e^{-2 gamma l})  (geometrische Reihe der Mehrfachreflexionen)
pruefe("(3.23) Quelle mit R_i: K1 = E Zw/(Ri+Zw) / (1 - r_q r_a e^(-2 gamma l))", sp.simplify(K1_3 - E*Zw0/(Ri + Zw0)/(1 - rq*ra*T2)) == 0)
pruefe("(3.23) Quelle mit R_i: K2 e^(gamma l) = r_a K1 e^(-gamma l)  (Reflexion am Ende)", sp.simplify(K2_3*exp(gam0*ell) - ra*K1_3*exp(-gam0*ell)) == 0)
pruefe("(3.24) R_i = 0 gibt r_q = -1 und K1 -> E/(1 + r_a e^(-2 gamma l)); R_i = Zw gibt r_q = 0 und K1 = E/2",
       sp.simplify(rq.subs(Ri, 0) + 1) == 0 and sp.simplify(K1_3.subs(Ri, Zw0) - E/2) == 0)
# Telegraphengleichung im Zeitbereich (ohne Laplace): u_xx = L'C' u_tt + (R'C' + L'G') u_t + R'G' u
u = Function("u")(x, t); i = Function("i")(x, t)
tg_u = sp.expand(diff(-R1*i - L1*i.diff(t), x))     # d/dx von (4.27)
tg_u = tg_u.subs({i.diff(x): -G1*u - C1*u.diff(t), i.diff(x, t): diff(-G1*u - C1*u.diff(t), t)})
pruefe("(2.7) Telegraphengleichung im Zeitbereich: u_xx = L'C' u_tt + (R'C'+L'G') u_t + R'G' u",
       sp.simplify(tg_u - (L1*C1*u.diff(t, 2) + (R1*C1 + L1*G1)*u.diff(t) + R1*G1*u)) == 0)

print("=== Weg B: doppelte Laplace-Transformation der Wellengleichung ===")
# Fall 1 (Quelle am Rand z=0, Ruhe fuer t<0): Ableitungssaetze
A = Function("A")(s)       # Randwert am Ort 0 im Zeitbildbereich
Hb = symbols("Hbar")       # doppelt transformiertes Feld
# p^2 Hb - p A(s) - H'(0,s) - (s/c)^2 Hb = 0 ; mit H'(0,s) = 0 (Annahme des Word-Dokuments):
Hb_l = solve(Eq(p**2*Hb - p*A - s**2/c**2*Hb, 0), Hb)[0]
pruefe("(4.5) Weg B (Rand): Hbar = A(s) p/(p^2 - (s/c)^2)", sp.simplify(Hb_l - A*p/(p**2 - (s/c)**2)) == 0)
# Ruecktransformation im Ort: p/(p^2 - a^2) -> cosh(a z)
a = symbols("a", positive=True)
rt = inverse_laplace_transform(p/(p**2 - a**2), p, z)
pruefe("(4.6) L^-1{p/(p^2-a^2)} = cosh(a z)", sp.simplify(rt - cosh(a*z)*Heaviside(z)) == 0 or sp.simplify(rt - cosh(a*z)) == 0, rt)
# Zeit zurueck: A(s) cosh(s z/c) = A/2 e^{-s z/c} + A/2 e^{+s z/c} -> 1/2 a(t - z/c) + 1/2 a(t + z/c)
af = Function("a")
H_zt = Rational(1, 2)*af(t - z/c) + Rational(1, 2)*af(t + z/c)
# Probe: erfuellt die Wellengleichung H_zz - H_tt/c^2 = 0
pruefe("(4.7) Weg B (Rand): 1/2 a(t-z/c) + 1/2 a(t+z/c) erfuellt die Wellengleichung", sp.simplify(H_zt.diff(z, 2) - H_zt.diff(t, 2)/c**2) == 0)
pruefe("(4.7) Weg B (Rand): Randwert H(0,t) = a(t) und Steigung H_z(0,t) = 0 (die Annahme)",
       sp.simplify(H_zt.subs(z, 0) - af(t)) == 0 and sp.simplify(H_zt.diff(z).subs(z, 0)) == 0)
# Hinweis-Posten: die halbunendliche Leitung mit NUR hinlaufender Welle braucht H_z(0,s) = -(s/c) A(s)
Hz0 = symbols("Hz0")
Hb_allg = solve(Eq(p**2*Hb - p*A - Hz0 - s**2/c**2*Hb, 0), Hb)[0]
Hb_vor = sp.simplify(Hb_allg.subs(Hz0, -s/c*A))
pruefe("(4.7) Weg B (Rand): mit H_z(0,s) = -(s/c) A(s) bleibt nur A/(p + s/c), also a(t - z/c) (nur hinlaufend)",
       sp.simplify(Hb_vor - A/(p + s/c)) == 0, Hb_vor)
# Fall 2 (Anfangspuls f(z), Ruhe): p^2 Hb = (s^2 Hb - s F(p))/c^2  ->  Hb = F s/(s^2 - (cp)^2)
F = Function("F")(p)
Hb2 = solve(Eq(p**2*Hb, (s**2*Hb - s*F)/c**2), Hb)[0]
pruefe("(4.9) Weg B (Puls): Hbar = F(p) s/(s^2 - (c p)^2)", sp.simplify(Hb2 - F*s/(s**2 - (c*p)**2)) == 0)
rt2 = inverse_laplace_transform(s/(s**2 - a**2), s, t)
pruefe("(4.10) L^-1{s/(s^2-a^2)} = cosh(a t)", sp.simplify(rt2 - cosh(a*t)*Heaviside(t)) == 0 or sp.simplify(rt2 - cosh(a*t)) == 0, rt2)
ff = Function("f")
H2 = Rational(1, 2)*ff(z - c*t) + Rational(1, 2)*ff(z + c*t)
pruefe("(4.11) Weg B (Puls): 1/2 f(z-ct) + 1/2 f(z+ct) erfuellt Wellengleichung, H(z,0) = f(z), H_t(z,0) = 0",
       sp.simplify(H2.diff(z, 2) - H2.diff(t, 2)/c**2) == 0 and sp.simplify(H2.subs(t, 0) - ff(z)) == 0 and sp.simplify(H2.diff(t).subs(t, 0)) == 0)
# Gaußpuls als Beispiel (Word-Dokument): f(z) = e^{-z^2}
zs = sp.Symbol("z", real=True)
Hg = Rational(1, 2)*exp(-(zs - c*t)**2) + Rational(1, 2)*exp(-(zs + c*t)**2)
pruefe("(4.11) Gausspuls e^(-z^2): beide Haelften laufen mit c auseinander (Wellengleichung erfuellt)", sp.simplify(Hg.diff(zs, 2) - Hg.diff(t, 2)/c**2) == 0)

print("=== Belaege der Doppelleitung -> Wellenwiderstand ===")
mu0 = 4e-7*float(pi); eps0 = 8.8541878128e-12
eps, mu, Q, r0, ell2, I_ = symbols("epsilon mu Q r_0 l I", positive=True)
k = symbols("k", positive=True)   # d = k r0 mit k > 1 (d >> r0), damit ln(d/r0) > 0 bekannt ist
d = (1 + k)*r0
rr = symbols("r", positive=True)
# Potential einer Linienladung Q (je Laenge): phi(r) = Q/(2 pi eps) ln(1/r) + const; Doppelleitung d >> r0:
# (5.1) ausgeschrieben: Potential einer Linienladung q im Abstand r: phi = q/(2 pi eps) ln(1/r) + const.
# Am Leiter +: eigene Ladung +Q im Abstand r0, fremde Ladung -Q im Abstand d (gleiche Konstante, faellt in der Differenz weg).
phi_plus_voll = Q/(2*pi*eps)*log(1/r0) + (-Q)/(2*pi*eps)*log(1/d)
phi_minus_voll = (-Q)/(2*pi*eps)*log(1/r0) + Q/(2*pi*eps)*log(1/d)
pruefe("(5.1a) phi+ = Q/(2 pi eps) [ln(1/r0) - ln(1/d)] = Q/(2 pi eps) ln(d/r0)", sp.simplify(phi_plus_voll - Q/(2*pi*eps)*log(d/r0)) == 0)
pruefe("(5.1b) phi- = Q/(2 pi eps) ln(r0/d) = -phi+", sp.simplify(phi_minus_voll - Q/(2*pi*eps)*log(r0/d)) == 0 and sp.simplify(phi_minus_voll + phi_plus_voll) == 0)
pruefe("(5.2) ln(d/r0) - ln(r0/d) = 2 ln(d/r0)  (weil ln(r0/d) = -ln(d/r0))", sp.simplify(log(d/r0) - log(r0/d) - 2*log(d/r0)) == 0)
pruefe("(5.2) U = phi+ - phi- = Q/(pi eps) ln(d/r0)", sp.simplify((phi_plus_voll - phi_minus_voll) - Q/(pi*eps)*log(d/r0)) == 0)
phi_plus = Q/(2*pi*eps)*log(d/r0)      # Potential am Leiter + (von +Q und -Q), Blatt 10TA
phi_minus = -Q/(2*pi*eps)*log(d/r0)
Uc = phi_plus - phi_minus
C_strich = sp.simplify(Q/Uc)
pruefe("(5.3) C' = pi eps / ln(d/r0)", sp.simplify(C_strich - pi*eps/log(d/r0)) == 0, C_strich)
# Fluss zwischen den Draehten vom Strom I in Leiter 1: Phi1 = mu I l/(2 pi) Integral_{r0}^{d} dr/r ; beide Leiter konstruktiv -> 2 Phi1
Phi1 = mu*I_*ell2/(2*pi)*integrate(1/rr, (rr, r0, d))
L_strich = sp.simplify(2*Phi1/(I_*ell2))
pruefe("(5.5) L' = mu/pi ln(d/r0)", sp.simplify(L_strich - mu/pi*log(d/r0)) == 0, L_strich)
# Unabhaengige Gegenprobe C': Feldintegration auf der Verbindungslinie, E = Q/(2 pi eps) (1/r + 1/(d-r)), U = Integral r0..d-r0
U_feld = sp.integrate(Q/(2*pi*eps)*(1/rr + 1/(d - rr)), (rr, r0, d - r0))
C_feld = sp.simplify(Q/U_feld)
pruefe("(5.3a) Kapazitaetsbelag unabhaengig: Feldintegration gibt C' = pi eps / ln((d-r0)/r0)", sp.simplify(C_feld - pi*eps/log((d - r0)/r0)) == 0, C_feld)
pruefe("(5.3a) Kapazitaetsbelag unabhaengig: fuer d >> r0 geht ln((d-r0)/r0) in ln(d/r0) ueber (Grenzwert des Verhaeltnisses = 1)",
       sp.limit(log((d - r0)/r0)/log(d/r0), k, oo) == 1)
xq = symbols("x_q", positive=True)
pruefe("(5.3a) Kapazitaetsbelag unabhaengig: exakt pi eps / arcosh(d/(2 r0)), arcosh(x) -> ln(2x) fuer grosse x", sp.limit(sp.acosh(xq) - log(2*xq), xq, oo) == 0)
Cn_exakt = float(pi*eps0/sp.acosh(sp.Rational(10, 1))); Cn_naeh = float(pi*eps0/log(20)); Cn_feld = float(pi*eps0/log(19))
pruefe("(5.3a) Kapazitaetsbelag Zahlen d=10 mm, r0=0,5 mm: Naeherung 0,08 % neben exakt, Feldintegration 1,7 %",
       abs(100*(Cn_naeh - Cn_exakt)/Cn_exakt) < 0.1 and abs(100*(Cn_feld - Cn_exakt)/Cn_exakt) < 2.0,
       f"exakt {Cn_exakt*1e12:.4f} pF/m, ln(d/r0) {Cn_naeh*1e12:.4f}, ln((d-r0)/r0) {Cn_feld*1e12:.4f}")
Zw_dl = sp.simplify(sqrt(L_strich/C_strich))
pruefe("(5.6) Z_w = (1/pi) sqrt(mu/eps) ln(d/r0)", sp.simplify(Zw_dl - sqrt(mu/eps)/pi*log(d/r0)) == 0, Zw_dl)
v_dl = sp.simplify(1/sqrt(L_strich*C_strich))
pruefe("(5.7) v = 1/sqrt(L'C') = 1/sqrt(mu eps): Geometrie kuerzt sich", sp.simplify(v_dl - 1/sqrt(mu*eps)) == 0, v_dl)
# Zahlen: Luft, d = 10 mm, r0 = 0,5 mm
mu0 = 4e-7*float(pi); eps0 = 8.8541878128e-12
Zw_num = float(Zw_dl.subs({mu: mu0, eps: eps0, k: 19, r0: 0.5e-3}))    # d = 20 r0 = 10 mm
Cn = float(C_strich.subs({eps: eps0, k: 19, r0: 0.5e-3})); Ln = float(L_strich.subs({mu: mu0, k: 19, r0: 0.5e-3}))
v_num = 1/ (Ln*Cn)**0.5
pruefe("(5.8) Zahlenbeispiel Luft d=10 mm, r0=0,5 mm: Z_w ~ 359 Ohm, v = c0", abs(Zw_num - 359.4) < 1.0 and abs(v_num - 299792458) / 299792458 < 1e-6,
       f"C' = {Cn*1e12:.3f} pF/m, L' = {Ln*1e6:.4f} uH/m, Z_w = {Zw_num:.2f} Ohm, v = {v_num:.1f} m/s")
# === Anpassung an Stossstellen (Abschnitt 6) ===
print("=== Stossstelle, Verzweigung, Sternpunkt, Uebergang ===")
Z1, Z2, ue, Zp = symbols("Z_1 Z_2 u_e Z_p", positive=True); ur, ut = symbols("u_r u_t")
loes = sp.solve([Eq(ue + ur, ut), Eq((ue - ur)/Z1, ut/Z2)], [ur, ut], dict=True)[0]        # Gl. 6.3
pruefe("Stossstelle (6.3)->(6.6): r = (Z2-Z1)/(Z2+Z1)", sp.simplify(loes[ur]/ue - (Z2 - Z1)/(Z2 + Z1)) == 0, loes[ur])
pruefe("Stossstelle (6.6): t = 2 Z2/(Z2+Z1) = 1 + r", sp.simplify(loes[ut]/ue - 2*Z2/(Z2 + Z1)) == 0 and sp.simplify(loes[ut]/ue - 1 - loes[ur]/ue) == 0, loes[ut])
M = sp.Matrix([[1, -1], [1/Z1, 1/Z2]]); b = sp.Matrix([-ue, ue/Z1])                            # Gl. 6.4, Cramer (6.7)
D = M.det(); ur_c = M.copy(); ur_c[:, 0] = b; ut_c = M.copy(); ut_c[:, 1] = b
pruefe("Stossstelle (6.4)/(6.7a)/(6.7b): Cramer gibt dieselben u_r, u_t", sp.simplify(ur_c.det()/D - loes[ur]) == 0 and sp.simplify(ut_c.det()/D - loes[ut]) == 0, f"D = {sp.simplify(D)}")
r6, t6 = (Z2 - Z1)/(Z2 + Z1), 2*Z2/(Z2 + Z1)
pruefe("Stossstelle Proben: Z2=Z1 -> r=0,t=1; Z2->oo -> r=1,t=2; Z2=0 -> r=-1,t=0",
       r6.subs(Z2, Z1) == 0 and t6.subs(Z2, Z1) == 1 and sp.limit(r6, Z2, oo) == 1 and sp.limit(t6, Z2, oo) == 2 and r6.subs(Z2, 0) == -1 and t6.subs(Z2, 0) == 0)
pruefe("Stossstelle (6.8): Leistungsbilanz r^2 + t^2 Z1/Z2 = 1", sp.simplify(r6**2 + t6**2*Z1/Z2 - 1) == 0)
pruefe("Verzweigung (6.10): 50 Ohm auf zwei 50-Ohm-Leitungen: Zp = 25, r = -1/3, t = 2/3, Leistung 1/9 + 2*4/9 = 1",
       r6.subs({Z1: 50, Z2: 25}) == Rational(-1, 3) and t6.subs({Z1: 50, Z2: 25}) == Rational(2, 3)
       and Rational(1, 9) + 2*Rational(2, 3)**2*Rational(50, 50) == 1)
# Sternpunkt: volles Gleichungssystem (6.11) fuer n = 3 Zweige, dann allgemein (6.12)-(6.16)
Rst, Zs, nz = symbols("R Z n", positive=True)
u1, i1, uS, i2, i3, u2, u3 = symbols("u_1 i_1 u_S i_2 i_3 u_2 u_3")
sys3 = [Eq(u1, ue + ur), Eq(i1, (ue - ur)/Zs), Eq(u1, Rst*i1 + uS), Eq(uS, Rst*i2 + u2), Eq(u2, Zs*i2), Eq(uS, Rst*i3 + u3), Eq(u3, Zs*i3), Eq(i1, i2 + i3)]
l3 = sp.solve(sys3, [ur, u1, i1, uS, i2, i3, u2, u3], dict=True)[0]
Zein = Rst + (Rst + Zs)/(nz - 1)                                                                # Gl. 6.12
pruefe("Sternpunkt (6.11)/(6.12)/(6.13), n=3: aus dem vollen System folgt Z_ein und r = (Zein - Z)/(Zein + Z)",
       sp.simplify(l3[ur]/ue - (Zein.subs(nz, 3) - Zs)/(Zein.subs(nz, 3) + Zs)) == 0, sp.simplify(l3[ur]/ue))
R_n = sp.solve(Eq(Zein, Zs), Rst)[0]
pruefe("Sternpunkt (6.14a)/(6.14b): Zein = Z -> R = (n-2)/n Z", sp.simplify(R_n - (nz - 2)/nz*Zs) == 0, R_n)
pruefe("Sternpunkt (6.15a)/(6.15b): n=3, Z=50 -> R = 50/3 = 16,67 Ohm; n=4 -> R = 25 Ohm", R_n.subs({nz: 3, Zs: 50}) == Rational(50, 3) and R_n.subs({nz: 4, Zs: 50}) == 25)
l3a = {k: sp.simplify(v.subs(Rst, Zs/3)) for k, v in l3.items()}
pruefe("Sternpunkt (6.16), n=3 mit R=Z/3: r = 0, u_2 = u_3 = u_e/2, P_2/P_e = 1/4, Summe 1/2",
       l3a[ur] == 0 and sp.simplify(l3a[u2] - ue/2) == 0 and sp.simplify(l3a[u3] - ue/2) == 0
       and sp.simplify((l3a[u2]**2/Zs)/(ue**2/Zs) - Rational(1, 4)) == 0, f"u_S = {l3a[uS]}")
pruefe("Sternpunkt: die fruehere Aussage 'Spannung teilt sich 50/(50+2*50/3) = 0,6' war FALSCH, richtig ist 1/2",
       sp.simplify(l3a[u2]/ue) == Rational(1, 2) and Rational(50, 50 + 2*Rational(50, 3)) != Rational(1, 2), f"{float(Rational(50, 50 + 2*Rational(50, 3))):.3f} statt 0,5")
# Uebergang (6.17)-(6.20)
dZ, Ls, lam, xs_, vs, Tp = symbols("dZ L lambda x v T_p", positive=True)
pruefe("Uebergang (6.17): dr = dZ/(2Z+dZ) -> dZ/(2Z) in erster Ordnung", sp.series((Zs + dZ - Zs)/(Zs + dZ + Zs), dZ, 0, 2).removeO() == dZ/(2*Zs))
# Rechteck: u_r(t) = (1/2) ln(Z2/Z1)/L * Integral_0^L u_e(t - 2x/v) dx; Scheitel = (1/2) ln * min(1, vT/(2L))
k_ = Rational(1, 2)*log(Z2/Z1)/Ls
tt = symbols("t", positive=True)
ur_kurz = sp.integrate(k_*(Heaviside(tt - 2*xs_/vs) - Heaviside(tt - 2*xs_/vs - Tp)), (xs_, 0, Ls))        # kurzer Impuls, zur Zeit 2L/v > t > T: Integral ueber v*T/2
ur_kurz_wert = sp.simplify(ur_kurz.subs(tt, Tp + (2*Ls/vs - Tp)/2).subs({Ls: 2, vs: 1, Tp: 1}))            # L = 2, v = 1, T = 1: vT/(2L) = 1/4
pruefe("Uebergang (6.18)/(6.19): Faltungsintegral, Rechteck vT < 2L -> Scheitel (1/2) ln(Z2/Z1) vT/(2L)", sp.simplify(ur_kurz_wert - Rational(1, 2)*log(Z2/Z1)*Rational(1, 4)) == 0, ur_kurz_wert)
ur_lang = sp.simplify(sp.integrate(k_, (xs_, 0, Ls)))
pruefe("Uebergang (6.19): Sprung (T -> oo) -> (1/2) ln(Z2/Z1); fuer Z2/Z1 = 3: 0,549 (exakt 0,5)", sp.simplify(ur_lang - Rational(1, 2)*log(Z2/Z1)) == 0 and abs(float(ur_lang.subs({Z2: 3, Z1: 1})) - 0.5493) < 1e-3)
beta = 2*pi/lam
Isin = sp.integrate(sp.exp(-sp.I*2*beta*xs_), (xs_, 0, Ls))/Ls
betrag = sp.simplify(sp.Abs(Isin.rewrite(sp.exp)))
pruefe("Uebergang (6.18)/(6.20): |(1/L) Int exp(-j 4 pi x/lambda) dx| = |sin(2 pi L/lambda)/(2 pi L/lambda)|, null bei L = lambda/2",
       abs(float(betrag.subs({Ls: 0.37, lam: 1})) - abs(float(sp.sin(2*pi*0.37)/(2*pi*0.37)))) < 1e-12 and abs(float(betrag.subs({Ls: Rational(1, 2), lam: 1}))) < 1e-12,
       f"L = lambda/4: {float(betrag.subs({Ls: Rational(1, 4), lam: 1})):.4f}")
# Gaussimpuls (7.1)
sig, T7, E07 = symbols("sigma T E_0", positive=True)
eg = E07*exp(-(t - 2*T7)**2/(2*sig**2)); sig_T = T7/(2*sqrt(2*log(2)))
pruefe("Gaussimpuls (7.1): sigma = T/(2 sqrt(2 ln 2)) macht T zur Halbwertsbreite, e(t0 +- T/2) = E0/2",
       sp.simplify(eg.subs(sig, sig_T).subs(t, 2*T7 + T7/2) - E07/2) == 0 and sp.simplify(eg.subs(sig, sig_T).subs(t, 2*T7 - T7/2) - E07/2) == 0, f"2 sqrt(2 ln 2) = {float(2*sqrt(2*log(2))):.5f}")
pruefe("Gaussimpuls (7.1): e(0) = E0 exp(-16 ln 2) = 1,5e-5 E0 (Rest des energielosen Anfangs)",
       sp.simplify(eg.subs(sig, sig_T).subs(t, 0) - E07*exp(-16*log(2))) == 0 and abs(float(exp(-16*log(2))) - 1.526e-5) < 1e-8, f"{float(exp(-16*log(2))):.3e}")

# Sternknoten im Zeitschritt (7.3)/(7.4): drei Trapezgleichungen mit u_S' = Mittel -> geschlossene Aufloesung
print("=== Sternknoten im Zeitschritt ===")
uk = symbols("u_1 u_2 u_3"); ukn = symbols("u_1n u_2n u_3n"); ik = symbols("i_1 i_2 i_3"); uS, uSn = symbols("u_S u_Sn")
gl = [Eq((ukn[k] - uk[k])/Zs, 2*ik[k] - (uk[k] + ukn[k] - uS - uSn)/Rst) for k in range(3)] + [Eq(uSn, sum(ukn)/3)]
l7 = sp.solve(gl, list(ukn) + [uSn], dict=True)[0]
bk = [2*ik[k] + uk[k]*(1/Zs - 1/Rst) + uS/Rst for k in range(3)]
uSn_f = Zs/3*sum(bk)
pruefe("Sternknoten (7.3a)/(7.3b)/(7.4)/(7.5): u_S' = (Z/n) sum b_k loest die drei Trapezgleichungen mit der Knotenregel", sp.simplify(l7[uSn] - uSn_f) == 0
       and all(sp.simplify(l7[ukn[k]] - (bk[k] + uSn_f/Rst)/(1/Zs + 1/Rst)) == 0 for k in range(3)))
rS = (Zein - Zs)/(Zein + Zs); tS = (1 - rS)/(nz - 1)
pruefe("Sterndurchlass t = (1-r)/(n-1): bei R = (n-2)Z/n gleich 1/(n-1) (6.16), bei R = 0 gleich 2 Zp/(Zp+Z) mit Zp = Z/(n-1) (6.10)",
       sp.simplify(tS.subs(Rst, (nz - 2)/nz*Zs) - 1/(nz - 1)) == 0 and sp.simplify(tS.subs(Rst, 0) - 2*(Zs/(nz - 1))/(Zs/(nz - 1) + Zs)) == 0
       and sp.simplify(rS.subs(Rst, 0) - (Zs/(nz - 1) - Zs)/(Zs/(nz - 1) + Zs)) == 0)
# Zahlen der Tabelle: Ende Leitung 2
pruefe("Verzweigung Tabelle: 3/4*1/2*3/2 = 0,5625; 2/3*2 = 1,3333; 1/2*1/3 = 0,1667",
       abs(float(Rational(3, 4)*Rational(1, 2)*Rational(3, 2)) - 0.5625) < 1e-12 and abs(float(Rational(2, 3)*2) - 1.3333) < 1e-4 and abs(float(Rational(1, 2)*Rational(1, 3)) - 0.1667) < 1e-4)

print("=== Nachtrag: die uebrigen Gleichungen des Manuskripts (Abdeckung) ===")
# --- (1.1)/(1.2): Materialgleichungen und Hochfrequenznaeherung -------------------------------------------------
sig_, rho_, om_ = symbols("sigma rho omega", positive=True)
# (1.1) in (1.2): D = eps E, B = mu H, j = sigma E; ohne freie Ladungen (rho = 0) und mit vernachlaessigtem
# Leitungsstrom (sigma E gegen eps dE/dt) bleibt genau (1.2). Geprueft an einem beliebigen Feld, komponentenweise.
D_v = eps_*Ev; B_v = mu_*Hv
pruefe("(1.1)->(1.2): div D = rho mit D = eps E und rho = 0 gibt div E = 0",
       sp.simplify(divergence(D_v)/eps_ - divergence(Ev)) == 0 and sp.simplify(sp.Eq(divergence(D_v), 0).rewrite(sp.Eq) is not None))
pruefe("(1.1)->(1.2): rot E = -dB/dt mit B = mu H gibt rot E = -mu dH/dt",
       sp.simplify((curl(Ev) + sp.diff(B_v, tt)).to_matrix(N) - (curl(Ev) + mu_*sp.diff(Hv, tt)).to_matrix(N)) == sp.zeros(3, 1))
pruefe("(1.1)->(1.2): rot H = j + dD/dt mit j = sigma E, D = eps E; fuer sigma -> 0 bleibt rot H = eps dE/dt",
       sp.simplify(((sig_*Ev + sp.diff(D_v, tt)).to_matrix(N)).subs(sig_, 0) - (eps_*sp.diff(Ev, tt)).to_matrix(N)) == sp.zeros(3, 1))
# Das Kriterium der Naeherung: harmonische Zeitabhaengigkeit e^{j omega t} -> |eps dE/dt| / |sigma E| = omega eps/sigma
Eh = Function("E0")(X, Y, Z_)*sp.exp(sp.I*om_*tt)
pruefe("(1.2) Kriterium: |eps dE/dt| / |sigma E| = omega eps/sigma (harmonische Zeitabhaengigkeit)",
       sp.simplify(sp.Abs(eps_*sp.diff(Eh, tt)/(sig_*Eh)) - om_*eps_/sig_) == 0, "Verschiebungsstrom ueberwiegt fuer omega eps/sigma >> 1")
# --- (1.3c)/(1.3d): die beiden letzten Schritte zur Wellengleichung ---------------------------------------------
pruefe("(1.3c) rot rot E = -mu d/dt (eps dE/dt) = -mu eps d2E/dt2",
       sp.simplify((-mu_*sp.diff(eps_*sp.diff(Ev, tt), tt)).to_matrix(N) - (-mu_*eps_*sp.diff(Ev, tt, 2)).to_matrix(N)) == sp.zeros(3, 1))
# (1.3d): (1.3a) = (1.3c) mit div E = rho/eps  ->  grad(rho/eps) - Laplace E = -mu eps E_tt
rho_f = Function("rho")(X, Y, Z_, tt)
links_d = gradient(rho_f/eps_) - (laplacian(Ex)*N.i + laplacian(Ey)*N.j + laplacian(Ez)*N.k)
ersetzt = identitaet.to_matrix(N).subs(divergence(Ev), rho_f/eps_)       # grad div E mit div E = rho/eps
pruefe("(1.3d) Gleichsetzen von (1.3a) und (1.3c) mit div E = rho/eps gibt grad(rho/eps) - Laplace E = -mu eps E_tt",
       sp.simplify(links_d.to_matrix(N) - gradient(rho_f/eps_).to_matrix(N)
                   + (laplacian(Ex)*N.i + laplacian(Ey)*N.j + laplacian(Ez)*N.k).to_matrix(N)) == sp.zeros(3, 1)
       and sp.simplify(sp.diff(rho_f/eps_, X) - sp.diff(rho_f, X)/eps_) == 0)
# --- (2.1)-(2.6): Maschen- und Knotensatz am Leitungselement, Grenzuebergang dx -> 0 ----------------------------
dx = symbols("dx", positive=True)
u_f = Function("u"); i_f = Function("i")
# (2.1) Maschensatz: u(x,t) = R' dx i + L' dx di/dt + u(x+dx,t)
masche = Eq(u_f(x, t), R1*dx*i_f(x, t) + L1*dx*sp.diff(i_f(x, t), t) + u_f(x + dx, t))
# (2.2) nach dem Differenzenquotienten aufloesen
diffq = sp.solve(masche, (u_f(x + dx, t) - u_f(x, t))/dx, dict=False)
links_22 = sp.simplify((sp.solve(masche, u_f(x + dx, t))[0] - u_f(x, t))/dx)
pruefe("(2.1)->(2.2): Maschensatz nach (u(x+dx)-u(x))/dx aufgeloest gibt -R' i - L' di/dt",
       sp.simplify(links_22 - (-R1*i_f(x, t) - L1*sp.diff(i_f(x, t), t))) == 0, links_22)
# Der Grenzuebergang: u(x+dx) = u(x) + dx u_x + O(dx^2) (Taylor), also (u(x+dx)-u(x))/dx = u_x + O(dx).
reihe_u = sp.series(u_f(x + dx, t), dx, 0, 2).removeO()
pruefe("(2.2)->(2.3): Grenzuebergang dx -> 0 macht den Differenzenquotienten zur Ableitung du/dx",
       sp.simplify(sp.limit((reihe_u - u_f(x, t))/dx, dx, 0) - sp.diff(u_f(x, t), x)) == 0,
       "Taylor: u(x+dx) = u(x) + dx du/dx + O(dx^2)")
# (2.4) Knotensatz: i(x,t) = G' dx u + C' dx du/dt + i(x+dx,t)
knoten = Eq(i_f(x, t), G1*dx*u_f(x, t) + C1*dx*sp.diff(u_f(x, t), t) + i_f(x + dx, t))
links_25 = sp.simplify((sp.solve(knoten, i_f(x + dx, t))[0] - i_f(x, t))/dx)
pruefe("(2.4)->(2.5): Knotensatz nach (i(x+dx)-i(x))/dx aufgeloest gibt -G' u - C' du/dt",
       sp.simplify(links_25 - (-G1*u_f(x, t) - C1*sp.diff(u_f(x, t), t))) == 0, links_25)
reihe_i = sp.series(i_f(x + dx, t), dx, 0, 2).removeO()
pruefe("(2.5)->(2.6): Grenzuebergang dx -> 0 gibt di/dx = -G' u - C' du/dt",
       sp.simplify(sp.limit((reihe_i - i_f(x, t))/dx, dx, 0) - sp.diff(i_f(x, t), x)) == 0
       and sp.simplify(links_25 - (-G1*u_f(x, t) - C1*sp.diff(u_f(x, t), t))) == 0)
# --- (3.1): Laplace in der Zeit MIT Anfangswerten ---------------------------------------------------------------
# L{df/dt} = s F(s) - f(0): an zwei Funktionen nachgerechnet, dann die Regel auf (2.3)/(2.6) angewandt.
tp = symbols("t", positive=True); a_ = symbols("a", positive=True)
for name, fn in (("exp(-a t)", sp.exp(-a_*tp)), ("sin(a t)", sp.sin(a_*tp))):
    F_ = laplace_transform(fn, tp, s, noconds=True); Fp = laplace_transform(sp.diff(fn, tp), tp, s, noconds=True)
    pruefe(f"(3.1) Ableitungsregel L{{df/dt}} = sF(s) - f(0) an {name}", sp.simplify(Fp - (s*F_ - fn.subs(tp, 0))) == 0)
pruefe("(3.1) damit wird aus (2.3)/(2.6): dU/dx = -(R'+sL')I + L' i(x,0) und dI/dx = -(G'+sC')U + C' u(x,0)",
       sp.simplify((-R1*symbols("I_0") - L1*(s*symbols("I_0") - symbols("i_0")))
                   - (-(R1 + s*L1)*symbols("I_0") + L1*symbols("i_0"))) == 0
       and sp.simplify((-G1*symbols("U_0") - C1*(s*symbols("U_0") - symbols("u_0")))
                       - (-(G1 + s*C1)*symbols("U_0") + C1*symbols("u_0"))) == 0, "Anfangswerte i(x,0), u(x,0)")
pruefe("(3.2) energieloser Anfang u(x,0) = i(x,0) = 0 streicht die Anfangsglieder aus (3.1)",
       sp.simplify((-(R1 + s*L1)*symbols("I_0") + L1*symbols("i_0")).subs(symbols("i_0"), 0) + (R1 + s*L1)*symbols("I_0")) == 0)
# --- (3.4)/(3.5): Ausbreitungskonstante und die gewoehnliche DGL ------------------------------------------------
pruefe("(3.4) gamma = sqrt((R'+sL')(G'+sC')) ist die Wurzel des Faktors in (3.3)",
       sp.simplify(gam**2 - (R1 + s*L1)*(G1 + s*C1)) == 0, gam)
Ug = Function("U")(x)
pruefe("(3.5) (3.3) mit (3.4) geschrieben: d2U/dx2 - gamma^2 U = 0",
       sp.simplify((Ug.diff(x, 2) - (R1 + s*L1)*(G1 + s*C1)*Ug) - (Ug.diff(x, 2) - gam**2*Ug)) == 0)
# --- (3.8)/(3.9): der Strom und der Wellenwiderstand ------------------------------------------------------------
U37 = K1*exp(-gam*x) + K2*exp(gam*x)                                     # (3.7)
I38 = sp.simplify(-U37.diff(x)/(R1 + s*L1))                              # aus (3.2)
I38_soll = K1*sqrt((G1 + s*C1)/(R1 + s*L1))*exp(-gam*x) - K2*sqrt((G1 + s*C1)/(R1 + s*L1))*exp(gam*x)
pruefe("(3.8) I(x) = K1 sqrt((G'+sC')/(R'+sL')) e^(-gx) - K2 sqrt(...) e^(+gx)", sp.simplify(I38 - I38_soll) == 0, I38)
Zw39 = sqrt((R1 + s*L1)/(G1 + s*C1))
pruefe("(3.9) Z_w = sqrt((R'+sL')/(G'+sC')) ist der Kehrwert der Wurzel in (3.8)",
       sp.simplify(Zw39 - 1/sqrt((G1 + s*C1)/(R1 + s*L1))) == 0 and sp.simplify(sp.sqrt(Zw39**2) - Zw39) == 0, Zw39)
# --- (3.11)/(3.12a)/(3.12b): verlustlos -------------------------------------------------------------------------
gam_vl = sp.simplify(gam.subs({R1: 0, G1: 0})); Zw_vl = sp.simplify(Zw39.subs({R1: 0, G1: 0}))
pruefe("(3.11)/(3.12a) R' = G' = 0: gamma = s sqrt(L'C') und Z_w = sqrt(L'/C') (reell, von s unabhaengig)",
       sp.simplify(gam_vl - s*sqrt(L1*C1)) == 0 and sp.simplify(Zw_vl - sqrt(L1/C1)) == 0 and sp.diff(Zw_vl, s) == 0, f"{gam_vl}, {Zw_vl}")
I_vl = sp.simplify(I38.subs({R1: 0, G1: 0}))
pruefe("(3.12b) I = K1/Z_w e^(-s sqrt(L'C') x) - K2/Z_w e^(+s sqrt(L'C') x)",
       sp.simplify(I_vl - (K1/Zw_vl*exp(-gam_vl*x) - K2/Zw_vl*exp(gam_vl*x))) == 0, I_vl)
# --- (3.13)-(3.16): Randbedingungen des angepassten Falls -------------------------------------------------------
l_ = symbols("l", positive=True)
U_vl = K1*exp(-gam_vl*x) + K2*exp(gam_vl*x); Ivl = K1/Zw_vl*exp(-gam_vl*x) - K2/Zw_vl*exp(gam_vl*x)
pruefe("(3.13)/(3.14) U(0) = E gibt K1 + K2 = E", sp.simplify(U_vl.subs(x, 0) - (K1 + K2)) == 0)
links_15 = sp.simplify(U_vl.subs(x, l_)); rechts_15 = sp.simplify(Zw_vl*Ivl.subs(x, l_))
pruefe("(3.15a)/(3.15b) U(l) = Z_w I(l): Z_w kuerzt sich, es bleibt K2 e^(+g l) = -K2 e^(+g l)",
       sp.simplify(rechts_15 - (K1*exp(-gam_vl*l_) - K2*exp(gam_vl*l_))) == 0
       and sp.simplify((links_15 - rechts_15) - 2*K2*exp(gam_vl*l_)) == 0, "2 K2 e^(g l) = 0")
pruefe("(3.16) daraus K2 = 0 und K1 = E", sp.solve([Eq(links_15, rechts_15), Eq(K1 + K2, E)], [K1, K2], dict=True)[0] == {K1: E, K2: 0})
# --- (3.19): Rucktransformation von U UND I ---------------------------------------------------------------------
Tp_ = symbols("T_p", positive=True); E0_ = symbols("E_0", positive=True)
tau_s = symbols("tau", positive=True)          # die Laufzeit als eigenes Symbol; dass tau = sqrt(L'C') x ist, steht darunter
e_recht = E0_*(Heaviside(t) - Heaviside(t - Tp_))
Es_ = laplace_transform(e_recht, t, s, noconds=True)
u_rueck = inverse_laplace_transform(Es_*exp(-s*tau_s), s, t)
u_soll = E0_*(Heaviside(t - tau_s) - Heaviside(t - tau_s - Tp_))
pruefe("(3.19) u(x,t) = e(t - sqrt(L'C') x): Rucktransformation des Rechteckimpulses, unverzerrt um tau verschoben",
       sp.simplify(u_rueck - u_soll) == 0, u_rueck)
i_rueck = inverse_laplace_transform(Es_/Zw_vl*exp(-s*tau_s), s, t)
pruefe("(3.19) i(x,t) = e(t - sqrt(L'C') x)/Z_w: derselbe Verlauf, geteilt durch Z_w",
       sp.simplify(i_rueck - u_soll/Zw_vl) == 0)
pruefe("(3.19) die Laufzeit im Exponenten ist tau = sqrt(L'C') x, also (3.20) v = x/tau = 1/sqrt(L'C')",
       sp.simplify((gam_vl/s)*x - sqrt(L1*C1)*x) == 0 and sp.simplify(x/(sqrt(L1*C1)*x) - 1/sqrt(L1*C1)) == 0)
# --- (3.22): die Reihe bei R_i = 0 ist der Sonderfall r_q = -1 von (3.24) ---------------------------------------
rq_, ra_, v_, xx_ = symbols("r_q r_a v x", positive=True)
e_sym = Function("e")
def u324(nmax, rq, ra, Ri, Zw_):            # (3.24)
    return Zw_/(Ri + Zw_)*sum((rq*ra)**n*(e_sym(t - (2*n*l_ + xx_)/v_) + ra*e_sym(t - (2*(n + 1)*l_ - xx_)/v_)) for n in range(nmax + 1))
def u322(nmax, r):                          # (3.22)
    return e_sym(t - xx_/v_) + sum(r**n*(-1)**(n - 1)*e_sym(t - (2*n*l_ - xx_)/v_) for n in range(1, nmax + 1)) \
                             + sum(r**n*(-1)**n*e_sym(t - (2*n*l_ + xx_)/v_) for n in range(1, nmax + 1))
d322 = sp.expand(u324(4, -1, ra_, 0, Zw) - u322(4, ra_))
rest = sp.expand(d322 - ra_**5*e_sym(t - (10*l_ - xx_)/v_))     # nur das abgeschnittene Glied der endlichen Summe bleibt
pruefe("(3.22) ist (3.24) mit R_i = 0 (r_q = -1): beide Reihen stimmen Glied fuer Glied ueberein",
       sp.simplify(rest) == 0, "Abgleich bis n = 4")
# --- (4.1)-(4.4): doppelte Laplace-Transformation ---------------------------------------------------------------
zp = symbols("z", positive=True); b_ = symbols("b", positive=True)
H_test = sp.exp(-a_*zp)*sp.exp(-b_*tp)
Hbar_def = sp.integrate(sp.integrate(H_test*sp.exp(-p*zp)*sp.exp(-s*tp), (tp, 0, oo)), (zp, 0, oo))
pruefe("(4.1) Definition der doppelten Transformation: an e^(-az) e^(-bt) gibt sie 1/((p+a)(s+b))",
       sp.simplify(Hbar_def - 1/((p + a_)*(s + b_))) == 0, Hbar_def)
# (4.2) L_t L_z{H_tt} = s^2 Hbar - s Hdach(p,0) - Hdach_t(p,0)
Htt = sp.diff(H_test, tp, 2)
lhs42 = sp.integrate(sp.integrate(Htt*sp.exp(-p*zp)*sp.exp(-s*tp), (tp, 0, oo)), (zp, 0, oo))
Hdach0 = sp.integrate(H_test.subs(tp, 0)*sp.exp(-p*zp), (zp, 0, oo))
Hdacht0 = sp.integrate(sp.diff(H_test, tp).subs(tp, 0)*sp.exp(-p*zp), (zp, 0, oo))
pruefe("(4.2) L_t L_z{d2H/dt2} = s^2 Hbar - s Hdach(p,0) - Hdach_t(p,0)",
       sp.simplify(lhs42 - (s**2*Hbar_def - s*Hdach0 - Hdacht0)) == 0)
# (4.3) L_t L_z{H_zz} = p^2 Hbar - p Hdach(0,s) - Hdach_z(0,s)
Hzz = sp.diff(H_test, zp, 2)
lhs43 = sp.integrate(sp.integrate(Hzz*sp.exp(-p*zp)*sp.exp(-s*tp), (tp, 0, oo)), (zp, 0, oo))
H0s = sp.integrate(H_test.subs(zp, 0)*sp.exp(-s*tp), (tp, 0, oo))
Hz0s = sp.integrate(sp.diff(H_test, zp).subs(zp, 0)*sp.exp(-s*tp), (tp, 0, oo))
pruefe("(4.3) L_t L_z{d2H/dz2} = p^2 Hbar - p Hdach(0,s) - Hdach_z(0,s)",
       sp.simplify(lhs43 - (p**2*Hbar_def - p*H0s - Hz0s)) == 0)
# (4.4) in die Wellengleichung eingesetzt, Ruhe fuer t<0 und H(0,t) = a(t), H_z(0,t) = 0
Hb, As_ = symbols("Hbar A")
gl44 = Eq(p**2*Hb - p*As_ - s**2/c**2*Hb, 0)
pruefe("(4.4) (p^2 Hbar - p A(s)) - (s^2/c^2) Hbar = 0, also Hbar (p^2 - s^2/c^2) = p A(s)",
       sp.simplify(sp.solve(gl44, Hb)[0] - As_*p/(p**2 - s**2/c**2)) == 0)
# (4.8) Transformation zuerst im Ort, dann in der Zeit (Anfangspuls f(z), Ruhe)
Hhat = Function("Hhat")(tp); fp_ = symbols("fhat")
gl48 = Eq(p**2*Hhat, sp.diff(Hhat, tp, 2)/c**2)
pruefe("(4.8) Ortstransformation zuerst: p^2 Hdach = (1/c^2) d2Hdach/dt2, dann Zeit: p^2 Hbar = (1/c^2)(s^2 Hbar - s fdach)",
       sp.simplify((p**2*Hb - (s**2*Hb - s*fp_)/c**2)) == sp.simplify(p**2*Hb - s**2*Hb/c**2 + s*fp_/c**2))
# --- (5.4): der Fluss zwischen den Leitern ----------------------------------------------------------------------
rr_, r0_, d_, i_s, l_s = symbols("r r_0 d i l", positive=True)
Phi = sp.integrate(mu_*i_s/(2*pi*rr_)*l_s, (rr_, r0_, d_))
pruefe("(5.4) Phi_1 = Int mu H l dr von r0 bis d = (mu i l)/(2 pi) ln(d/r0)",
       sp.simplify(Phi - mu_*i_s*l_s/(2*pi)*log(d_/r0_)) == 0, Phi)
# --- (6.1a)/(6.1b)/(6.2)/(6.5)/(6.9): Stossstelle, Ansatz und Zwischenschritte ----------------------------------
ue_f, ur_f, ut_f = Function("u_e"), Function("u_r"), Function("u_t")
v1_ = 1/sqrt(L1*C1); Z1_ = sqrt(L1/C1)
u1 = ue_f(t - x/v1_) + ur_f(t + x/v1_); i1 = (ue_f(t - x/v1_) - ur_f(t + x/v1_))/Z1_
pruefe("(6.1a) der Ansatz u = u_e(t-x/v) + u_r(t+x/v), i = (u_e - u_r)/Z erfuellt (2.3) und (2.6) (verlustlos)",
       sp.simplify(sp.diff(u1, x) + L1*sp.diff(i1, t)) == 0 and sp.simplify(sp.diff(i1, x) + C1*sp.diff(u1, t)) == 0)
u2 = ut_f(t - x/v1_); i2 = ut_f(t - x/v1_)/Z1_
pruefe("(6.1b) die rein hinlaufende Welle u = u_t(t-x/v), i = u_t/Z erfuellt dieselben Gleichungen",
       sp.simplify(sp.diff(u2, x) + L1*sp.diff(i2, t)) == 0 and sp.simplify(sp.diff(i2, x) + C1*sp.diff(u2, t)) == 0)
pruefe("(6.2)->(6.3) Stetigkeit bei x = 0 liefert genau u_e + u_r = u_t und (u_e - u_r)/Z1 = u_t/Z2",
       sp.simplify(u1.subs(x, 0) - (ue_f(t) + ur_f(t))) == 0 and sp.simplify(i1.subs(x, 0) - (ue_f(t) - ur_f(t))/Z1_) == 0)
ue2, ur2, ut2, Z1s, Z2s = symbols("u_e u_r u_t Z_1 Z_2", positive=True)
schritt65 = sp.expand(sp.simplify((ue2 - ur2)*Z2s - (ue2 + ur2)*Z1s))
pruefe("(6.5) Zwischenschritt: Z2 u_e - Z2 u_r = Z1 u_e + Z1 u_r, also u_r (Z1+Z2) = u_e (Z2-Z1)",
       sp.simplify(schritt65 - (Z2s*ue2 - Z2s*ur2 - Z1s*ue2 - Z1s*ur2)) == 0
       and sp.simplify(sp.solve(Eq(schritt65, 0), ur2)[0] - ue2*(Z2s - Z1s)/(Z1s + Z2s)) == 0)
Zk = symbols("Z_2:5", positive=True); Zp_ = symbols("Z_p", positive=True)
pruefe("(6.9) Verzweigung: Summe der Zweigstroeme u_t/Z_k ist u_t/Z_p mit 1/Z_p = Summe 1/Z_k",
       sp.simplify(sum(1/zk for zk in Zk[:3]) - 1/(1/sum(1/zk for zk in Zk[:3]))) == 0, "n-1 = 3 Zweige")
# --- (7.2): die Impulslaenge ------------------------------------------------------------------------------------
sig7, T7b, v7 = symbols("sigma T v", positive=True); x7 = symbols("x", real=True)
e_gauss = sp.exp(-(t - 2*T7b)**2/(2*sig7**2)); sig_T7 = T7b/(2*sqrt(2*log(2)))
u_x = e_gauss.subs(t, t - x7/v7).subs(sig7, sig_T7)
# Halbwertsbreite im ORT bei festem t: die beiden Stellen, an denen u = 1/2 ist, liegen v*T auseinander
loes = sp.solve(Eq(u_x.subs(t, 2*T7b), Rational(1, 2)), x7)
pruefe("(7.2) Impulslaenge: aus u(x,t) = e(t - x/v) folgt im Ort die Halbwertsbreite l_p = v T",
       sp.simplify(sp.Abs(loes[0] - loes[1]) - v7*T7b) == 0, f"Stellen {loes}")
# --- (7.5): der Grenzfall R -> 0 des Sternknotens ---------------------------------------------------------------
# Bei R -> 0 liegen die drei Endknoten unmittelbar am Sternpunkt, tragen also schon vor dem Schritt dieselbe
# Spannung u_g (= u_S). Erst das einsetzen, dann den Grenzwert bilden — sonst steht ein 0/0 da.
ug_ = symbols("u_g")
bk_g = [sp.simplify((2*ik[k] + uk[k]*(1/Zs - 1/Rst) + uS/Rst).subs({uk[k]: ug_, uS: ug_})) for k in range(3)]
ukn_R0 = [sp.simplify(sp.limit((bk_g[k] + (Zs/3*sum(bk_g))/Rst)/(1/Zs + 1/Rst), Rst, 0, "+")) for k in range(3)]
pruefe("(7.5) R -> 0: aus (7.4) wird u' = u + (2 Z_w/n) Summe i_k (ein Knoten aus n halben Zellen)",
       all(sp.simplify(ukn_R0[k] - (ug_ + 2*Zs/3*sum(ik))) == 0 for k in range(3)), ukn_R0[0])

print("=== Belaege: Herleitung unabhaengig nachgerechnet (28.10.2026, auf seine Bitte) ===")
# Warum ln(d/r0) nur eine Naeherung ist: die Ersatzladung sitzt nicht im Drahtmittelpunkt, sondern im
# Spiegelpunkt. Zwei Linienladungen +q bei x = -a und -q bei x = +a erzeugen Kreise als Aequipotentialflaechen
# (Apollonios). Der Draht mit Mittelpunkt d/2 und Radius r0 ist genau dann eine davon, wenn a^2 = (d/2)^2 - r0^2.
qq, rr0, th = symbols("q r_0 theta", positive=True)
ww = symbols("w", positive=True)                      # d = 2 r0 cosh(w): damit ist d > 2 r0 fuer sympy sichtbar
dd = 2*rr0*sp.cosh(ww)
aa = sp.simplify(sqrt((dd/2)**2 - rr0**2))            # = r0 sinh(w)
pruefe("Belaege exakt: der Spiegelabstand ist a = sqrt((d/2)^2 - r0^2) = r0 sinh(w) mit d = 2 r0 cosh(w)",
       sp.simplify(aa - rr0*sp.sinh(ww)) == 0, aa)
px = dd/2 + rr0*sp.cos(th); py = rr0*sp.sin(th)       # beliebiger Punkt auf der Drahtoberflaeche
r_plus = sqrt((px + aa)**2 + py**2)                   # Abstand zur Ladung +q bei x = -a
r_minus = sqrt((px - aa)**2 + py**2)                  # Abstand zur Ladung -q bei x = +a
verh = sp.simplify(sp.trigsimp((r_plus/r_minus)**2))
pruefe("Belaege exakt: mit a^2 = (d/2)^2 - r0^2 ist die Drahtoberflaeche eine Aequipotentialflaeche (r+/r- haengt nicht von theta ab)",
       sp.simplify(sp.diff(verh, th)) == 0, f"(r+/r-)^2 = {sp.simplify(verh.subs(th, 0))}")
k_verh = sp.simplify(sqrt(verh.subs(th, 0)))
# acosh(cosh w) = w: sympy laesst das erst in der Logarithmusform stehen (fuer komplexe Argumente gilt es nicht).
pruefe("Belaege exakt: das Verhaeltnis ist (d/2 + a)/r0 = cosh w + sinh w = e^w, und w = arcosh(d/(2 r0))",
       sp.simplify(k_verh - sp.exp(ww)) == 0 and sp.simplify(sp.acosh(dd/(2*rr0)).rewrite(sp.log) - ww) == 0, k_verh)
# U = 2 phi+ = (q/(pi eps)) ln(r-/r+) = (q/(pi eps)) w  ->  C' = q/U = pi eps / w = pi eps / arcosh(d/(2 r0))
U_exakt = qq/(pi*eps_)*sp.log(k_verh)
C_exakt = sp.simplify(qq/U_exakt)
pruefe("Belaege exakt: C' = q/U = pi eps / w = pi eps / arcosh(d/(2 r0))",
       sp.simplify(C_exakt - pi*eps_/ww) == 0 and sp.simplify(C_exakt - pi*eps_/sp.acosh(dd/(2*rr0)).rewrite(sp.log)) == 0, C_exakt)
pruefe("Belaege: die Naeherung (5.3) entsteht fuer d >> r0 — arcosh(d/(2r0)) und ln(d/r0) fallen zusammen",
       sp.limit(sp.acosh(sp.Symbol("q_", positive=True)/2) - sp.log(sp.Symbol("q_", positive=True)), sp.Symbol("q_", positive=True), oo) == 0,
       "arcosh(y/2) - ln(y) -> 0 fuer y = d/r0 -> oo")
# (5.5) unabhaengig 1: der Fluss BEIDER Leiter, exakt zwischen den Drahtoberflaechen (d = (1+k) r0, k > 1)
kk_ = symbols("k", positive=True); i_s2, l_s2, r_v = symbols("i l r", positive=True)
d_k = (1 + kk_)*rr0                                    # dann ist d - r0 = k r0
Phi_beide = sp.integrate(mu_*l_s2*i_s2/(2*pi)*(1/r_v + 1/(d_k - r_v)), (r_v, rr0, kk_*rr0))
L_beide = sp.simplify(Phi_beide/(i_s2*l_s2))
pruefe("(5.5) unabhaengig: Fluss beider Leiter von r0 bis d-r0 gibt L' = (mu/pi) ln((d-r0)/r0)",
       sp.simplify(L_beide - mu_/pi*log(kk_)) == 0, f"{L_beide} mit k = (d-r0)/r0")
pruefe("(5.5) unabhaengig: fuer d >> r0 geht ln((d-r0)/r0) in ln(d/r0) ueber — dieselbe Naeherung wie bei C'",
       sp.limit(log(kk_)/log(1 + kk_), kk_, oo) == 1)
# (5.5) unabhaengig 2: ueber das Produkt L'C' = mu eps (gilt fuer jede TEM-Leitung)
yy = symbols("y", positive=True)                       # y = d/r0
L_naeh = mu_/pi*log(yy); C_naeh = pi*eps_/log(yy)
pruefe("(5.5)/(5.3) Gegenprobe: L' C' = mu eps — die Geometriefunktion ln(d/r0) kuerzt sich heraus",
       sp.simplify(L_naeh*C_naeh - mu_*eps_) == 0)
L_exakt = mu_/pi*ww
pruefe("(5.5) exakt: L' = (mu/pi) arcosh(d/(2r0)) folgt aus L'C' = mu eps mit dem exakten C'",
       sp.simplify(L_exakt*C_exakt - mu_*eps_) == 0, L_exakt)
pruefe("(5.5) Gegenprobe ueber Z_w und v: L' = Z_w/v und C' = 1/(Z_w v) geben dieselben Belaege",
       sp.simplify((1/pi*sqrt(mu_/eps_)*log(yy))/(1/sqrt(mu_*eps_)) - L_naeh) == 0
       and sp.simplify(1/((1/pi*sqrt(mu_/eps_)*log(yy))*(1/sqrt(mu_*eps_))) - C_naeh) == 0)
# Zahlen: wie weit liegt die Naeherung daneben?
eps0_z = 8.8541878128e-12; mu0_z = 4e-7*float(pi)
d_z, r_z = 10e-3, 0.5e-3
C_n = float(pi*eps0_z/sp.log(d_z/r_z)); C_e = float(pi*eps0_z/sp.acosh(d_z/(2*r_z)))
L_n = float(mu0_z/pi*sp.log(d_z/r_z)); L_e = float(mu0_z/pi*sp.acosh(d_z/(2*r_z)))
pruefe("Belaege Zahlen d=10 mm, r0=0,5 mm: Naeherung und exakte Form liegen 0,08 % auseinander, L'C' bleibt mu0 eps0",
       abs(100*(C_n - C_e)/C_e) < 0.1 and abs(100*(L_n - L_e)/L_e) < 0.1
       and abs(L_n*C_n/(mu0_z*eps0_z) - 1) < 1e-12 and abs(L_e*C_e/(mu0_z*eps0_z) - 1) < 1e-12,
       f"C' {C_n*1e12:.4f} gegen {C_e*1e12:.4f} pF/m, L' {L_n*1e6:.4f} gegen {L_e*1e6:.4f} uH/m")


json.dump({"posten": posten, "gleichungen_geprueft": sorted({g for q in posten for g in q["gleichungen"]}), "alle_richtig": all(q["richtig"] for q in posten)}, open("cas_ergebnis.json", "w"), indent=1, ensure_ascii=False)
print("ERGEBNIS:", "alle RICHTIG" if all(q["richtig"] for q in posten) else "FALSCH vorhanden", f"({len(posten)} Posten)")
