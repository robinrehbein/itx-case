"""Sockel wie beim Mac Studio: eingerückter Ring, rundum durchgehend gelocht (auch in den
Ecken und über die Trennfuge), Bodenlippe für Gummifüße. Schraubpfosten und Fugenflansche
stehen frei hinter dem Ring, damit kein Loch verdeckt ist."""
import math

import Part
from FreeCAD import Vector as V

import params as P
from parts.common import (Spec, box, rrect_prism, hex_grid, holes_x, holes_y, cyl_z,
                          fuse_all, cut_all, split_with_flanges, envelope_plinth,
                          cut_holes_split, solid)
from parts.floor import plinth_screw_positions

Z0 = -P.T_FLOOR - P.PLINTH_H
Z1 = -P.T_FLOOR
ZL = Z0 + P.PLINTH_LIP_T
D = P.PLINTH_VENT_D


def outline(off):
    i = P.PLINTH_INSET + off
    return (P.OUT_X0 + i, P.OUT_X1 - i, P.OUT_Y0 + i, P.OUT_Y1 - i, max(P.PLINTH_R - off, 0.5))


def _grid(u0, u1, anchor):
    # Spalte auf der Fuge ist eine Ein-Loch-Spalte (mehr Material am Stoß)
    return hex_grid(u0, u1, ZL, Z1, d=D, pitch=P.PLINTH_VENT_PITCH, edge=P.PLINTH_VENT_EDGE,
                    col_at=anchor, col_odd=True)


def vent_sets():
    x0, x1, y0, y1, r = outline(0)
    sides = _grid(x0 + r, x1 - r, P.SPLIT_X)
    ends = _grid(y0 + r, y1 - r, (y0 + y1) / 2)
    return sides, ends


def corner_levels():
    """Lochhöhen in den Eckbögen: wie eine Zwei-Loch-Spalte der geraden Seiten."""
    return sorted({round(z, 4) for (_, z) in vent_sets()[0]})[::2]


def corner_holes():
    x0, x1, y0, y1, r = outline(0)
    tools = []
    for (cx, sx) in ((x0 + r, -1), (x1 - r, 1)):
        for (cy, sy) in ((y0 + r, -1), (y1 - r, 1)):
            dv = V(sx, sy, 0).normalize()
            for z in corner_levels():
                tools.append((cx, Part.makeCylinder(D / 2, r + 0.5, V(cx, cy, z) + dv * 1.0, dv)))
    return tools


def vent_area():
    sides, ends = vent_sets()
    n = 2 * len(sides) + 2 * len(ends) + 4 * len(corner_levels())
    return n * math.pi * D * D / 4


def feet():
    """C: vier Füße statt Sockelring, von unten in den Boden geschraubt. Der Spalt unter dem
    Boden ist rundum offen (Zuluft der Karte)."""
    out = []
    z0, z1 = Z1 - P.FOOT_H, Z1
    for i, (x, y) in enumerate(plinth_screw_positions()):
        body = cyl_z(x, y, z0, z1, P.FOOT_D / 2)
        body = body.makeFillet(1.5, [e for e in body.Edges if abs(e.BoundBox.ZMin - z0) < 1e-6])
        hole = cyl_z(x, y, z0 - 1, z1 + 1, P.M3_CLEAR / 2).fuse(
            cyl_z(x, y, z0 - 1, z1 - 4.0, 3.3))
        out.append(Spec(f"fuss_{i + 1}", solid(body.cut(hole)), (0.30, 0.30, 0.32),
                        explode=(0, 0, -100)))
    gap = 2 * (P.OUT_L + P.OUT_W) * P.FOOT_H - 4 * P.FOOT_D * P.FOOT_H
    return out, gap


def build():
    if P.FEET:
        return feet()
    x0, x1, y0, y1, r = outline(0)
    t = P.PLINTH_T
    ring = rrect_prism(x0, x1, y0, y1, r, Z0, Z1).cut(
        rrect_prism(*outline(t)[:4], outline(t)[4], Z0 - 1, Z1 + 1))
    lip = rrect_prism(*outline(t)[:4], outline(t)[4], Z0, ZL).cut(
        rrect_prism(*outline(t + P.PLINTH_LIP_W)[:4], outline(t + P.PLINTH_LIP_W)[4],
                    Z0 - 1, ZL + 1))

    # Schraubpfosten: frei stehend, über eine Fußplatte auf Lippenhöhe mit dem Ring verbunden
    adds, hcuts = [], []
    rp = P.PLINTH_POST_D / 2
    for (x, y) in plinth_screw_positions():
        left = y < P.INNER_W / 2
        yw = y0 + t if left else y1 - t           # Innenfläche Ring
        ya, yb = sorted((yw - 0.5 if left else yw + 0.5, y))
        adds.append(box(x - rp - 3, x + rp + 3, ya, yb, Z0, ZL))
        adds.append(cyl_z(x, y, Z0, Z1, rp))
        hcuts.append(cyl_z(x, y, Z0 - 1, Z1 + 1, P.M3_CLEAR / 2))
        hcuts.append(cyl_z(x, y, Z0 - 1, Z1 - 4.0, 3.3))     # Schraubenkopf versenkt
    shape = cut_all(fuse_all([ring, lip] + adds), hcuts)

    # Fugenflansche: 4 mm hinter dem Ring, stehen auf einer Fußplatte auf dem Bett
    g, fd = P.PLINTH_FLANGE_GAP, P.FLANGE_D

    def rib(yw, sgn):
        ya, yb = sorted((yw + sgn * g, yw + sgn * (g + fd)))
        pa, pb = sorted((yw - sgn * 0.5, yw + sgn * (g + fd)))

        def f(xa, xb):
            lo = xa - 10.0 if xa < P.SPLIT_X - 1e-6 else xa
            hi = xb + 10.0 if xb > P.SPLIT_X + 1e-6 else xb
            return box(xa, xb, ya, yb, Z0, Z1).fuse(box(lo, hi, pa, pb, Z0, ZL))
        return f

    ribs = [rib(y0 + t, 1), rib(y1 - t, -1)]
    zc = (ZL + Z1) / 2
    bolts = [(y0 + t + g + fd / 2, zc), (y1 - t - g - fd / 2, zc)]
    a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts, envelope_plinth())

    sides, ends = vent_sets()
    xs_pts, tools = [], []
    for (ya, yb) in ((y0 - 1, y0 + t + 0.5), (y1 - t - 0.5, y1 + 1)):
        xs_pts += [q[0] for q in sides]
        tools += holes_y(sides, ya, yb, D)
    for (xa, xb) in ((x0 - 1, x0 + t + 0.5), (x1 - t - 0.5, x1 + 1)):
        xs_pts += [xa] * len(ends)
        tools += holes_x(ends, xa, xb, D)
    for (cx, tool) in corner_holes():
        xs_pts.append(cx)
        tools.append(tool)
    a, b = cut_holes_split(a, b, P.SPLIT_X, xs_pts, tools, D / 2)
    col = (0.30, 0.30, 0.32)
    return [Spec("sockel_vorn", a, col, explode=(-25, 0, -150)),
            Spec("sockel_hinten", b, col, explode=(25, 0, -150))], vent_area()
