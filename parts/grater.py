"""Reibe im Stil des Mac Pro 2019 (nur Variante C): Rahmen mit Lippe außen, Einleger von
innen, dazwischen Filtergewebe, gehalten von Magneten 6 x 1 mm.

Der Einleger hat außen Kegelmulden (45°) im Wabenraster, die sich an Graten treffen, und
Löcher auf den Dreieckszentren (dort treffen sich drei Mulden). Die Spitze jeder Mulde geht
als kleines Loch durch. Gedruckt wird der Einleger mit der
Außenseite nach oben: die Mulden sind dann nach oben offene 45°-Flächen, die Innenseite
liegt flach auf dem Bett.

Eine Fläche wird beschrieben durch:
  axis   "x" (Front, Rückwand), "y" (Seitenwände) oder "z" (Deckel): Flächennormale
  out    Koordinate der Außenseite des Einlegers
  sgn    +1, wenn die Außenseite in +axis liegt (Deckel, Rückwand, rechts), sonst -1
  (u, v) Koordinaten in der Fläche: x-Flächen (y, z), y-Flächen (x, z), Deckel (x, y)
"""
import math

import Part
from FreeCAD import Vector as V

import params as P
from parts.common import rrect_prism, rrect_x, rrect_y

SQ3 = math.sqrt(3.0)


def _pt(axis, w, u, v):
    return {"x": V(w, u, v), "y": V(u, w, v), "z": V(u, v, w)}[axis]


def _dir(axis, s):
    return {"x": V(s, 0, 0), "y": V(0, s, 0), "z": V(0, 0, s)}[axis]


def _box(axis, u0, u1, v0, v1, w0, w1):
    from parts.common import box
    if axis == "x":
        return box(w0, w1, u0, u1, v0, v1)
    if axis == "y":
        return box(u0, u1, w0, w1, v0, v1)
    return box(u0, u1, v0, v1, w0, w1)


def slab(axis, w0, w1, u0, u1, v0, v1, r):
    """Abgerundetes Rechteck in (u, v), Dicke w0..w1 entlang axis."""
    if axis == "x":
        return rrect_x(w0, w1, u0, u1, v0, v1, r)
    if axis == "y":
        return rrect_y(u0, u1, v0, v1, w0, w1, r)
    return rrect_prism(u0, u1, v0, v1, r, w0, w1)


def lattice(u0, u1, v0, v1, anchor_u=None):
    """Muldenmitten (A) und Lochmitten (B, C) im Fenster, zentriert. anchor_u: eine Linie
    u = konst. läuft genau durch Muldenmitten und Löcher (dort liegt die Fuge)."""
    p = P.GR_PITCH
    dv = p * SQ3 / 2
    m_a = 1.0
    m_b = P.GR_HOLE_D / 2 + 0.5
    nu = int((u1 - u0) / p) + 2
    nv = int((v1 - v0) / dv) + 2
    cu, cv = (u0 + u1) / 2 if anchor_u is None else anchor_u, (v0 + v1) / 2
    A, BC = [], []
    for j in range(-nv, nv + 1):
        for i in range(-nu, nu + 1):
            u = cu + i * p + (j % 2) * p / 2
            v = cv + j * dv
            if u0 + m_a <= u <= u1 - m_a and v0 + m_a <= v <= v1 - m_a:
                A.append((u, v))
            for (du, dvv) in ((p / 2, p * SQ3 / 6), (0.0, p * SQ3 / 3)):
                bu, bv = u + du, v + dvv
                if u0 + m_b <= bu <= u1 - m_b and v0 + m_b <= bv <= v1 - m_b:
                    BC.append((bu, bv))
    return A, sorted(set((round(a, 4), round(b, 4)) for (a, b) in BC))


def insert_tools(axis, out, sgn, win, anchor_u=None):
    """Kegel von außen und Löcher von innen für ein Fenster (u0, u1, v0, v1)."""
    A, BC = lattice(*win, anchor_u=anchor_u)
    R, e = P.GR_R, 0.3
    inner = out - sgn * P.GR_T
    tools = []
    for (u, v) in A:
        base = _pt(axis, out + sgn * e, u, v)
        tools.append(Part.makeCone(R + e, 0.0, R + e, base, _dir(axis, -sgn)))
    for (u, v) in BC:
        tools.append(Part.makeCylinder(P.GR_HOLE_D / 2, P.GR_HOLE_H + 1.0,
                                       _pt(axis, inner - sgn * 1.0, u, v), _dir(axis, sgn)))
    return tools


def magnet_spots(rect, seam_u=None):
    """Magnetmitten auf dem Auflagerand: Seitenmitten, lange Seiten zusätzlich bei 1/4 und 3/4
    (über 250 mm in Sechsteln). Mit seam_u fallen Magnete nahe der Fuge weg."""
    u0, u1, v0, v1 = rect
    h = P.GR_LAP / 2
    spots = []
    for (a0, a1, fixed, along_u) in ((u0, u1, v0 + h, True), (u0, u1, v1 - h, True),
                                     (v0, v1, u0 + h, False), (v0, v1, u1 - h, False)):
        n = 5 if (a1 - a0) > 250 else (3 if (a1 - a0) > 150 else 1)
        for k in range(n):
            t = (k + 1) / (n + 1)
            a = a0 + 20 + (a1 - a0 - 40) * t if n > 1 else (a0 + a1) / 2
            spots.append((a, fixed) if along_u else (fixed, a))
    if seam_u is not None:
        spots = [q for q in spots if abs(q[0] - seam_u) >= 12.0]
    return spots


def rects(recess):
    """Tasche -> (Tasche, Einleger, Fenster)."""
    u0, u1, v0, v1 = recess
    c, L = P.GR_CLEAR, P.GR_LAP
    ins = (u0 + c, u1 - c, v0 + c, v1 - c)
    win = (ins[0] + L, ins[1] - L, ins[2] + L, ins[3] - L)
    return recess, ins, win


def frame_cuts(axis, outer, sgn, recess, thick, r=6.0, seam_u=None):
    """Schnitte im Rahmen: Fenster durch, Tasche von innen bis zur Lippe, Magnettaschen in
    der Lippe. outer = Außenfläche des Rahmens, thick = Rahmendicke."""
    rec, ins, win = rects(recess)
    lip_in = outer - sgn * P.GR_LIP              # Innenseite der Lippe
    far = outer - sgn * (thick + 1.0)
    w = sorted((outer + sgn * 1.0, far))
    cuts = [slab(axis, w[0], w[1], *win, r)]
    w = sorted((lip_in, far))
    cuts.append(slab(axis, w[0], w[1], *rec, r + P.GR_LAP))
    d, depth = P.GR_MAG
    for (u, v) in magnet_spots(ins, seam_u):
        cuts.append(Part.makeCylinder(d / 2, depth + 0.01,
                                      _pt(axis, lip_in - sgn * 0.01, u, v), _dir(axis, sgn)))
    return cuts


def insert(axis, outer, sgn, recess, r=6.0, seam_u=None):
    """Einleger: Außenseite liegt über dem Filter an der Lippe."""
    rec, ins, win = rects(recess)
    out = outer - sgn * (P.GR_LIP + P.GR_FILTER)
    w = sorted((out, out - sgn * P.GR_T))
    body = slab(axis, w[0], w[1], *ins, r + P.GR_LAP - P.GR_CLEAR)
    tools = insert_tools(axis, out, sgn, win, anchor_u=seam_u)
    d, depth = P.GR_MAG
    for (u, v) in magnet_spots(ins, seam_u):
        tools.append(Part.makeCylinder(d / 2, depth + 0.01,
                                       _pt(axis, out + sgn * 0.01, u, v), _dir(axis, -sgn)))
    return body.cut(tools)


def insert_pair(axis, outer, sgn, recess, seam_u, r=6.0):
    """Ein durchgehender Einleger, an der Fuge u = seam_u in zwei Teile geteilt. Im
    Reibenfeld ist die Fuge gerade und liegt genau auf einer Reihe aus Muldenmitten und
    Löchern. Im glatten Auflagerand greift die innere Hälfte des vorderen Teils GR_SEAM_LAP
    weit unter das hintere Teil; so tragen sich die Teile an beiden Enden der Fuge."""
    from parts.common import BIG
    full = insert(axis, outer, sgn, recess, r, seam_u)
    wv0, wv1 = rects(recess)[2][2:]
    out = outer - sgn * (P.GR_LIP + P.GR_FILTER)
    wm = out - sgn * P.GR_T / 2
    g, L, S = P.GR_SEAM_GAP, P.GR_SEAM_LAP, seam_u

    def inner_half(c):
        return (-BIG, c) if sgn > 0 else (c, BIG)

    def rims(u1, c, m):
        w0, w1 = inner_half(c)
        return _box(axis, -BIG, u1, -BIG, wv0 - m, w0, w1).fuse(
            _box(axis, -BIG, u1, wv1 + m, BIG, w0, w1))

    reg_a = _box(axis, -BIG, S - g / 2, -BIG, BIG, -BIG, BIG).fuse(
        rims(S + L - g / 2, wm - sgn * g / 2, 0.0))
    reg_b = _box(axis, S + g / 2, BIG, -BIG, BIG, -BIG, BIG).cut(
        rims(S + L + g / 2, wm + sgn * g / 2, -g))
    return full.common(reg_a), full.common(reg_b)


def open_fraction(n=240):
    """Offener Anteil der Reibe in der Projektion (Abtastung einer Wabenzelle)."""
    p, R, t = P.GR_PITCH, P.GR_R, P.GR_T
    rh, hh = P.GR_HOLE_D / 2, P.GR_HOLE_H
    dv = p * SQ3 / 2
    A = [(i * p + (j % 2) * p / 2, j * dv) for j in range(-2, 4) for i in range(-2, 4)]
    BC = [(u + du, v + dw) for (u, v) in A for (du, dw) in ((p / 2, p * SQ3 / 6), (0, p * SQ3 / 3))]
    hit = 0
    for a in range(n):
        for b in range(n):
            u, v = p * (a + 0.5) / n, dv * (b + 0.5) / n
            od = max(0.0, R - min(math.hypot(u - x, v - y) for (x, y) in A))
            idp = hh if min(math.hypot(u - x, v - y) for (x, y) in BC) <= rh else 0.0
            if od >= t or od + idp >= t:
                hit += 1
    return hit / (n * n)
