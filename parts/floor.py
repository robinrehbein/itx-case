"""Boden: voller Grundriss, gelocht über dem Sockel, Randfalz für die Seitenwände,
Dome für Front, Rückwand und Board-Träger. Bei A trägt der Boden auch das Board
(Abstandshalter) und den Netzteil-Halter."""
import params as P
from parts.common import (Spec, cyl_z, rrect_prism, hex_grid, holes_z, fuse_all,
                          cut_all, dome_floor, insert_down, insert_up, split_with_flanges,
                          envelope_case, seam_envelope, cut_holes_split)


def standoff_positions():
    """ITX-Löcher im Block (u, v)."""
    return {k: (P.BOARD_X1 - d, P.BOARD_V0 + l) for k, (d, l) in P.ITX_HOLES.items()}


def base_mounts():
    """Dome auf der Board-Ebene (Block): (u, v, Höhe). A: Boden, B: Träger."""
    m = [(u, v, P.STANDOFF) for (u, v) in standoff_positions().values()]
    m += [(u, v, P.LOW_BOSS_H) for (u, v) in P.PSU_BOSS]
    if not P.LYING:   # Stützen des Leitblechs
        m += [(u, P.BAFFLE_POST_V, P.LOW_BOSS_H) for u in P.BAFFLE_POSTS_U]
    return m


def tray_dome_y():
    return P.Y_BASE - P.TAB_D / 2


def dome_positions():
    d = []
    d += [(5.0, y) for y in P.FRONT_TABS_Y]
    d += [(P.INNER_L - 5.0, y) for y in P.REAR_TABS_Y_BOT]
    d += [(x, tray_dome_y()) for x in P.TRAY_TABS_X]
    return d


def rear_low_positions():
    return [(P.INNER_L - 5.0, y) for y in P.REAR_LOW_BOSS_Y]


def plinth_screw_positions():
    yl = P.OUT_Y0 + P.PLINTH_INSET + P.PLINTH_T + P.PLINTH_POST_OFF
    yr = P.OUT_Y1 - P.PLINTH_INSET - P.PLINTH_T - P.PLINTH_POST_OFF
    return [(x, yl if s == "L" else yr) for (x, s) in P.PLINTH_TABS]


def gpu_support_boss():
    s = P.GPU_SUPPORT
    return (s["x"] + 20.0, s["y"])


def low_boss_positions():
    """Niedrige Dome mit Einschmelzmutter von oben (Gehäusekoordinaten)."""
    pos = [gpu_support_boss()]
    if P.LYING:
        pos += [(u, v) for (u, v, h) in base_mounts() if h == P.LOW_BOSS_H]
    return pos


def keep_discs():
    pts = dome_positions() + plinth_screw_positions() + low_boss_positions() + rear_low_positions()
    if P.LYING:
        pts += list(standoff_positions().values())
    return pts


def vent_points():
    """Lochfrei bleiben nur: die Fugenflansche selbst (2 x 4 mm), Dome, Schraubsockel und
    bei B der Streifen unter dem Board-Träger."""
    i = P.PLINTH_INSET + P.PLINTH_T + 2.0
    keep = [(P.SPLIT_X - P.FLANGE_T, P.SPLIT_X + P.FLANGE_T, -999, 999)]
    if not P.LYING:
        keep.append((-999, 999, P.Y_BASE - 1.0, P.Y_BASE + P.T_TRAY + 1.0))
    rb = P.DOME_D / 2
    for (x, y) in keep_discs():
        keep.append((x - rb, x + rb, y - rb, y + rb))
    return hex_grid(P.OUT_X0 + i, P.OUT_X1 - i, P.OUT_Y0 + i, P.OUT_Y1 - i, keep,
                    corner_r=max(P.PLINTH_R - P.PLINTH_T - 2.0, 0.0), col_at=P.SPLIT_X)


def rib_y_ranges():
    """Fugenflansch unter dem Boden-Innenraum (y0, y1); bei B endet er vor dem Träger."""
    if P.LYING:
        return [(11.0, P.INNER_W - 11.0)]
    return [(11.0, P.Y_BASE - 6.0)]


def build():
    plate = rrect_prism(P.OUT_X0, P.OUT_X1, P.OUT_Y0, P.OUT_Y1, P.CORNER_R, -P.T_FLOOR, 0)
    pts = vent_points()

    rim = rrect_prism(0, P.INNER_L, 0, P.INNER_W, P.CORNER_RI, 0, P.RIM_H).cut(
        rrect_prism(P.RIM_W, P.INNER_L - P.RIM_W, P.RIM_W, P.INNER_W - P.RIM_W,
                    max(P.CORNER_RI - P.RIM_W, 0.5), -1, P.RIM_H + 1))
    adds, cuts = [rim], []
    for (x, y) in dome_positions():
        d, h = dome_floor(x, y)
        adds.append(d)
        cuts.append(h)
    if P.LYING:
        for (x, y, h) in base_mounts():
            if h != P.LOW_BOSS_H:
                d, hole = dome_floor(x, y, h)
                adds.append(d)
                cuts.append(hole)
    for (x, y) in low_boss_positions():
        adds.append(cyl_z(x, y, 0, P.LOW_BOSS_H, P.DOME_D / 2))
        cuts.append(insert_down(x, y, P.LOW_BOSS_H))
    for (x, y) in plinth_screw_positions():
        adds.append(cyl_z(x, y, 0, P.LOW_BOSS_H, P.DOME_D / 2))
        cuts.append(insert_up(x, y, -P.T_FLOOR))
    for (x, y) in rear_low_positions():
        # Rückwand-Nase steht auf diesem Dom; Schraube von unten, Kopf versenkt
        adds.append(cyl_z(x, y, 0, P.RIM_H, P.DOME_D / 2))
        cuts.append(cyl_z(x, y, -P.T_FLOOR - 1, P.RIM_H + 1, P.M3_CLEAR / 2))
        cuts.append(cyl_z(x, y, -P.T_FLOOR - 1, -P.T_FLOOR + 3.0, P.M3_HEAD_D / 2))
    shape = cut_all(fuse_all([plate] + adds), cuts)

    ribs = [(y0, y1, 0.0, P.FLANGE_D) for (y0, y1) in rib_y_ranges()]
    y0, y1 = rib_y_ranges()[0]
    n = max(2, int((y1 - y0) // 50) + 1)
    bolts = [(y0 + 10 + i * (y1 - y0 - 20) / (n - 1), 5.0) for i in range(n)]
    a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts, seam_envelope(envelope_case()))
    a, b = cut_holes_split(a, b, P.SPLIT_X, [q[0] for q in pts],
                           holes_z(pts, -P.T_FLOOR - 1, 0.5))
    col = (0.78, 0.78, 0.80)
    return [Spec("boden_vorn", a, col, explode=(-25, 0, -70)),
            Spec("boden_hinten", b, col, explode=(25, 0, -70))], len(pts)
