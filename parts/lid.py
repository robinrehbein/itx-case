"""Deckel: voller Grundriss mit gerundeter Oberkante, Lochfeld über der GPU (TOP_VENT),
Magnettaschen über den Seitenwänden, Dome für die Wandlaschen."""
import params as P
from parts.common import (Spec, rrect_prism, hex_grid, holes_z, cyl_z, fuse_all, cut_all,
                          dome_lid, split_with_flanges, envelope_case)

TOP = P.INNER_H + P.T_LID


def dome_positions():
    d = []
    d += [(5.0, y) for y in P.FRONT_TABS_Y]
    d += [(P.INNER_L - 5.0, y) for y in P.REAR_TABS_Y_TOP]
    d += [(x, P.MID_Y1 + P.TAB_D / 2) for x in P.MID_TABS_X_TOP]
    return d


def magnet_positions():
    yl = P.OUT_Y0 + P.MAGNET_FROM_OUTER
    yr = P.OUT_Y1 - P.MAGNET_FROM_OUTER
    return [(x, yl) for x in P.MAGNET_X] + [(x, yr) for x in P.MAGNET_X]


def vent_points():
    v = P.TOP_VENT
    keep = [(P.SPLIT_X - 11, P.SPLIT_X + 11, -999, 999)]
    return hex_grid(v["x0"], v["x1"], v["y0"], v["y1"], keep)


def build():
    plate = rrect_prism(P.OUT_X0, P.OUT_X1, P.OUT_Y0, P.OUT_Y1, P.CORNER_R, P.INNER_H, TOP)
    top_edges = [e for e in plate.Edges
                 if abs(e.BoundBox.ZMin - TOP) < 1e-6 and abs(e.BoundBox.ZMax - TOP) < 1e-6]
    # Rundung oben; die ersten 1 mm auf dem Bett als 45°-Fase, damit die Kante druckbar bleibt
    plate = plate.makeFillet(P.LID_EDGE_R, top_edges).common(
        plate.makeChamfer(P.LID_EDGE_BED_CHAMFER, top_edges))
    pts = vent_points()
    plate = cut_all(plate, holes_z(pts, P.INNER_H - 1, TOP + 1))

    adds, cuts = [], []
    for (x, y) in dome_positions():
        d, h = dome_lid(x, y)
        adds.append(d)
        cuts.append(h)
    for (x, y) in magnet_positions():
        cuts.append(cyl_z(x, y, P.INNER_H - 0.01, P.INNER_H + P.MAGNET_H, P.MAGNET_D / 2))
    shape = cut_all(fuse_all([plate] + adds), cuts)

    z0 = P.INNER_H - P.FLANGE_D
    ribs = [(11.0, P.MID_Y0 - 1.0, z0, P.INNER_H),
            (P.MID_Y1 + 1.0, P.INNER_W - 11.0, z0, P.INNER_H)]
    zb = P.INNER_H - 5.0
    bolts = [(30.0, zb), (70.0, zb), (120.0, zb), (200.0, zb), (245.0, zb)]
    a, b = split_with_flanges(shape, P.SPLIT_X, ribs, bolts, envelope_case())
    col = (0.80, 0.80, 0.82)
    rot = [((1, 0, 0), 180)]   # Sichtfläche aufs Bett
    return [Spec("deckel_vorn", a, col, print_rot=rot, explode=(-25, 0, 120)),
            Spec("deckel_hinten", b, col, print_rot=rot, explode=(25, 0, 120))], len(pts)
