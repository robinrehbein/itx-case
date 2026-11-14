"""Headless-Build:  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd build.py

Erzeugt out/step/*.step (Montagelage), out/stl/*.stl (Druckorientierung),
out/assembly.FCStd (mit Dummies) und out/report.txt. Exit-Code != 0 bei Fehlern.

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
from parts import floor, lid, side_walls, panels, midwall, plinth, extras, dummies  # noqa: E402
from parts.common import hole_area, VGROOVE_LOG  # noqa: E402

OUT = os.path.join(ROOT, "out")
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
log("== Bauteile ==")
t0 = time.time()
floor_parts, n_floor = timed("Boden", floor.build)
lid_parts, n_lid = timed("Deckel", lid.build)
side_parts, (n_gpu_side, n_psu_side) = timed("Seitenwände", side_walls.build)
front = timed("Front", panels.front)
rear, (rear_d15, rear_gpu) = timed("Rückwand", panels.rear)
mid_parts = timed("Mittelwand", midwall.build)
plinth_parts, a_pl = timed("Sockel", plinth.build)
extra_parts, fit_parts = timed("Extras", extras.build)
dummy_parts = timed("Dummies", dummies.build)

case_parts = floor_parts + lid_parts + side_parts + [front, rear] + mid_parts + plinth_parts
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
split_names = [p.name for p in floor_parts + lid_parts + side_parts + plinth_parts]
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
a_fl = hole_area(floor.vent_points())
a_gs = hole_area(side_walls.gpu_vent_points())
# offener Anteil vor den GPU-Lüftern (Kartenfläche ohne Blechzone)
fx0, fx1 = max(P.GPU_X0, P.GPU_SIDE_VENT["x0"]), P.INNER_L - P.GPU_RAIL_DEPTH
fz0, fz1 = P.GPU_Z0, min(P.GPU_Z0 + P.GPU["H"], P.GPU_SIDE_VENT["z1"])
fan_pts = [q for q in side_walls.gpu_vent_points() if fx0 <= q[0] <= fx1 and fz0 <= q[1] <= fz1]
gs_field = (fx1 - fx0) * (fz1 - fz0)
a_fan = hole_area(fan_pts)
side_psu, side_board = side_walls.board_vent_points()
a_ps, a_bs = hole_area(side_psu), hole_area(side_board)
top_board, top_gpu = lid.vent_points()
a_tb, a_tg = hole_area(top_board), hole_area(top_gpu)
a_rd = hole_area(rear_d15)
a_rg = hole_area(rear_gpu)
g = P.GPU_OPEN
a_open = (g["y1"] - g["y0"]) * (g["z1"] - g["z0"]) * 0.5   # Slotblech ~50 % offen
fan140 = math.pi * (70 ** 2 - 22 ** 2)
fan95 = math.pi * (47.5 ** 2 - 14 ** 2)
front_board, front_gpu, _ = panels.front_vent_points()
a_fb, a_fg = hole_area(front_board), hole_area(front_gpu)
lines = [
    f"Wabenfeld offen (theoretisch): {hex_ratio*100:.1f} %",
    "Zuluft:",
    f"  Front Board-Kammer    {a_fb/100:7.0f} cm²  (gerade vor dem CPU-Kühler)",
    f"  Sockelring            {a_pl/100:7.0f} cm²  (Engstelle der Bodenzuluft)",
    f"  Boden (über Sockel)   {a_fl/100:7.0f} cm²",
    f"  Seitenwand GPU        {a_gs/100:7.0f} cm²  (vor der Karte {a_fan/gs_field*100:.1f} % offen)",
    "Abluft:",
    f"  Rückwand Board-Kammer {a_rd/100:7.0f} cm²  (1x 140-mm-Lüfter frei: {fan140/100:.0f} cm²)",
    f"  Deckel Board-Kammer   {a_tb/100:7.0f} cm²",
    f"  Seitenwand Netzteil   {a_ps/100:7.0f} cm²  (hinter dem Netzteil)",
    f"  Deckel GPU-Kammer     {a_tg/100:7.0f} cm²",
    f"  Rückwand GPU-Kammer   {a_rg/100:7.0f} cm²  + Slotblech ~{a_open/100:.0f} cm²",
    f"  Front GPU-Kammer      {a_fg/100:7.0f} cm²",
    "Ohne feste Richtung (nicht in den Summen):",
    f"  Seitenwand Board-Kammer {a_bs/100:5.0f} cm²  (neben Kühler und Board)",
    f"Summen: Zuluft {(min(a_pl, a_fl) + a_gs + a_fb)/100:.0f} cm², "
    f"Abluft {(a_rd + a_tb + a_ps + a_tg + a_rg + a_open + a_fg)/100:.0f} cm²",
    f"Vergleich: 3x 95-mm-GPU-Lüfter ~{3*fan95/100:.0f} cm², 2x 140 mm D15 ~{2*fan140/100:.0f} cm²",
]
for line in lines:
    log("  " + line)
if a_fan / gs_field < 0.40:
    warnings.append("GPU-Seitenwand unter 40 % offen")

# --------------------------------------------------------------------------
log("\n== Maße ==")
for k, val in P.summary().items():
    log(f"  {k}: {val}")
r_sq, r_bend = dummies.riser_length()
log(f"  Riser-Flachband Stecker -> Sockel: {r_sq:.0f} mm eckig, ~{r_bend:.0f} mm mit Biegeradien")
if r_bend > 250:
    warnings.append(f"Riser-Bahn {r_bend:.0f} mm: 250-mm-Riser reicht nicht")
if P.COOLER_AIR < 3:
    errors.append(f"Luft über dem Kühler nur {P.COOLER_AIR:.1f} mm")
if P.GPU_SLOTS == 4 and P.BRACKET_SLOT_Y0 < P.FLAT_Y0:
    warnings.append("4-Slot-Öffnung reicht in den Eckbogen der Rückwand (siehe README)")
if P.GPU["T"] > P.GPU_THICK_MAX:
    errors.append("GPU dicker als die Kammer")

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
