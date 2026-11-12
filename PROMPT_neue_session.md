# Prompt für eine neue Claude-Session auf dem Mac

> Einfügen in **Claude Code** (Terminal oder Claude Desktop → Code) auf dem Mac, in einem leeren Ordner, z. B. `~/itx-case`.
> Computer Use (Mac-Steuerung) darf aktiv sein, wird aber nur für die Sichtprüfung gebraucht.

---

Du konstruierst für mich ein **3D-druckbares Mini-ITX-Gehäuse** und hast dafür die Steuerung über meinen Mac.

## Werkzeug und Arbeitsweise (bitte genau so)

1. **FreeCAD, per Python-Skript gesteuert.** Onshape lässt sich im Browser nur über unzuverlässiges Klicken bedienen. Prüfe deshalb, ob FreeCAD installiert ist (`/Applications/FreeCAD.app`). Fehlt es, frag mich und installiere es dann mit `brew install --cask freecad`.
2. Modelliere **parametrisch in Python**: eine Datei `params.py` mit allen Maßen und pro Bauteil ein Modul in `parts/`. Ein Skript `build.py` läuft headless mit `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd build.py` und erzeugt:
   - `out/step/*.step` und `out/stl/*.stl` (jedes Druckteil schon in Druckorientierung),
   - `out/assembly.FCStd` (Baugruppe mit Dummy-Komponenten),
   - PNG-Ansichten (isometrisch, Explosionsansicht, beide Seiten offen).
3. **Computer Use** nur, um `assembly.FCStd` in der FreeCAD-Oberfläche zu öffnen, Screenshots zu machen und optisch zu prüfen. Konstruiert wird immer im Code, nie per Klick.
4. Lege ein Git-Repository an und committe nach jedem funktionierenden Zwischenstand.
5. **Frag mich zuerst** nach dem genauen Modell von Grafikkarte, Mainboard und Netzteil. Sag ich „weiß ich noch nicht“, arbeitest du mit den Standardwerten unten weiter.

## Komponenten

| Teil | Maße (mm) | Hinweise |
|---|---|---|
| Mainboard Mini-ITX | 170 × 170 | Lochbild und I/O-Fenster laut Spezifikation, siehe „Unsicher“ |
| Noctua NH-D15 | 165 hoch, 150 breit, 161 tief (mit 2 Lüftern) | Lüfter blasen von vorn nach hinten |
| RX 9070 XT (Custom-Karte) | Parameter: Länge ≤ 340, Höhe ≤ 140, Dicke ≤ 65 | 3 Slots, Parameter für 4 vorsehen |
| SFX-Netzteil | 125 × 63,5 × 100 | Parameter für SFX-L (130 tief) vorsehen |
| PCIe-Riser (4.0/5.0 x16) | ca. 200–250 lang | Kaufteil |

## Layout: Sandwich mit Mittelwand (schon entschieden)

Ein NH-D15 ragt auf ITX-Boards über den PCIe-Slot. Deshalb kein Standard-Layout:

- Eine **Mittelwand** teilt das Gehäuse in zwei Kammern. Auf der einen Seite sitzt das Board mit dem D15, auf der anderen die GPU parallel zur Wand, Backplate zur Wand, Lüfter zur Seitenwand. Die Verbindung läuft über ein Riser-Kabel, das unten durch eine Öffnung in der Mittelwand geführt wird.
- Das Gehäuse liegt als niedriger, breiter Block auf dem Tisch. Board und GPU stehen senkrecht.
- Koordinaten: x von vorne nach hinten, y von links (GPU-Kammer) nach rechts (Board-Kammer), z nach oben.
- Startmaße (innen):
  - Länge 358 (= GPU 340 + 18),
  - GPU-Kammer 85 (3 Luft zur Backplate + 65 Karte + 17 Abstand der Lüfter zur Seitenwand),
  - Mittelwand 5,
  - Board-Kammer 181 (6 Abstandshalter + 1,6 Platine + 165 Kühler + 8 Luft),
  - Höhe 210.
- Außenmaße damit ca. **366 × 277 × 220 mm** plus 12 mm Sockel, also rund 22 Liter.
- Board in der Board-Kammer: I/O nach hinten, Unterkante des Boards ca. 22 mm über dem Boden. Darunter ist Platz, damit der Riser umbiegen kann. Sockel-Mitte als Parameter: ca. 90 mm von der I/O-Kante, ca. 105 mm von der Unterkante. Prüfen, dass der Kühler (± 75 in z, ± 80,5 in x um den Sockel) überall frei bleibt.
- Netzteil vorne in der Board-Kammer, flach liegend, Lüfter nach unten über einem gelochten Boden. Die Rückseite des Netzteils zeigt zur gelochten Seitenwand, dort geht die warme Luft raus. Strom kommt über eine C14-Einbaubuchse hinten und ein kurzes internes Verlängerungskabel.
- GPU-Slotblech an der Rückwand: Die Karte steht aufrecht (Kontakte unten, Blechlasche oben). Die Lasche liegt auf einer waagerechten Leiste. Darin ein durchgehender M3-Mutternkanal, damit die Schraubposition frei wählbar ist. Den Riser-Halter höhen- und längsverstellbar machen (Langlöcher, ± 8 mm), dazu eine Stütze gegen das Durchhängen der GPU.
- Kabeldurchführung oben vorn in der Mittelwand (GPU-Stromkabel). Optional eine Öffnung hinter dem CPU-Sockel.

## Design: clean und minimalistisch wie ein Mac Studio

- **Deckel und Boden** als Abdeckplatten mit dem vollen Grundriss: abgerundetes Rechteck, senkrechte Ecken r ≈ 22, oben 2–3 mm Rundung.
- **Seitenwände** laufen mit Viertelkreis um die Ecken herum, dazwischen ebene Front- und Rückwand. Alle Außenflächen sind bündig.
- **Keine sichtbaren Schrauben:**
  - Front, Rück- und Mittelwand werden innen über Laschen in Dome mit M3-Einschmelzmuttern in Boden und Deckel geschraubt.
  - Seitenwände stehen unten in einem schmalen Rand am Boden und werden oben von Magneten (10 × 3 mm) gehalten.
- Lüftung über **Felder aus kleinen runden Löchern** (Ø 4, Wabenraster, Abstand 6) in sauber begrenzten Flächen mit Rand. Keine Schlitze, keine Lüftergitter-Optik.
- **Sockel wie beim Mac Studio:** ein um ca. 16 mm eingerückter Ring (12 hoch), rundum gelocht. Darüber ist der Boden gelocht. So kommt die Frischluft unsichtbar von unten.
- Front fast leer: nur ein 16-mm-Taster (Edelstahl, Vandalismusschutz) unten rechts. USB-C vorne als optionaler Parameter.

## Luftstrom (Pflicht)

- Zuluft: von unten durch den Sockelring und den gelochten Boden sowie durch die Seitenwand vor den GPU-Lüftern.
- Abluft: Der D15 bläst direkt durch das Lochfeld in der Rückwand. GPU-Wärme geht über ein Lochfeld im Deckel über der GPU-Kammer raus (Parameter `top_vent`) und über die Rückwand.
- Freie Lochfläche vor den GPU-Lüftern mindestens ca. 40 %.
- Gib im Ergebnis eine kurze Abschätzung der freien Querschnitte (Zuluft gegen Abluft) aus.

## Drucker: Voron 2.4, 300 mm

- Maximale Teilegröße **290 × 290 × 270**. Größere Teile automatisch teilen.
- Trennstellen: außen eine gerade Fuge mit kleiner V-Nut als bewusste Schattenfuge. Innen hat jede Hälfte einen Flansch (10 hoch, 4 dick), beide Flansche werden mit M3-Schraube und Mutter verschraubt. Optional zusätzlich kleben. Flansche dürfen keine Komponenten berühren.
- Zu teilen sind voraussichtlich: Boden (2), Deckel (2), Sockelring (2), Mittelwand (2), jede Seitenwand (2). Front und Rückwand passen jeweils am Stück.
- Druckorientierung: Sichtflächen aufs Druckbett, keine Stützen nötig, Wandstärken 3–5 mm. Material: PETG oder ABS/ASA (Voron ist geschlossen, ASA empfohlen).
- Einschmelzmuttern M3 (Bohrung Ø 4,0–4,2, Tiefe 5,5), Schrauben M3 Linsenkopf.

## Zusätzliche Druckteile

Netzteil-Halter mit Spannbügel, Riser-Halter, GPU-Stütze, Kabelkamm sowie ein **Passtest-Teil**: eine 2-mm-Platte mit ITX-Lochbild, I/O-Fenster und Slotleiste, um vor dem großen Druck alles zu prüfen.

## Prüfungen, bevor du „fertig“ sagst

1. **Kollisionsprüfung im Code:** Schnittmenge aus allen Gehäuseteilen und den Dummy-Körpern (Board, D15, GPU mit Kabelbiegeradius 35 mm oben, Netzteil, Riser) muss null sein. Außerdem eine Fehlermeldung, wenn ein Druckteil größer als 290 × 290 × 270 ist.
2. Alle Teile sind wasserdicht (manifold), STLs lassen sich fehlerfrei laden.
3. Screenshots in FreeCAD per Computer Use: Gesamtansicht, beide Kammern offen, Explosionsansicht. Zeig sie mir.

## Unsicher, bitte verifizieren statt raten

- **Mini-ITX-Lochbild:** Nach meiner Erinnerung relativ zu Loch C: (0,0), (154,94; 0), (22,86; 157,48), (154,94; 157,48). Loch C liegt neben dem PCIe-Slot, die Slot-Mittellinie ca. 1,57 mm Richtung I/O. Prüfe das gegen die Spezifikation (ATX/Mini-ITX-Spec-PDF) und richte die Achsen richtig aus.
- **I/O-Fenster:** 158,75 × 44,45 mm. Lage relativ zu Board und Abstandshalter-Ebene aus der ATX-Spezifikation übernehmen.
- **PCIe-Slotblech:** Länge, Laschenhöhe über der Kontaktkante, Slotabstand 20,32 mm.
- **Netzteil-Einbaumaße** und C14-Buchse (Ausschnitt, Lochabstand). Erst den genauen Typ mit mir festlegen.
- Lieber ein Passtest-Teil mehr als ein falsch gedrucktes 10-Stunden-Teil.

## Lieferumfang

- Repository mit Code, STEP, STL und `assembly.FCStd`.
- `README.md` auf Deutsch: Teileliste mit Druckzeit-Schätzung, Einkaufsliste (Einschmelzmuttern, Schrauben, Muttern, Magnete, Riser, C14-Buchse mit Kabel, Taster, Gummifüße), Slicer-Einstellungen, Montage-Reihenfolge.
- Alle Maße als Parameter in `params.py`, damit ich GPU, Netzteil oder Kühler später ändern kann.
