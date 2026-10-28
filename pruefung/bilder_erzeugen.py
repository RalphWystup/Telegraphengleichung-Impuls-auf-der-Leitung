#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schaubilder für Manuskript und Beamer-Fassung (matplotlib, keine Fremdbilder): Ersatzschaltbild des Leitungselements,
Doppelleitung, Verschiebungssatz, d'Alembert-Zerfall eines Gaußpulses, Weg-Zeit-Bild der Reflexionen, Sternpunkt-Anpassung."""
import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
B = "/workspace/Telegraphengleichung/bilder/"
plt.rcParams.update({"font.size": 12, "font.family": "DejaVu Sans"})

def widerstand(ax, x, y, w=0.9, h=0.3, senkrecht=False, text=""):
    if senkrecht: ax.add_patch(Rectangle((x - h/2, y - w/2), h, w, fill=False, lw=1.6)); ax.text(x + 0.25, y, text, va="center")
    else: ax.add_patch(Rectangle((x - w/2, y - h/2), w, h, fill=False, lw=1.6)); ax.text(x, y + 0.32, text, ha="center")
def spule(ax, x, y, w=0.9, text=""):
    xs = np.linspace(x - w/2, x + w/2, 200); ys = y + 0.16*np.abs(np.sin(4*np.pi*(xs - (x - w/2))/w))
    ax.plot(xs, ys, "k", lw=1.6); ax.text(x, y + 0.36, text, ha="center")
def kondensator(ax, x, y, text=""):
    ax.plot([x - 0.22, x + 0.22], [y + 0.08, y + 0.08], "k", lw=2.2); ax.plot([x - 0.22, x + 0.22], [y - 0.08, y - 0.08], "k", lw=2.2); ax.text(x + 0.3, y, text, va="center")

# 1 Ersatzschaltbild des Leitungselements
fig, ax = plt.subplots(figsize=(9, 3.6)); ax.set_xlim(-0.6, 8.2); ax.set_ylim(-0.6, 2.6); ax.axis("off")
ax.plot([0, 1.1], [2, 2], "k", lw=1.6); widerstand(ax, 1.6, 2, text="R' dx"); ax.plot([2.05, 2.6], [2, 2], "k", lw=1.6); spule(ax, 3.1, 2, text="L' dx"); ax.plot([3.55, 7.2], [2, 2], "k", lw=1.6)
ax.plot([0, 7.2], [0, 0], "k", lw=1.6)
# Die Querzweige: die Leitung führt BIS AN das Bauteil und hinter ihm weiter — nicht durch das Symbol hindurch.
# (Befund 28.10.2026: die senkrechte Linie lief durchgezogen durch Leitwert UND Kondensator, beim Kondensator
#  also quer zwischen den Platten hindurch — das wäre ein Kurzschluss des Bauteils.)
widerstand(ax, 4.3, 1.0, senkrecht=True, text="G' dx")          # Rechteck von y = 0,55 bis y = 1,45
ax.plot([4.3, 4.3], [2, 1.45], "k", lw=1.6); ax.plot([4.3, 4.3], [0.55, 0], "k", lw=1.6)
kondensator(ax, 5.6, 1.0, text="C' dx")                          # Platten bei y = 1,08 und y = 0,92
ax.plot([5.6, 5.6], [2, 1.08], "k", lw=1.6); ax.plot([5.6, 5.6], [0.92, 0], "k", lw=1.6)
for x in (0, 7.2):
    ax.add_patch(Circle((x, 2), 0.07, color="k")); ax.add_patch(Circle((x, 0), 0.07, color="k"))
ax.annotate("", (0.9, 2.25), (0.1, 2.25), arrowprops=dict(arrowstyle="->", lw=1.4)); ax.text(0.45, 2.38, "i(x,t)", ha="center")
ax.annotate("", (7.1, 2.25), (6.3, 2.25), arrowprops=dict(arrowstyle="->", lw=1.4)); ax.text(6.7, 2.38, "i(x+dx,t)", ha="center")
ax.annotate("", (-0.3, 0.2), (-0.3, 1.8), arrowprops=dict(arrowstyle="->", lw=1.4)); ax.text(-0.45, 1.0, "u(x,t)", ha="right", va="center")
ax.annotate("", (7.5, 0.2), (7.5, 1.8), arrowprops=dict(arrowstyle="->", lw=1.4)); ax.text(7.65, 1.0, "u(x+dx,t)", ha="left", va="center")
ax.text(0, -0.45, "x", ha="center"); ax.text(7.2, -0.45, "x + dx", ha="center")
ax.set_title("Ersatzschaltbild eines Leitungselements der Länge dx")
fig.tight_layout(); fig.savefig(B + "esb_leitungselement.png", dpi=150); plt.close(fig)

# 2 Doppelleitung (Querschnitt) mit Feldlinien-Andeutung
fig, ax = plt.subplots(figsize=(7, 3.6)); ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-2.2, 4.2); ax.set_ylim(-1.8, 1.8)
for xc, lab, col in ((0, "+Q*, i", "tab:red"), (2, "−Q*, −i", "tab:blue")):
    ax.add_patch(Circle((xc, 0), 0.25, color=col, alpha=.85)); ax.text(xc, -0.55, lab, ha="center", color=col)
ax.annotate("", (1.75, 0.9), (0.25, 0.9), arrowprops=dict(arrowstyle="<->", lw=1.3)); ax.text(1.0, 1.0, "d", ha="center")
ax.annotate("", (0.25, -1.1), (0.0, -1.1), arrowprops=dict(arrowstyle="<->", lw=1.1)); ax.text(0.12, -1.35, "r₀", ha="center")
th = np.linspace(0, 2*np.pi, 300)
for r in (0.45, 0.75, 1.1): ax.plot(r*np.cos(th), r*np.sin(th), color="tab:red", lw=.8, alpha=.5); ax.plot(2 + r*np.cos(th), r*np.sin(th), color="tab:blue", lw=.8, alpha=.5)
ax.text(3.0, 1.2, "C' = πε / ln(d/r₀)\nL' = (μ/π) ln(d/r₀)\nZ_w = √(L'/C')\nv = 1/√(L'C') = 1/√(με)", va="top", fontsize=11, bbox=dict(boxstyle="round", fc="w"))
ax.set_title("Doppelleitung (Querschnitt), d ≫ r₀")
fig.tight_layout(); fig.savefig(B + "doppelleitung.png", dpi=150); plt.close(fig)

# 3 Verschiebungssatz: Impuls am Eingang und an der Stelle x
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
t = np.linspace(-1, 8, 1000); e = ((t >= 0) & (t < 2)).astype(float); tau = 3.5
ax[0].plot(t, e, lw=2); ax[0].set_title("Eingang: e(t)"); ax[0].set_xlabel("t"); ax[0].set_ylabel("u"); ax[0].grid(alpha=.3)
ax[1].plot(t, ((t >= tau) & (t < tau + 2)).astype(float), lw=2, color="tab:orange"); ax[1].axvline(tau, ls="--", color="gray")
ax[1].annotate("", (tau, 0.55), (0, 0.55), arrowprops=dict(arrowstyle="->", lw=1.2, color="gray")); ax[1].text(tau/2, 0.6, "τ = √(L'C')·x", ha="center", color="dimgray")
ax[1].set_title("an der Stelle x: u(x,t) = e(t − τ)"); ax[1].set_xlabel("t"); ax[1].grid(alpha=.3)
fig.tight_layout(); fig.savefig(B + "verschiebungssatz.png", dpi=150, bbox_inches="tight"); plt.close(fig)

# 4 d'Alembert: Gaußpuls zerfällt in zwei Hälften
fig, ax = plt.subplots(figsize=(9, 3.4)); z = np.linspace(-8, 8, 1200); c = 1.0
for k, tt in enumerate((0, 1.5, 3.0, 4.5)):
    H = 0.5*np.exp(-(z - c*tt)**2) + 0.5*np.exp(-(z + c*tt)**2)
    ax.plot(z, H + 0*k, lw=2, label=f"t = {tt:.1f}", alpha=1 - 0.18*k)
ax.set_xlabel("z"); ax.set_ylabel("H"); ax.legend(); ax.grid(alpha=.3)
ax.set_title("Weg B: f(z) = e^{−z²} bei t = 0 → ½f(z−ct) + ½f(z+ct)")
fig.tight_layout(); fig.savefig(B + "dalembert_gausspuls.png", dpi=150); plt.close(fig)

# 5 Weg-Zeit-Bild der Reflexionen (Leerlauf, R_i = 0)
fig, ax = plt.subplots(figsize=(6.5, 4.2)); l = 1.0; v = 1.0
for n in range(4):
    t0 = 2*n*l/v; ax.plot([0, l], [t0, t0 + l/v], color="tab:blue" if n % 2 == 0 else "tab:red", lw=2)
    ax.plot([l, 0], [t0 + l/v, t0 + 2*l/v], color="tab:blue" if n % 2 == 0 else "tab:red", lw=2, ls="--")
    ax.text(l*0.5, t0 + 0.5*l/v + 0.1, "+1" if n % 2 == 0 else "−1", color="tab:blue" if n % 2 == 0 else "tab:red", ha="center")
    ax.text(l*0.5, t0 + 1.5*l/v + 0.1, "r = +1" if n % 2 == 0 else "r·(−1) = −1", color="tab:blue" if n % 2 == 0 else "tab:red", ha="center")
ax.set_xlabel("x"); ax.set_ylabel("t"); ax.set_xticks([0, l]); ax.set_xticklabels(["0 (Generator, R_i = 0)", "l (Leerlauf)"]); ax.set_yticks([0, 2, 4, 6]); ax.set_yticklabels(["0", "2τ₀", "4τ₀", "6τ₀"])
ax.set_title("Weg-Zeit-Bild: am Ende r = +1, am Generator −1"); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(B + "wegzeit_leerlauf.png", dpi=150); plt.close(fig)

# 6 Sternpunkt-Anpassung (ohne gedrehte Bauteile; Beschriftung außerhalb der Linien)
fig, ax = plt.subplots(figsize=(8.5, 4.6)); ax.axis("off"); ax.set_xlim(-0.3, 9.6); ax.set_ylim(-2.9, 2.6)
ax.plot([0, 1.2], [0, 0], "k", lw=1.6); widerstand(ax, 1.75, 0, w=0.9, text="R"); ax.plot([2.2, 3.2], [0, 0], "k", lw=1.6); ax.add_patch(Circle((3.2, 0), 0.09, color="k"))
ax.text(0.0, -0.5, "von der Quelle, 50 Ω", ha="left", fontsize=11)
for y, lab in ((1.5, "Leitung 2, Z_w = 50 Ω"), (-1.5, "Leitung 3, Z_w = 50 Ω")):
    ax.plot([3.2, 4.2], [0, y], "k", lw=1.6); ax.plot([4.2, 4.9], [y, y], "k", lw=1.6); widerstand(ax, 5.35, y, w=0.9, text="R"); ax.plot([5.8, 7.4], [y, y], "k", lw=1.6)
    ax.text(7.5, y, lab, va="center", fontsize=11)
ax.text(4.75, -2.5, "Von jedem Zweig aus gesehen:  R + (R+50 Ω) ∥ (R+50 Ω) = R + (R+50 Ω)/2 = 50 Ω\n⇒ 100 Ω = 3R + 50 Ω  ⇒  R = 50/3 Ω = 16,67 Ω", ha="center", fontsize=11, bbox=dict(boxstyle="round", fc="w"))
ax.set_title("Reflexionsfreier Verteiler 1 auf 2 (Sternpunkt)")
fig.tight_layout(); fig.savefig(B + "sternpunkt_anpassung.png", dpi=150); plt.close(fig)
print("6 Bilder geschrieben")

# 7 Skizze Kapazitätsbelag (Querschnitt, Ladungen, Abstände, Aufpunkt)
fig, ax = plt.subplots(figsize=(8, 3.8)); ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1.6, 6.2); ax.set_ylim(-1.9, 1.9)
ax.add_patch(Circle((0, 0), 0.3, color="tab:red", alpha=.85)); ax.add_patch(Circle((4, 0), 0.3, color="tab:blue", alpha=.85))
ax.text(0, 0.5, "+Q*", ha="center", color="tab:red", fontsize=13); ax.text(4, 0.5, "−Q*", ha="center", color="tab:blue", fontsize=13)
ax.text(0, -0.55, "Leiter +, φ₊", ha="center"); ax.text(4, -0.55, "Leiter −, φ₋", ha="center")
ax.plot([0, 0.3*np.cos(2.3)], [0, 0.3*np.sin(2.3)], "k", lw=1); ax.text(-0.45, 0.35, "r₀", ha="center")
ax.annotate("", (4, -1.2), (0, -1.2), arrowprops=dict(arrowstyle="<->", lw=1.2)); ax.text(2, -1.45, "d  (d ≫ r₀)", ha="center")
P = 1.6; ax.plot([P], [0], "ko"); ax.text(P, 0.18, "P", ha="center")
ax.annotate("", (P, 0.9), (0, 0.9), arrowprops=dict(arrowstyle="<->", lw=1)); ax.text(P/2, 1.0, "r", ha="center")
ax.annotate("", (4, 0.9), (P, 0.9), arrowprops=dict(arrowstyle="<->", lw=1)); ax.text((P + 4)/2, 1.0, "d − r", ha="center")
ax.annotate("", (P + 0.7, 0), (P + 0.1, 0), arrowprops=dict(arrowstyle="->", lw=1.6, color="tab:green")); ax.text(P + 0.4, -0.3, "E(r) = Q*/(2πε)·(1/r + 1/(d−r))", ha="center", color="tab:green", fontsize=10)
ax.text(5.2, 1.2, "φ(r) = Q*/(2πε)·ln(1/r) + const\nU = φ₊ − φ₋ = (Q*/πε)·ln(d/r₀)\nC' = Q*/U = πε / ln(d/r₀)", va="top", fontsize=10, bbox=dict(boxstyle="round", fc="w"))
ax.set_title("Kapazitätsbelag der Doppelleitung (Querschnitt)")
fig.tight_layout(); fig.savefig(B + "belag_kapazitaet.png", dpi=150); plt.close(fig)

# 8 Skizze Induktivitätsbelag (Seitenansicht; Feldkreise links als Stirnansicht, Formeln unten mit Platz)
fig, ax = plt.subplots(figsize=(9.5, 5.2)); ax.axis("off"); ax.set_xlim(-2.6, 8.9); ax.set_ylim(-3.6, 2.6)
for y, col, lab in ((1.2, "tab:red", "Leiter 1: Strom i →"), (-1.2, "tab:blue", "Leiter 2: Strom −i ←")):
    ax.add_patch(Rectangle((0, y - 0.12), 7, 0.24, color=col, alpha=.85)); ax.text(3.5, y + 0.3 if y > 0 else y - 0.45, lab, ha="center", color=col, fontsize=11)
ax.annotate("", (6.2, 1.2), (3.5, 1.2), arrowprops=dict(arrowstyle="->", lw=2, color="w")); ax.annotate("", (0.8, -1.2), (3.5, -1.2), arrowprops=dict(arrowstyle="->", lw=2, color="w"))
ax.add_patch(Rectangle((0, -1.08), 7, 2.16, fill=True, fc="tab:green", alpha=.12, ec="tab:green", lw=1.5))
ax.text(3.5, 0.15, "Fläche A zwischen den Drähten", ha="center", va="center", fontsize=11); ax.text(3.5, -0.35, "dA = l·dr,  Φ₁ = ∫_A μ H_φ dA", ha="center", va="center", fontsize=11)
ax.annotate("", (7, 2.1), (0, 2.1), arrowprops=dict(arrowstyle="<->", lw=1.2)); ax.text(3.5, 2.25, "Länge l", ha="center")
ax.annotate("", (7.4, -1.08), (7.4, 1.08), arrowprops=dict(arrowstyle="<->", lw=1.2)); ax.text(7.55, 0, "r von r₀ bis d", ha="left", va="center")
# Stirnansicht links: Leiter 1 als Punkt mit Feldkreisen H_phi = i/(2 pi r)
th = np.linspace(0, 2*np.pi, 200); cx = -1.6
ax.add_patch(Circle((cx, 1.2), 0.12, color="tab:red")); ax.text(cx, 1.2, "⊙", ha="center", va="center", color="w", fontsize=8)
for rr_ in (0.35, 0.65, 0.95): ax.plot(cx + rr_*np.cos(th), 1.2 + rr_*np.sin(th), color="tab:red", lw=.9, alpha=.7)
ax.text(cx, 2.35, "Stirnansicht Leiter 1", ha="center", fontsize=9); ax.text(cx, -0.1, "H_φ = i/(2πr)", ha="center", fontsize=10, color="tab:red")
ax.add_patch(Circle((cx, -1.2), 0.12, color="tab:blue")); ax.text(cx, -1.2, "⊗", ha="center", va="center", color="w", fontsize=8)
ax.text(3.2, -2.5, "Φ₁ = (μ i l / 2π) · ∫ dr/r von r₀ bis d = (μ i l / 2π) · ln(d/r₀)\nLeiter 2 trägt zwischen den Drähten gleichsinnig bei:  Φ = 2Φ₁ = L·i\n⇒  L' = L/l = (μ/π) · ln(d/r₀)", ha="center", va="center", fontsize=10.5, bbox=dict(boxstyle="round", fc="w"))
ax.set_title("Induktivitätsbelag der Doppelleitung (Seitenansicht)")
fig.tight_layout(); fig.savefig(B + "belag_induktivitaet.png", dpi=150); plt.close(fig)
print("Belagsskizzen geschrieben")
