#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut die Laborseite Telegraphen_Labor_<FASSUNG>.html: Reiter LABOR (Impulsausbreitung aus den hergeleiteten Regeln,
zwei Wege live gegeneinander, Quelle mit R_i, Abschluss Z_a, Zeitlupe) und Reiter MANUSKRIPT (dieselbe Markdown-Quelle,
mit MathML und eingebetteten Bildern). Rechenkern: labor/labor_kern.js (in Node gegen Python geprüft). Eine Datei, kein Netz."""
import json, re, subprocess, time, base64
from pathlib import Path
H = Path(__file__).resolve().parent
FASSUNG = "1.5"; STAND = "28.10.2026"
kern = (H / "labor" / "labor_kern.js").read_text(encoding="utf-8").split("if (typeof module !== 'undefined')")[0]
# Manuskript als HTML-Rumpf mit MathML und eingebetteten Bildern
r = subprocess.run(["pandoc", "MANUSKRIPT_TELEGRAPHENGLEICHUNG.md", "-s", "--embed-resources", "--mathml", "-o", "-"], cwd=H, capture_output=True, text=True)
doku = re.search(r"<body[^>]*>(.*)</body>", r.stdout, re.S).group(1)
doku = doku.replace("<script", "<!--script").replace("</script>", "</script-->")       # kein Fremdskript im Reiter
REVISION = json.dumps({"revision": f"Telegraphen_Labor_{FASSUNG}", "datum": STAND, "projekt": "Telegraphengleichung",
    "gebaut_von": ["baue_labor.py (labor/labor_kern.js + MANUSKRIPT_TELEGRAPHENGLEICHUNG.md)"], "aenderungen": ["1.1: Quellenwiderstand als beschriftetes Eingabefeld mit Vorgaben 0 und Z_w; Oszilloskop mit Achsenmarken, Zeitzeiger und Erklaerung", "1.2: Wellenwiderstand, v und tau0 live bei der Leitung; Knoepfe R_i = Z_w, Z_a = Z_w (als Wert) und beide anpassen; Impulsdauer mit Impulslaenge v*T; Gaussimpuls nach Gl. 7.1 mit sigma(t)", "1.4: Reiter Rechenweg — jeder Schritt der Simulation mit seiner Gleichungsnummer und den eingestellten Zahlen (ZURUECKGEZOGEN: die Hilfsfunktion des Reiters hiess schritt() wie der Zeitschritt des Labors und hat ihn ueberschrieben — die Seite rechnete nicht mehr)", "1.5: derselbe Reiter, Hilfsfunktion in wegschritt() umbenannt; labor/vollprobe.js spielt alle Bedienelemente durch, labor/pruefe_seite.js nimmt die Seite mit harten Sollwerten ab (die Zeit muss laufen, beide Wege muessen sich decken)", "1.3: Reiter Verzweigung (Sternpunkt 1 auf 2, ein R fuer alle drei Zweige, optimal oder frei, eigener Start); feine Spannungsskala (1-2-5-Raster) und Amplitude jedes Impulses direkt am Impuls; Ersatzschaltbild im Manuskript berichtigt"],
    "rechenregeln": ["Weg 1: Gl. 3.24 (Summe verzoegerter Impulse, Verschiebungssatz)", "Weg 2: Gl. 2.3/2.6 Leapfrog, dt = dx/v, Randknoten halbe Zellen mit Trapezregel", "Belaege Gl. 5.3/5.5", "Gaussimpuls Gl. 7.1, Impulslaenge Gl. 7.2"],
    "pruefung": "labor/vollprobe.js (alle Knoepfe und Eingaben), labor/pruefe_seite.js (Abnahme im Browser), labor/pruefe_kern.js (Node) gegen pruefung/impuls_auf_leitung.py: <= 3e-14 V in zehn Faellen (sechs Rechteck, ein Gauss, drei Verzweigung); pruefung/abdeckung.py weist nach, dass alle 18 Rechenregeln dieser Seite und alle 92 Gleichungen des Manuskripts mit dem CAS nachgerechnet sind"}, ensure_ascii=False, indent=1)

seite = r"""<meta charset="utf-8">
<script type="application/json" id="revision">__REVISION__</script>
<title>Telegraphen-Labor · Fassung __FASSUNG__</title>
<style>
:root{--tinte:#1c1f24;--flaeche:#fff;--rand:#d6dae0;--grau:#5b6270;--akzent:#1f5fa8;--hinter:#f4f5f7}
*{box-sizing:border-box} body{margin:0;background:var(--hinter);color:var(--tinte);font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif}
.kopf{display:flex;align-items:center;gap:22px;padding:10px 20px;background:var(--flaeche);border-bottom:1px solid var(--rand)}
.marke{font-weight:600;font-size:17px}.marke span{font-weight:400;color:var(--grau);margin-left:10px;font-size:13px}
.reiter{flex-shrink:0;white-space:nowrap;margin-left:auto}
.reiter button{border:0;background:none;padding:8px 14px;font:inherit;color:var(--grau);border-bottom:2px solid transparent;cursor:pointer}
.reiter button.an{color:var(--akzent);border-bottom-color:var(--akzent)}
#ansicht-labor,#ansicht-stern{display:grid;grid-template-columns:330px 1fr;gap:16px;padding:16px}
label.radio{display:flex;gap:8px;align-items:center}
.karte{background:var(--flaeche);border:1px solid var(--rand);border-radius:8px;padding:14px 16px}
.karte h3{margin:0 0 8px;font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--grau)}
label{display:block;font-size:13px;color:var(--grau);margin-top:8px}
input[type=number],select{width:100%;padding:5px 7px;font:inherit;border:1px solid var(--rand);border-radius:5px}
input[type=range]{width:100%}
.zeile{display:grid;grid-template-columns:1fr 1fr;gap:8px}
button.k{margin-top:10px;padding:7px 12px;font:inherit;border:1px solid var(--akzent);background:var(--akzent);color:#fff;border-radius:6px;cursor:pointer}
button.k.leise{background:var(--flaeche);color:var(--akzent)}
canvas{width:100%;background:#14171c;border-radius:6px;display:block}
.werte{font-family:ui-monospace,Consolas,monospace;font-size:13px;line-height:1.7;white-space:pre-wrap}
.ergebnis{margin-top:8px;padding:6px 8px;background:var(--hinter);border-radius:5px;color:var(--akzent);font-weight:600}
#ansicht-doku{max-width:900px;margin:0 auto;padding:20px 24px;background:var(--flaeche)}
#ansicht-doku img{max-width:100%}#ansicht-doku table{border-collapse:collapse}#ansicht-doku td,#ansicht-doku th{border:1px solid var(--rand);padding:4px 8px}
.hinweis{font-size:13px;color:var(--grau);margin-top:8px}
.wegtext{max-width:1000px;margin:0 auto;padding:20px 24px;background:var(--flaeche)}
.wegtext h2{margin:0 0 6px;font-size:21px}.wegtext h3{margin:26px 0 10px;font-size:15px;color:var(--akzent);border-bottom:1px solid var(--rand);padding-bottom:5px}
.vorsatz{color:var(--tinte);margin:0 0 14px}
.nachweis{background:#eef5ff;border:1px solid #cfe0f7;border-radius:7px;padding:10px 13px;font-size:13.5px;color:#14427c}
.schritt{display:grid;grid-template-columns:34px 1fr;gap:12px;padding:11px 0;border-top:1px solid var(--rand)}
.schritt:first-child{border-top:0}
.nr{width:26px;height:26px;border-radius:50%;background:var(--akzent);color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600}
.titel{font-weight:600}
.gl{display:inline-block;margin-left:8px;padding:1px 7px;border:1px solid var(--akzent);border-radius:10px;color:var(--akzent);font-size:11.5px;font-weight:600;vertical-align:1px}
.formel{font-family:ui-monospace,Consolas,monospace;font-size:13.5px;margin:5px 0 3px;color:var(--tinte)}
.zahlen{font-family:ui-monospace,Consolas,monospace;font-size:13px;color:#0a6b3d;white-space:pre-wrap}
.warum{font-size:13px;color:var(--grau);margin-top:3px}
.nz{font-family:ui-monospace,Consolas,monospace}
</style>
<header class="kopf"><div class="marke">Telegraphen-Labor<span>Stand __STAND__ · Fassung __FASSUNG__ — Impuls auf der Leitung, gerechnet nach den Gleichungen des Manuskripts</span></div>
<nav class="reiter"><button id="r-labor" class="an" onclick="zeige('labor')">Labor</button><button id="r-stern" onclick="zeige('stern')">Verzweigung</button><button id="r-weg" onclick="zeige('weg')">Rechenweg</button><button id="r-doku" onclick="zeige('doku')">Manuskript</button></nav></header>
<div id="ansicht-labor">
 <div>
  <div class="karte"><h3>Leitung (Doppelleitung, Gl. 5.3/5.5)</h3>
   <div class="zeile"><label>Abstand d / mm<input type="number" id="d" value="10" step="0.5" min="1"></label><label>Drahtradius r₀ / mm<input type="number" id="r0" value="0.5" step="0.1" min="0.05"></label></div>
   <div class="zeile"><label>ε_r<input type="number" id="epsr" value="1" step="0.1" min="1"></label><label>Länge l / m<input type="number" id="l" value="3" step="0.5" min="0.2"></label></div>
   <div class="werte ergebnis" id="zwAnzeige">—</div>
  </div>
  <div class="karte"><h3>Quelle e(t), Innenwiderstand R_i</h3>
   <div class="zeile"><label>Form<select id="form"><option value="rechteck">Rechteck</option><option value="gauss">Gauß</option></select></label><label>Höhe E₀ / V<input type="number" id="E0" value="1" step="0.1"></label></div>
   <div class="zeile"><label>Impulsdauer T / ns<input type="number" id="T" value="2" step="0.5" min="0.1"></label><label>Quellenwiderstand R_i / Ω<input type="number" id="Ri" value="0" step="1" min="0"></label></div>
   <div class="hinweis" id="impulslaenge">—</div>
   <div class="zeile"><button class="k leise" onclick="$('Ri').value=0;$('Ri').dispatchEvent(new Event('change'))">R_i = 0 (ideale Quelle)</button><button class="k leise" onclick="setzeRi()">R_i = Z_w übernehmen</button></div>
  </div>
  <div class="karte"><h3>Abschluss Z_a (Gl. 3.21)</h3>
   <label>Art<select id="art"><option value="anpassung">Anpassung Z_a = Z_w</option><option value="leerlauf">Leerlauf</option><option value="kurzschluss">Kurzschluss</option><option value="wert">Wert in Ω</option></select></label>
   <label>Z_a / Ω (bei „Wert")<input type="number" id="Za" value="100" step="10" min="0"></label>
   <div class="zeile"><button class="k leise" onclick="setzeZa()">Z_a = Z_w übernehmen</button><button class="k leise" onclick="setzeRi();setzeZa()">R_i und Z_a = Z_w (beide anpassen)</button></div>
   <div class="hinweis" id="zaAnzeige">—</div>
  </div>
  <div class="karte"><h3>Zeitlupe</h3>
   <label>Dargestellte Zeit je Sekunde: <span id="zlText">2 ns/s</span><input type="range" id="zl" min="0.2" max="20" step="0.2" value="2"></label>
   <button class="k" id="kStart" onclick="start()">Start</button> <button class="k leise" onclick="halt()">Halt</button> <button class="k leise" onclick="schritt(1)">Schritt</button>
   <div class="hinweis" id="hinweis">Einstellen, dann Start. Weg 1: Summe verzögerter Impulse (Gl. 3.24); Weg 2: Zeitschritte der Leitungsgleichungen (Gl. 2.3/2.6).</div>
  </div>
  <div class="karte"><h3>Kennwerte (gerechnet)</h3><div class="werte" id="werte">—</div></div>
 </div>
 <div>
  <div class="karte"><h3>u(x,t) längs der Leitung — Weg 1 durchgezogen, Weg 2 gestrichelt</h3><canvas id="linie" height="300"></canvas></div>
  <div class="karte" style="margin-top:16px"><h3>Oszilloskop: Spannung über der Zeit an drei festen Stellen — Weg 1 Linien, Weg 2 Punkte</h3><canvas id="szene" height="260"></canvas>
  <div class="hinweis">Drei Messpunkte wie drei Tastköpfe: am Eingang x = 0 (blau), in der Leitungsmitte x = l/2 (grün), am Ende x = l (rot). Die Kurven wachsen mit der Zeit; die Zeitachse reicht von 0 bis 8 τ₀. Linie = geschlossene Lösung (Weg 1), Punkte = Zeitschrittverfahren (Weg 2); liegen Punkte auf den Linien, stimmen beide Wege. Ablesen: Laufzeit τ₀ zwischen blauem und rotem Einsatz, Verdopplung am Leerlauf, Vorzeichenwechsel am Kurzschluss, Teiler Z_w/(R_i+Z_w) am Eingang.</div></div>
 </div>
</div>
<div id="ansicht-stern" style="display:none">
 <div>
  <div class="karte"><h3>Verzweigung 1 auf 2 (Abschnitt 6)</h3>
   <div class="hinweis">Leitung, Quelle (Form, E₀, T, R_i) und Abschluss Z_a gelten wie auf dem Reiter Labor; alle drei Leitungen haben die Länge l. In jedem der drei Zweige liegt derselbe Widerstand R zum Sternpunkt (Gl. 6.11).</div>
   <div class="werte ergebnis" id="sternWerte">—</div>
  </div>
  <div class="karte"><h3>Anpasswiderstand R (alle drei Zweige gleich)</h3>
   <label><input type="radio" name="rart" value="opt" checked onchange="sternNeu()"> optimal: R = Z_w/3 (Gl. 6.14b), reflexionsfrei</label>
   <label><input type="radio" name="rart" value="frei" onchange="sternNeu()"> frei einstellbar</label>
   <label>R / Ω (bei „frei")<input type="number" id="Rfrei" value="0" step="1" min="0" onchange="sternNeu()"></label>
   <div class="zeile"><button class="k leise" onclick="$('Rfrei').value=0;document.querySelector('input[name=rart][value=frei]').checked=true;sternNeu()">R = 0 (nackte Verzweigung)</button><button class="k leise" onclick="$('Rfrei').value=P.Zw.toFixed(2);document.querySelector('input[name=rart][value=frei]').checked=true;sternNeu()">R = Z_w</button></div>
   <div class="werte" id="sternFaktoren">—</div>
  </div>
  <div class="karte"><h3>Zeitlupe (wie Labor: <span id="zlText2">2 ns/s</span>)</h3>
   <button class="k" id="kStart2" onclick="sternStart()">Start</button> <button class="k leise" onclick="sternHalt()">Halt</button> <button class="k leise" onclick="sternSchritt(1)">Schritt</button> <button class="k leise" onclick="sternNeu()">Zurück auf t = 0</button>
   <div class="hinweis">Weg 1: Summe verzögerter Impulse mit den Faktoren Z_w/(R_i+Z_w), r_q, r_a und den Sternfaktoren r, t (Gl. 6.13); Weg 2: Leapfrog auf drei Leitungen mit dem Sternknoten (Gl. 7.3–7.5).</div>
  </div>
 </div>
 <div>
  <div class="karte"><h3>u(x,t) auf den drei Leitungen — Weg 1 durchgezogen, Weg 2 gestrichelt</h3><canvas id="sternLinie" height="420"></canvas></div>
  <div class="karte" style="margin-top:16px"><h3>Oszilloskop: Eingang, Sternpunkt u_S, Ende von Leitung 2 — Weg 1 Linien, Weg 2 Punkte</h3><canvas id="sternSzene" height="240"></canvas>
  <div class="hinweis">Bei R = Z_w/3 läuft nichts zum Generator zurück (r = 0) und an jeder abgehenden Leitung kommt die halbe Spannung an (Gl. 6.16). Bei R = 0 ist r = −1/3, t = 2/3 (Gl. 6.10). Linie = Weg 1, Punkte = Weg 2.</div></div>
 </div>
</div>
<div id="ansicht-weg" style="display:none">
 <div class="wegtext">
  <h2>Wie diese Seite rechnet</h2>
  <p class="vorsatz">Die Simulation benutzt <b>keine eigenen Formeln</b>. Jeder Rechenschritt ist eine nummerierte
  Gleichung aus dem Manuskript im Reiter nebenan; die Nummer steht an jedem Schritt. Unten stehen beide Wege
  Schritt für Schritt, mit den Zahlen, die gerade eingestellt sind — so lässt sich jeder Schritt von Hand
  nachrechnen.</p>
  <div class="nachweis" id="wegNachweis">—</div>
  <h3>A · Von der Geometrie zu den Kennwerten der Leitung</h3><div id="wegA"></div>
  <h3>B · Weg 1: die geschlossene Lösung (Laplace und Verschiebungssatz)</h3><div id="wegB"></div>
  <h3>C · Weg 2: das Zeitschrittverfahren (dieselben Leitungsgleichungen, ohne Laplace)</h3><div id="wegC"></div>
  <h3>D · Der Sternpunkt im Reiter „Verzweigung"</h3><div id="wegD"></div>
  <h3>E · Warum beide Wege dasselbe ergeben müssen</h3>
  <p>Weg 1 löst die Leitungsgleichungen im Bildbereich geschlossen und transformiert mit dem Verschiebungssatz
  zurück; Weg 2 löst dieselben Gleichungen (2.3) und (2.6) im Zeitbereich schrittweise, ohne je eine
  Laplace-Transformation zu benutzen. Zwei Verfahren, eine Quelle: Wenn beide Kurven im Labor-Reiter
  übereinanderliegen, ist das kein Zufall, sondern die Probe. Beim Zeitschritt
  <span class="nz">Δt = Δx/v</span> ist das Leapfrog-Verfahren für die verlustlose Leitung sogar exakt — der
  Impuls springt je Schritt genau eine Zelle weiter, und die Abweichung bleibt auf Rundungsresten stehen
  (gemessen: <span id="wegAbw">—</span>).</p>
 </div>
</div>
<div id="ansicht-doku" style="display:none">__DOKU__</div>
<script>
__KERN__
const $=id=>document.getElementById(id);
function zeige(w){ for(const a of ['labor','stern','weg','doku']){ $('ansicht-'+a).style.display=(w===a)?((a==='doku'||a==='weg')?'block':'grid'):'none'; $('r-'+a).classList.toggle('an',w===a);} if(w==='stern'&&!SZ) sternNeu(); if(w==='weg') rechenweg(); }
let P=null, Z=null, lauf=0, tAnzeige=0, verlaeufe=null, N=600, letzteZeit=0;
function lese(){
  const d=+$('d').value, r0=+$('r0').value, epsr=+$('epsr').value, l=+$('l').value; const b=LABOR.belaege(d,r0,epsr);
  const art=$('art').value; const Za = art==='anpassung'?b.Zw : art==='leerlauf'?Infinity : art==='kurzschluss'?0 : +$('Za').value;
  const T=+$('T').value*1e-9; const e=LABOR.quelle($('form').value, +$('E0').value, T);
  return {...b, l, Ri:+$('Ri').value, Za, e, T, art};
}
function belaegeJetzt(){ return LABOR.belaege(+$('d').value, +$('r0').value, +$('epsr').value); }
function setzeRi(){ $('Ri').value=belaegeJetzt().Zw.toFixed(2); $('Ri').dispatchEvent(new Event('change')); }
function setzeZa(){ $('art').value='wert'; $('Za').value=belaegeJetzt().Zw.toFixed(2); $('Za').dispatchEvent(new Event('change')); }
function neu(){
  P=lese(); Z=LABOR.zeitschritt(P,N); tAnzeige=0; verlaeufe={t:[],u0:[],um:[],ul:[],w0:[],wm:[],wl:[]};
  $('zwAnzeige').textContent=`Z_w = ${P.Zw.toFixed(2)} Ω   (Gl. 5.6)\nv = ${(P.v/1e8).toFixed(4)}·10⁸ m/s   τ₀ = ${(P.l/P.v*1e9).toFixed(3)} ns`;
  $('impulslaenge').textContent=`Impulslänge v·T = ${(P.v*P.T).toFixed(3)} m (Gl. 7.2) bei l = ${P.l} m` + (P.v*P.T > P.l ? ' — länger als die Leitung' : '');
  $('zaAnzeige').textContent=`wirksam: Z_a = ${P.Za===Infinity?'∞ (Leerlauf)':P.Za.toFixed(2)+' Ω'}, r_a = ${((P.Za===Infinity)?1:(P.Za-P.Zw)/(P.Za+P.Zw)).toFixed(4)};  R_i = ${P.Ri.toFixed(2)} Ω, r_q = ${((P.Ri-P.Zw)/(P.Ri+P.Zw)).toFixed(4)}`;
  const ra=(P.Za===Infinity)?1:(P.Za-P.Zw)/(P.Za+P.Zw), rq=(P.Ri-P.Zw)/(P.Ri+P.Zw);
  $('werte').textContent=`C' = ${(P.C1*1e12).toFixed(3)} pF/m   L' = ${(P.L1*1e6).toFixed(4)} µH/m\nZ_w = ${P.Zw.toFixed(2)} Ω   v = ${(P.v/1e8).toFixed(4)}·10⁸ m/s\nτ₀ = l/v = ${(P.l/P.v*1e9).toFixed(3)} ns\nTeiler Z_w/(R_i+Z_w) = ${(P.Zw/(P.Ri+P.Zw)).toFixed(4)}\nr_a = ${ra.toFixed(4)}   r_q = ${rq.toFixed(4)}\nZeitschritt Weg 2: dt = ${(Z.dt*1e12).toFixed(2)} ps, ${N} Zellen`;
  zeichne();
}
function stand(){ return {t_ns:tAnzeige*1e9, Zw:P?P.Zw:null, v:P?P.v:null, ra:P?((P.Za===Infinity)?1:(P.Za-P.Zw)/(P.Za+P.Zw)):null, laeuft:!!lauf}; }
function schritt(k){ if(!Z) neu(); for(let j=0;j<k;j++){ const t=Z.t; Z.schritt(); tAnzeige=t;
   if(verlaeufe.t.length===0 || t-verlaeufe.t[verlaeufe.t.length-1] >= P.l/P.v/150){ verlaeufe.t.push(t); verlaeufe.u0.push(Z.u[0]); verlaeufe.um.push(Z.u[N/2]); verlaeufe.ul.push(Z.u[N]);
     verlaeufe.w0.push(LABOR.geschlossen(P,0,t)); verlaeufe.wm.push(LABOR.geschlossen(P,P.l/2,t)); verlaeufe.wl.push(LABOR.geschlossen(P,P.l,t)); } }
  zeichne(); }
function start(){ if(!Z) neu(); if(lauf) return; letzteZeit=performance.now(); lauf=requestAnimationFrame(bild); $('kStart').textContent='Läuft …'; }
function halt(){ if(lauf){cancelAnimationFrame(lauf); lauf=0;} $('kStart').textContent='Start'; }
function bild(now){ const dtReal=(now-letzteZeit)/1000; letzteZeit=now; const zl=+$('zl').value*1e-9;    // dargestellte Sekunden je echter Sekunde
  const k=Math.max(1, Math.round(dtReal*zl/Z.dt)); schritt(Math.min(k, 4000)); if(tAnzeige < 8*P.l/P.v) lauf=requestAnimationFrame(bild); else halt(); }
$('zl').addEventListener('input',()=>{$('zlText').textContent=(+$('zl').value).toFixed(1)+' ns/s';});
for(const id of ['d','r0','epsr','l','form','E0','T','Ri','art','Za']) $(id).addEventListener('change',()=>{halt(); neu(); if(SZ) sternNeu(); if($('ansicht-weg').style.display!=='none') rechenweg();});
$('zl').addEventListener('input',()=>{$('zlText2').textContent=(+$('zl').value).toFixed(1)+' ns/s';});
function rahmen(c,w,h){ c.fillStyle='#14171c'; c.fillRect(0,0,w,h); }
/* Feine Spannungsskala (28.10.2026 auf seine Bitte): Schrittweite nach der 1-2-5-Regel, so dass rund
   acht beschriftete Linien im Bild stehen; jede fünfte Linie heller. */
function schrittweite(spanne, ziel){ const roh=spanne/ziel, e=Math.pow(10,Math.floor(Math.log10(roh))), m=roh/e;
  return (m<=1?1:m<=2?2:m<=2.5?2.5:m<=5?5:10)*e; }
function spannungsskala(c,x0,x1,ty,umax,einheit){
  const d=schrittweite(umax,6), n=Math.floor(umax/d+1e-9);
  c.font='11px system-ui'; c.textAlign='right';
  for(let k=-n;k<=n;k++){ const u=k*d, y=ty(u);
    c.strokeStyle = (k===0)?'#5b6577':'#262c38'; c.lineWidth=(k===0)?1.2:1;
    c.beginPath(); c.moveTo(x0,y); c.lineTo(x1,y); c.stroke();
    c.fillStyle = (k===0)?'#c7ccd4':'#7f8899';
    c.fillText(u.toFixed(Math.max(0,-Math.floor(Math.log10(d))))+(k===n?' '+einheit:''), x0-6, y+4); }
  return d;
}
/* Jeder zusammenhängende Bereich mit |u| über der Schwelle ist ein Impuls; sein Scheitelwert wird angeschrieben. */
function impulse(ys,schwelle){ const aus=[]; let k=0;
  while(k<ys.length){ if(Math.abs(ys[k])>schwelle){ let j=k,best=k;
      while(j<ys.length && Math.abs(ys[j])>schwelle){ if(Math.abs(ys[j])>Math.abs(ys[best])) best=j; j++; }
      aus.push({von:k, bis:j-1, mitte:(k+j-1)/2, wert:ys[best]}); k=j; } else k++; }
  return aus; }
function beschrifteImpulse(c,ys,tx,ty,farbe,schwelle,nachkomma,yFrei){
  c.font='bold 12px system-ui'; c.textAlign='center'; c.fillStyle=farbe;
  const frei = yFrei===undefined?30:yFrei;                 // darüber liegt die Überschrift des Bildes
  for(const q of impulse(ys,schwelle)){ const x=tx(q.mitte), y=ty(q.wert);
    const yT = (q.wert>=0 && y-7>frei) ? y-7 : y+16;       // in die Lücke schreiben, nicht über den Rand
    c.fillText(q.wert.toFixed(nachkomma===undefined?3:nachkomma)+' V', x, yT);
    c.strokeStyle=farbe; c.lineWidth=1; c.beginPath(); c.moveTo(x-5,y); c.lineTo(x+5,y); c.stroke(); }
  return impulse(ys,schwelle).length; }
function zeichne(){
  if(!P) return;
  const el=$('linie'), dpr=window.devicePixelRatio||1, w=el.clientWidth, h=+el.getAttribute('height'); el.width=w*dpr; el.height=h*dpr; el.style.height=h+'px';
  const c=el.getContext('2d'); c.setTransform(dpr,0,0,dpr,0,0); rahmen(c,w,h);
  const E0=Math.abs(+$('E0').value)||1, umax=2.2*E0, x0=62, x1=w-16, y0=h-28, yM=(h-28)/2+8, sk=(y0-16)/2/umax;
  const tyL=u=>yM-u*sk;
  const dL=spannungsskala(c,x0,x1,tyL,umax,'V');
  c.fillStyle='#c7ccd4'; c.font='12px system-ui'; c.textAlign='left'; c.fillText('x = 0 (Quelle, R_i = '+P.Ri+' Ω)',x0,h-8); c.textAlign='right'; c.fillText('x = l ('+($('art').selectedOptions[0].text)+')',x1,h-8);
  c.fillText('t = '+(tAnzeige*1e9).toFixed(2)+' ns   Raster '+dL.toFixed(2)+' V',x1,18);
  // Weg 1 (geschlossen) an 300 Stellen
  const w1=[]; for(let k=0;k<=300;k++) w1.push(LABOR.geschlossen(P,P.l*k/300,tAnzeige));
  c.strokeStyle='#4ea1ff'; c.lineWidth=2; c.beginPath();
  for(let k=0;k<=300;k++){ const px=x0+(x1-x0)*k/300, py=tyL(w1[k]); k?c.lineTo(px,py):c.moveTo(px,py);} c.stroke();
  beschrifteImpulse(c,w1,k=>x0+(x1-x0)*k/300,tyL,'#9ad0ff',0.01*E0);
  // Weg 2 (Zeitschritt)
  c.strokeStyle='#ffb347'; c.setLineDash([6,5]); c.beginPath();
  for(let k=0;k<=N;k++){ const px=x0+(x1-x0)*k/N, py=yM-Z.u[k]*sk; k?c.lineTo(px,py):c.moveTo(px,py);} c.stroke(); c.setLineDash([]);
  // Zeitverläufe
  const es=$('szene'), w2=es.clientWidth, h2=+es.getAttribute('height'); es.width=w2*dpr; es.height=h2*dpr; es.style.height=h2+'px';
  const c2=es.getContext('2d'); c2.setTransform(dpr,0,0,dpr,0,0); rahmen(c2,w2,h2);
  const tEnd=8*P.l/P.v, tx=t=>62+(w2-78)*t/tEnd, ty=u=>(h2-28)/2+8-u*((h2-28)/2-12)/umax;
  const dO=spannungsskala(c2,62,w2-16,ty,umax,'V');
  c2.fillStyle='#c7ccd4'; c2.font='12px system-ui'; c2.textAlign='right'; c2.fillText('t von 0 bis 8 τ₀ = '+(tEnd*1e9).toFixed(1)+' ns   Raster '+dO.toFixed(2)+' V',w2-16,18);
  c2.strokeStyle='#2c3340'; for(let k=1;k<8;k++){ c2.beginPath(); c2.moveTo(tx(k*P.l/P.v),16); c2.lineTo(tx(k*P.l/P.v),h2-26); c2.stroke(); } c2.textAlign='center'; c2.fillStyle='#7f8899'; for(let k=1;k<8;k+=2) c2.fillText(k+' τ₀',tx(k*P.l/P.v),h2-8);
  c2.strokeStyle='#9aa3b2'; c2.setLineDash([3,3]); c2.beginPath(); c2.moveTo(tx(Math.min(tAnzeige,tEnd)),16); c2.lineTo(tx(Math.min(tAnzeige,tEnd)),h2-26); c2.stroke(); c2.setLineDash([]);
  const farben={u0:'#4ea1ff',um:'#7bd88f',ul:'#ff6b6b'}; const namen={u0:'u(0,t)',um:'u(l/2,t)',ul:'u(l,t)'};
  let lx=70; c2.textAlign='left'; for(const k of ['u0','um','ul']){ c2.fillStyle=farben[k]; c2.fillText(namen[k]+(k==='u0'?' Eingang':k==='um'?' Mitte':' Ende'),lx,18); lx+=Math.min(170,(w2-220)/3);
    const wk=k.replace('u','w'); c2.strokeStyle=farben[k]; c2.lineWidth=1.6; c2.beginPath();
    verlaeufe.t.forEach((t,i)=>{ const px=tx(t), py=ty(verlaeufe[wk][i]); i?c2.lineTo(px,py):c2.moveTo(px,py);}); c2.stroke();
    c2.fillStyle=farben[k]; verlaeufe.t.forEach((t,i)=>{ if(i%3===0) c2.fillRect(tx(t)-1.5, ty(verlaeufe[k][i])-1.5,3,3); });
    beschrifteImpulse(c2,verlaeufe[wk],i=>tx(verlaeufe.t[Math.round(i)]||0),ty,farben[k],0.02*E0,3,34); }
}
/* ---- Reiter Verzweigung: Sternpunkt 1 auf 2, alle Einstellungen von der Hauptseite, R fuer alle drei Zweige gleich ---- */
let SZ=null, SR=0, SST=null, sLauf=0, sT=0, sVerl=null, sLetzte=0; const NS=400;
function sternR(){ const art=document.querySelector('input[name=rart]:checked').value; return art==='opt' ? LABOR.stern(P,0).Ropt : Math.max(0,+$('Rfrei').value); }
function sternNeu(){ sternHalt(); if(!P) neu(); SR=sternR(); const s=LABOR.stern(P,SR); SZ=LABOR.verzweigungZeitschritt(P,SR,NS); SST=LABOR.verzweigungStrahlen(P,SR,8*P.l/P.v); sT=0; sVerl={t:[],e:[],s:[],z:[],we:[],ws:[],wz:[]};
  const ra=(P.Za===Infinity)?1:(P.Za-P.Zw)/(P.Za+P.Zw), rq=(P.Ri-P.Zw)/(P.Ri+P.Zw);
  $('sternWerte').textContent=`Z_w = ${P.Zw.toFixed(2)} Ω   τ₀ = ${(P.l/P.v*1e9).toFixed(3)} ns je Leitung\nR_i = ${P.Ri.toFixed(2)} Ω (r_q = ${rq.toFixed(4)})   Z_a = ${P.Za===Infinity?'∞':P.Za.toFixed(2)+' Ω'} (r_a = ${ra.toFixed(4)})`;
  $('sternFaktoren').textContent=`R = ${SR.toFixed(2)} Ω   (optimal R = Z_w/3 = ${s.Ropt.toFixed(2)} Ω)\nZ_ein = R + (R+Z_w)/2 = ${s.Zein.toFixed(2)} Ω   (Gl. 6.12)\nr = (Z_ein−Z_w)/(Z_ein+Z_w) = ${s.r.toFixed(4)}   (Gl. 6.13)\nt = (1−r)/2 = ${s.t.toFixed(4)} je abgehender Leitung\nStrahlen in Weg 1: ${SST.length}   Zeitschritt Weg 2: dt = ${(SZ.dt*1e12).toFixed(2)} ps, ${NS} Zellen je Leitung`;
  sternZeichne(); }
function sternSchritt(k){ if(!SZ) sternNeu(); for(let j=0;j<k;j++){ const t=SZ.t; SZ.schritt(); sT=t;
   if(sVerl.t.length===0 || t-sVerl.t[sVerl.t.length-1] >= P.l/P.v/150){ sVerl.t.push(t); sVerl.e.push(SZ.u[0][0]); sVerl.s.push(SZ.uS); sVerl.z.push(SZ.u[1][NS]);
     sVerl.we.push(LABOR.verzweigungGeschlossen(P,SST,0,0,t)); sVerl.ws.push((LABOR.verzweigungGeschlossen(P,SST,0,P.l,t)+LABOR.verzweigungGeschlossen(P,SST,1,0,t)+LABOR.verzweigungGeschlossen(P,SST,2,0,t))/3); /* u_S = Mittel der drei Endspannungen (Knotenregel bei gleichem R) */ sVerl.wz.push(LABOR.verzweigungGeschlossen(P,SST,1,P.l,t)); } }
  sternZeichne(); }
function sternStart(){ if(!SZ) sternNeu(); if(sLauf) return; sLetzte=performance.now(); sLauf=requestAnimationFrame(sternBild); $('kStart2').textContent='Läuft …'; }
function sternHalt(){ if(sLauf){cancelAnimationFrame(sLauf); sLauf=0;} $('kStart2').textContent='Start'; }
function sternBild(now){ const dtReal=(now-sLetzte)/1000; sLetzte=now; const zl=+$('zl').value*1e-9; const k=Math.max(1,Math.round(dtReal*zl/SZ.dt)); sternSchritt(Math.min(k,4000)); if(sT < 8*P.l/P.v) sLauf=requestAnimationFrame(sternBild); else sternHalt(); }
function sternZeichne(){
  if(!SZ) return; const E0=Math.abs(+$('E0').value)||1, umax=2.2*E0;
  const el=$('sternLinie'), dpr=window.devicePixelRatio||1, w=el.clientWidth, h=+el.getAttribute('height'); el.width=w*dpr; el.height=h*dpr; el.style.height=h+'px';
  const c=el.getContext('2d'); c.setTransform(dpr,0,0,dpr,0,0); rahmen(c,w,h);
  const hs=h/3, x0=62, x1=w-16, sk=(hs-30)/2/umax;
  const namen=['Leitung 1: Quelle (x = 0) → Sternpunkt (x = l)','Leitung 2: Sternpunkt (x = 0) → Abschluss (x = l)','Leitung 3: Sternpunkt (x = 0) → Abschluss (x = l)'];
  let dS=0;
  for(let k=0;k<3;k++){ const yM=hs*k+hs/2+6, tyS=u=>yM-u*sk;
    dS=spannungsskala(c,x0,x1,tyS,umax,'V');
    c.fillStyle='#c7ccd4'; c.font='12px system-ui'; c.textAlign='left'; c.fillText(namen[k],x0,hs*k+14);
    const w1s=[]; for(let j=0;j<=200;j++) w1s.push(LABOR.verzweigungGeschlossen(P,SST,k,P.l*j/200,sT));
    c.strokeStyle='#4ea1ff'; c.lineWidth=2; c.beginPath();
    for(let j=0;j<=200;j++){ const px=x0+(x1-x0)*j/200, py=tyS(w1s[j]); j?c.lineTo(px,py):c.moveTo(px,py);} c.stroke();
    c.strokeStyle='#ffb347'; c.setLineDash([6,5]); c.beginPath();
    for(let j=0;j<=NS;j++){ const px=x0+(x1-x0)*j/NS, py=tyS(SZ.u[k][j]); j?c.lineTo(px,py):c.moveTo(px,py);} c.stroke(); c.setLineDash([]);
    beschrifteImpulse(c,w1s,j=>x0+(x1-x0)*j/200,tyS,'#9ad0ff',0.01*E0); }
  c.fillStyle='#c7ccd4'; c.textAlign='right'; c.fillText('t = '+(sT*1e9).toFixed(2)+' ns   R = '+SR.toFixed(2)+' Ω   Raster '+dS.toFixed(2)+' V',x1,14);
  // Oszilloskop
  const es=$('sternSzene'), w2=es.clientWidth, h2=+es.getAttribute('height'); es.width=w2*dpr; es.height=h2*dpr; es.style.height=h2+'px';
  const c2=es.getContext('2d'); c2.setTransform(dpr,0,0,dpr,0,0); rahmen(c2,w2,h2);
  const tEnd=8*P.l/P.v, tx=t=>62+(w2-78)*t/tEnd, ty=u=>(h2-28)/2+8-u*((h2-28)/2-12)/umax;
  const dO2=spannungsskala(c2,62,w2-16,ty,umax,'V');
  c2.fillStyle='#c7ccd4'; c2.font='12px system-ui'; c2.textAlign='right'; c2.fillText('t von 0 bis 8 τ₀ = '+(tEnd*1e9).toFixed(1)+' ns   Raster '+dO2.toFixed(2)+' V',w2-16,18);
  c2.strokeStyle='#2c3340'; for(let k=1;k<8;k++){ c2.beginPath(); c2.moveTo(tx(k*P.l/P.v),16); c2.lineTo(tx(k*P.l/P.v),h2-26); c2.stroke(); } c2.textAlign='center'; c2.fillStyle='#7f8899'; for(let k=1;k<8;k+=2) c2.fillText(k+' τ₀',tx(k*P.l/P.v),h2-8);
  c2.strokeStyle='#9aa3b2'; c2.setLineDash([3,3]); c2.beginPath(); c2.moveTo(tx(Math.min(sT,tEnd)),16); c2.lineTo(tx(Math.min(sT,tEnd)),h2-26); c2.stroke(); c2.setLineDash([]);
  const farben={e:'#4ea1ff',s:'#7bd88f',z:'#ff6b6b'}; const namen2={e:'u(0,t) Eingang Leitung 1',s:'u_S Sternpunkt',z:'u(l,t) Ende Leitung 2'};
  let lx=70; c2.textAlign='left'; for(const k of ['e','s','z']){ c2.fillStyle=farben[k]; c2.fillText(namen2[k],lx,18); lx+=Math.min(200,(w2-180)/3);
    const wk='w'+k; c2.strokeStyle=farben[k]; c2.lineWidth=1.6; c2.beginPath();
    sVerl.t.forEach((t,i)=>{ const px=tx(t), py=ty(sVerl[wk][i]); i?c2.lineTo(px,py):c2.moveTo(px,py);}); c2.stroke();
    c2.fillStyle=farben[k]; sVerl.t.forEach((t,i)=>{ if(i%3===0) c2.fillRect(tx(t)-1.5, ty(sVerl[k][i])-1.5,3,3); });
    beschrifteImpulse(c2,sVerl[wk],i=>tx(sVerl.t[Math.round(i)]||0),ty,farben[k],0.02*E0,3,34); }
}
/* ---- Reiter „Rechenweg": jeder Schritt der Simulation mit seiner Gleichung aus dem Manuskript und den
   Zahlen, die gerade eingestellt sind. Nichts hier rechnet selbst — die Werte kommen aus demselben Kern. ---- */
function zz(v, n, e){ if(v===Infinity) return '∞'; if(Math.abs(v)<1e-12) v=0;   // Rundungsreste sind null, nicht -7,9e-17
  return (Math.abs(v)>=1e4||(Math.abs(v)<1e-3&&v!==0)) ? v.toExponential(n===undefined?3:n)+(e||'') : v.toFixed(n===undefined?3:n)+(e||''); }
function wegschritt(nr, titel, gl, formel, zahlen, warum){   // NICHT schritt() nennen: so hiess schon der Zeitschritt des Labors
  return `<div class="schritt"><div class="nr">${nr}</div><div><span class="titel">${titel}</span>`+
         (gl?`<span class="gl">Gl. ${gl}</span>`:'')+
         `<div class="formel">${formel}</div><div class="zahlen">${zahlen}</div>`+
         (warum?`<div class="warum">${warum}</div>`:'')+`</div></div>`;
}
function rechenweg(){
  if(!P) neu();
  const d=+$('d').value, r0=+$('r0').value, er=+$('epsr').value, l=P.l, E0=+$('E0').value, T=P.T;
  const q=Math.log(d/r0), ra=(P.Za===Infinity)?1:(P.Za-P.Zw)/(P.Za+P.Zw), rq=(P.Ri-P.Zw)/(P.Ri+P.Zw);
  const teiler=P.Zw/(P.Ri+P.Zw), tau0=l/P.v, form=$('form').value;
  $('wegA').innerHTML =
    wegschritt(1,'Kapazitätsbelag aus der Geometrie','5.3',
      "C' = π·ε_r·ε₀ / ln(d/r₀)",
      `C' = π · ${er} · 8,854·10⁻¹² / ln(${d}/${r0}) = π · ${er} · 8,854·10⁻¹² / ${zz(q,4)} = ${zz(P.C1*1e12,4,' pF/m')}`,
      'Die Näherung gilt für d ≫ r₀; exakt stünde arcosh(d/2r₀) statt ln(d/r₀) — 0,08 % Unterschied bei diesen Maßen.') +
    wegschritt(2,'Induktivitätsbelag aus derselben Geometrie','5.5',
      "L' = (μ₀/π)·ln(d/r₀)",
      `L' = (4π·10⁻⁷/π) · ${zz(q,4)} = ${zz(P.L1*1e6,4,' µH/m')}`,
      'Dieselbe Geometriefunktion wie bei C′, nur im Zähler statt im Nenner — deshalb kürzt sie sich in v heraus.') +
    wegschritt(3,'Wellenwiderstand und Ausbreitungsgeschwindigkeit','5.6, 5.7',
      "Z_w = √(L'/C')     v = 1/√(L'C')",
      `Z_w = √(${zz(P.L1*1e6,4)}·10⁻⁶ / ${zz(P.C1*1e12,4)}·10⁻¹²) = ${zz(P.Zw,2,' Ω')}\n`+
      `v = 1/√(L'C') = ${zz(P.v/1e8,4)}·10⁸ m/s     τ₀ = l/v = ${zz(tau0*1e9,3,' ns')} bei l = ${l} m`,
      'Z_w ist reell und von s unabhängig, weil R′ = G′ = 0 gesetzt ist (3.11) — die Leitung verzerrt nicht.');
  // ---- Weg 1
  let glieder='';
  const nmax=4; let g=1;
  for(let n=0;n<=nmax;n++){
    const t1=(2*n*l+P.l/2)/P.v, t2=(2*(n+1)*l-P.l/2)/P.v;
    glieder += `n = ${n}:  ${zz(teiler*g,4)} · e(t − ${zz(t1*1e9,3)} ns)   +   ${zz(teiler*g*ra,4)} · e(t − ${zz(t2*1e9,3)} ns)\n`;
    g *= rq*ra; if(Math.abs(g)<1e-6) break;
  }
  $('wegB').innerHTML =
    wegschritt(4,'Reflexionsfaktor am Abschluss','3.21',
      'r_a = (Z_a − Z_w)/(Z_a + Z_w)',
      `Z_a = ${P.Za===Infinity?'∞ (Leerlauf)':zz(P.Za,2,' Ω')}   →   r_a = ${zz(ra,4)}`,
      'r_a = +1 bei Leerlauf, −1 bei Kurzschluss, 0 bei Anpassung.') +
    wegschritt(5,'Reflexionsfaktor am Generator und Eingangsteiler','3.23',
      'r_q = (R_i − Z_w)/(R_i + Z_w)      Teiler = Z_w/(R_i + Z_w)',
      `R_i = ${zz(P.Ri,2,' Ω')}   →   r_q = ${zz(rq,4)}   Teiler = ${zz(teiler,4)}`,
      'Die Leitung wirkt am Eingang wie der Widerstand Z_w — deshalb der Spannungsteiler.') +
    wegschritt(6,'Die Quelle liefert den Impuls e(t)', form==='gauss'?'7.1':'',
      form==='gauss' ? 'e(t) = E₀·exp(−(t−2T)²/2σ²)·σ(t),  σ = T/(2√(2 ln2))'
                     : 'e(t) = E₀ für 0 ≤ t < T, sonst 0',
      form==='gauss' ? `E₀ = ${E0} V, T = ${zz(T*1e9,2)} ns (Halbwertsbreite), σ = ${zz(T/2.3548*1e9,3)} ns, Scheitel bei ${zz(2*T*1e9,2)} ns`
                     : `E₀ = ${E0} V, T = ${zz(T*1e9,2)} ns   →   Impulslänge auf der Leitung v·T = ${zz(P.v*T,3,' m')}`,
      'Der Faktor σ(t) ist Voraussetzung des Verschiebungssatzes: vor t = 0 ist die Leitung in Ruhe.') +
    wegschritt(7,'Die Reihe der verzögerten Impulse','3.24',
      'u(x,t) = Z_w/(R_i+Z_w) · Σₙ (r_q·r_a)ⁿ [ e(t − (2nl+x)/v) + r_a·e(t − (2(n+1)l−x)/v) ]',
      `für x = l/2 = ${zz(l/2,3)} m lauten die ersten Glieder:\n${glieder}`,
      'Jedes Glied ist derselbe Impuls, nur später und kleiner — mehr steckt nicht dahinter.') +
    wegschritt(8,'Rücktransformation: der Verschiebungssatz','3.18, 3.19',
      'ℒ{f(t−T)·σ(t−T)} = e^(−sT)·F(s)   ⟹   u(x,t) = e(t − √(L′C′)·x)',
      `Laufzeit bis x: τ(x) = √(L'C')·x;  bis zum Ende τ₀ = ${zz(tau0*1e9,3,' ns')}`,
      'Der Faktor e^(−sτ) im Bildbereich IST die Verzögerung im Zeitbereich — keine Tabelle nötig.');
  // ---- Weg 2
  const dt=Z.dt, dx=Z.dx;
  $('wegC').innerHTML =
    wegschritt(9,'Das Gitter und der Zeitschritt','',
      'Δx = l/N,   Δt = Δx/v   (Courant-Zahl 1)',
      `N = ${N} Zellen,  Δx = ${zz(dx*1000,4,' mm')},  Δt = ${zz(dt*1e12,2,' ps')},  Schritte bis 8τ₀: ${Math.round(8*tau0/dt)}`,
      'Bei Δt = Δx/v springt der Impuls je Schritt genau eine Zelle weiter — dann ist das Verfahren exakt.') +
    wegschritt(10,'Strom-Halbschritt aus der ersten Leitungsgleichung','2.3',
      '∂u/∂x = −L′·∂i/∂t   ⟹   i_k ← i_k − (Δt/L′)·(u_{k+1} − u_k)/Δx',
      `Δt/L' = ${zz(dt/P.L1,3)} ;  der Strom auf halben Zellen wird aus dem Spannungsgefälle fortgeschrieben`,
      'Spannung an den Knoten, Strom dazwischen — versetzt, daher „Leapfrog".') +
    wegschritt(11,'Spannungs-Halbschritt aus der zweiten Leitungsgleichung','2.6',
      '∂i/∂x = −C′·∂u/∂t   ⟹   u_k ← u_k − (Δt/C′)·(i_k − i_{k−1})/Δx',
      `Δt/C' = ${zz(dt/P.C1,3)} ;  nur die inneren Knoten, die Ränder folgen gesondert`,
      'Genau die beiden Gleichungen, aus denen Weg 1 die Telegraphengleichung gewonnen hat.') +
    wegschritt(12,'Der Randknoten an der Quelle (halbe Zelle, Trapezregel)','2.3, 3.23',
      P.Ri===0 ? 'R_i = 0:  u₀ ← e(t)   (die Quelle prägt die Spannung ein)'
               : "u₀ ← [ (R_i−Z_w)·u₀ + Z_w·(e(t)+e(t−Δt)) − 2·R_i·Z_w·i₀ ] / (R_i+Z_w)",
      P.Ri===0 ? `R_i = 0 Ω — am Generator wird mit r_q = −1 reflektiert`
               : `R_i = ${zz(P.Ri,2,' Ω')},  Z_w = ${zz(P.Zw,2,' Ω')}  →  dieselbe Reflexion r_q = ${zz(rq,4)} wie in Weg 1`,
      'Gemessen: ohne Trapezregel (explizit, oder Quellspannung nicht gemittelt) weicht die Lösung um 0,25 bis 1 V ab.') +
    wegschritt(13,'Der Randknoten am Abschluss','3.21',
      P.Za===Infinity ? 'Leerlauf:  u_N ← u_N + 2·Z_w·i_{N−1}' :
      (P.Za===0 ? 'Kurzschluss:  u_N ← 0' : 'u_N ← [ (Z_a−Z_w)·u_N + 2·Z_a·Z_w·i_{N−1} ] / (Z_a+Z_w)'),
      `Z_a = ${P.Za===Infinity?'∞':zz(P.Za,2,' Ω')}  →  r_a = ${zz(ra,4)} — derselbe Faktor, den Weg 1 in die Reihe setzt`,
      'Die Randbedingung ist dieselbe Physik, einmal im Bildbereich (Weg 1), einmal pro Zeitschritt (Weg 2).');
  // ---- Verzweigung
  const Ropt=LABOR.stern(P,0).Ropt, sR=(typeof SR==='number'&&SZ)?SR:Ropt, s=LABOR.stern(P,sR);
  $('wegD').innerHTML =
    wegschritt(14,'Was Leitung 1 am Sternpunkt sieht','6.12',
      'Z_ein = R + (R + Z)/(n − 1)',
      `R = ${zz(sR,2,' Ω')},  n = 3 Zweige  →  Z_ein = ${zz(s.Zein,2,' Ω')}   (reflexionsfrei wäre R = (n−2)/n·Z = ${zz(Ropt,2,' Ω')})`,
      'R in Reihe mit der Parallelschaltung der beiden anderen Zweige zu je R + Z.') +
    wegschritt(15,'Reflexion und Durchlass am Stern','6.13, 6.16',
      'r = (Z_ein − Z)/(Z_ein + Z)      t = (1 − r)/(n − 1)',
      `r = ${zz(s.r,4)},  t = ${zz(s.t,4)} je abgehender Leitung`,
      'Bei R = Z_w/3 ist r = 0 und t = ½: die halbe Spannung läuft weiter, die halbe Leistung wird in den drei Widerständen zu Wärme.') +
    wegschritt(16,'Der Sternknoten im Zeitschritt','7.3a, 7.3b, 7.4, 7.5',
      "u_S′ = (Z_w/n)·Σ b_k ,   u_k′ = (b_k + u_S′/R)/(1/Z_w + 1/R)",
      sR===0 ? 'R = 0: die drei Endknoten fallen zu einem zusammen, u′ = u + (2Z_w/n)·Σ i_k  (7.5)'
             : `mit b_k = 2·i_k + u_k·(1/Z_w − 1/R) + u_S/R;  R = ${zz(sR,2,' Ω')}`,
      'Kein Gleichungssystem muss gelöst werden: die Knotenregel in S erlaubt die geschlossene Auflösung.');
  $('wegNachweis').innerHTML =
    '<b>Nachgerechnet.</b> Jede hier genannte Gleichung ist mit einem CAS-Skript (sympy) geprüft: '+
    '<b>115 Posten, alle RICHTIG</b>. <code>pruefung/abdeckung.py</code> hält die Liste gegen alle nummerierten '+
    'Gleichungen des Manuskripts und gegen die Rechenregeln dieser Seite: <b>92 von 92 Gleichungen, 18 von 18 '+
    'Rechenregeln</b>. Dazu die Gegenprobe im Zeitbereich: zehn Fälle, Weg 2 gegen Weg 1 höchstens 2·10⁻¹² V.';
  const r=PRUEFSTAND_abweichung(); $('wegAbw').textContent = r;
}
function PRUEFSTAND_abweichung(){
  if(!Z||!P) return '—';
  if(tAnzeige < Z.dt) return 'im Reiter Labor auf Start drücken — vor dem ersten Zeitschritt gibt es nichts zu vergleichen';
  let dmax=0; for(let k=0;k<=N;k++) dmax=Math.max(dmax,Math.abs(Z.u[k]-LABOR.geschlossen(P,P.l*k/N,tAnzeige)));
  return dmax.toExponential(2)+' V über die ganze Leitung, bei t = '+(tAnzeige*1e9).toFixed(2)+' ns';
}
/* Diagnoseschnittstelle (Hausregel: jede Seite trägt window.PRUEFSTAND) */
window.PRUEFSTAND={ fassung:'__FASSUNG__', kern:LABOR,
  stellen:(o)=>{ for(const k in o){ if($(k)) $(k).value=o[k]; } halt(); neu(); return stand(); },
  rechne:(schritte)=>{ halt(); schritt(schritte||1); const w1=[],w2=[]; for(let k=0;k<=N;k++){ w1.push(LABOR.geschlossen(P,P.l*k/N,tAnzeige)); w2.push(Z.u[k]); }
     let d=0; for(let k=0;k<=N;k++) d=Math.max(d,Math.abs(w1[k]-w2[k])); return {t_ns:tAnzeige*1e9, max_abw_V:d, u_ende_w1:w1[N], u_ende_w2:w2[N], u_mitte_w1:w1[N/2]}; },
  stand, parameter:()=>P, rechenweg:()=>{ zeige('weg'); return {schritte:document.querySelectorAll('#ansicht-weg .schritt').length, gleichungen:[...document.querySelectorAll('#ansicht-weg .gl')].map(e=>e.textContent.replace('Gl. ','')).join(' ').split(/[ ,]+/).filter(Boolean)}; },
  stern:{ stellen:(o)=>{ zeige('stern'); if(o.rart) document.querySelector('input[name=rart][value='+o.rart+']').checked=true; if(o.R!==undefined) $('Rfrei').value=o.R; sternNeu(); return {R:SR, ...LABOR.stern(P,SR)}; },
          rechne:(schritte)=>{ sternHalt(); sternSchritt(schritte||1); let d=0; const u1=[],u2=[]; for(let j=0;j<=NS;j++){ for(const k of [0,1,2]){ d=Math.max(d,Math.abs(SZ.u[k][j]-LABOR.verzweigungGeschlossen(P,SST,k,P.l*j/NS,sT))); } }
             return {t_ns:sT*1e9, max_abw_V:d, uS:SZ.uS, u2_ende_w2:SZ.u[1][NS], u2_ende_w1:LABOR.verzweigungGeschlossen(P,SST,1,P.l,sT), u1_ende:SZ.u[0][NS], strahlen:SST.length}; },
          stand:()=>({t_ns:sT*1e9, R:SR, laeuft:!!sLauf}) } };
neu();
</script>
"""
seite = (seite.replace("__REVISION__", REVISION).replace("__FASSUNG__", FASSUNG).replace("__STAND__", STAND)
              .replace("__KERN__", kern).replace("__DOKU__", doku))
ziel = H / f"Telegraphen_Labor_{FASSUNG}.html"; ziel.write_text(seite, encoding="utf-8")
print(f"{ziel.name}: {len(seite)/1e6:.2f} MB")
