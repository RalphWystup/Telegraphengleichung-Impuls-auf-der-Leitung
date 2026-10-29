# Die Telegraphengleichung: vom Maxwell-Feld zum Impuls auf der Leitung

<img src="Foto_Ralph_Wystup.jpg" align="right" width="140" alt="Prof. Dr.-Ing. Ralph Wystup">

Prof. Dr.-Ing. Ralph Wystup M.Sc. — erstellt mit KI und Agent (Claude Code, Anthropic)

**Seite öffnen:** https://ralphwystup.github.io/Telegraphengleichung-Impuls-auf-der-Leitung/ — das Telegraphen-Labor 1.8: ein Impuls läuft über eine Doppelleitung, gerechnet
nach den im Manuskript hergeleiteten Regeln, auf zwei Wegen live gegeneinander (geschlossene Lösung mit dem
Verschiebungssatz und Zeitschrittverfahren); Quelle mit Innenwiderstand, Abschluss, Sternpunkt-Verteiler, Zeitlupe;
das Manuskript als Reiter in der Seite. Läuft offline.

Aus den Maxwellschen Gleichungen wird die Wellengleichung, aus dem Ersatzschaltbild der Leitung die
Telegraphengleichung. Zwei getrennte, geschlossene Lösungswege: Laplace in der Zeit mit dem Verschiebungssatz
(Weg A) und die doppelte Laplace-Transformation (Weg B). Kein Sinus — ein Impuls, der läuft, reflektiert wird und
durch Stoßstellen geht. Dazu die Beläge der Doppelleitung, der Wellenwiderstand, die Anpassung an Stoßstellen mit
dem Gleichungssystem, der reflexionsfreie Sternpunkt und der stetige Übergang. Jede Gleichung ist mit einem
CAS-Skript nachgerechnet (121 von 121 RICHTIG), der Impuls im Zeitbereich ohne Laplace gegengerechnet (≤ 2·10⁻¹² V).

![Der Impuls auf der angepassten Leitung](bilder/impuls_momentaufnahmen.png)

**Manuskript:** [`MANUSKRIPT_TELEGRAPHENGLEICHUNG_1.5.pdf`](MANUSKRIPT_TELEGRAPHENGLEICHUNG_1.5.pdf) — Manuskript 1.5 · Labor 1.8 · 29. Oktober 2026. **Beamer-Fassung:** [`BEAMER_TELEGRAPHENGLEICHUNG_1.5.pdf`](BEAMER_TELEGRAPHENGLEICHUNG_1.5.pdf) — derselbe Text,
entzerrt auf Folien, nichts weggelassen.

## Was drin ist

| Datei | Inhalt |
|:--|:--|
| [`Telegraphen_Labor_1.8.html`](Telegraphen_Labor_1.8.html) | das Telegraphen-Labor: Reiter Labor (Impuls, R_i, Z_a, Zeitlupe), Verzweigung (Sternpunkt 1 auf 2 mit R), Manuskript |
| [`MANUSKRIPT_TELEGRAPHENGLEICHUNG_1.5.pdf`](MANUSKRIPT_TELEGRAPHENGLEICHUNG_1.5.pdf) / [`.md`](MANUSKRIPT_TELEGRAPHENGLEICHUNG.md) | das Manuskript: Maxwell → Wellengleichung, Weg A, Weg B, Beläge, Stoßstellen, Prüfung, Zusammenfassung |
| [`BEAMER_TELEGRAPHENGLEICHUNG_1.5.pdf`](BEAMER_TELEGRAPHENGLEICHUNG_1.5.pdf) | die Beamer-Fassung (16:9), gesetzt aus derselben Quelle |
| `labor/` | der Rechenkern der Seite (`labor_kern.js`), seine Prüfungen in Node und im Browser und der vollständige Durchlauf `vollprobe.js` (55 Schritte) |
| `pruefung/` | CAS-Skript (sympy) mit Ergebnis, Abdeckungsnachweis, Zeitbereichsrechnung mit Ergebnis, Bilderzeugung und der dritte, unabhängige Weg `dritter_weg_netzwerk.py` (LC-Kette aus den Kirchhoffschen Gesetzen, ohne Reflexionsfaktoren) |
| `bilder/` | die Bilder des Manuskripts |
| `baue_labor.py`, `baue_beamer.py`, `beamer_kopf.tex` | die Bauskripte (pandoc, xelatex) |
| `index.html` | leitet auf die Seite weiter, damit GitHub Pages sie unter der Adresse oben zeigt |

## Prüfung

`pruefung/abdeckung.py` haelt die Liste der geprueften Gleichungen gegen alle nummerierten Gleichungen des
Manuskripts und gegen die Rechenregeln der Seite; sein Ergebnis: **alle Gleichungen und alle Rechenregeln sind
nachgerechnet.** Das CAS-Skript sagt je Gleichung RICHTIG oder FALSCH; das Zeitschrittverfahren (Leapfrog mit Δt = Δx/v, Randknoten
als halbe Zellen mit Trapezregel) wird in zehn Fällen gegen die geschlossene Lösung gehalten; der Kern der Seite wird
in Node gegen die Python-Zahlen und im echten Browser geprüft. Die Zahlen stehen im Manuskript, Abschnitt „Prüfung durch Rechnung".

## Lizenz

MIT, siehe [LICENSE](LICENSE).
