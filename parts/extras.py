"""Extra-Druckteile: Netzteil-Halter mit Bügel, Riser-Halter, GPU-Stütze, Kabelkamm,
Passtest-Teile."""
import params as P
from FreeCAD import Vector as V
from parts.common import (Spec, box, cyl_x, cyl_y, cyl_z, rrect_prism, rrect_y, rrect_x,
                          wedge_y, fuse_all, cut_all, insert_down)
from parts.floor import gpu_support_boss
from parts.midwall import standoff_positions
from parts.panels import io_window

B = P.LOW_BOSS_H


def slot_z(x0, x1, y, z0, z1, r):
    """Langloch senkrecht (Achse z), entlang x."""
    return fuse_all([cyl_z(x0, y, z0, z1, r), cyl_z(x1, y, z0, z1, r),
                     box(x0, x1, y - r, y + r, z0, z1)])


def slot_y_vert(x, z0, z1, y0, y1, r):
    """Langloch durch eine Platte in der x-z-Ebene, entlang z."""
    return fuse_all([cyl_y(x, z0, y0, y1, r), cyl_y(x, z1, y0, y1, r),
                     box(x - r, x + r, y0, y1, z0, z1)])


# --------------------------------------------------------------------------
def psu_holder():
    x0, x1, y0, y1 = P.PSU_X0, P.PSU_X1, P.PSU_Y0, P.PSU_Y1
    z0, z1 = B, P.PSU_Z0
    frame = box(x0, x1, y0, y1, z0, z1).cut(box(x0 + 6, x1 - 6, y0 + 6, y1 - 6, z0 - 1, z1 + 1))
    adds, cuts = [frame], []
    for (x, y) in P.PSU_BOSS:
        if y < y0:
            ya, yb = y0 - 6, y0 + 1
        else:
            ya, yb = y1 - 1, y1 + 6
        adds.append(box(x - 6, x + 6, ya, yb, z0, z0 + 4))
        cuts.append(cyl_z(x, y, z0 - 1, z1 + 1, P.M3_CLEAR / 2))
    # Pfosten für den Bügel (Einschmelzmutter seitlich)
    yc = (y0 + y1) / 2
    for (px0, px1, ins_from) in ((x0 - 6, x0, x0 - 6), (x1, x1 + 6, x1 + 6)):
        adds.append(box(px0, px1, yc - 10, yc + 10, z0, 34))
        if ins_from < x0:
            cuts.append(cyl_x(yc, 28, ins_from - 0.01, ins_from + P.INSERT_DEPTH, P.INSERT_D / 2))
        else:
            cuts.append(cyl_x(yc, 28, ins_from - P.INSERT_DEPTH, ins_from + 0.01, P.INSERT_D / 2))
    shape = cut_all(fuse_all(adds), cuts)
    return Spec("netzteil_halter", shape, (0.25, 0.25, 0.27), group="extra",
                explode=(0, 0, -30))


def psu_strap():
    x0, x1 = P.PSU_X0 - 9, P.PSU_X1 + 9
    yc = (P.PSU_Y0 + P.PSU_Y1) / 2
    zt = P.PSU_Z1
    band = box(x0, x1, yc - 10, yc + 10, zt, zt + 3)
    legs = [box(x0, x0 + 3, yc - 10, yc + 10, 22, zt + 3),
            box(x1 - 3, x1, yc - 10, yc + 10, 22, zt + 3)]
    holes = [cyl_x(yc, 28, x0 - 1, x0 + 4, P.M3_CLEAR / 2), cyl_x(yc, 28, x1 - 4, x1 + 1, P.M3_CLEAR / 2)]
    shape = cut_all(fuse_all([band] + legs), holes)
    return Spec("netzteil_buegel", shape, (0.25, 0.25, 0.27), group="extra",
                print_rot=[((1, 0, 0), 90)], explode=(0, 0, 90))


# --------------------------------------------------------------------------
def riser_holder():
    (bx0, by), (bx1, _) = P.RISER_BOSS
    a = P.RISER_ADJ
    base = box(bx0 - 12, bx1 + 12, 56, 70, B, B + 3)
    ups = [box(204, 216, 60, 64, B, 24), box(321, 333, 60, 64, B, 24)]
    cuts = [slot_z(bx0 - a, bx0 + a, by, B - 1, B + 4, P.M3_CLEAR / 2),
            slot_z(bx1 - a, bx1 + a, by, B - 1, B + 4, P.M3_CLEAR / 2)]
    zn = 14.0
    for x in (210.0, 327.0):
        cuts.append(slot_y_vert(x, zn - a, zn + a, 59, 65, P.M3_CLEAR / 2))
    shape = cut_all(fuse_all([base] + ups), cuts)
    return Spec("riser_halter", shape, (0.20, 0.45, 0.80), group="extra", explode=(0, -40, -20))


def riser_tray():
    plate = box(204, 333, 64, 84, 9, 12)
    flange = box(204, 333, 64, 67, 9, 19)
    cuts = [cyl_y(210.0, 14.0, 63, 68, P.M3_CLEAR / 2), cyl_y(327.0, 14.0, 63, 68, P.M3_CLEAR / 2)]
    # Langlöcher für die Riser-Platine (Lochabstand je nach Riser)
    for x in (214.0, 323.0):
        cuts.append(cyl_z(x, 78, 8, 13, P.M3_CLEAR / 2))
    for y in (70.0, 78.0):
        cuts.append(fuse_all([cyl_z(222, y, 8, 13, 1.7), cyl_z(315, y, 8, 13, 1.7),
                              box(222, 315, y - 1.7, y + 1.7, 8, 13)]))
    shape = cut_all(plate.fuse(flange), cuts)
    return Spec("riser_traeger", shape, (0.20, 0.45, 0.80), group="extra", explode=(0, -40, 10))


# --------------------------------------------------------------------------
def gpu_support():
    bx, by = gpu_support_boss()
    px = P.GPU_SUPPORT_X
    foot = box(px - 6, bx + P.GPU_SUPPORT_ADJ + 6, by - 8, by + 8, B, B + 4)
    post = box(px - 6, px + 6, by - 8, by + 8, B, P.GPU_Z0 - 1.0)
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
    shape.translate(V(40, 30, 188))
    return Spec("kabelkamm", shape, (0.15, 0.15, 0.15), group="loose", explode=(0, 0, 60))


# --------------------------------------------------------------------------
def fit_test():
    """Passtest: Board-Platte (2 mm, ITX-Löcher auf Säulen in Abstandshalter-Höhe) + Rückwand-Platte
    (2 mm, I/O-Fenster, GPU-Slotöffnung, Leiste mit Mutternkanal). Gesteckt über Zapfen."""
    X1 = P.INNER_L
    yb0, yb1 = P.MID_Y1 - 2, P.MID_Y1
    board = box(P.BOARD_X0 - 6, X1, yb0, yb1, P.BOARD_Z0 - 8, P.BOARD_Z1 + 6)
    win = box(P.BOARD_X0 + 25, P.BOARD_X1 - 25, yb0 - 1, yb1 + 1, P.BOARD_Z0 + 25, P.BOARD_Z1 - 25)
    adds, cuts = [], [win]
    for (x, z) in standoff_positions().values():
        adds.append(cyl_y(x, z, yb1 - 0.5, P.BOARD_Y0, 4.0))
        cuts.append(cyl_y(x, z, yb0 - 1, P.BOARD_Y0 + 1, P.M3_CLEAR / 2))
    tenons = [(40.0, 60.0), (130.0, 150.0)]
    for (z0, z1) in tenons:
        adds.append(box(X1 - 1, X1 + 2.0, yb0, yb1, z0, z1))
    plate_b = cut_all(fuse_all([board] + adds), cuts)

    xr0, xr1 = X1, X1 + 2.0
    rear = box(xr0, xr1, P.FLAT_Y0 + 1, 150.0, 10.0, 195.0)
    iy0, iy1, iz0, iz1 = io_window()
    g = P.GPU_OPEN
    rcuts = [rrect_x(xr0 - 1, xr1 + 1, iy0, iy1, iz0, iz1, 0.99),
             rrect_x(xr0 - 1, xr1 + 1, g["y0"], g["y1"], g["z0"], g["z1"], 2.0)]
    for (z0, z1) in tenons:
        rcuts.append(box(xr0 - 1, xr1 + 1, yb0 - 0.15, yb1 + 0.15, z0 - 0.15, z1 + 0.15))
    rail = box(X1 - P.GPU_RAIL_DEPTH, xr0 + 0.5, P.FLAT_Y0 + 1, P.MID_Y0 - 1,
               P.GPU_RAIL_Z0, P.GPU_RAIL_Z1)
    sx = X1 - 6.0
    cz0 = P.GPU_RAIL_Z0 + 1.2
    rcuts.append(box(sx - P.M3_NUT_AF / 2, sx + P.M3_NUT_AF / 2, P.FLAT_Y0, P.MID_Y0 - 4,
                     cz0, cz0 + P.M3_NUT_T + 0.2))
    for y in P.GPU_SLOT_CENTERS_Y:
        rcuts.append(cyl_z(sx, y, P.GPU_RAIL_Z0 - 1, P.GPU_RAIL_Z1 + 1, P.M3_CLEAR / 2))
    plate_r = cut_all(rear.fuse(rail), rcuts)
    col = (0.95, 0.55, 0.10)
    return [Spec("passtest_board", plate_b, col, group="fit", print_rot=[((1, 0, 0), 90)]),
            Spec("passtest_rueckwand", plate_r, col, group="fit", print_rot=[((0, 1, 0), 90)])]


def build():
    return [psu_holder(), psu_strap(), riser_holder(), riser_tray(), gpu_support(),
            cable_comb()], fit_test()
