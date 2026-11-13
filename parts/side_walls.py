"""Seitenwände: laufen mit Viertelkreis um die Ecken bis zur Front/Rückwand.
Unten im Randfalz des Bodens, oben mit Magneten 10x3 im Deckel gehalten.
Links: Lochfeld vor den GPU-Lüftern. Rechts: Lochfeld vor dem Netzteil."""
import params as P
from parts.common import (Spec, box, rrect_prism, wedge_x, hex_grid, holes_y, cyl_z, fuse_all,
                          cut_all, split_with_flanges, envelope_case, BIG)

H = P.INNER_H


def ring():
    outer = rrect_prism(P.OUT_X0, P.OUT_X1, P.OUT_Y0, P.OUT_Y1, P.CORNER_R, 0, H)
    inner = rrect_prism(0, P.INNER_L, 0, P.INNER_W, P.CORNER_RI, -1, H + 1)
    return outer.cut(inner)


SIDE_RIB_Z = [(P.RIM_H + 0.5, 24.0), (186.0, H - 0.5)]   # kurze Flanschpaare oben/unten


def seam_keep():
    k = [(P.SPLIT_X - 1.5, P.SPLIT_X + 1.5, -999, 999)]
    k += [(P.SPLIT_X - P.FLANGE_T - 1, P.SPLIT_X + P.FLANGE_T + 1, z0 - 1, z1 + 1)
          for (z0, z1) in SIDE_RIB_Z]
    return k


def gpu_vent_points():
    v = P.GPU_SIDE_VENT
    return hex_grid(v["x0"], v["x1"], v["z0"], v["z1"], seam_keep(), pitch=P.GPU_SIDE_PITCH)


def psu_vent_points():
    v = P.PSU_VENT
    return hex_grid(v["x0"], v["x1"], v["z0"], v["z1"], seam_keep())


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

    gpts = gpu_vent_points()
    left = cut_all(left, holes_y(gpts, P.OUT_Y0 - 1, 1))
    ppts = psu_vent_points()
    right = cut_all(right, holes_y(ppts, P.INNER_W - 1, P.OUT_Y1 + 1))

    out = []
    col = (0.70, 0.71, 0.74)
    for side, shape in (("L", left), ("R", right)):
        adds, cuts = [], []
        for x in P.MAGNET_X:
            b, p = magnet_boss(x, side)
            adds.append(b)
            cuts.append(p)
        shape = cut_all(fuse_all([shape] + adds), cuts)
        if side == "L":
            ry0, ry1, yb = -1.0, P.FLANGE_D, P.FLANGE_D / 2
        else:
            ry0, ry1, yb = P.INNER_W - P.FLANGE_D, P.INNER_W + 1.0, P.INNER_W - P.FLANGE_D / 2
        ribs = [(ry0, ry1, z0, z1) for (z0, z1) in SIDE_RIB_Z]
        bolts = [(yb, (z0 + z1) / 2) for (z0, z1) in SIDE_RIB_Z]
        a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts, envelope_case())
        name = "seite_links" if side == "L" else "seite_rechts"
        ey = -130 if side == "L" else 130
        out.append(Spec(name + "_vorn", a, col, explode=(-25, ey, 0)))
        out.append(Spec(name + "_hinten", b, col, explode=(25, ey, 0)))
    return out, (len(gpts), len(ppts))
