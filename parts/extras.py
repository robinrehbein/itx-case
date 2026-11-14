"""Extra-Druckteile: Netzteil-Halter mit Klammer, GPU-Stütze, Kabelkamm, Passtest-Teile.
Netzteil-Halter und Klammer entstehen im Block und werden mit place() ins Gehäuse gestellt."""
import params as P
from FreeCAD import Vector as V
from parts.common import (Spec, box, cyl_x, cyl_y, cyl_z, rrect_x, fuse_all, cut_all,
                          insert_down, place, PLACE_UNDO)
from parts.floor import gpu_support_boss, standoff_positions
from parts.panels import rail_rect

B = P.LOW_BOSS_H
CT = P.CRADLE_T
G = 0.5      # Spiel rund um das Netzteil


def slot_z(x0, x1, y, z0, z1, r):
    """Langloch senkrecht (Achse z), entlang x."""
    return fuse_all([cyl_z(x0, y, z0, z1, r), cyl_z(x1, y, z0, z1, r),
                     box(x0, x1, y - r, y + r, z0, z1)])


# --------------------------------------------------------------------------
def _hook_boss():
    """Verstärkung an der Wand v0 des Halters für die Klammer (u, v0, v1)."""
    uc = (P.PSU_X0 + P.PSU_X1) / 2
    return uc, P.PSU_V0 - G - 10.0, P.PSU_V0 - G


def psu_holder():
    """Wanne unter dem hochkant stehenden Netzteil. Volle Wände an der blanken Seite (v0)
    und zum Kühler (u1); an der Lüfterseite (u0) und an den Anschlüssen (v1) nur Ecken."""
    x0, x1 = P.PSU_X0 - G, P.PSU_X1 + G
    y0, y1 = P.PSU_V0 - G, P.PSU_V1 + G
    w0, w1 = B, P.PSU_W0
    wt = w1 + P.CRADLE_H
    plate = box(x0 - CT, x1 + CT, y0 - CT, y1 + CT, w0, w1)
    adds = [plate,
            box(x0 - CT, x1 + CT, y0 - CT, y0, w0, wt),            # v0
            box(x1, x1 + CT, y0 - CT, y1 + CT, w0, wt)]            # u1
    for (ya, yb) in ((y0 - CT, y0 + 12), (y1 - 12, y1 + CT)):    # u0: nur Ecken
        adds.append(box(x0 - CT, x0, ya, yb, w0, wt))
    for (xa, xb) in ((x0 - CT, x0 + 10), (x1 - 10, x1 + CT)):    # v1: nur Ecken
        adds.append(box(xa, xb, y1, y1 + CT, w0, wt))
    cuts = []
    for (u, v) in P.PSU_BOSS:
        ya, yb = (v - 6, y0 - CT + 0.01) if v < y0 else (y1 + CT - 0.01, v + 6)
        adds.append(box(u - 6, u + 6, ya, yb, w0, w0 + 4))
        cuts.append(cyl_z(u, v, w0 - 1, w0 + 5, P.M3_CLEAR / 2))
    uc, hv0, hv1 = _hook_boss()
    adds.append(box(uc - 7, uc + 7, hv0, hv1, w0, wt))
    cuts.append(insert_down(uc, (hv0 + hv1) / 2 - 1.5, wt))
    # Bodenplatte offen unter der Mitte (Luft, Gewicht)
    cuts.append(box(x0 + 12, x1 - 12, y0 + 12, y1 - 12, w0 - 1, w1 + 1))
    shape = cut_all(fuse_all(adds), cuts)
    return Spec("netzteil_halter", place(shape), (0.25, 0.25, 0.27), group="extra",
                print_rot=list(PLACE_UNDO), explode=(0, 0, -30) if P.LAYOUT == "A" else (0, 30, 0))


def psu_clamp():
    """Klammer an der blanken Seite: Fuß auf dem Halter, Steg hoch, Lippe über das Netzteil."""
    uc, hv0, hv1 = _hook_boss()
    wt = P.PSU_W0 + P.CRADLE_H
    t = 4.0
    foot = box(uc - 7, uc + 7, hv0, hv1, wt, wt + 4)
    leg = box(uc - 7, uc + 7, hv1 - t, hv1, wt, P.PSU_W1 + 3)
    lip = box(uc - 7, uc + 7, hv1 - t, P.PSU_V0 + 20, P.PSU_W1 + 0.5, P.PSU_W1 + 3.5)
    hole = cyl_z(uc, (hv0 + hv1) / 2 - 1.5, wt - 1, wt + 5, P.M3_CLEAR / 2)
    shape = cut_all(fuse_all([foot, leg, lip]), [hole])
    return Spec("netzteil_klammer", place(shape), (0.25, 0.25, 0.27), group="extra",
                print_rot=list(PLACE_UNDO) + [((0, 1, 0), 90)],
                explode=(0, 0, 60) if P.LAYOUT == "A" else (0, 0, -60))


# --------------------------------------------------------------------------
def gpu_support():
    """Pfosten unter der Kartenvorderkante, Fuß mit Langloch zum Einstellen."""
    bx, by = gpu_support_boss()
    s = P.GPU_SUPPORT
    px = s["x"]
    foot = box(px - 6, bx + P.GPU_SUPPORT_ADJ + 6, by - 8, by + 8, B, B + 4)
    post = box(px - 6, px + 6, by - 8, by + 8, B, s["ztop"])
    cut = slot_z(bx - P.GPU_SUPPORT_ADJ, bx + P.GPU_SUPPORT_ADJ, by, B - 1, B + 5, P.M3_CLEAR / 2)
    shape = cut_all(fuse_all([foot, post]), [cut])
    return Spec("gpu_stuetze", shape, (0.20, 0.45, 0.80), group="extra", explode=(0, -40, 0))


# --------------------------------------------------------------------------
def cable_comb():
    n, pitch, d = 8, 4.2, 3.6
    w = n * pitch + 4
    body = box(0, w, 0, 10, 0, 8)
    cuts = []
    for i in range(n):
        x = 2 + pitch / 2 + i * pitch
        cuts.append(cyl_y(x, 4.5, -1, 11, d / 2))
        cuts.append(box(x - 1.3, x + 1.3, -1, 11, 4.5, 9))
    shape = cut_all(body, cuts)
    shape.translate(V(P.PSU_X1 + 10, 20, P.INNER_H - 30))
    return Spec("kabelkamm", shape, (0.15, 0.15, 0.15), group="loose", explode=(0, 0, 60))


# --------------------------------------------------------------------------
def fit_test():
    """Passtest im Block: Board-Platte (2 mm, ITX-Löcher auf Säulen in Abstandshalter-Höhe)
    und Rückwand-Platte (2 mm, I/O-Fenster, GPU-Slotöffnung, Leiste mit Mutternkanal).
    Gesteckt über Zapfen. Prüft die Lage von Slot, Blende und Lochbild zueinander."""
    X1 = P.INNER_L
    vb0, vb1 = P.BOARD_V0 - 6, P.BOARD_V1 + 6
    plate = box(P.BOARD_X0 - 6, X1, vb0, vb1, -2, 0)
    win = box(P.BOARD_X0 + 25, P.BOARD_X1 - 25, P.BOARD_V0 + 25, P.BOARD_V1 - 25, -3, 1)
    adds, cuts = [], [win]
    for (u, v) in standoff_positions().values():
        adds.append(cyl_z(u, v, -0.5, P.STANDOFF, 4.0))
        cuts.append(cyl_z(u, v, -3, P.STANDOFF + 1, P.M3_CLEAR / 2))
    tenons = [(P.BOARD_V0 + 30, P.BOARD_V0 + 50), (P.BOARD_V1 - 50, P.BOARD_V1 - 30)]
    for (v0, v1) in tenons:
        adds.append(box(X1 - 1, X1 + 2.0, v0, v1, -2, 0))
    plate_b = cut_all(fuse_all([plate] + adds), cuts)

    xr0, xr1 = X1, X1 + 2.0
    rear = box(xr0, xr1, P.BRACKET_SLOT_V0 - 4, P.IO_V1 + 6, -2, P.GPU_TAB_W + 6)
    rcuts = [rrect_x(xr0 - 1, xr1 + 1, P.IO_V0, P.IO_V1, P.IO_W0, P.IO_W1, 0.99),
             rrect_x(xr0 - 1, xr1 + 1, *P.GPU_OPEN_V, *P.GPU_OPEN_W, 2.0)]
    for (v0, v1) in tenons:
        rcuts.append(box(xr0 - 1, xr1 + 1, v0 - 0.15, v1 + 0.15, -2.15, 0.15))
    (rv0, rv1), (rw0, rw1) = rail_rect()
    rail = box(X1 - P.GPU_RAIL_DEPTH, xr0 + 0.5, rv0, rv1, rw0, rw1)
    sx = X1 - 6.0
    cw0 = rw0 + 1.2
    rcuts.append(box(sx - P.M3_NUT_AF / 2, sx + P.M3_NUT_AF / 2, rv0 - 1, rv1 - 3.0,
                     cw0, cw0 + P.M3_NUT_T + 0.2))
    for v in P.GPU_SLOT_CENTERS_V:
        rcuts.append(cyl_z(sx, v, rw0 - 1, rw1 + 1, P.M3_CLEAR / 2))
    plate_r = cut_all(rear.fuse(rail), rcuts)
    col = (0.95, 0.55, 0.10)
    return [Spec("passtest_board", plate_b, col, group="fit"),
            Spec("passtest_rueckwand", plate_r, col, group="fit", print_rot=[((0, 1, 0), 90)])]


def build():
    return [psu_holder(), psu_clamp(), gpu_support(), cable_comb()], fit_test()
