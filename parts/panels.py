"""Front- und Rückwand (eben, zwischen den Eckbögen, am Stück gedruckt)."""
import params as P
from parts.common import (Spec, box, cyl_x, rrect_x, hex_grid, holes_x, fuse_all, cut_all)

H = P.INNER_H


def tab(x0, x1, y, z0, z1, hole_x):
    t = box(x0, x1, y - P.TAB_W / 2, y + P.TAB_W / 2, z0, z1)
    from parts.common import cyl_z
    return t, cyl_z(hole_x, y, z0 - 1, z1 + 1, P.M3_CLEAR / 2)


def front():
    shape = box(P.OUT_X0, 0, P.FLAT_Y0, P.FLAT_Y1, 0, H)
    adds, cuts = [], []
    for y in P.FRONT_TABS_Y:
        for (z0, z1) in (P.TAB_Z_BOT, P.TAB_Z_TOP):
            t, h = tab(-1.0, P.TAB_D, y, z0, z1, 5.0)
            adds.append(t)
            cuts.append(h)
    cuts.append(cyl_x(P.BUTTON_Y, P.BUTTON_Z, P.OUT_X0 - 1, 1, P.BUTTON_D / 2))
    if P.USB_C:
        cuts.append(rrect_x(P.OUT_X0 - 1, 1, P.BUTTON_Y - P.USBC_W / 2, P.BUTTON_Y + P.USBC_W / 2,
                            P.USBC_Z - P.USBC_H / 2, P.USBC_Z + P.USBC_H / 2, P.USBC_H / 2 - 0.01))
    shape = cut_all(fuse_all([shape] + adds), cuts)
    return Spec("front", shape, (0.86, 0.86, 0.88), print_rot=[((0, 1, 0), -90)],
                explode=(-140, 0, 0))


def io_window():
    y0 = P.BOARD_Y1 - P.IO_BELOW_PCB_TOP
    z0 = P.BOARD_Z0 + P.IO_FROM_BOTTOM
    return y0, y0 + P.IO_H, z0, z0 + P.IO_W


def rear_vent_points():
    """Ein Lochfeld über die ganze Rückwand (wie beim Mac Studio); I/O-Fenster,
    Slotöffnung, GPU-Leiste und C14 sind mit gleichem Rand ausgespart.
    Rückgabe getrennt nach Kammer: (Board-Kammer, GPU-Kammer)."""
    iy0, iy1, iz0, iz1 = io_window()
    m = P.IO_KEEPOUT + 0.5                    # ausgedünnte Zone um das I/O-Fenster
    g = P.GPU_OPEN
    cy0, cy1 = P.C14_Y - P.C14_W / 2, P.C14_Y + P.C14_W / 2
    cz0, cz1 = P.C14_Z - P.C14_H / 2, P.C14_Z + P.C14_H / 2
    keep = [(iy0 - m, iy1 + m, iz0 - m, iz1 + m),
            (g["y0"], g["y1"], g["z0"], g["z1"]),
            (g["y1"], iy0, g["z0"], g["z1"]),              # Steg zwischen den Ausschnitten
            (-999, P.MID_Y0, P.GPU_RAIL_Z0, P.GPU_RAIL_Z1 + P.REAR_RAIL_CLEAR),
            (cy0 - 4, cy1 + 4, cz0 - 4, cz1 + 4)]
    v = P.REAR_VENT
    pts = hex_grid(v["y0"], v["y1"], v["z0"], v["z1"], keep, corner_r=v["r"])
    ym = (P.MID_Y0 + P.MID_Y1) / 2
    return [q for q in pts if q[0] >= ym], [q for q in pts if q[0] < ym]


def rear():
    X1 = P.INNER_L
    shape = box(X1, P.OUT_X1, P.FLAT_Y0, P.FLAT_Y1, 0, H)
    adds, cuts = [], []
    for y in P.REAR_TABS_Y_BOT:
        t, h = tab(X1 - P.TAB_D, X1 + 1.0, y, *P.TAB_Z_BOT, hole_x=X1 - 5.0)
        adds.append(t)
        cuts.append(h)
    for y in P.REAR_TABS_Y_TOP:
        t, h = tab(X1 - P.TAB_D, X1 + 1.0, y, *P.TAB_Z_TOP, hole_x=X1 - 5.0)
        adds.append(t)
        cuts.append(h)

    # Leiste für die GPU-Lasche mit durchgehendem M3-Mutternkanal (Ende vorn offen)
    ry0, ry1 = P.FLAT_Y0 + 1.0, P.MID_Y0 - 1.0
    rx0 = X1 - P.GPU_RAIL_DEPTH
    adds.append(box(rx0, X1 + 1.0, ry0, ry1, P.GPU_RAIL_Z0, P.GPU_RAIL_Z1))
    sx = X1 - 6.0
    cz0 = P.GPU_RAIL_Z0 + 1.2
    cuts.append(box(sx - P.M3_NUT_AF / 2, sx + P.M3_NUT_AF / 2, ry0 - 1, ry1 - 3.0,
                    cz0, cz0 + P.M3_NUT_T + 0.2))
    from parts.common import cyl_z
    for y in P.GPU_SLOT_CENTERS_Y:
        cuts.append(cyl_z(sx, y, P.GPU_RAIL_Z0 - 1, P.GPU_RAIL_Z1 + 1, P.M3_CLEAR / 2))

    # I/O-Fenster, innen auf 1.2 mm ausgedünnt (Clip der I/O-Blende)
    iy0, iy1, iz0, iz1 = io_window()
    cuts.append(rrect_x(X1 - 1, P.OUT_X1 + 1, iy0, iy1, iz0, iz1, 0.99))
    m = P.IO_KEEPOUT + 0.5
    cuts.append(box(X1 - 1, P.OUT_X1 - P.IO_PANEL_T, iy0 - m, iy1 + m, iz0 - m, iz1 + m))

    # Slotblech-Öffnung GPU
    g = P.GPU_OPEN
    cuts.append(rrect_x(X1 - 1, P.OUT_X1 + 1, g["y0"], g["y1"], g["z0"], g["z1"], 2.0))

    # C14 (Schnapp-Einbau), innen auf C14_PANEL_T ausgedünnt
    cy0, cy1 = P.C14_Y - P.C14_W / 2, P.C14_Y + P.C14_W / 2
    cz0_, cz1_ = P.C14_Z - P.C14_H / 2, P.C14_Z + P.C14_H / 2
    cuts.append(box(X1 - 1, P.OUT_X1 + 1, cy0, cy1, cz0_, cz1_))
    cuts.append(box(X1 - 1, P.OUT_X1 - P.C14_PANEL_T, cy0 - 4, cy1 + 4, cz0_ - 4, cz1_ + 4))

    d15, gpu = rear_vent_points()
    cuts += holes_x(d15 + gpu, X1 - 1, P.OUT_X1 + 1)
    shape = cut_all(fuse_all([shape] + adds), cuts)
    return Spec("rueckwand", shape, (0.86, 0.86, 0.88), print_rot=[((0, 1, 0), 90)],
                explode=(140, 0, 0)), (d15, gpu)
