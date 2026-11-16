"""Deckel: voller Grundriss mit gerundeter Oberkante, ein Lochfeld über die ganze Fläche
(TOP_VENT), Magnettaschen über den Seitenwänden, Dome für die Wandlaschen."""
import params as P
from parts import grater
from parts.common import (Spec, rrect_prism, hex_grid, holes_z, split_blind, cyl_z, fuse_all, cut_all,
                          dome_lid, split_with_flanges, envelope_case, cut_holes_split)

TOP = P.INNER_H + P.T_LID


def dome_positions():
    d = []
    d += [(5.0, y) for y in P.FRONT_TABS_Y]
    d += [(P.INNER_L - 5.0, y) for y in P.REAR_TABS_Y_TOP]
    if P.TRAY_TABS_X:
        d += [(x, P.Y_BASE - P.TAB_D / 2) for x in P.TRAY_TABS_X]
    return d


def magnet_positions():
    yl = P.OUT_Y0 + P.MAGNET_FROM_OUTER
    yr = P.OUT_Y1 - P.MAGNET_FROM_OUTER
    return [(x, yl) for x in P.MAGNET_X] + [(x, yr) for x in P.MAGNET_X]


# Fugenflansch (y0, y1, z0, z1). A: neben dem Kabelbogen der Karte, B: vor dem Träger.
if P.LYING:
    SEAM_RIB = (P.GPU_V1 + 6.0, P.INNER_W - 11.0, P.INNER_H - P.FLANGE_D, P.INNER_H)
else:
    SEAM_RIB = (11.0, P.Y_BASE - 6.0, P.INNER_H - P.FLANGE_D, P.INNER_H)


def vent_sets():
    """Feld läuft ohne Lücke über die Trennfuge (Lochspalte auf der Fuge).
    Rückgabe: (durchgehend, blind). Blind sind die Löcher über Fugenflansch und Domen."""
    v = P.TOP_VENT
    pts = hex_grid(v["x0"], v["x1"], v["y0"], v["y1"], corner_r=v["r"], col_at=P.SPLIT_X)
    rects = [(P.SPLIT_X - P.FLANGE_T, P.SPLIT_X + P.FLANGE_T, SEAM_RIB[0], SEAM_RIB[1])]
    if not P.LYING:   # Oberkante des Board-Trägers
        rects.append((-999, 999, P.Y_BASE, P.Y_BASE + P.T_TRAY))
    discs = [(x, y, P.DOME_D / 2) for (x, y) in dome_positions()]
    return split_blind(pts, rects, discs)


def vent_points():
    """Offene Löcher des Deckels (bei C keine, dort sitzt die Reibe)."""
    return [] if P.GRATER else vent_sets()[0]


def grater_recesses():
    """C: je Deckelhälfte eine Tasche (x0, x1, y0, y1); über der Fuge bleibt ein Steg."""
    v = P.TOP_VENT
    y1 = min(v["y1"], P.Y_BASE - 12.0) if P.Y_BASE else v["y1"]
    return [(v["x0"], P.SPLIT_X - 5.0, v["y0"], y1), (P.SPLIT_X + 5.0, v["x1"], v["y0"], y1)]


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
    shape = cut_all(fuse_all([plate] + adds), cuts)

    ribs = [SEAM_RIB]
    zb = P.INNER_H - 5.0
    y0, y1 = SEAM_RIB[0] + 10.0, SEAM_RIB[1] - 10.0
    n = max(2, int((y1 - y0) // 50) + 1)
    bolts = [(y0 + i * (y1 - y0) / (n - 1), zb) for i in range(n)]
    a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts, envelope_case())
    col = (0.80, 0.80, 0.82)
    rot = [((1, 0, 0), 180)]   # Sichtfläche aufs Bett
    if P.GRATER:
        ra, rb = grater_recesses()
        a = a.cut(grater.frame_cuts("z", TOP, 1, ra, P.T_LID))
        b = b.cut(grater.frame_cuts("z", TOP, 1, rb, P.T_LID))
        ins = [Spec("deckel_einleger_vorn", grater.insert("z", TOP, 1, ra), (0.80, 0.80, 0.83),
                    explode=(-25, 0, 200)),
               Spec("deckel_einleger_hinten", grater.insert("z", TOP, 1, rb), (0.80, 0.80, 0.83),
                    explode=(25, 0, 200))]
        return [Spec("deckel_vorn", a, col, print_rot=rot, explode=(-25, 0, 120)),
                Spec("deckel_hinten", b, col, print_rot=rot, explode=(25, 0, 120))] + ins, 0
    tools = (holes_z(through, P.INNER_H - 1, TOP + 1)
             + holes_z(blind, P.INNER_H + P.VENT_BLIND_SKIN, TOP + 1))
    a, b = cut_holes_split(a, b, P.SPLIT_X, [q[0] for q in through + blind], tools)
    return [Spec("deckel_vorn", a, col, print_rot=rot, explode=(-25, 0, 120)),
            Spec("deckel_hinten", b, col, print_rot=rot, explode=(25, 0, 120))], len(through)
