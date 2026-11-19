"""Deckel: voller Grundriss mit gerundeter Oberkante, ein Lochfeld über die ganze Fläche
(TOP_VENT), Magnettaschen über den Seitenwänden, Dome für die Wandlaschen."""
import params as P
from parts import grater
from parts.common import (Spec, box, rrect_prism, hex_grid, holes_z, split_blind, cyl_z, fuse_all, cut_all,
                          dome_lid, split_with_flanges, envelope_case, seam_envelope, cut_holes_split)

TOP = P.INNER_H + P.T_LID


def dome_positions():
    d = []
    d += [(5.0, y) for y in P.FRONT_TABS_Y]
    d += [(P.INNER_L - 5.0, y) for y in P.REAR_TABS_Y_TOP]
    if P.TRAY_TOP_TABS_X:
        d += [(x, P.Y_BASE + P.T_TRAY + P.TAB_D / 2) for x in P.TRAY_TOP_TABS_X]
    return d


def magnet_positions():
    if P.CORNER_MAGNETS:
        m, s = P.CORNER_MAG_IN, P.CORNER_MAG_SIDE
        xs, ys = (m, P.INNER_L - m), (s, P.INNER_W - s)
        return [(x, y) for x in xs for y in ys]
    yl = P.OUT_Y0 + P.MAGNET_FROM_OUTER
    yr = P.OUT_Y1 - P.MAGNET_FROM_OUTER
    return [(x, yl) for x in P.MAGNET_X] + [(x, yr) for x in P.MAGNET_X]


def grater_recess():
    """Reibe im Deckel: eine Tasche über beide Hälften (x0, x1, y0, y1), rundum mit demselben
    Abstand zum Außenrand wie Front und Seitenwände (Eckbogen + GR_EDGE)."""
    m = P.CORNER_R + P.GR_EDGE
    return (P.OUT_X0 + m, P.OUT_X1 - m, P.OUT_Y0 + m, P.OUT_Y1 - m)


def grater_recesses():
    return [grater_recess()]


# Fugenflansch (y0, y1, z0, z1). A: neben dem Kabelbogen der Karte, B: vor dem Träger.
# Mit Reibe kein Flansch: der Rand ist zu schmal, darunter sitzen die Flansche der
# Seitenwände. Jede Deckelhälfte ist mit Front bzw. Rückwand verschraubt, die Fuge wird
# verklebt und über die überlappenden Einleger ausgerichtet.
_ZR = (P.INNER_H - P.FLANGE_D, P.INNER_H)
if P.GRATER_LID:
    SEAM_RIBS = []
elif P.LYING:
    SEAM_RIBS = [(P.GPU_V1 + 6.0, P.INNER_W - 11.0) + _ZR]
else:
    SEAM_RIBS = [(11.0, P.Y_BASE - 6.0) + _ZR]
SEAM_RIB = SEAM_RIBS[0] if SEAM_RIBS else None


def vent_sets():
    """Feld läuft ohne Lücke über die Trennfuge (Lochspalte auf der Fuge).
    Rückgabe: (durchgehend, blind). Blind sind die Löcher über Fugenflansch und Domen."""
    v = P.TOP_VENT
    pts = hex_grid(v["x0"], v["x1"], v["y0"], v["y1"], corner_r=v["r"], col_at=P.SPLIT_X)
    rects = [(P.SPLIT_X - P.FLANGE_T, P.SPLIT_X + P.FLANGE_T, r[0], r[1]) for r in SEAM_RIBS]
    if not P.LYING:   # Oberkante des Board-Trägers
        rects.append((-999, 999, P.Y_BASE, P.Y_BASE + P.T_TRAY))
    discs = [(x, y, P.DOME_D / 2) for (x, y) in dome_positions()]
    return split_blind(pts, rects, discs)


def vent_points():
    """Offene Löcher des Deckels (bei C keine, dort sitzt die Reibe)."""
    return [] if P.GRATER_LID else vent_sets()[0]


def build():
    plate = rrect_prism(P.OUT_X0, P.OUT_X1, P.OUT_Y0, P.OUT_Y1, P.CORNER_R, P.INNER_H, TOP)
    top_edges = [e for e in plate.Edges
                 if abs(e.BoundBox.ZMin - TOP) < 1e-6 and abs(e.BoundBox.ZMax - TOP) < 1e-6]
    # Rundung oben; die ersten 1 mm auf dem Bett als 45°-Fase, damit die Kante druckbar bleibt
    plate = plate.makeFillet(P.LID_EDGE_R, top_edges).common(
        plate.makeChamfer(P.LID_EDGE_BED_CHAMFER, top_edges))
    through, blind = vent_sets()

    adds, cuts = [], []
    for (x, y) in dome_positions():
        d, h = dome_lid(x, y)
        adds.append(d)
        cuts.append(h)
    for (x, y) in magnet_positions():
        cuts.append(cyl_z(x, y, P.INNER_H - 0.01, P.INNER_H + P.MAGNET_H, P.MAGNET_D / 2))
    if P.CORNER_MAGNETS:   # Leiste innen an der Oberkante beider Seitenwände
        g0, g1, lh = P.LID_LIP
        x0, x1 = P.FLAT_X0 + 4.0, P.FLAT_X1 - 4.0
        adds.append(box(x0, x1, g0, g1, P.INNER_H - lh, P.INNER_H))
        adds.append(box(x0, x1, P.INNER_W - g1, P.INNER_W - g0, P.INNER_H - lh, P.INNER_H))
    if P.GRATER:           # Schattenfuge an der Unterkante des Deckels
        r = P.REVEAL
        cuts.append(rrect_prism(P.OUT_X0 - 1, P.OUT_X1 + 1, P.OUT_Y0 - 1, P.OUT_Y1 + 1,
                                P.CORNER_R + 1, P.INNER_H - 1, P.INNER_H + r).cut(
            rrect_prism(P.OUT_X0 + r, P.OUT_X1 - r, P.OUT_Y0 + r, P.OUT_Y1 - r,
                        P.CORNER_R - r, P.INNER_H - 2, P.INNER_H + r + 1)))
    shape = cut_all(fuse_all([plate] + adds), cuts)

    ribs = list(SEAM_RIBS)
    zb = P.INNER_H - 5.0
    if P.GRATER_LID:
        bolts = [((r[0] + r[1]) / 2, zb) for r in SEAM_RIBS]
    else:
        y0, y1 = SEAM_RIB[0] + 10.0, SEAM_RIB[1] - 10.0
        n = max(2, int((y1 - y0) // 50) + 1)
        bolts = [(y0 + i * (y1 - y0) / (n - 1), zb) for i in range(n)]
    a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts, seam_envelope(envelope_case()))
    col = (0.80, 0.80, 0.82)
    rot = [((1, 0, 0), 180)]   # Sichtfläche aufs Bett
    if P.GRATER_LID:
        rec = grater_recess()
        cuts = grater.frame_cuts("z", TOP, 1, rec, P.T_LID, seam_u=P.SPLIT_X)
        a, b = a.cut(cuts), b.cut(cuts)
        ia, ib = grater.insert_pair("z", TOP, 1, rec, P.SPLIT_X)
        ins = [Spec("deckel_einleger_vorn", ia, (0.80, 0.80, 0.83), explode=(-25, 0, 200)),
               Spec("deckel_einleger_hinten", ib, (0.80, 0.80, 0.83), explode=(25, 0, 200))]
        return [Spec("deckel_vorn", a, col, print_rot=rot, explode=(-25, 0, 120)),
                Spec("deckel_hinten", b, col, print_rot=rot, explode=(25, 0, 120))] + ins, 0
    tools = (holes_z(through, P.INNER_H - 1, TOP + 1)
             + holes_z(blind, P.INNER_H + P.VENT_BLIND_SKIN, TOP + 1))
    a, b = cut_holes_split(a, b, P.SPLIT_X, [q[0] for q in through + blind], tools)
    return [Spec("deckel_vorn", a, col, print_rot=rot, explode=(-25, 0, 120)),
            Spec("deckel_hinten", b, col, print_rot=rot, explode=(25, 0, 120))], len(through)
