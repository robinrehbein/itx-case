"""Boden: voller Grundriss, gelocht über dem Sockel, Randfalz für die Seitenwände,
Dome für Front-/Rück-/Mittelwand, Sockel für Netzteil-, Riser- und GPU-Halter."""
import params as P
from parts.common import (Spec, box, cyl_z, rrect_prism, hex_grid, holes_z, fuse_all,
                          cut_all, dome_floor, insert_down, insert_up, split_with_flanges,
                          envelope_case, cut_holes_split)


def dome_positions():
    d = []
    d += [(5.0, y) for y in P.FRONT_TABS_Y]
    d += [(P.INNER_L - 5.0, y) for y in P.REAR_TABS_Y_BOT]
    d += [(x, P.MID_Y1 + P.TAB_D / 2) for x in P.MID_TABS_X_BOT]
    return d


def plinth_screw_positions():
    yl = P.OUT_Y0 + P.PLINTH_INSET + P.PLINTH_T + P.PLINTH_POST_OFF
    yr = P.OUT_Y1 - P.PLINTH_INSET - P.PLINTH_T - P.PLINTH_POST_OFF
    return [(x, yl if s == "L" else yr) for (x, s) in P.PLINTH_TABS]


def gpu_support_boss():
    return (P.GPU_SUPPORT_X + 20.0, P.GPU_SUPPORT_Y)


def low_boss_positions():
    return list(P.PSU_BOSS) + list(P.RISER_BOSS) + [gpu_support_boss()]


def vent_points():
    """Lochfrei bleiben nur: der Streifen unter der Mittelwand, die Fugenflansche selbst
    (2 x 4 mm), Dome und Schraubsockel."""
    i = P.PLINTH_INSET + P.PLINTH_T + 2.0
    keep = [(-999, 999, P.MID_Y0 - 1, P.MID_Y1 + 1),
            (P.SPLIT_X - P.FLANGE_T, P.SPLIT_X + P.FLANGE_T, -999, 999)]
    rb = P.DOME_D / 2
    for (x, y) in dome_positions() + plinth_screw_positions() + low_boss_positions():
        keep.append((x - rb, x + rb, y - rb, y + rb))
    return hex_grid(P.OUT_X0 + i, P.OUT_X1 - i, P.OUT_Y0 + i, P.OUT_Y1 - i, keep,
                    corner_r=max(P.PLINTH_R - P.PLINTH_T - 2.0, 0.0), col_at=P.SPLIT_X)


def build():
    plate = rrect_prism(P.OUT_X0, P.OUT_X1, P.OUT_Y0, P.OUT_Y1, P.CORNER_R, -P.T_FLOOR, 0)
    pts = vent_points()

    rim = rrect_prism(0, P.INNER_L, 0, P.INNER_W, P.CORNER_RI, 0, P.RIM_H).cut(
        rrect_prism(P.RIM_W, P.INNER_L - P.RIM_W, P.RIM_W, P.INNER_W - P.RIM_W,
                    P.CORNER_RI - P.RIM_W, -1, P.RIM_H + 1))
    adds, cuts = [rim], []
    for (x, y) in dome_positions():
        d, h = dome_floor(x, y)
        adds.append(d)
        cuts.append(h)
    for (x, y) in low_boss_positions():
        adds.append(cyl_z(x, y, 0, P.LOW_BOSS_H, P.DOME_D / 2))
        cuts.append(insert_down(x, y, P.LOW_BOSS_H))
    for (x, y) in plinth_screw_positions():
        adds.append(cyl_z(x, y, 0, P.LOW_BOSS_H, P.DOME_D / 2))   # bleibt unter dem Netzteil-Halter
        cuts.append(insert_up(x, y, -P.T_FLOOR))
    shape = cut_all(fuse_all([plate] + adds), cuts)

    ribs = [(11.0, P.MID_Y0 - 1.0, 0.0, P.FLANGE_D),
            (P.MID_Y1 + 1.0, P.INNER_W - 11.0, 0.0, P.FLANGE_D)]
    bolts = [(30.0, 5.0), (70.0, 5.0), (120.0, 5.0), (200.0, 5.0), (245.0, 5.0)]
    a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts, envelope_case())
    a, b = cut_holes_split(a, b, P.SPLIT_X, [q[0] for q in pts],
                           holes_z(pts, -P.T_FLOOR - 1, 0.5))
    col = (0.78, 0.78, 0.80)
    return [Spec("boden_vorn", a, col, explode=(-25, 0, -70), minutes=None),
            Spec("boden_hinten", b, col, explode=(25, 0, -70))], len(pts)
