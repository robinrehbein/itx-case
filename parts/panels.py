"""Front- und Rückwand (eben, zwischen den Eckbögen, am Stück gedruckt)."""
import params as P
from parts.common import (Spec, box, cyl_x, cyl_z, rrect_x, hex_grid, holes_x, fuse_all,
                          cut_all, place, insert_up)
from parts import grater

H = P.INNER_H


def tab(x0, x1, y, z0, z1, hole_x):
    t = box(x0, x1, y - P.TAB_W / 2, y + P.TAB_W / 2, z0, z1)
    return t, cyl_z(hole_x, y, z0 - 1, z1 + 1, P.M3_CLEAR / 2)


def front_recess():
    """C: Tasche für den Reiben-Einleger (y0, y1, z0, z1); darüber das Rahmenband mit Taster."""
    return (P.FLAT_Y0 + P.GR_EDGE, P.FLAT_Y1 - P.GR_EDGE,
            P.VENT_Z0, H - P.GRATER_TOP_BAND)


def front_insert():
    shape = grater.insert("x", P.OUT_X0, -1, front_recess())
    return Spec("front_einleger", shape, (0.80, 0.80, 0.83), print_rot=[((0, 1, 0), 90)],
                explode=(-220, 0, 0))


def front_vent_points():
    """Lochfeld der Front, gleiches Bild wie die Rückwand; um den Taster bleibt ein Kreis frei."""
    v = P.FRONT_VENT
    if not v or P.GRATER:
        return []
    keep = []
    if P.USB_C:
        keep.append((P.USBC_Y - P.USBC_W / 2 - 2, P.USBC_Y + P.USBC_W / 2 + 2,
                     P.USBC_Z - P.USBC_H / 2 - 2, P.USBC_Z + P.USBC_H / 2 + 2))
    rk = P.BUTTON_KEEP_R + P.VENT_D / 2
    return [q for q in hex_grid(v["y0"], v["y1"], v["z0"], v["z1"], keep, corner_r=v["r"])
            if (q[0] - P.BUTTON_Y) ** 2 + (q[1] - P.BUTTON_Z) ** 2 >= rk * rk]


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
        cuts.append(rrect_x(P.OUT_X0 - 1, 1, P.USBC_Y - P.USBC_W / 2, P.USBC_Y + P.USBC_W / 2,
                            P.USBC_Z - P.USBC_H / 2, P.USBC_Z + P.USBC_H / 2, P.USBC_H / 2 - 0.01))
    cuts += holes_x(front_vent_points(), P.OUT_X0 - 1, 1)
    if P.GRATER:
        cuts += grater.frame_cuts("x", P.OUT_X0, -1, front_recess(), P.T_WALL)
    shape = cut_all(fuse_all([shape] + adds), cuts)
    return Spec("front", shape, (0.86, 0.86, 0.88), print_rot=[((0, 1, 0), -90)],
                explode=(-140, 0, 0))


def io_window():
    """(y0, y1, z0, z1) des I/O-Fensters in der Rückwand."""
    return P.rect_vw(P.IO_V0, P.IO_V1, P.IO_W0, P.IO_W1)


def gpu_open():
    return P.rect_vw(*P.GPU_OPEN_V, *P.GPU_OPEN_W)


def c14_rect(m=0.0):
    return P.rect_vw(P.C14_V - P.C14_W / 2 - m, P.C14_V + P.C14_W / 2 + m,
                     P.C14_W_POS - P.C14_H / 2 - m, P.C14_W_POS + P.C14_H / 2 + m)


def rail_rect():
    """Leiste unter der Slotblech-Lasche (Block): v-Bereich, w-Bereich."""
    return (P.BRACKET_SLOT_V0 - 1.0, P.GPU_V1 + 1.0), (P.GPU_RAIL_W0, P.GPU_RAIL_W1)


def rear_vent_points():
    """Ein Lochfeld über die ganze Rückwand (wie beim Mac Studio); I/O-Fenster,
    Slotöffnung, GPU-Leiste und C14 sind mit gleichem Rand ausgespart."""
    iy0, iy1, iz0, iz1 = io_window()
    m = P.IO_KEEPOUT + 0.5                    # ausgedünnte Zone um das I/O-Fenster
    gy0, gy1, gz0, gz1 = gpu_open()
    (rv0, rv1), (rw0, rw1) = rail_rect()
    keep = [(iy0 - m, iy1 + m, iz0 - m, iz1 + m),
            (gy0, gy1, gz0, gz1),
            P.rect_vw(rv0, rv1, rw0, rw1 + P.REAR_RAIL_CLEAR),
            c14_rect(4.0)]
    v = P.REAR_VENT
    return hex_grid(v["y0"], v["y1"], v["z0"], v["z1"], keep, corner_r=v["r"])


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
    # Nasen unten (nur A): stehen auf niedrigen Bodendomen, Schraube von unten
    for y in P.REAR_LOW_BOSS_Y:
        z0 = P.RIM_H
        adds.append(box(X1 - 8.0, X1 + 1.0, y - 4.0, y + 4.0, z0, z0 + P.REAR_LOW_BOSS_H))
        cuts.append(insert_up(X1 - 5.0, y, z0))

    # Leiste für die GPU-Lasche mit durchgehendem M3-Mutternkanal (ein Ende offen)
    (rv0, rv1), (rw0, rw1) = rail_rect()
    rx0 = X1 - P.GPU_RAIL_DEPTH
    adds.append(place(box(rx0, X1 + 1.0, rv0, rv1, rw0, rw1)))
    sx = X1 - 6.0
    cw0 = rw0 + 1.2
    cuts.append(place(box(sx - P.M3_NUT_AF / 2, sx + P.M3_NUT_AF / 2, rv0 - 1, rv1 - 3.0,
                          cw0, cw0 + P.M3_NUT_T + 0.2)))
    for v in P.GPU_SLOT_CENTERS_V:
        cuts.append(place(cyl_z(sx, v, rw0 - 1, rw1 + 1, P.M3_CLEAR / 2)))

    # I/O-Fenster, innen auf 1.2 mm ausgedünnt (Clip der I/O-Blende)
    iy0, iy1, iz0, iz1 = io_window()
    cuts.append(rrect_x(X1 - 1, P.OUT_X1 + 1, iy0, iy1, iz0, iz1, 0.99))
    m = P.IO_KEEPOUT + 0.5
    cuts.append(box(X1 - 1, P.OUT_X1 - P.IO_PANEL_T, iy0 - m, iy1 + m, iz0 - m, iz1 + m))

    # Slotblech-Öffnung GPU
    gy0, gy1, gz0, gz1 = gpu_open()
    cuts.append(rrect_x(X1 - 1, P.OUT_X1 + 1, gy0, gy1, gz0, gz1, 2.0))

    # C14 (Schnapp-Einbau), innen auf C14_PANEL_T ausgedünnt
    cy0, cy1, cz0, cz1 = c14_rect()
    cuts.append(box(X1 - 1, P.OUT_X1 + 1, cy0, cy1, cz0, cz1))
    ty0, ty1, tz0, tz1 = c14_rect(4.0)
    cuts.append(box(X1 - 1, P.OUT_X1 - P.C14_PANEL_T, ty0, ty1, tz0, tz1))

    pts = rear_vent_points()
    cuts += holes_x(pts, X1 - 1, P.OUT_X1 + 1)
    shape = cut_all(fuse_all([shape] + adds), cuts)
    return Spec("rueckwand", shape, (0.86, 0.86, 0.88), print_rot=[((0, 1, 0), 90)],
                explode=(140, 0, 0)), pts
