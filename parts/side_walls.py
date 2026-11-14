"""Seitenwände: laufen mit Viertelkreis um die Ecken bis zur Front/Rückwand.
Unten im Randfalz des Bodens, oben mit Magneten 10x3 im Deckel gehalten.
Beide Wände tragen das gleiche Lochfeld, auf gleicher Höhe wie Front und Rückwand.
Bei A sitzt das linke Feld vor den GPU-Lüftern."""
import params as P
from parts.common import (Spec, box, rrect_prism, wedge_x, hex_grid, holes_y, split_blind, cyl_z,
                          fuse_all,
                          cut_all, split_with_flanges, envelope_case, cut_holes_split, BIG)

H = P.INNER_H


def ring():
    outer = rrect_prism(P.OUT_X0, P.OUT_X1, P.OUT_Y0, P.OUT_Y1, P.CORNER_R, 0, H)
    inner = rrect_prism(0, P.INNER_L, 0, P.INNER_W, P.CORNER_RI, -1, H + 1)
    return outer.cut(inner)


# kurze Flanschpaare unter und über dem Lochfeld (das Feld läuft über die Fuge durch)
SIDE_RIB_Z = [(P.RIM_H + 0.5, 18.0), (H - 15.0, H - 0.5)]


def side_ribs(side):
    """Flansche stützenfrei für den stehenden Druck: unten bis aufs Bett (neben dem
    Randfalz), oben mit 45°-Keil darunter."""
    d = P.FLANGE_D
    (lz0, lz1), (uz0, uz1) = SIDE_RIB_Z
    if side == "L":
        yw, yi, yr = -1.0, d, P.RIM_W + 0.5          # Wand, innen, neben dem Falz
    else:
        yw, yi, yr = P.INNER_W + 1.0, P.INNER_W - d, P.INNER_W - P.RIM_W - 0.5
    ya, yb = sorted((yw, yi))
    yra, yrb = sorted((yr, yi))

    def lower(x0, x1):
        return box(x0, x1, ya, yb, lz0, lz1).fuse(box(x0, x1, yra, yrb, 0.0, lz1))

    def upper(x0, x1):
        w = wedge_x(x0, x1, [(yw, uz0 - d - 1), (yw, uz0), (yi, uz0)])
        return box(x0, x1, ya, yb, uz0, uz1).fuse(w)

    return [lower, upper]


def blind_zones():
    """Zonen (x0, x1, z0, z1), hinter denen innen Material an der Wand sitzt: Fugenflansche
    mit Stützkeil und die Magnetnasen. Löcher dort werden Sacklöcher."""
    d = P.FLANGE_D
    (lz0, lz1), (uz0, uz1) = SIDE_RIB_Z
    zones = [(P.SPLIT_X - P.FLANGE_T, P.SPLIT_X + P.FLANGE_T, 0.0, lz1),
             (P.SPLIT_X - P.FLANGE_T, P.SPLIT_X + P.FLANGE_T, uz0 - d - 1, uz1)]
    zb = H - P.MAGNET_BOSS_H - P.MAGNET_BOSS_DEPTH + 1.0   # hier tritt der Keil aus der Wand
    zones += [(x - 8.0, x + 8.0, zb, H) for x in P.MAGNET_X]
    return zones


def _field(v):
    pts = hex_grid(v["x0"], v["x1"], v["z0"], v["z1"], corner_r=v["r"], col_at=P.SPLIT_X)
    return split_blind(pts, blind_zones())


def vent_sets():
    """(durchgehend, blind); beide Wände haben dasselbe Feld."""
    return _field(P.SIDE_VENT)


def vent_points():
    return vent_sets()[0]


def magnet_boss(x, side):
    d, h = P.MAGNET_BOSS_DEPTH, P.MAGNET_BOSS_H
    zb = H - h
    if side == "L":
        y0, y1 = -1.0, d
        wedge = wedge_x(x - 8, x + 8, [(-1.0, zb - d), (-1.0, zb), (d, zb)])
        ym = P.OUT_Y0 + P.MAGNET_FROM_OUTER
    else:
        y0, y1 = P.INNER_W - d, P.INNER_W + 1.0
        wedge = wedge_x(x - 8, x + 8, [(P.INNER_W + 1.0, zb - d), (P.INNER_W + 1.0, zb),
                                       (P.INNER_W - d, zb)])
        ym = P.OUT_Y1 - P.MAGNET_FROM_OUTER
    boss = box(x - 8, x + 8, y0, y1, zb, H).fuse(wedge)
    pocket = cyl_z(x, ym, H - P.MAGNET_H, H + 0.01, P.MAGNET_D / 2)
    return boss, pocket


def build():
    r = ring()
    left = r.common(box(-BIG, BIG, -BIG, P.FLAT_Y0, -BIG, BIG))
    right = r.common(box(-BIG, BIG, P.FLAT_Y1, BIG, -BIG, BIG))

    sk = P.VENT_BLIND_SKIN
    t, bl = vent_sets()
    vents = {"L": (t + bl, holes_y(t, P.OUT_Y0 - 1, 0.5) + holes_y(bl, P.OUT_Y0 - 1, -sk)),
             "R": (t + bl, holes_y(t, P.INNER_W - 0.5, P.OUT_Y1 + 1)
                   + holes_y(bl, P.INNER_W + sk, P.OUT_Y1 + 1))}

    out = []
    col = (0.70, 0.71, 0.74)
    for side, shape in (("L", left), ("R", right)):
        adds, cuts = [], []
        for x in P.MAGNET_X:
            b, p = magnet_boss(x, side)
            adds.append(b)
            cuts.append(p)
        shape = cut_all(fuse_all([shape] + adds), cuts)
        yb = P.FLANGE_D / 2 if side == "L" else P.INNER_W - P.FLANGE_D / 2
        ribs = side_ribs(side)
        bolts = [(yb, (z0 + z1) / 2) for (z0, z1) in SIDE_RIB_Z]
        a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts, envelope_case())
        pts, tools = vents[side]
        a, b = cut_holes_split(a, b, P.SPLIT_X, [q[0] for q in pts], tools)
        name = "seite_links" if side == "L" else "seite_rechts"
        ey = -130 if side == "L" else 130
        out.append(Spec(name + "_vorn", a, col, explode=(-25, ey, 0)))
        out.append(Spec(name + "_hinten", b, col, explode=(25, ey, 0)))
    return out, len(t)
