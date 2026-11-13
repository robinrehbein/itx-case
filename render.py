"""PNG-Ansichten der Montage. Läuft in der FreeCAD-GUI (freecadcmd kann nicht rendern):

    /Applications/FreeCAD.app/Contents/MacOS/FreeCAD render.py

Öffnet out/assembly.FCStd, speichert out/png/*.png und beendet FreeCAD wieder.
Mit RENDER_KEEP_OPEN=1 bleibt FreeCAD offen (Explosionsansicht aktiv).
"""
import os

import FreeCAD as App
import FreeCADGui as Gui

ROOT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
OUT = os.path.join(ROOT, "out")
PNG = os.path.join(OUT, "png")
os.makedirs(PNG, exist_ok=True)

doc = App.openDocument(os.path.join(OUT, "assembly.FCStd"))
gdoc = Gui.getDocument(doc.Name)
Gui.ActiveDocument = gdoc
parts = [o for o in doc.Objects if o.TypeId == "Part::Feature"]
base = {o.Name: o.Placement.copy() for o in parts}

for o in parts:
    vo = o.ViewObject
    vo.ShapeColor = o.Farbe[:3]
    vo.LineColor = (0.25, 0.25, 0.25)
    vo.LineWidth = 1.0
    if o.Gruppe == "dummy":
        vo.Transparency = 15


def show(pred):
    for o in parts:
        o.ViewObject.Visibility = bool(pred(o))


def reset():
    for o in parts:
        o.Placement = base[o.Name]


def explode(scale=1.0):
    for o in parts:
        e = o.Explode
        o.Placement = App.Placement(base[o.Name].Base + App.Vector(e.x, e.y, e.z) * scale,
                                    base[o.Name].Rotation)


# Blickrichtungen in Gehäusekoordinaten (x vorn->hinten, y links->rechts, z oben)
DIRS = {
    "iso": (1, 1, -0.8),        # von vorn links oben
    "iso_rear": (-1, 1, -0.8),  # von hinten links oben
    "iso_right": (1, -1, -0.8), # von vorn rechts oben
    "left": (0, 1, 0),          # auf die linke Seite (GPU-Kammer)
    "right": (0, -1, 0),        # auf die rechte Seite (Board-Kammer)
    "top": (0, 0, -1),
    "front": (1, 0, 0),
    "rear": (-1, 0, 0),
    "iso_low": (1, 1, 0.9),     # von vorn links unten (Sockel und Boden)
}


def look(d):
    """Kamera blickt in Richtung d, z bleibt oben."""
    d = App.Vector(*d).normalize()
    zc = d.negative()
    up = App.Vector(0, 1, 0) if abs(d.z) > 0.99 else App.Vector(0, 0, 1)
    yc = (up - zc * up.dot(zc)).normalize()
    xc = yc.cross(zc)
    m = App.Matrix(xc.x, yc.x, zc.x, 0,
                   xc.y, yc.y, zc.y, 0,
                   xc.z, yc.z, zc.z, 0,
                   0, 0, 0, 1)
    Gui.ActiveDocument.ActiveView.setCameraOrientation(App.Rotation(m).Q)


def snap(name, view="iso", w=1800, h=1200):
    v = Gui.ActiveDocument.ActiveView
    look(DIRS[view])
    v.fitAll()
    Gui.updateGui()
    v.saveImage(os.path.join(PNG, name + ".png"), w, h, "White")


def is_open_hidden(o):
    n = o.Name
    return n.startswith("deckel") or n.startswith("seite")


v = Gui.ActiveDocument.ActiveView
v.setAxisCross(False)

# 1 Gesamtansicht
reset()
show(lambda o: o.Gruppe != "dummy")
snap("01_gesamt_vorn")   # erster Aufruf wärmt die Ansicht an
snap("01_gesamt_vorn")
snap("02_gesamt_hinten", "iso_rear")
snap("02b_seite_links", "left")
snap("02c_rueckwand", "rear")
snap("02d_front", "front")
snap("02e_unten", "iso_low")

# 2 Kammern offen (Deckel und Seitenwände ausgeblendet, Komponenten sichtbar)
show(lambda o: not is_open_hidden(o))
snap("03_offen_iso")
snap("04_offen_gpu_kammer", "left")
snap("05_offen_board_kammer", "right")
snap("05b_offen_board_iso", "iso_right")
snap("06_offen_oben", "top")

# 3 Explosionsansicht
show(lambda o: True)
explode(1.0)
snap("07_explosion")
show(lambda o: o.Gruppe != "dummy")
snap("08_explosion_ohne_komponenten")

if os.environ.get("RENDER_KEEP_OPEN") != "1":
    App.closeDocument(doc.Name)
    os._exit(0)
