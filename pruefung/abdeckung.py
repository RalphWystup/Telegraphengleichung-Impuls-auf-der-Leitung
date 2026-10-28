#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Abdeckungsnachweis: Ist JEDE Gleichung des Manuskripts mit dem CAS nachgerechnet — und jede Rechenregel,
nach der die Laborseite rechnet?

Seine Forderung vom 28.10.2026: „sind alle! Gleichungen im Manuskript und im html mit CAS nachgerechnet! alle!"
Dieses Skript beantwortet das maschinell und sagt am Ende VOLLSTAENDIG oder nennt jede Luecke.

Drei Quellen werden gegeneinander gehalten:
  1. MANUSKRIPT_TELEGRAPHENGLEICHUNG.md   — jede nummerierte Gleichung steht als \\tag{x.y} da.
  2. pruefung/cas_ergebnis.json           — jeder CAS-Posten nennt in seinem Namen die Gleichungen, die er prueft.
  3. labor/labor_kern.js                  — der Rechenkern der Seite nennt in Kommentaren „Gl. x.y" die Regeln,
                                            nach denen er rechnet; jede davon muss im CAS stehen.
  4. baue_labor.py, Reiter „Rechenweg"    — dort steht jeder Rechenschritt der Simulation mit seiner
                                            Gleichungsnummer; auch die muessen im Manuskript und im CAS stehen.
Aufruf:  python3 abdeckung.py       (Rueckgabe 0 = vollstaendig)
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

H = Path(__file__).resolve().parent.parent
MANU = H / "MANUSKRIPT_TELEGRAPHENGLEICHUNG.md"
CAS = Path(__file__).resolve().parent / "cas_ergebnis.json"
KERN = H / "labor" / "labor_kern.js"
SEITE = H / "baue_labor.py"          # darin steht der Reiter „Rechenweg" mit seinen Gleichungsnummern

# Gleichungen, die nichts zu rechnen geben: reine Vereinbarungen und Definitionen. Jede steht hier mit Grund —
# eine Ausnahme ohne Begruendung waere eine Luecke mit gruenem Haken.
OHNE_RECHNUNG = {
    "1.1": "die Maxwellschen Gleichungen selbst — Ausgangspunkt, nicht Folgerung (ihre Umformung in (1.2) ist geprueft)",
    "3.11": "die Festsetzung R' = 0, G' = 0 (Idealisierung); was daraus folgt, steht in (3.12a/b) und ist geprueft",
    "4.1": "die Definition der doppelten Laplace-Transformation (an einer Testfunktion dennoch nachgerechnet)",
    "6.2": "die Stetigkeitsforderung an der Stossstelle — physikalische Setzung; ihre Folge (6.3) ist geprueft",
    "6.11": "das Gleichungssystem des Sternpunkts als Aufstellung; seine Loesung (6.12)/(6.13) ist geprueft",
}


def nummern(text: str) -> list[str]:
    return re.findall(r"\((\d+\.\d+[a-d]?)\)", text)


def main() -> int:
    manuskript = MANU.read_text(encoding="utf-8")
    soll = []
    for t in re.findall(r"\\tag\{([^}]*)\}", manuskript):
        if t not in soll:
            soll.append(t)
    erg = json.loads(CAS.read_text(encoding="utf-8"))
    posten = erg["posten"]
    geprueft: dict[str, list[str]] = {}
    for q in posten:
        for g in q.get("gleichungen", []):
            geprueft.setdefault(g, []).append(q["posten"])

    print(f"Manuskript: {len(soll)} nummerierte Gleichungen")
    print(f"CAS:        {len(posten)} Posten, {sum(1 for q in posten if q['richtig'])} RICHTIG, "
          f"{len(geprueft)} verschiedene Gleichungen genannt")

    fehler = 0
    offen = [g for g in soll if g not in geprueft and g not in OHNE_RECHNUNG]
    if offen:
        print(f"\nFEHLER  {len(offen)} Gleichung(en) ohne CAS-Posten: {', '.join(offen)}")
        fehler += len(offen)
    unbekannt = sorted(g for g in geprueft if g not in soll)
    if unbekannt:
        print(f"\nFEHLER  CAS nennt Nummern, die es im Manuskript nicht gibt: {', '.join(unbekannt)}")
        fehler += len(unbekannt)
    falsch = [q["posten"] for q in posten if not q["richtig"]]
    if falsch:
        print(f"\nFEHLER  {len(falsch)} Posten FALSCH:")
        for n in falsch:
            print(f"          {n}")
        fehler += len(falsch)

    # Die Rechenregeln der Laborseite: jede im Kern genannte Gleichung muss geprueft sein.
    kern = KERN.read_text(encoding="utf-8")
    im_kern = sorted({g for g in re.findall(r"Gl\.\s*(\d+\.\d+[a-d]?)", kern)}, key=lambda g: [int(p) for p in g.rstrip("abcd").split(".")])
    print(f"\nLaborseite (labor_kern.js): rechnet nach {len(im_kern)} Gleichungen — {', '.join(im_kern)}")
    luecke = [g for g in im_kern if g not in geprueft]
    if luecke:
        print(f"FEHLER  im Kern benutzt, aber nicht im CAS: {', '.join(luecke)}")
        fehler += len(luecke)
    nicht_im_manuskript = [g for g in im_kern if g not in soll]
    if nicht_im_manuskript:
        print(f"FEHLER  im Kern benutzt, steht aber nicht im Manuskript: {', '.join(nicht_im_manuskript)}")
        fehler += len(nicht_im_manuskript)

    # Der Reiter „Rechenweg" der Seite nennt an jedem Schritt seine Gleichung — auch die muss geprueft sein.
    seite = SEITE.read_text(encoding="utf-8")
    block = seite[seite.index("function rechenweg()"):seite.index("function PRUEFSTAND_abweichung")]
    im_reiter = sorted({g for g in re.findall(r"schritt\(\d+,[^,]*,\s*'([\d.,a-d ]*)'", block) for g in re.findall(r"\d+\.\d+[a-d]?", g)},
                       key=lambda g: [int(x) for x in g.rstrip("abcd").split(".")])
    print(f"Reiter \u201eRechenweg\u201c: {len(im_reiter)} Gleichungen genannt — {', '.join(im_reiter)}")
    luecke2 = [g for g in im_reiter if g not in geprueft]
    if luecke2:
        print(f"FEHLER  im Reiter genannt, aber nicht im CAS: {', '.join(luecke2)}")
        fehler += len(luecke2)
    fremd = [g for g in im_reiter if g not in soll]
    if fremd:
        print(f"FEHLER  im Reiter genannt, steht aber nicht im Manuskript: {', '.join(fremd)}")
        fehler += len(fremd)

    if OHNE_RECHNUNG:
        print(f"\nOhne eigene Rechnung ({len(OHNE_RECHNUNG)}), jede mit Grund:")
        for g, warum in sorted(OHNE_RECHNUNG.items()):
            print(f"  ({g})  {warum}")

    json.dump({"gleichungen_manuskript": soll, "geprueft": {g: p for g, p in sorted(geprueft.items())},
               "ohne_rechnung": OHNE_RECHNUNG, "kern_gleichungen": im_kern, "reiter_gleichungen": im_reiter, "fehler": fehler},
              open(Path(__file__).resolve().parent / "abdeckung.json", "w"), indent=1, ensure_ascii=False)

    if fehler:
        print(f"\nABDECKUNG UNVOLLSTAENDIG — {fehler} Befund(e)")
        return 1
    print(f"\nABDECKUNG VOLLSTAENDIG: alle {len(soll)} Gleichungen des Manuskripts und alle {len(im_kern)} "
          f"Rechenregeln der Laborseite sind mit dem CAS nachgerechnet (oder als Setzung begruendet).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
