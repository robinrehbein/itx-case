# ITX-Case – 3D-druckbares Mini-ITX-Gehäuse

Ein flacher, breiter Block im Stil des Mac Studio mit zwei Kammern. Links steht die GPU aufrecht
parallel zur Mittelwand. Rechts sitzen Board, Noctua NH-D15 und SFX-Netzteil. Ein Riser-Kabel
verbindet beide Kammern unten durch die Mittelwand. Die Zuluft kommt unsichtbar durch den
gelochten Sockel und den Boden.

| | |
|---|---|
| Außen (ohne Sockel) | 366 × 279 × 220 mm |
| Höhe mit Sockel | 232 mm |
| Innen | 358 × 271 × 210 mm |
| GPU-Kammer / Board-Kammer | 85 / 181 mm (5 mm Mittelwand) |
| Luft über dem Kühler | 8,4 mm |
| Drucker | Voron 2.4 300, Teile ≤ 290 × 290 × 270 mm |

![Gesamtansicht](out/png/01_gesamt_vorn.png)

## Bauen

```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd build.py   # STEP, STL, FCStd, Prüfungen
/Applications/FreeCAD.app/Contents/MacOS/FreeCAD render.py             # PNG-Ansichten (GUI)
```

`build.py` bricht mit Exit-Code 1 ab, wenn eine Prüfung fehlschlägt. Das Protokoll steht in
`out/report.txt`, die Teiletabelle in `out/parts.tsv`. Optionen lassen sich per Umgebungsvariable
setzen, ohne `params.py` zu ändern: `GPU_PROFILE=max`, `PSU_TYPE=SFX-L`, `QUICK=1` (nur Prüfungen,
kein Export).

| Pfad | Inhalt |
|---|---|
| `params.py` | alle Maße und Optionen |
| `parts/` | ein Modul pro Bauteilgruppe (`floor`, `lid`, `side_walls`, `panels`, `midwall`, `plinth`, `extras`, `dummies`) |
| `out/step/` | STEP pro Teil in Montagelage, `_baugruppe.step` komplett |
| `out/stl/` | STL pro Teil in Druckorientierung |
| `out/assembly.FCStd` | Montage mit Dummy-Komponenten (Gruppen Gehäuse/Halter/Komponenten) |
| `out/png/` | Gesamtansicht, beide Kammern offen, Explosionsansicht |

## Prüfungen (Stand des letzten Builds)

1. **Kollisionen:** Gehäuse und Halter gegen alle Dummies (Board mit I/O-Block, NH-D15,
   GPU mit 35-mm-Kabelbogen und Slotblech, Netzteil, Riser mit Stecker, Kabel und Sockel,
   Taster, C14): Schnittvolumen 0. Druckteile untereinander: keine Überschneidung. Das gilt
   für die Profile `reaper`, `max` und `SFX-L`.
2. **Druckbett:** Alle Teile passen nach dem Drehen in die Druckorientierung auf das Bett.
3. **Manifold:** Alle 22 STLs sind geschlossene Körper ohne Non-Manifold-Kanten.

## Teileliste

Die Zeiten sind grobe Schätzungen aus Volumen und Oberfläche (0,4-mm-Düse, 0,2-mm-Schicht).
Der Slicer ist maßgeblich.

| Teil | Druckmaß (mm) | Orientierung | Zeit | ASA |
|---|---|---|---|---|
| boden_vorn / boden_hinten | 179 / 187 × 279 × 15 | Unterseite aufs Bett | 7 h + 7 h | 246 g |
| deckel_vorn / deckel_hinten | 181 / 189 × 283 × 15 | Oberseite aufs Bett | 7 h + 7 h | 290 g |
| seite_links_vorn / _hinten | 179 / 187 × 22 × 210 | stehend | 4,5 h + 4,5 h | 146 g |
| seite_rechts_vorn / _hinten | 179 / 187 × 22 × 210 | stehend | 4,5 h + 5 h | 189 g |
| front | 210 × 235 × 14 | Sichtseite aufs Bett | 6 h | 117 g |
| rueckwand | 210 × 235 × 17 | Sichtseite aufs Bett | 4 h | 69 g |
| mittelwand_vorn / _hinten | 173 / 182 × 210 × 15 | GPU-Seite aufs Bett | 5 h + 5 h | 217 g |
| sockel_vorn / _hinten | 163 / 171 × 247 × 12 | stehend, Lippe unten | 1 h + 1 h | 28 g |
| netzteil_halter | 137 × 112 × 31 | wie eingebaut | 1 h | 17 g |
| netzteil_buegel | 143 × 56 × 20 | Steg aufs Bett | 0,6 h | 9 g |
| riser_halter | 161 × 14 × 21 | wie eingebaut | 0,4 h | 5 g |
| riser_traeger | 129 × 20 × 10 | wie eingebaut | 0,4 h | 5 g |
| gpu_stuetze | 47 × 16 × 21 | wie eingebaut | 0,3 h | 3 g |
| kabelkamm | 38 × 10 × 8 | wie eingebaut | 0,2 h | 1 g |
| passtest_board | 182 × 184 × 8 | flach | 1,6 h | 23 g |
| passtest_rueckwand | 185 × 131 × 15 | flach | 1,1 h | 16 g |
| **Summe Gehäuse + Halter** | | | **ca. 80 h** | **ca. 1,4 kg** |

**Zuerst die zwei Passtest-Teile drucken.** Sie prüfen die Maße, die nicht sicher sind (siehe
unten), mit echtem Board und echter Karte, bevor 80 Stunden Druckzeit anfallen.

## Einkaufsliste

| Teil | Menge | Hinweis |
|---|---|---|
| M3-Einschmelzmuttern, 5–5,7 mm lang, Außen-Ø ca. 4,6 | 50 | 35 verbaut (Bohrung Ø4,1, Tiefe 5,5) |
| Zylinderkopfschrauben M3 × 8 | 40 | Wandlaschen, Netzteil, Riser, GPU-Stütze, Leiste |
| Zylinderkopfschrauben M3 × 12 | 30 | Trennflansche (2 × 4 mm), Sockel an Boden |
| Zylinderkopfschrauben M3 × 6 | 10 | Board auf Einschmelzmuttern, GPU-Slotblech |
| M3-Muttern (DIN 934) | 30 | Flansche, Mutternkanal der GPU-Leiste |
| Neodym-Scheibenmagnete 10 × 3 mm | 16 | 8 im Deckel, 8 in den Seitenwänden, **Polung beachten** |
| PCIe-4.0-x16-Riserkabel, 150–200 mm | 1 | gerade Buchse, Stecker gerade; Kabel läuft unter dem Board durch die Mittelwand |
| C14-Einbaubuchse, Schnappbefestigung, Ausschnitt 27,5 × 19,8 mm, Wandstärke 1–2 mm | 1 | mit internem Kabel C14 → C13 gewinkelt, ca. 30 cm |
| Vandalismus-Taster 16 mm, Taster (nicht rastend), max. 28 mm Einbautiefe | 1 | mit Kabel für den Power-Switch-Header |
| Gummifüße selbstklebend, Ø8 × 2–3 mm | 8 | auf die Sockellippe |
| optional: USB-C-Einbaubuchse mit Verlängerung | 1 | `USB_C = True` |
| SFX-Netzteil ≥ 750 W | 1 | PowerColor empfiehlt für die Reaper mindestens 750 W |

## Slicer-Einstellungen (Voron 2.4, ASA)

| Einstellung | Wert |
|---|---|
| Material | ASA (bevorzugt, wärmefest) oder PETG |
| Düse / Schicht | 0,4 mm / 0,2 mm (Sichtteile 0,16 mm) |
| Perimeter | 4 (Wände 4 mm werden damit fast voll) |
| Ober-/Unterlagen | 5 / 5 |
| Infill | 25 % Gyroid |
| Stützen | **keine**, alle Teile sind stützenfrei ausgelegt |
| Bett / Düse | 105 °C / 250–260 °C (ASA), Kammer geschlossen und aufgeheizt |
| Kühlung | 20–40 % ASA, nur für Brücken mehr |
| Brim | 5 mm bei Seitenwänden und Sockel (hoch und schmal) |
| Nahtposition | hinten bzw. an der Innenseite (`Rear` / gemalt) |
| Bügeln | Deckel- und Bodenunterseite optional (Sichtflächen liegen auf dem Bett, Textur-PEI ergibt eine gleichmäßige Oberfläche) |

Einschmelzmuttern mit einer Lötspitze bei ca. 245 °C setzen.

## Montage-Reihenfolge

1. **Passtest:** `passtest_board` mit dem Board verschrauben (Muttern hinten), `passtest_rueckwand`
   über die Zapfen stecken. Prüfen: I/O-Blende rastet im Fenster ein. Riser einstecken, Karte mit
   Slotblech an die Leiste setzen: Die Lasche muss auf der Leiste aufliegen, und die Karte darf
   nicht an der Leiste anstoßen. Abweichungen in `params.py` korrigieren (`ITX_HOLE_C`,
   `IO_FROM_BOTTOM`, `BRACKET_TAB_ABOVE_FINGERS`, `GPU_RAIL_H`).
2. **Einschmelzmuttern** in alle Dome und Bossen setzen (Boden von oben, Plinth-Bossen von unten,
   Deckel von unten, Mittelwand-Abstandshalter, Netzteil-Halterpfosten).
3. **Magnete** in Deckel und Seitenwände kleben (Sekundenkleber oder Epoxid). Vorher die Polung
   festlegen: Deckel-Magnete alle mit Nordpol nach unten, Seitenwand-Magnete mit Südpol nach oben.
4. **Hälften verschrauben:** Boden, Deckel, Sockel, Mittelwand und beide Seitenwände jeweils an den
   Flanschen mit M3 × 12 und Mutter. V-Nut außen sauber ausrichten, erst dann anziehen.
5. **Sockel unter den Boden** schrauben (4 × M3 × 12 von unten), Gummifüße auf die Lippe kleben.
6. **Riser-Halter, GPU-Stütze und Netzteil-Halter** auf den Boden schrauben (die Langlöcher
   zunächst nur leicht anziehen).
7. **Front** (Taster vorher einbauen) und **Rückwand** (C14 vorher einschnappen) in den Randfalz
   setzen und unten über die Laschen in die Bodendome schrauben.
8. **Mittelwand** einsetzen und unten verschrauben. Das Board mit montiertem NH-D15 (Lüfter
   blasen nach hinten) auf die Abstandshalter schrauben, Riser vorher in den Slot stecken und das
   Kabel unten durch die Mittelwand führen.
9. **Netzteil** flach auf den Halter legen (Lüfter nach unten, Rückseite zur rechten Seitenwand),
   C14-Verlängerung einstecken, Bügel überlegen und seitlich verschrauben.
10. **GPU:** Riserbuchse auf den Träger schrauben, Höhe und Länge über die Langlöcher einstellen,
    Karte einstecken, Lasche auf die Leiste schrauben (Mutter im Kanal vorher an die Slotposition
    schieben), GPU-Stütze unter die Kartenvorderkante schieben.
11. **Kabel** oben vorn durch die Mittelwand ziehen, mit dem Kabelkamm ordnen.
12. **Deckel** aufsetzen und von innen über die Laschen von Front, Rückwand und Mittelwand
    verschrauben.
13. **Seitenwände** unten in den Randfalz stellen und oben andrücken: Die Magnete halten sie.
    Zum Öffnen oben nach außen kippen und abheben.

## Luftstrom und freie Querschnitte

Löcher Ø4 im Wabenraster mit 6 mm Abstand (theoretisch 40,3 % offen).

| | Fläche | Bemerkung |
|---|---|---|
| **Zuluft** Sockelring | 38 cm² | Engstelle der Bodenzuluft, zusätzlich ca. 35 cm² Spalt unter der Lippe bei 3-mm-Füßen |
| Boden über dem Sockel | 244 cm² | |
| Seitenwand vor der GPU | 211 cm² | 40,9 % offen vor der Karte |
| Seitenwand Netzteil | 27 cm² | Netzteil-Abluft |
| **Abluft** Rückwand hinter dem D15 | 56 cm² | ein 140-mm-Lüfter hat ca. 139 cm² freie Fläche |
| Deckel über der GPU (`TOP_VENT`) | 69 cm² | |
| Rückwand GPU | 12 cm² + ca. 29 cm² | Lochfeld plus Slotblech |

Engstellen: Die Bodenzuluft hängt am Sockelring, und hinter dem D15 bleibt wegen des
I/O-Fensters nur ein Teil der Rückwand für Löcher. Wer mehr Luft braucht, stellt
`PLINTH_H` auf 16 (drei Lochreihen statt zwei) oder vergrößert das Feld `REAR_D15_VENT`.

## Entscheidungen

- **Wandstärke 4 mm überall** statt 3 mm an den Seiten. Seitenwand-Eckbögen und Front/Rückwand
  stoßen dadurch bündig aneinander. Folge: außen 279 statt ca. 277 mm breit.
- **Raster 5,7 mm in der GPU-Seitenwand** statt 6 mm. Mit 6 mm wäre das Feld wegen der Fuge
  nur ca. 36 % offen gewesen; die Vorgabe von mindestens 40 % hat Vorrang. Die Lochgröße bleibt Ø4.
- **Seitenwand-Flansche nur oben und unten** (je ein Paar 20 mm lang), damit die Fuge vor den
  GPU-Lüftern Löcher behalten kann.
- **GPU-Kammer bleibt 85 mm** für Karten bis 340 × 140 × 65 mm (Profil `max`), obwohl die Reaper
  nur 42 mm dick ist. Sie hat dadurch 40 mm Luft vor den Lüftern.
- **Laschen der Mittelwand nur auf der Board-Seite.** Oben sitzen sie nur außerhalb des Kühlers
  (x = 30, 140, 351), weil über dem D15 nur 8 mm Luft bleiben.
- **Rückwand oben in der GPU-Kammer ohne Lasche**, wegen des Kabelbogens. Gehalten wird sie dort
  von der Leiste und der Mittelwand-Nachbarschaft.
- **Netzteil 25 mm vor der Seitenwand**, damit ein gewinkelter C13-Stecker in die Netzteilbuchse
  passt.
- **Gemeinsame Trennstelle x = 175 mm** für Boden, Deckel, Sockel, Mittelwand und Seitenwände.
  Alle Fugen liegen außen in einer Linie.

## Unsicher – mit dem Passtest prüfen

| Maß | Wert in `params.py` | Stand |
|---|---|---|
| ITX-Lochbild | C(0,0), F(154,94; 0), H(22,86; 157,48), J(154,94; 157,48) mit erster Koordinate **Richtung vorn**, zweiter **quer** | Abstände sind die 0,1"-Rasterwerte aus ATX/microATX (6,1" / 6,2" / 0,9"). Deine Liste stimmt, wenn die erste Koordinate Richtung vorn zählt; quer gelesen läge die vordere Lochreihe nur 2,4 mm vor der Platinenkante. Loch C: 10,16 mm von der I/O-Kante, 6,17 mm von der Slot-Kante – aus Zeichnungen, nicht aus der Spezifikation. |
| I/O-Fenster | 158,75 × 44,45, Unterkante 3,81 unter Platinenoberseite, Wand 1,2 mm, Ecken r 0,99, Sperrzone 2,5 | Aus ATX 2.2, Abschnitt 3.3.5 (Text). Die Lage entlang der Kante (`IO_FROM_BOTTOM` = 5,6) ist geschätzt; die Zeichnung (Fig. 3/4) war nur als Bild verfügbar. |
| PCIe-Slotblech | Länge 120,02, Slotabstand 20,32, Lasche 112 über der Fingerunterkante, Leiste 6 mm hoch | Slotabstand sicher (0,8"). Laschenhöhe und Freiraum unter der Lasche geschätzt. |
| NH-D15-Höhe | 165 mm ab Platine | Die Noctua-Seite nennt für den NH-D15 G2 168 mm (`COOLER_PROFILE = "NH-D15 G2"` lässt dann 5,4 mm Luft). |
| Reaper-Maße | 304 × 127 × 42 mm (mit Blech), 2 × 8-Pin | Händlerangaben; Karte ohne Blech 289 × 111 × 41. |
| Sockel-/Slotlage | Sockel 90 mm von I/O, 105 mm von unten; Slot 10 mm von unten, 45–134 mm von I/O | Parameter, für das kommende Board anpassen. Für das Z590I Vision D nicht verifiziert. |
| Netzteil und C14 | SFX 125 × 63,5 × 100; C14-Schnappbuchse 27,5 × 19,8 | Typ festgelegt, konkretes Modell offen. |

**Option 4 Slots:** Bei `GPU_SLOTS = 4` reicht die Slotöffnung (81 mm) in den Eckbogen der
Rückwand (die ebene Fläche beginnt bei y = 18). Für eine 4-Slot-Karte müsste die GPU-Kammer
breiter werden (`GPU_THICK_MAX`), `build.py` warnt dann.
