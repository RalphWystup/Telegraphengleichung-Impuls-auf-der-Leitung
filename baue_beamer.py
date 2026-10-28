#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Beamer-Fassung aus derselben Markdown-Quelle, entzerrt und GEMESSEN:
- Jeder Unterabschnitt wird in Einheiten zerlegt (Formel, Bild, Tabelle, Liste, Absatz) und auf Rahmen verteilt;
  ein Bild oder eine Tabelle steht allein, ein Satz, der eine Formel einleitet (endet mit ':'), bleibt bei ihr,
  eine Fortsetzung nach der Formel (beginnt klein, z. B. „also ist") bleibt bei ihr.
- Nach jedem Satz liest das Skript das xelatex-Protokoll: jede zu breite Zeile (Overfull \\hbox) wird der Formel
  zugeordnet und die Formel an \\Longrightarrow bzw. am zweiten Gleichheitszeichen umgebrochen, sonst verkleinert;
  jeder zu hohe Rahmen (Overfull \\vbox) wird weiter geteilt. Das wiederholt sich, bis das Protokoll leer ist.
Sein Wort 28.10.2026: „weniger Gleichungen auf manche Seiten, manche Seiten sind einfach überladen" und
„nichts weglassen, sondern mehr Seiten". Nichts wird gekürzt: jede Einheit der Quelle erscheint genau einmal."""
import re, subprocess, sys, pathlib
H = pathlib.Path(__file__).resolve().parent
S = pathlib.Path("/tmp/claude-1000/-workspace/0b518e72-6cfa-4059-ab7a-f9cc02a3e816/scratchpad/beamer"); S.mkdir(parents=True, exist_ok=True)
FASSUNG = re.search(r"Fassung (\d+\.\d+)", (H / "MANUSKRIPT_TELEGRAPHENGLEICHUNG.md").read_text(encoding="utf-8")).group(1)
ZIEL = H / f"BEAMER_TELEGRAPHENGLEICHUNG_{FASSUNG}.pdf"

q = (H / "MANUSKRIPT_TELEGRAPHENGLEICHUNG.md").read_text(encoding="utf-8")
kopf, rumpf = q.split("\n---\n", 1)[0] + "\n---\n", q.split("\n---\n", 1)[1]
kopf = kopf.replace('documentclass: article\ngeometry: margin=2.3cm\nfontsize: 11pt', 'fontsize: 11pt\naspectratio: 169\ntheme: Boadilla\ncolortheme: seahorse\nnavigation: empty\nsection-titles: true')
kopf = re.sub(r"header-includes:\n(  - .*\n)+", "", kopf)   # Präambel kommt aus beamer_kopf.tex (-H), nicht aus dem YAML
assert "header-includes" not in kopf

def bloecke(text):
    """Zerlegt einen Unterabschnitt in Einheiten: Formelblock ($$...$$, ggf. mehrzeilig), Bild, Tabelle, Liste, Absatz."""
    zeilen = text.split("\n"); aus = []; puffer = []; art = None
    def schliesse():
        nonlocal puffer, art
        if puffer and "".join(puffer).strip(): aus.append([art or "absatz", "\n".join(puffer)])
        puffer = []; art = None
    i = 0
    while i < len(zeilen):
        z = zeilen[i]
        if z.startswith("$$"):
            schliesse(); blk = [z]
            if not (z.count("$$") >= 2 and len(z) > 2):
                i += 1
                while i < len(zeilen) and "$$" not in zeilen[i]: blk.append(zeilen[i]); i += 1
                if i < len(zeilen): blk.append(zeilen[i])
            aus.append(["formel", "\n".join(blk)]); i += 1; continue
        if z.startswith("!["):
            schliesse(); aus.append(["bild", z]); i += 1; continue
        if z.startswith("|"):
            schliesse(); blk = []
            while i < len(zeilen) and zeilen[i].startswith("|"): blk.append(zeilen[i]); i += 1
            aus.append(["tabelle", "\n".join(blk)]); continue
        if z.strip() == "":
            schliesse(); i += 1; continue
        if re.match(r"^([-*]|\d+\.)\s", z):                        # jeder Listenpunkt eine Einheit (Nummern bleiben: pandoc startnum)
            schliesse(); art = "liste"; puffer.append(z); i += 1
            while i < len(zeilen) and zeilen[i].startswith(("  ", "\t")) and zeilen[i].strip(): puffer.append(zeilen[i]); i += 1
            schliesse(); continue
        if art is None: art = "absatz"
        puffer.append(z); i += 1
    schliesse(); return aus

def gewicht(art, inhalt):
    if art == "formel":  return 3 + inhalt.count("\\\\") + (1 if "gathered" in inhalt or "aligned" in inhalt else 0)
    if art == "absatz":  return 1 + inhalt.count("\n") // 2
    if art == "liste":   return 1 + inhalt.count("\n") // 2 + 2 * (inhalt.count("$$") // 2)
    return 7                                                        # bild, tabelle: allein auf dem Rahmen

def einleitung(inhalt):
    """Ein Absatz ohne Satzende (':' oder ein Wort wie „lautet") leitet die folgende Formel ein."""
    return not inhalt.rstrip().endswith((".", "!", "?", ")", "\"", "“", "”"))
def gruppen(einheiten):
    """Gruppe = [Einleitungsabsatz] + Formel/Liste + [kurze, klein beginnende Fortsetzung]; eine Einleitung bindet vorwärts (Vorrang)."""
    aus = []
    for k, e in enumerate(einheiten):
        art, inhalt = e
        folgt = einheiten[k + 1][0] if k + 1 < len(einheiten) else None
        if art in ("formel", "liste") and aus and len(aus[-1]) == 1 and aus[-1][0][0] == "absatz" and einleitung(aus[-1][0][1]):
            aus[-1].append(e); continue                                       # Einleitung + Formel
        if art == "absatz" and aus and aus[-1][-1][0] == "formel" and len(aus[-1]) <= 2 and not (folgt in ("formel", "liste") and einleitung(inhalt)) \
           and (inhalt[:1].islower() or (inhalt.count("\n") == 0 and len(inhalt) < 90)):
            aus[-1].append(e); continue                                       # Formel + Fortsetzung
        aus.append([e])
    return aus

SPLIT = {}          # je Rahmen (Schlüssel: Inhalt seiner ersten Einheit) die höchste Zahl von Gruppen, wenn er zu hoch war
def rahmen(titel, gr, maxg):
    """Verteilt die Gruppen auf Rahmen; Bild oder Tabelle allein. Gibt Liste von (Rahmentitel, Einheiten, Gruppen) zurück."""
    seiten, akt, g = [], [], 0
    stuecke = []
    for grp in gr:                                                            # eine Gruppe schwerer als der Rahmen zerfällt in ihre Einheiten —
        paar = len(grp) == 2 and grp[0][0] == "absatz" and grp[1][0] == "formel" and grp[0][1].count("\n") <= 2   # außer kurze Einleitung + Formel
        stuecke.extend([[e] for e in grp] if sum(gewicht(a, i) for a, i in grp) > maxg and not paar else [grp])
    for grp in stuecke:
        w = sum(gewicht(a, i) for a, i in grp); allein = any(a in ("bild", "tabelle") for a, _ in grp)
        voll = akt and len(akt) >= SPLIT.get(akt[0][0][1], 99)                 # dieser Rahmen war zu hoch: weniger Gruppen
        if akt and (g + w > maxg or allein or voll): seiten.append(akt); akt, g = [], 0
        akt.append(grp); g += w
        if allein: seiten.append(akt); akt, g = [], 0
    if akt: seiten.append(akt)
    return [(titel if k == 0 else f"{titel} ({k + 1})", [e for grp in s for e in grp], s) for k, s in enumerate(seiten)]

# --- Quelle in Unterabschnitte zerlegen ---------------------------------------------------------------------------
teile = []          # (art, titel, gruppen) — art 'abschnitt' = Zeile "# ...", 'unter' = Rahmenquelle
abschnitt, unter, puffer = None, None, []
def leere():
    global puffer
    txt = "\n".join(puffer)
    if unter is not None: teile.append(["unter", unter, gruppen(bloecke(txt))])
    elif abschnitt is not None and txt.strip(): teile.append(["unter", abschnitt, gruppen(bloecke(txt))])
    puffer = []
for z in rumpf.split("\n"):
    if z.startswith("# "):
        leere(); abschnitt = z[2:].strip(); unter = None; teile.append(["abschnitt", z, None]); continue
    if z.startswith("## "):
        leere(); unter = z[3:].strip(); continue
    puffer.append(z)
leere()
anzahl_quelle = sum(len(grp) for t in teile if t[0] == "unter" for grp in t[2])

# --- Satz und Messung ---------------------------------------------------------------------------------------------
MAXG = {}           # je Unterabschnitt (Index in teile) die Rahmenlast; Start 8
STUFE = {}          # je Formel (Identität = Inhalt) die Behandlungsstufe 0..4
KLEIN = {}          # je Rahmentitel: Schriftgröße für Textrahmen ohne Formel
BILD = {}           # je Bildzeile: Breite in Prozent

def tiefe_split(s, trenner):
    """Trennt s an trenner, aber nur außerhalb von {}-Klammern und \\left...\\right."""
    teile_, akt, t, k = [], "", 0, 0
    i = 0
    while i < len(s):
        if s.startswith("\\left", i): k += 1
        if s.startswith("\\right", i): k -= 1
        if s[i] == "{": t += 1
        if s[i] == "}": t -= 1
        if t == 0 and k == 0 and s.startswith(trenner, i):
            teile_.append(akt); akt = ""; i += len(trenner); continue
        akt += s[i]; i += 1
    teile_.append(akt); return teile_

def breite(f):
    """Grobe Satzbreite einer Formelzeile in Zeichen: Brüche zählen mit der längeren Hälfte, Befehle als ein Zeichen."""
    f = re.sub(r"\\tag\{[^}]*\}", "", f)
    for _ in range(6):
        f = re.sub(r"\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}", lambda m: max(m.group(1), m.group(2), key=len), f)
        f = re.sub(r"\\sqrt\{([^{}]*)\}", lambda m: " " + m.group(1), f)
        f = re.sub(r"[\^_]\{([^{}]*)\}", lambda m: m.group(1)[: (len(m.group(1)) + 1) // 2], f)
    f = re.sub(r"\\(left|right|,|;|!|quad|qquad|operatorname|mathbf|boxed|begin\{[a-z]*\}|end\{[a-z]*\})", "  ", f)
    f = re.sub(r"\\[A-Za-z]+", "a", f); f = re.sub(r"[{}\s]", "", f)
    return max((len(z) for z in f.split("\\\\")), default=0)

def umbrechen(formel):
    """Stufe 1: Formel an \\Longrightarrow oder am zweiten '=' umbrechen (gathered/aligned). None, wenn nichts geht."""
    m = re.match(r"\$\$(.*)\$\$\s*$", formel, re.S)
    if not m: return None
    inhalt = m.group(1).strip()
    if "gathered" in inhalt or "aligned" in inhalt or "pmatrix" in inhalt or "vmatrix" in inhalt: return None
    tag = re.search(r"\\tag\{[^}]*\}", inhalt); tagtxt = tag.group(0) if tag else ""; inhalt = inhalt.replace(tagtxt, "").strip()
    for tr in ("\\quad\\Longrightarrow\\quad", "\\;\\Longrightarrow\\;", "\\Longrightarrow"):
        st = tiefe_split(inhalt, tr)
        if len(st) > 1:
            return "$$\\begin{gathered}" + (" \\\\ \\Longrightarrow ").join(x.strip() for x in st) + "\\end{gathered}" + tagtxt + "$$"
    for tr in (",\\qquad", "\\qquad"):
        st = tiefe_split(inhalt, tr)
        if len(st) > 1:
            return "$$\\begin{gathered}" + " \\\\ ".join(x.strip().rstrip(",") + ("," if j < len(st) - 1 else "") for j, x in enumerate(st)) + "\\end{gathered}" + tagtxt + "$$"
    st = tiefe_split(inhalt, "=")
    if len(st) > 2:                                                 # Gleichungskette: jedes Glied in eine Zeile
        return "$$\\begin{aligned}" + st[0].strip() + " &= " + " \\\\ &= ".join(x.strip() for x in st[1:]) + "\\end{aligned}" + tagtxt + "$$"
    return None

def formel_text(inhalt):
    """Formel nach Behandlungsstufe: 0 roh, 1 umgebrochen, 2 small, 3 footnotesize, 4 scriptsize (jeweils ab Stufe 2 zusätzlich umgebrochen)."""
    st = STUFE.get(inhalt, 0); f = inhalt
    if st >= 1:
        u = umbrechen(inhalt)
        if u: f = u
    gr = {2: "\\small", 3: "\\footnotesize", 4: "\\scriptsize", 5: "\\tiny"}.get(st)
    if gr: f = "```{=latex}\n\\begingroup" + gr + "\n```\n\n" + f + "\n\n```{=latex}\n\\endgroup\n```"
    return f

def baue_md():
    aus, rahmenliste = [kopf], []
    for idx, (art, titel, gr) in enumerate(teile):
        if art == "abschnitt": aus.append(titel); continue
        for rt, einheiten, grps in rahmen(titel, gr, MAXG.get(idx, 8)):
            rahmenliste.append((idx, rt, einheiten, grps))
            stuecke = []
            for a, i in einheiten:
                if a == "formel": stuecke.append(formel_text(i))
                elif a == "bild": stuecke.append(re.sub(r"\{width=\d+%\}", "", i) + "{width=80%% height=%d%%}" % BILD.get(i, 58))
                else: stuecke.append(i)
            gr_ = KLEIN.get(einheiten[0][1])
            inhalt = "\n\n".join(stuecke)
            if gr_: inhalt = "```{=latex}\n\\begingroup" + gr_ + "\n```\n\n" + inhalt + "\n\n```{=latex}\n\\endgroup\n```"
            aus.append(f"## {rt}\n\n{inhalt}\n")
    return "\n".join(aus), rahmenliste

def setzen(md):
    (S / "b.md").write_text(md, encoding="utf-8")
    r = subprocess.run(["pandoc", str(S / "b.md"), "-t", "beamer", "--slide-level=2", "-s", "-o", str(S / "b.tex"),
                        "-H", str(H / "beamer_kopf.tex"), "-V", "mainfont=DejaVu Sans", "-V", "monofont=DejaVu Sans Mono"], capture_output=True, text=True, cwd=H)
    if r.returncode: print(r.stderr[-800:]); sys.exit(1)
    for f in ("b.aux", "b.log", "b.nav", "b.snm", "b.toc", "b.out"): (S / f).unlink(missing_ok=True)
    r = subprocess.run(["xelatex", "-interaction=batchmode", "-halt-on-error", f"-output-directory={S}", str(S / "b.tex")], capture_output=True, text=True, cwd=H)
    log = (S / "b.log").read_text(encoding="utf-8", errors="replace")
    if "! " in log and r.returncode:
        print("xelatex-Fehler:", "\n".join(l for l in log.split("\n") if l.startswith("!"))[:600]); sys.exit(1)
    tex = (S / "b.tex").read_text(encoding="utf-8").split("\n")
    anf = [k for k, z in enumerate(tex) if z.startswith("\\begin{frame}")]
    def rahmen_nr(zeile):            # Nummer des Rahmens (0-basiert) zur tex-Zeile
        return max(k for k, a in enumerate(anf) if a + 1 <= zeile) if any(a + 1 <= zeile for a in anf) else None
    hbox = [(float(m.group(1)), rahmen_nr(int(m.group(3))), m.group(2).startswith("in paragraph")) for m in re.finditer(r"Overfull \\hbox \(([\d.]+)pt too wide\) (detected at line|in paragraph at lines) (\d+)", log)
            if float(m.group(1)) >= 4.0]                                       # unter 4 pt (1,4 mm) bleibt es
    vbox = [(float(m.group(1)), rahmen_nr(int(m.group(2)))) for m in re.finditer(r"Overfull \\vbox \(([\d.]+)pt too high\) (?:detected at line|has occurred while \\output is active|in paragraph at lines)\s*(\d+)?", log) if m.group(2)]
    seiten = re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(S / "b.pdf")], capture_output=True, text=True).stdout)
    return hbox, vbox, int(seiten.group(1)) if seiten else 0, len(anf)

for runde in range(1, 9):
    md, rahmenliste = baue_md()
    hbox, vbox, seiten, nf = setzen(md)
    assert nf == len(rahmenliste), f"Rahmenzahl tex {nf} != md {len(rahmenliste)}"
    print(f"Runde {runde}: {seiten} Seiten, {len(rahmenliste)} Rahmen, zu breit {len(hbox)}, zu hoch {len(vbox)}")
    if not hbox and not vbox: break
    for zubreit, nr, im_text in hbox:
        if nr is None: continue
        idx, rt, einheiten, grps = rahmenliste[nr]
        formeln = [i for a, i in einheiten if a == "formel"]
        if formeln and not im_text:                                           # „detected at line" = Formelsatz; „in paragraph" = Fließtext
            # die breiteste Formel zuerst; schon behandelte eine Stufe weiter
            # die (geschätzt) breiteste Formel in ihrer jetzigen Form; eine schon behandelte wird nur weiterbehandelt, wenn keine andere breiter ist
            ziel = max(formeln, key=lambda f: breite(formel_text(f)))
            s = STUFE.get(ziel, 0)                                   # Stufe 1 (Umbruch) nur, wenn er möglich ist; sonst direkt verkleinern
            STUFE[ziel] = min(3, s + 1 if (s >= 1 or umbrechen(ziel) is not None) else 2)
        else:
            KLEIN[einheiten[0][1]] = {None: "\\small", "\\small": "\\footnotesize", "\\footnotesize": "\\scriptsize"}.get(KLEIN.get(einheiten[0][1]), "\\scriptsize")
    for hoehe, nr in vbox:
        if nr is None: continue
        idx, rt, einheiten, grps = rahmenliste[nr]
        if len(grps) > 1:
            SPLIT[einheiten[0][1]] = len(grps) - 1                # nur diesen Rahmen teilen: die letzte Gruppe wandert auf den nächsten
        elif any(a == "bild" for a, _ in einheiten):
            for a, i in einheiten:
                if a == "bild": BILD[i] = max(30, BILD.get(i, 58) - 8)
        else:
            KLEIN[einheiten[0][1]] = {None: "\\small", "\\small": "\\footnotesize", "\\footnotesize": "\\scriptsize"}.get(KLEIN.get(einheiten[0][1]), "\\scriptsize")
else:
    print("WARNUNG: nach 8 Runden noch nicht sauber");
md, rahmenliste = baue_md()
hbox, vbox, seiten, nf = setzen(md)                      # Schlussdurchläufe: zweimal setzen, damit die Gesamtzahl in der Fußzeile stimmt
subprocess.run(["xelatex", "-interaction=batchmode", f"-output-directory={S}", str(S / "b.tex")], capture_output=True, text=True, cwd=H)
subprocess.run(["xelatex", "-interaction=batchmode", f"-output-directory={S}", str(S / "b.tex")], capture_output=True, text=True, cwd=H)
print(f"Schluss: zu breit {len(hbox)}, zu hoch {len(vbox)}")
anzahl_rahmen = sum(len(e) for _, _, e, _ in rahmenliste)
assert anzahl_rahmen == sum(len(grp) for t in teile if t[0] == "unter" for grp in t[2]) == anzahl_quelle, "Einheiten verloren"
(H / "BEAMER_TELEGRAPHENGLEICHUNG.md").write_text(md, encoding="utf-8")
subprocess.run(["cp", str(S / "b.pdf"), str(ZIEL)], check=True)
print(f"{ZIEL.name}: {seiten} Seiten, {len(rahmenliste)} Rahmen, {anzahl_quelle} Einheiten der Quelle, alle enthalten; "
      f"umgebrochen/verkleinert: {sum(1 for v in STUFE.values() if v >= 1)} Formeln, {len(KLEIN)} Textrahmen, zu hohe Rahmen geteilt: {len(SPLIT)}")
