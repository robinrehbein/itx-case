"""Sockel wie beim Mac Studio: eingerückter Ring, rundum gelocht, Bodenlippe für Gummifüße,
oben Laschen zum Verschrauben mit dem Boden (von unten, unsichtbar)."""
import params as P
from parts.common import (Spec, box, rrect_prism, wedge_x, hex_grid, holes_x, holes_y, cyl_z,
                          fuse_all, cut_all, split_with_flanges, envelope_plinth)
from parts.floor import plinth_screw_positions

Z0 = -P.T_FLOOR - P.PLINTH_H
Z1 = -P.T_FLOOR


def outline(off):
    i = P.PLINTH_INSET + off
    return (P.OUT_X0 + i, P.OUT_X1 - i, P.OUT_Y0 + i, P.OUT_Y1 - i, max(P.PLINTH_R - off, 0.5))


def vent_sets():
    x0, x1, y0, y1, r = outline(0)
    zl = Z0 + P.PLINTH_LIP_T
    seam = (P.SPLIT_X - 12, P.SPLIT_X + 12, -999, 999)
    tabs = [(x - 11, x + 11, -999, 999) for (x, _) in P.PLINTH_TABS]
    sides = hex_grid(x0 + r + 2, x1 - r - 2, zl, Z1, [seam] + tabs, edge=0.4)
    ends = hex_grid(y0 + r + 2, y1 - r - 2, zl, Z1, [], edge=0.4)
    return sides, ends


def build():
    x0, x1, y0, y1, r = outline(0)
    t = P.PLINTH_T
    ring = rrect_prism(x0, x1, y0, y1, r, Z0, Z1).cut(
        rrect_prism(*outline(t)[:4], outline(t)[4], Z0 - 1, Z1 + 1))
    lip = rrect_prism(*outline(t)[:4], outline(t)[4], Z0, Z0 + P.PLINTH_LIP_T).cut(
        rrect_prism(*outline(t + P.PLINTH_LIP_W)[:4], outline(t + P.PLINTH_LIP_W)[4],
                    Z0 - 1, Z0 + P.PLINTH_LIP_T + 1))
    sides, ends = vent_sets()
    cuts = holes_y(sides, y0 - 1, y0 + t + 1) + holes_y(sides, y1 - t - 1, y1 + 1) \
        + holes_x(ends, x0 - 1, x0 + t + 1) + holes_x(ends, x1 - t - 1, x1 + 1)
    shape = cut_all(ring.fuse(lip), cuts)

    adds, hcuts = [], []
    for (x, y) in plinth_screw_positions():
        left = y < P.INNER_W / 2
        yw = y0 + t if left else y1 - t           # Innenfläche Ring
        ya, yb = (yw - 1, y + 5) if left else (y - 5, yw + 1)
        adds.append(box(x - 7, x + 7, ya, yb, Z1 - 3, Z1))
        d = abs(yb - ya)
        if left:
            adds.append(wedge_x(x - 7, x + 7, [(yw - 1, Z1 - 3 - d), (yw - 1, Z1 - 3), (yb, Z1 - 3)]))
        else:
            adds.append(wedge_x(x - 7, x + 7, [(yw + 1, Z1 - 3 - d), (yw + 1, Z1 - 3), (ya, Z1 - 3)]))
        hcuts.append(cyl_z(x, y, Z0 - 1, Z1 + 1, P.M3_CLEAR / 2))
    clip = box(-1e4, 1e4, -1e4, 1e4, Z0 + P.PLINTH_LIP_T, Z1)
    adds = [a.common(clip) for a in adds]
    shape = cut_all(fuse_all([shape] + adds), hcuts)

    zr0, zr1 = Z0, Z1   # Flansche stehen auf dem Bett
    ribs = [(y0 + t - 1, y0 + t + P.FLANGE_D, zr0, zr1),
            (y1 - t - P.FLANGE_D, y1 - t + 1, zr0, zr1)]
    zc = (Z0 + P.PLINTH_LIP_T + Z1) / 2
    bolts = [(y0 + t + P.FLANGE_D / 2, zc), (y1 - t - P.FLANGE_D / 2, zc)]
    a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts, envelope_plinth())
    col = (0.30, 0.30, 0.32)
    return [Spec("sockel_vorn", a, col, explode=(-25, 0, -150)),
            Spec("sockel_hinten", b, col, explode=(25, 0, -150))], (sides, ends)
