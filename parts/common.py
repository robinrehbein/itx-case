"""Geometrie-Helfer (FreeCAD Part API)."""
import math

import FreeCAD as App
import Part

import params as P

V = App.Vector
BIG = 5000.0
VGROOVE_LOG = []   # (Teil-x, Kanten, Methode) für den Bericht


class Spec:
    """Ein druckbares Teil bzw. eine Dummy-Komponente in Montagelage."""

    def __init__(self, name, shape, color=(0.85, 0.85, 0.85), group="case",
                 print_rot=None, explode=(0, 0, 0), printable=True, minutes=None):
        self.name = name
        self.shape = shape
        self.color = color
        self.group = group
        # Liste von (Achse, Winkel) für die Druckorientierung
        self.print_rot = print_rot or []
        self.explode = explode
        self.printable = printable
        self.minutes = minutes


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl_x(y, z, x0, x1, r):
    return Part.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))


def cyl_y(x, z, y0, y1, r):
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def cyl_z(x, y, z0, z1, r):
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))


def rrect_wire(x0, x1, y0, y1, r, z):
    r = min(r, (x1 - x0) / 2 - 1e-3, (y1 - y0) / 2 - 1e-3)
    if r <= 0.01:
        pts = [V(x0, y0, z), V(x1, y0, z), V(x1, y1, z), V(x0, y1, z), V(x0, y0, z)]
        return Part.makePolygon(pts)
    s = math.sqrt(0.5)
    e = []
    e.append(Part.LineSegment(V(x0 + r, y0, z), V(x1 - r, y0, z)).toShape())
    e.append(Part.Arc(V(x1 - r, y0, z), V(x1 - r + r * s, y0 + r - r * s, z), V(x1, y0 + r, z)).toShape())
    e.append(Part.LineSegment(V(x1, y0 + r, z), V(x1, y1 - r, z)).toShape())
    e.append(Part.Arc(V(x1, y1 - r, z), V(x1 - r + r * s, y1 - r + r * s, z), V(x1 - r, y1, z)).toShape())
    e.append(Part.LineSegment(V(x1 - r, y1, z), V(x0 + r, y1, z)).toShape())
    e.append(Part.Arc(V(x0 + r, y1, z), V(x0 + r - r * s, y1 - r + r * s, z), V(x0, y1 - r, z)).toShape())
    e.append(Part.LineSegment(V(x0, y1 - r, z), V(x0, y0 + r, z)).toShape())
    e.append(Part.Arc(V(x0, y0 + r, z), V(x0 + r - r * s, y0 + r - r * s, z), V(x0 + r, y0, z)).toShape())
    return Part.Wire(e)


def rrect_prism(x0, x1, y0, y1, r, z0, z1):
    return Part.Face(rrect_wire(x0, x1, y0, y1, r, z0)).extrude(V(0, 0, z1 - z0))


def rrect_x(x0, x1, y0, y1, z0, z1, r):
    """Abgerundetes Rechteck in der y-z-Ebene, extrudiert entlang x (für Ausschnitte)."""
    s = rrect_prism(y0, y1, z0, z1, r, 0, x1 - x0)
    # (y,z,0..h) -> (x,y,z)
    m = App.Matrix(0, 0, 1, x0,
                   1, 0, 0, 0,
                   0, 1, 0, 0,
                   0, 0, 0, 1)
    return s.transformGeometry(m)


def rrect_y(x0, x1, z0, z1, y0, y1, r):
    """Abgerundetes Rechteck in der x-z-Ebene, extrudiert entlang y."""
    s = rrect_prism(x0, x1, z0, z1, r, 0, y1 - y0)
    s.rotate(V(0, 0, 0), V(1, 0, 0), 90)   # (a,b,c) -> (a,-c,b)
    s.translate(V(0, y1, 0))
    return s


def wedge_x(x0, x1, pts_yz):
    """Prisma mit Polygon-Querschnitt (y,z), extrudiert entlang x."""
    poly = Part.makePolygon([V(x0, y, z) for (y, z) in pts_yz] + [V(x0, pts_yz[0][0], pts_yz[0][1])])
    return Part.Face(poly).extrude(V(x1 - x0, 0, 0))


def wedge_y(y0, y1, pts_xz):
    poly = Part.makePolygon([V(x, y0, z) for (x, z) in pts_xz] + [V(pts_xz[0][0], y0, pts_xz[0][1])])
    return Part.Face(poly).extrude(V(0, y1 - y0, 0))


def hex_prism_x(y, z, x0, x1, af):
    r = af / math.sqrt(3)
    pts = [V(x0, y + r * math.cos(math.radians(a)), z + r * math.sin(math.radians(a)))
           for a in range(0, 360, 60)]
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(V(x1 - x0, 0, 0))


def fuse_all(shapes):
    shapes = [s for s in shapes if s is not None]
    if not shapes:
        return None
    if len(shapes) == 1:
        return shapes[0]
    return shapes[0].fuse(shapes[1:]).removeSplitter()


def cut_all(shape, tools):
    tools = [t for t in tools if t is not None]
    if not tools:
        return shape
    return shape.cut(tools)


def place(shape):
    """Blockkörper (x=u, y=v, z=w) -> Gehäusekoordinaten (siehe params.to_case)."""
    if P.LYING or shape is None:
        return shape
    s = shape.copy()
    s.rotate(V(0, 0, 0), V(1, 0, 0), 90)     # (u, v, w) -> (u, -w, v)
    s.translate(V(0, P.Y_BASE, 0))
    return s


# Druckorientierung eines Blockteils im Gehäuse: erst zurück in den Block drehen
PLACE_UNDO = [] if P.LYING else [((1, 0, 0), -90)]


def solid(shape):
    if shape.ShapeType == "Solid":
        return shape
    sols = shape.Solids
    if len(sols) == 1:
        return sols[0]
    return shape


# --------------------------------------------------------------------------
# Lochfelder
# --------------------------------------------------------------------------
def _in_rrect(u, v, u0, u1, v0, v1, r):
    if not (u0 - 1e-6 <= u <= u1 + 1e-6 and v0 - 1e-6 <= v <= v1 + 1e-6):
        return False
    r = min(r, (u1 - u0) / 2, (v1 - v0) / 2)
    if r <= 0:
        return True
    cu = min(max(u, u0 + r), u1 - r)
    cv = min(max(v, v0 + r), v1 - r)
    return (u - cu) ** 2 + (v - cv) ** 2 <= r * r + 1e-6


def _hex_core(a0, a1, b0, b1, p, anchor=None, odd=False):
    """Wabenraster: Linien im Abstand p*sqrt(3)/2 entlang a, darauf Löcher im Abstand p
    entlang b, jede zweite Linie um p/2 versetzt. anchor: eine Linie liegt genau auf a."""
    da = p * math.sqrt(3) / 2
    if anchor is None:
        n = int((a1 - a0) / da + 1e-6) + 1
        k0, base = 0, a0 + ((a1 - a0) - (n - 1) * da) / 2
    else:
        k0, base = -int(math.floor((anchor - a0) / da + 1e-6)), anchor
    nb = int((b1 - b0) / p + 1e-6) + 1
    bstart = b0 + ((b1 - b0) - (nb - 1) * p) / 2
    out = []
    k = k0
    while base + k * da <= a1 + 1e-6:
        b = bstart + (p / 2 if (k + (1 if odd else 0)) % 2 else 0.0)
        while b <= b1 + 1e-6:
            out.append((base + k * da, b))
            b += p
        k += 1
    return out


def hex_grid(u0, u1, v0, v1, keep=(), d=None, pitch=None, edge=None, corner_r=0.0,
             col_at=None, col_odd=False):
    """Mittelpunkte eines Wabenrasters, symmetrisch im Feld (sauberer Rand).
    keep: Rechtecke (u0,u1,v0,v1), die frei bleiben. corner_r: Eckradius des Feldes.
    col_at=None: Lochreihen entlang u, in v versetzt.
    col_at=u:    Lochspalten entlang v, eine Spalte genau auf u. So schneidet eine Trennfuge
                 bei u nur Lochmitten – das Feld läuft ohne Lücke über die Fuge."""
    d = d or P.VENT_D
    pitch = pitch or P.VENT_PITCH
    edge = P.VENT_EDGE if edge is None else edge
    r = d / 2
    m = r + edge
    ua, ub = u0 + m, u1 - m
    va, vb = v0 + m, v1 - m
    if ub < ua or vb < va:
        return []
    if col_at is None:
        raw = [(u, v) for (v, u) in _hex_core(va, vb, ua, ub, pitch)]
    else:
        raw = _hex_core(ua, ub, va, vb, pitch, anchor=col_at, odd=col_odd)
    rc = max(corner_r - m, 0.0)
    pts = []
    for (u, v) in raw:
        if not _in_rrect(u, v, ua, ub, va, vb, rc):
            continue
        if any(a0 - m < u < a1 + m and b0 - m < v < b1 + m for (a0, a1, b0, b1) in keep):
            continue
        pts.append((u, v))
    return pts


def holes_z(pts, z0, z1, d=None):
    r = (d or P.VENT_D) / 2
    return [cyl_z(u, v, z0, z1, r) for (u, v) in pts]


def holes_y(pts, y0, y1, d=None):
    """pts = (x, z)"""
    r = (d or P.VENT_D) / 2
    return [cyl_y(u, v, y0, y1, r) for (u, v) in pts]


def holes_x(pts, x0, x1, d=None):
    """pts = (y, z)"""
    r = (d or P.VENT_D) / 2
    return [cyl_x(u, v, x0, x1, r) for (u, v) in pts]


def split_blind(pts, rects=(), discs=(), d=None):
    """Teilt Lochmitten in (durchgehend, blind). Blind ist jedes Loch, das eine Zone berührt:
    rects = (u0, u1, v0, v1), discs = (u, v, Radius). Hinter diesen Löchern sitzt ein Flansch
    oder Dom; sie werden als Sackloch geschnitten, damit das Feld außen geschlossen aussieht."""
    r = (d or P.VENT_D) / 2

    def hit(u, v):
        if any(a0 - r < u < a1 + r and b0 - r < v < b1 + r for (a0, a1, b0, b1) in rects):
            return True
        return any((u - cu) ** 2 + (v - cv) ** 2 < (rd + r) ** 2 for (cu, cv, rd) in discs)

    return [q for q in pts if not hit(*q)], [q for q in pts if hit(*q)]


def hole_area(pts, d=None):
    d = d or P.VENT_D
    return len(pts) * math.pi * d * d / 4


# --------------------------------------------------------------------------
# Befestigung
# --------------------------------------------------------------------------
def insert_down(x, y, ztop):
    """Bohrung für Einschmelzmutter von oben."""
    return cyl_z(x, y, ztop - P.INSERT_DEPTH, ztop + 0.01, P.INSERT_D / 2)


def insert_up(x, y, zbot):
    return cyl_z(x, y, zbot - 0.01, zbot + P.INSERT_DEPTH, P.INSERT_D / 2)


def dome_floor(x, y, h=None):
    h = h or P.DOME_H
    return cyl_z(x, y, 0, h, P.DOME_D / 2), insert_down(x, y, h)


def dome_lid(x, y, h=None):
    h = h or P.DOME_H
    return cyl_z(x, y, P.INNER_H - h, P.INNER_H, P.DOME_D / 2), insert_up(x, y, P.INNER_H - h)


# --------------------------------------------------------------------------
# Trennstellen
# --------------------------------------------------------------------------
def envelope_case():
    """Außenhülle für die V-Nut-Erkennung (Boden, Wände, Deckel)."""
    return rrect_prism(P.OUT_X0, P.OUT_X1, P.OUT_Y0, P.OUT_Y1, P.CORNER_R,
                       -P.T_FLOOR, P.INNER_H + P.T_LID)


def envelope_plinth():
    i = P.PLINTH_INSET
    return rrect_prism(P.OUT_X0 + i, P.OUT_X1 - i, P.OUT_Y0 + i, P.OUT_Y1 - i, P.PLINTH_R,
                       -P.T_FLOOR - P.PLINTH_H, -P.T_FLOOR)


def _on_envelope(pt, env_faces, tol=1e-3):
    v = Part.Vertex(pt)
    for f in env_faces:
        if f.distToShape(v)[0] < tol:
            return True
    return False


def vgroove(piece, xs, envelope, size=None):
    """Außenkanten an der Fuge anfasen -> beide Hälften ergeben eine V-Nut."""
    size = size or P.VGROOVE
    piece = solid(piece)
    env_faces = envelope.Faces
    edges = []
    for e in piece.Edges:
        bb = e.BoundBox
        if abs(bb.XMin - xs) > 1e-4 or abs(bb.XMax - xs) > 1e-4:
            continue
        p = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter))
        if _on_envelope(p, env_faces):
            edges.append(e)
    side = "A" if piece.BoundBox.XMin < xs - 1e-3 else "B"
    if not edges:
        VGROOVE_LOG.append((side, 0, "keine Außenkante"))
        return piece
    try:
        res = piece.makeChamfer(size, edges)
        if res.isValid() and res.Volume > 0:
            VGROOVE_LOG.append((side, len(edges), "V-Fase"))
            return res
    except Exception:
        pass
    # Rückfall: rechteckige Schattenfuge
    inner = envelope.makeOffsetShape(-size, 0.01)
    notch = envelope.cut(inner).common(box(xs - size, xs + size, -BIG, BIG, -BIG, BIG))
    VGROOVE_LOG.append((side, len(edges), "Rechteckfuge (Rückfall)"))
    return solid(piece.cut(notch))


def split_with_flanges(shape, xs, ribs, bolts, envelope=None, side_b_nut=True):
    """Teilt bei x = xs. ribs: Querschnitte (y0,y1,z0,z1) der Flansche oder Funktionen
    f(x0, x1) -> Körper, bolts: (y,z).
    Gibt (A, B) zurück, A = vorn (x < xs)."""
    a = solid(shape.common(box(-BIG, xs, -BIG, BIG, -BIG, BIG)))
    b = solid(shape.common(box(xs, BIG, -BIG, BIG, -BIG, BIG)))
    if envelope is not None:
        a = vgroove(a, xs, envelope)
        b = vgroove(b, xs, envelope)
    t = P.FLANGE_T

    def rib(r, x0, x1):
        return r(x0, x1) if callable(r) else box(x0, x1, *r)

    rib_a = [rib(r, xs - t, xs) for r in ribs]
    rib_b = [rib(r, xs, xs + t) for r in ribs]
    a = solid(fuse_all([a] + rib_a))
    b = solid(fuse_all([b] + rib_b))
    cut_a, cut_b = [], []
    for (y, z) in bolts:
        cut_a.append(cyl_x(y, z, xs - t - 1, xs + 0.01, P.M3_CLEAR / 2))
        cut_b.append(cyl_x(y, z, xs - 0.01, xs + t + 1, P.M3_CLEAR / 2))
        if side_b_nut:
            cut_b.append(hex_prism_x(y, z, xs + t - P.M3_NUT_T, xs + t + 0.1, P.M3_NUT_AF))
    a = solid(cut_all(a, cut_a))
    b = solid(cut_all(b, cut_b))
    return a, b


def cut_holes_split(a, b, xs, pts_x, tools, r=None):
    """Löcher erst nach dem Teilen schneiden (V-Nut bleibt eine saubere Fase).
    Löcher auf der Fuge werden zu Halblöchern in beiden Hälften."""
    r = (P.VENT_D / 2) if r is None else r
    ta = [t for x, t in zip(pts_x, tools) if x - r < xs]
    tb = [t for x, t in zip(pts_x, tools) if x + r > xs]
    return solid(cut_all(a, ta)), solid(cut_all(b, tb))
