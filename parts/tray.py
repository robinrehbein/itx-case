"""Board-Träger (nur B): 5-mm-Platte vor der rechten Seitenwand, trägt das Board auf
Abstandshaltern und den Netzteil-Halter. Dahinter bleiben 11 mm für Kabel. Entsteht im
Block (x=u, y=v, z=w) und wird mit place() ins Gehäuse gestellt."""
import params as P
from parts.common import (Spec, box, cyl_y, cyl_z, rrect_prism, fuse_all, cut_all,
                          split_with_flanges, insert_down, place, PLACE_UNDO)
from parts.floor import base_mounts

X0, X1 = P.RIM_W + 0.2, P.INNER_L - P.RIM_W - 0.2   # über dem Randfalz frei
T = P.T_TRAY


def build():
    V = P.INNER_V
    # oben 1 mm Luft: dort ragen die Reiben-Einleger des Deckels 0,8 mm nach innen
    shape = box(X0, X1, 0, V - 1.0, -T, 0)
    adds, cuts = [], []
    # Laschen unten zu den Bodendomen (Board-Seite), oben zu den Deckeldomen (Kabelseite)
    v0, v1 = P.TAB_Z_BOT
    for x in P.TRAY_TABS_X:
        adds.append(box(x - P.TAB_W / 2, x + P.TAB_W / 2, v0, v1, -1.0, P.TAB_D))
        cuts.append(cyl_y(x, P.TAB_D / 2, v0 - 1, v1 + 1, P.M3_CLEAR / 2))
    v0, v1 = P.TAB_Z_TOP
    wc = -T - P.TAB_D / 2
    for x in P.TRAY_TOP_TABS_X:
        adds.append(box(x - P.TAB_W / 2, x + P.TAB_W / 2, v0, v1, -T - P.TAB_D, -T + 1.0))
        cuts.append(cyl_y(x, wc, v0 - 1, v1 + 1, P.M3_CLEAR / 2))
    for (u, v, h) in base_mounts():
        r = 5.0 if h > P.LOW_BOSS_H else P.DOME_D / 2
        adds.append(cyl_z(u, v, -1.0, h, r))
        cuts.append(insert_down(u, v, h))
    for (u0, u1, v0, v1) in P.TRAY_CUTOUTS:
        cuts.append(rrect_prism(u0, u1, v0, v1, 6.0, -T - 1, 0.5))
    shape = cut_all(fuse_all([shape] + adds), cuts)

    ribs = [(14.0, V - 14.0, -1.0, P.FLANGE_D)]
    bolts = [(40.0, 5.0), (V / 2, 5.0), (V - 40.0, 5.0)]
    a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts)
    col = (0.62, 0.63, 0.66)
    return [Spec("traeger_vorn", place(a), col, print_rot=list(PLACE_UNDO), explode=(-25, 50, 0)),
            Spec("traeger_hinten", place(b), col, print_rot=list(PLACE_UNDO), explode=(25, 50, 0))]
