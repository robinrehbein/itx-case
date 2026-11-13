"""Mittelwand (5 mm): trägt das Board auf Abstandshaltern (Slot-Kante oben), Tasche für das
Riser-Flachband hinter dem Board, Riser-Durchführung unten, Kabeldurchführung oben vorn.
Laschen nur auf der Board-Seite (GPU-Seite hat 3 mm Luft)."""
import params as P
from parts.common import (Spec, box, cyl_y, cyl_z, rrect_y, fuse_all, cut_all, split_with_flanges)

H = P.INNER_H
X0, X1 = P.RIM_W + 0.2, P.INNER_L - P.RIM_W - 0.2   # über dem Randfalz frei


def standoff_positions():
    """ITX-Löcher in Gehäusekoordinaten (x, z)."""
    return {k: (P.BOARD_X1 - d, P.BOARD_Z1 - l) for k, (d, l) in P.ITX_HOLES.items()}


def build():
    y0, y1 = P.MID_Y0, P.MID_Y1
    shape = box(X0, X1, y0, y1, 0, H)
    adds, cuts = [], []
    yt = y1 + P.TAB_D / 2
    for x in P.MID_TABS_X_BOT:
        adds.append(box(x - P.TAB_W / 2, x + P.TAB_W / 2, y1 - 1, y1 + P.TAB_D, *P.TAB_Z_BOT))
        cuts.append(cyl_z(x, yt, P.TAB_Z_BOT[0] - 1, P.TAB_Z_BOT[1] + 1, P.M3_CLEAR / 2))
    for x in P.MID_TABS_X_TOP:
        adds.append(box(x - P.TAB_W / 2, x + P.TAB_W / 2, y1 - 1, y1 + P.TAB_D, *P.TAB_Z_TOP))
        cuts.append(cyl_z(x, yt, P.TAB_Z_TOP[0] - 1, P.TAB_Z_TOP[1] + 1, P.M3_CLEAR / 2))
    for (x, z) in standoff_positions().values():
        adds.append(cyl_y(x, z, y1 - 1, P.BOARD_Y0, 5.0))
        cuts.append(cyl_y(x, z, P.BOARD_Y0 - P.INSERT_DEPTH, P.BOARD_Y0 + 0.01, P.INSERT_D / 2))
    r = P.RISER_PASS
    cuts.append(rrect_y(r["x0"], r["x1"], r["z0"] - 5, r["z1"], y0 - 1, y1 + 1, 3.0))
    k = P.RISER_POCKET
    cuts.append(box(k["x0"], k["x1"], y1 - k["depth"], y1 + 1, k["z0"] - 4, k["z1"]))
    c = P.CABLE_PASS
    cuts.append(rrect_y(c["x0"], c["x1"], c["z0"], c["z1"], y0 - 1, y1 + 1, 6.0))
    shape = cut_all(fuse_all([shape] + adds), cuts)

    ribs = [(y1 - 1, y1 + P.FLANGE_D, 14.0, H - 14.0)]
    yb = y1 + P.FLANGE_D / 2
    bolts = [(yb, 40.0), (yb, 100.0), (yb, 160.0)]
    a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts)
    col = (0.62, 0.63, 0.66)
    rot = [((1, 0, 0), 90)]   # GPU-Seite aufs Bett, Abstandshalter/Laschen nach oben
    return [Spec("mittelwand_vorn", a, col, print_rot=rot, explode=(-25, -50, 0)),
            Spec("mittelwand_hinten", b, col, print_rot=rot, explode=(25, -50, 0))]
