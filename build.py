"""Headless-Build:  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd build.py

LAYOUT=A (liegend, Standard), B (stehend) oder C (stehend, M3-Stil) wählt die Variante.
Erzeugt out/<LAYOUT>/step/*.step (Montagelage), out/<LAYOUT>/stl/*.stl (Druckorientierung),
out/<LAYOUT>/assembly.FCStd (mit Dummies) und out/<LAYOUT>/report.txt.
Exit-Code != 0 bei Fehlern.

Die Teile entstehen in Modellkoordinaten (y links -> rechts, Linkssystem) und werden
hier an der Ebene y = INNER_W / 2 gespiegelt, damit sie im rechtshändigen FreeCAD-Raum
und in STEP/STL die richtige Händigkeit haben (siehe params.py).
"""
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
sys.path.insert(0, ROOT)
for m in [k for k in sys.modules if k == "params" or k.startswith("parts")]:
    del sys.modules[m]

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402
import MeshPart  # noqa: E402

import params as P  # noqa: E402
from parts import floor, lid, side_walls, panels, tray, plinth, extras, dummies, cables  # noqa: E402
from parts.common import hole_area, VGROOVE_LOG, envelope_case, envelope_plinth  # noqa: E402

VARIANT = P.LAYOUT if (P.GPU_PROFILE, P.PSU_TYPE) == ("reaper", "SFX") else \
    f"{P.LAYOUT}-{P.GPU_PROFILE}-{P.PSU_TYPE}"
OUT = os.path.join(ROOT, "out", VARIANT)   # Profil-Varianten landen daneben (nicht im Repo)
QUICK = os.environ.get("QUICK") == "1"     # QUICK=1: ohne STL/STEP-Export
LOG = []


def log(msg=""):
    print(msg, flush=True)
    LOG.append(msg)


def timed(label, fn):
    t = time.time()
    r = fn()
    log(f"  {label:<28} {time.time() - t:6.1f} s")
    return r


# --------------------------------------------------------------------------
log(f"== Variante {P.summary()['Variante']}, GPU {P.GPU_PROFILE}, {P.PSU_TYPE} ==")
log("== Bauteile ==")
t0 = time.time()
floor_parts, n_floor = timed("Boden", floor.build)
lid_parts, n_lid = timed("Deckel", lid.build)
side_parts, n_side = timed("Seitenwände", side_walls.build)
front = timed("Front", panels.front)
front_ins = [timed("Front-Einleger", panels.front_insert)] if P.GRATER else []
rear_ins = [timed("Rückwand-Einleger", panels.rear_insert)] if P.GRATER_REAR else []
rear, rear_pts = timed("Rückwand", panels.rear)
mid_parts = timed("Board-Träger", tray.build) if not P.LYING else []
plinth_parts, a_pl = timed("Sockel", plinth.build)
extra_parts, fit_parts = timed("Extras", extras.build)
dummy_parts = timed("Dummies", dummies.build)
cable_parts, cable_info = timed("Kabelwege", cables.build)
dummy_parts += cable_parts

case_parts = (floor_parts + lid_parts + side_parts + [front] + front_ins + [rear] + rear_ins
              + mid_parts + plinth_parts)
assembly_printed = case_parts + [p for p in extra_parts if p.group == "extra"]
all_printed = case_parts + extra_parts + fit_parts


def to_freecad(p):
    """Modell -> FreeCAD-Raum. Drehungen der Druckorientierung werden mitgespiegelt
    (Achse gespiegelt, Winkel umgekehrt), damit dieselbe Fläche auf dem Bett liegt."""
    vol = p.shape.Volume
    p.shape = p.shape.mirror(App.Vector(0, P.INNER_W / 2, 0), App.Vector(0, 1, 0))
    if abs(p.shape.Volume - vol) > 1e-3 * max(vol, 1.0):
        raise RuntimeError(f"{p.name}: Spiegelung verändert das Volumen")
    p.print_rot = [((a[0], -a[1], a[2]), -ang) for a, ang in p.print_rot]
    p.explode = (p.explode[0], -p.explode[1], p.explode[2])


timed("Spiegeln (Händigkeit)", lambda: [to_freecad(p) for p in all_printed + dummy_parts])

errors, warnings = [], []

log("\n== V-Nut an den Trennstellen ==")
split_names = [p.name for p in floor_parts + lid_parts[:2]
               + [p for p in side_parts if "einleger" not in p.name]
               + ([] if P.FEET else plinth_parts)]
for name, (side, n, how) in zip(split_names, VGROOVE_LOG):
    log(f"  {name:<22} {n:2d} Kanten  {how}")
    if how != "V-Fase":
        warnings.append(f"{name}: {how}")

# --------------------------------------------------------------------------
log("\n== Gültigkeit ==")
for p in all_printed:
    s = p.shape
    if not s.isValid() or len(s.Solids) != 1:
        errors.append(f"{p.name}: Geometrie ungültig oder nicht genau ein Körper "
                      f"(valid={s.isValid()}, solids={len(s.Solids)})")
log("  ok" if not errors else "\n".join("  " + e for e in errors))


# --------------------------------------------------------------------------
def overlap(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    try:
        return a.common(b).Volume
    except Exception as e:  # pragma: no cover
        return float("nan")


log("\n== Kollision Gehäuse/Halter <-> Komponenten ==")
coll = 0
for d in dummy_parts:
    for p in assembly_printed:
        v = overlap(p.shape, d.shape)
        if not (v < 1e-3):
            coll += 1
            errors.append(f"Kollision {p.name} <-> {d.name}: {v:.3f} mm³")
            log(f"  FEHLER {p.name} <-> {d.name}: {v:.3f} mm³")
log(f"  {'keine Kollision' if coll == 0 else f'{coll} Kollisionen'}")

if cable_parts:
    log("\n== Kabelwege gegen Komponenten ==")
    comp = {d.name.replace("dummy_", ""): d for d in dummy_parts if d.name.startswith("dummy_")}
    cc = 0
    for c in cable_parts:
        ends = cable_info[c.name][1]
        for key, d in comp.items():
            if key in ends or (key == "board" and "board" in ends):
                continue
            v = overlap(c.shape, d.shape)
            if not (v < 1e-3):
                cc += 1
                errors.append(f"Kabelweg {c.name} läuft durch {d.name}: {v:.1f} mm³")
                log(f"  FEHLER {c.name} <-> {d.name}: {v:.1f} mm³")
    log(f"  {'frei' if cc == 0 else f'{cc} Konflikte'}")

log("\n== Überschneidung Druckteile untereinander ==")
ov = 0
for i, a in enumerate(assembly_printed):
    for b in assembly_printed[i + 1:]:
        v = overlap(a.shape, b.shape)
        if not (v < 1e-3):
            ov += 1
            errors.append(f"Überschneidung {a.name} <-> {b.name}: {v:.3f} mm³")
            log(f"  FEHLER {a.name} <-> {b.name}: {v:.3f} mm³")
log(f"  {'keine' if ov == 0 else f'{ov} Überschneidungen'}")


# --------------------------------------------------------------------------
def print_shape(p):
    s = p.shape.copy()
    for axis, ang in p.print_rot:
        s.rotate(App.Vector(0, 0, 0), App.Vector(*axis), ang)
    bb = s.BoundBox
    s.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    return s


def minutes_estimate(shape):
    # grobe Schätzung Voron 2.4, 0.4 mm Düse, 0.2 mm Schicht, 4 Perimeter, 25 % Infill
    vol_cm3 = shape.Volume / 1000.0
    area_cm2 = shape.Area / 100.0
    return 1.1 * vol_cm3 + 0.12 * area_cm2 + 6


log("\n== Druckbett / Manifold / Export ==")
os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)
os.makedirs(os.path.join(OUT, "step"), exist_ok=True)
rows = []
for p in all_printed:
    s = print_shape(p)
    bb = s.BoundBox
    dims = sorted([bb.XLength, bb.YLength])[::-1] + [bb.ZLength]
    fits = bb.XLength <= P.BED[0] and bb.YLength <= P.BED[1] and bb.ZLength <= P.BED[2]
    if not fits:
        errors.append(f"{p.name}: zu groß für das Druckbett "
                      f"({bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} > "
                      f"{P.BED[0]:.0f} x {P.BED[1]:.0f} x {P.BED[2]:.0f})")
    manifold = "-"
    if not QUICK:
        mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.04, AngularDeflection=0.3,
                                      Relative=False)
        solid_ok = mesh.isSolid() and not mesh.hasNonManifolds()
        manifold = "ja" if solid_ok else "NEIN"
        if not solid_ok:
            errors.append(f"{p.name}: STL nicht manifold")
        mesh.write(os.path.join(OUT, "stl", p.name + ".stl"))
        p.shape.exportStep(os.path.join(OUT, "step", p.name + ".step"))
    mins = minutes_estimate(p.shape)
    p.minutes = mins
    grams = p.shape.Volume / 1000.0 * 1.07 * 0.55   # ASA, ~55 % gefüllt
    rows.append((p.name, bb.XLength, bb.YLength, bb.ZLength, fits, manifold, mins, grams))
    log(f"  {p.name:<22} {bb.XLength:6.1f} x {bb.YLength:6.1f} x {bb.ZLength:6.1f}  "
        f"{'passt' if fits else 'ZU GROSS'}  manifold={manifold}  ~{mins/60:4.1f} h  ~{grams:4.0f} g")


# --------------------------------------------------------------------------
log("\n== Freie Querschnitte (Ø%.1f, Raster %.1f; Sockel Ø%.1f) =="
    % (P.VENT_D, P.VENT_PITCH, P.PLINTH_VENT_D))
hex_ratio = math.pi * (P.VENT_D / 2) ** 2 / (P.VENT_PITCH ** 2 * math.sqrt(3) / 2)
side_pts = side_walls.vent_points()
a_fl = hole_area(floor.vent_points())
a_side = hole_area(side_pts)
a_top = hole_area(lid.vent_points())
a_front = hole_area(panels.front_vent_points())
a_rear = hole_area(rear_pts)
if P.GRATER or P.GRATER_LID:
    from parts import grater
    f_open = grater.open_fraction()

    def win_area(rec):
        u0, u1, v0, v1 = grater.rects(rec)[2]
        return (u1 - u0) * (v1 - v0)
    if P.GRATER:
        a_front = f_open * win_area(panels.front_recess())
    if P.GRATER_SIDES:
        a_side = f_open * win_area(side_walls.grater_recess())
    if P.GRATER_REAR:
        a_rear = f_open * win_area(panels.rear_recess())
    a_grater_top = f_open * sum(win_area(r) for r in lid.grater_recesses())
    log(f"  Reibe: {f_open*100:.1f} % der Fensterfläche offen (Abtastung)")
y0, y1, z0, z1 = panels.gpu_open()
a_open = (y1 - y0) * (z1 - z0) * 0.5   # Slotblech ~50 % offen
fan95 = math.pi * (47.5 ** 2 - 14 ** 2)
fan140 = math.pi * (70 ** 2 - 22 ** 2)
# Fläche vor den GPU-Lüftern (Kartenfläche ohne Blechzone)
fx0, fx1 = P.GPU_X0, P.INNER_L - P.GPU_RAIL_DEPTH
if P.LYING:
    fan_face = "linke Seitenwand"
    fz0, fz1 = max(P.GPU_W0, P.SIDE_VENT["z0"]), min(P.GPU_W1, P.SIDE_VENT["z1"])
    fan_pts = [q for q in side_pts if fx0 <= q[0] <= fx1 and fz0 <= q[1] <= fz1]
    fan_field = (fx1 - fx0) * (fz1 - fz0)
else:
    fan_face = "Boden"
    fy0, fy1 = P.Y_BASE - P.GPU_W1, P.Y_BASE - P.GPU_W0
    fan_pts = [q for q in floor.vent_points() if fx0 <= q[0] <= fx1 and fy0 <= q[1] <= fy1]
    fan_field = (fx1 - fx0) * (fy1 - fy0)
a_fan = hole_area(fan_pts)
gpu_in = (a_side + min(a_pl, a_fl) / 2) if P.LYING else (min(a_pl, a_fl) + a_side / 2)
if P.GRATER_LID:
    a_top = a_grater_top
lines = [
    f"Wabenfeld offen (theoretisch): {hex_ratio*100:.1f} %",
    f"  Front                 {a_front/100:7.0f} cm²  (vor Netzteil und CPU-Kühler)",
    f"  Rückwand              {a_rear/100:7.0f} cm²  + Slotblech ~{a_open/100:.0f} cm²",
    f"  Seitenwand je Seite   {a_side/100:7.0f} cm²",
    f"  Deckel                {a_top/100:7.0f} cm²",
    f"  Boden (über Sockel)   {a_fl/100:7.0f} cm²",
    (f"  Spalt unter dem Boden {a_pl/100:7.0f} cm²  (Füße {P.FOOT_H:.0f} mm, rundum offen)" if P.FEET
     else f"  Sockelring            {a_pl/100:7.0f} cm²  (Engstelle der Bodenzuluft)"),
    f"GPU saugt durch: {fan_face}, vor der Karte {a_fan/fan_field*100:.1f} % offen",
    f"Vergleich: 3x 95-mm-GPU-Lüfter ~{3*fan95/100:.0f} cm², 2x 140 mm D15 ~{2*fan140/100:.0f} cm²",
]
for line in lines:
    log("  " + line)
if a_fan / fan_field < 0.40:
    warnings.append(f"GPU-Ansaugfläche ({fan_face}) unter 40 % offen")
if not P.LYING and not P.FEET and a_pl < 3 * fan95:
    warnings.append(f"Sockelring {a_pl/100:.0f} cm² kleiner als die GPU-Lüfterfläche "
                    f"{3*fan95/100:.0f} cm²: die Karte holt den Rest über Seitenwände und Front")

if cable_info:
    log("\n== Kabellängen (Weg im Modell, + 30 mm je Stecker) ==")
    for name, (ln, ends) in cable_info.items():
        log(f"  {name:<14} {ln:5.0f} mm Weg, Kabel ca. {ln + 60:4.0f} mm")

# --------------------------------------------------------------------------
log("\n== Maße ==")
for k, val in P.summary().items():
    log(f"  {k}: {val}")
vol_case = envelope_case().Volume / 1e6
vol_pl = 0.0 if P.FEET else envelope_plinth().Volume / 1e6
log(f"  Volumen außen: {vol_case + vol_pl:.1f} l (Gehäuse {vol_case:.1f} l, "
    f"{'Füße nicht gezählt' if P.FEET else f'Sockel {vol_pl:.1f} l'})")
log(f"  Volumen innen: {P.INNER_L * P.INNER_W * P.INNER_H / 1e6:.1f} l (Quader ohne Eckbögen)")
air = (P.INNER_H - P.COOLER_W1) if P.LYING else (P.Y_BASE - P.COOLER_W1)
if air < 3:
    errors.append(f"Luft am Kühlerende nur {air:.1f} mm")
iy0, iy1, iz0, iz1 = panels.io_window()
m = P.IO_KEEPOUT
if iy0 - m < P.FLAT_Y0 or iy1 + m > P.FLAT_Y1:
    errors.append("I/O-Fenster reicht in den Eckbogen der Rückwand")
if P.GPU_OPEN_V[1] + 2 > P.IO_V0:
    errors.append("Slotblech-Öffnung und I/O-Fenster überschneiden sich")
if P.rect_vw(*P.GPU_OPEN_V, *P.GPU_OPEN_W)[0] < P.FLAT_Y0 + 1:
    errors.append("Slotblech-Öffnung reicht in den Eckbogen der Rückwand")

# --------------------------------------------------------------------------
log("\n== Montage-Dokument ==")
doc = App.newDocument("ITX_Case")


def add(p, group_obj):
    o = doc.addObject("Part::Feature", p.name)
    o.Shape = p.shape
    o.addProperty("App::PropertyColor", "Farbe", "ITX")
    o.Farbe = p.color
    o.addProperty("App::PropertyVector", "Explode", "ITX")
    o.Explode = App.Vector(*p.explode)
    o.addProperty("App::PropertyString", "Gruppe", "ITX")
    o.Gruppe = p.group
    group_obj.addObject(o)
    return o


groups = {}
for name in ("Gehaeuse", "Halter", "Komponenten"):
    groups[name] = doc.addObject("App::DocumentObjectGroup", name)
for p in case_parts:
    add(p, groups["Gehaeuse"])
for p in extra_parts:
    add(p, groups["Halter"])
for p in dummy_parts:
    add(p, groups["Komponenten"])
doc.recompute()
fc_path = os.path.join(OUT, "assembly.FCStd")
doc.saveAs(fc_path)
if not QUICK:
    Part.export([o for o in doc.Objects if o.TypeId == "Part::Feature" and o.Gruppe != "dummy"],
                os.path.join(OUT, "step", "_baugruppe.step"))
log(f"  {fc_path}")

# --------------------------------------------------------------------------
log("\n== Ergebnis ==")
for w in warnings:
    log("  WARNUNG " + w)
for e in errors:
    log("  FEHLER " + e)
log(f"  {'OK' if not errors else f'{len(errors)} Fehler'} – {time.time() - t0:.0f} s")

with open(os.path.join(OUT, "report.txt"), "w") as f:
    f.write("\n".join(LOG) + "\n")
with open(os.path.join(OUT, "parts.tsv"), "w") as f:
    f.write("name\tx\ty\tz\tpasst\tmanifold\tminuten\tgramm\n")
    for r in rows:
        f.write("\t".join(str(round(c, 1)) if isinstance(c, float) else str(c) for c in r) + "\n")

if errors:
    os._exit(1)
os._exit(0)
