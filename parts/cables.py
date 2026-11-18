"""Kabelwege (nur stehende Varianten) als Züge aus Quadern im Block (x=u, y=v, z=w).
Sie gehen als Dummies in die Kollisionsprüfung ein und liefern die Längen für kurze
Custom-Kabel. Die Anschlusslagen am Board sind Annahmen (params: ATX24_V, EPS_U,
GPU_POWER_U), mit dem neuen Board prüfen."""
import params as P
from parts.common import Spec, box, fuse_all, place

BACK = -P.T_TRAY - P.TRAY_BACK / 2      # Mitte des Kabelraums hinter dem Träger


def routes():
    """name -> (Punkte, Querschnitt (u, v, w), Bauteile an den Enden)."""
    v1 = P.PSU_V1
    return {
        # 24-Pin flach: hinter den Träger, unten wieder durch den Durchbruch vor dem Board
        "kabel_24pin": ([(46, v1, 70), (46, 222, 70), (46, 222, BACK), (46, P.ATX24_V, BACK),
                         (103, P.ATX24_V, BACK), (103, P.ATX24_V, 15),
                         (P.BOARD_X0 - 2, P.ATX24_V, 15)], (20, 10, 6), ("netzteil", "board")),
        # EPS 8-Pin über den Kühler bis über die Buchse an der Board-Oberkante
        "kabel_eps": ([(30, v1, 100), (30, 230.5, 100), (P.EPS_U, 230.5, 100),
                       (P.EPS_U, 230.5, 15)], (10, 10, 6), ("netzteil",)),
        # 2 x 8-Pin zur Karte: vor dem Kühler nach unten, im Kabelbogen zur Buchse
        "kabel_gpu": ([(62, v1, 118), (62, 222, 118), (62, 222, 160), (62, 40, 160),
                       (P.GPU_POWER_U, 40, 160), (P.GPU_POWER_U, 40, P.GPU_W1 + 2)],
                      (14, 14, 14), ("netzteil", "gpu")),
        # Kaltgerätekabel C14 -> Netzteil an der linken Wand entlang, unter dem Kühler
        "kabel_c14": ([(P.INNER_L - P.C14_DEPTH, P.C14_V, P.C14_W_POS),
                       (290, P.C14_V, P.C14_W_POS), (290, 70, P.C14_W_POS), (290, 70, 178),
                       (85, 70, 178), (85, 218, 178), (85, 218, 40), (68, 218, 40),
                       (68, v1, 40)], (9, 9, 9), ("c14", "netzteil")),
    }


def _boxes(pts, size):
    h = [s / 2 for s in size]
    out = []
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        k = [j for j in range(3) if abs(p[j] - q[j]) > 1e-9][0]
        lo, hi = [], []
        for j in range(3):
            if j == k:
                a, b = sorted((p[j], q[j]))
                e = h[k]
                # an inneren Ecken um den halben Querschnitt verlängern, an den Enden nicht
                start_inner, end_inner = i > 0, i + 1 < len(pts) - 1
                lo_inner = start_inner if p[j] < q[j] else end_inner
                hi_inner = end_inner if p[j] < q[j] else start_inner
                lo.append(a - (e if lo_inner else 0.0))
                hi.append(b + (e if hi_inner else 0.0))
            else:
                lo.append(p[j] - h[j])
                hi.append(p[j] + h[j])
        out.append(box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    return out


def length(pts):
    return sum(sum(abs(a - b) for a, b in zip(pts[i], pts[i + 1])) for i in range(len(pts) - 1))


def build():
    if P.LYING:
        return [], {}
    specs, info = [], {}
    for name, (pts, size, ends) in routes().items():
        specs.append(Spec(name, place(fuse_all(_boxes(pts, size))), (0.95, 0.85, 0.20),
                          group="dummy", printable=False))
        info[name] = (length(pts), ends)
    return specs, info
