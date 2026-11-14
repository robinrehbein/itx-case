"""Dummy-Komponenten für Kollisionsprüfung und Montageansicht. Entstehen im Block
(x=u, y=v, z=w) und werden mit place() ins Gehäuse gestellt."""
import params as P
from parts.common import Spec, box, cyl_x, fuse_all, place


def _spec(name, shape, color):
    return Spec(name, place(shape), color, group="dummy", printable=False)


def board():
    pcb = box(P.BOARD_X0, P.BOARD_X1, P.BOARD_V0, P.BOARD_V1, P.BOARD_W0, P.BOARD_W1)
    io = box(P.BOARD_X1 - 24, P.INNER_L, P.IO_V0 + 1.5, P.IO_V1 - 1.5,
             P.BOARD_W1, P.IO_W1 - 1.5)
    b = P.CPU_BACKPLATE
    back = box(P.SOCKET_X - b["w"] / 2, P.SOCKET_X + b["w"] / 2,
               P.SOCKET_V - b["w"] / 2, P.SOCKET_V + b["w"] / 2,
               P.BOARD_W0 - b["t"], P.BOARD_W0)
    return _spec("dummy_board", fuse_all([pcb, io, back]), (0.10, 0.45, 0.20))


def cooler():
    s = box(P.SOCKET_X - P.COOLER_KEEP_X, P.SOCKET_X + P.COOLER_KEEP_X,
            P.SOCKET_V - P.COOLER_KEEP_V, P.SOCKET_V + P.COOLER_KEEP_V,
            P.BOARD_W1, P.COOLER_W1)
    return _spec("dummy_nhd15", s, (0.55, 0.40, 0.30))


def gpu():
    g = P.GPU
    body = box(P.GPU_X0, P.GPU_BRACKET_X0, P.GPU_V0, P.GPU_V1, P.GPU_W0, P.GPU_W1)
    # Freiraum über der Leiste: Karte nahe am Blech nur bis Leistenunterkante
    notch = box(P.INNER_L - P.GPU_RAIL_DEPTH - 1, P.INNER_L, P.GPU_V0 - 1, P.GPU_V1 + 1,
                P.GPU_RAIL_W0, 999)
    body = body.cut(notch)
    bw0 = P.GPU_TAB_W - P.BRACKET_LEN
    bracket = box(P.GPU_BRACKET_X0, P.INNER_L, P.GPU_V1 - g["slots"] * P.SLOT_PITCH, P.GPU_V1,
                  bw0, P.GPU_RAIL_W0)
    cables = box(P.GPU_X0, P.INNER_L - P.GPU_CABLE_REAR_FREE, P.GPU_V0, P.GPU_V1,
                 P.GPU_W1, P.GPU_W1 + P.GPU_CABLE_BEND)
    # Kontaktfinger im Slot
    fingers = box(P.GPU_FINGER_X0, P.GPU_FINGER_X1, P.GPU_PCB_V - 0.8, P.GPU_PCB_V + 0.8,
                  P.BOARD_W1 + 0.5, P.GPU_W0)
    return _spec("dummy_gpu", fuse_all([body, bracket, cables, fingers]), (0.75, 0.10, 0.10))


def psu():
    s = box(P.PSU_X0, P.PSU_X1, P.PSU_V0, P.PSU_V1, P.PSU_W0, P.PSU_W1)
    return _spec("dummy_netzteil", s, (0.15, 0.15, 0.15))


def keepouts():
    # Taster: Körper + Mutter, dahinter Raum für Anschlüsse und Leitung zum F_PANEL
    btn = cyl_x(P.BUTTON_V, P.BUTTON_W, 0, P.BUTTON_DEPTH, 11.0).fuse(
        cyl_x(P.BUTTON_V, P.BUTTON_W, P.BUTTON_DEPTH, P.BUTTON_DEPTH + P.BUTTON_CABLE, 7.0))
    c14 = box(P.INNER_L - P.C14_DEPTH, P.INNER_L, P.C14_V - 15, P.C14_V + 15,
              P.C14_W_POS - 12, P.C14_W_POS + 12)
    return [_spec("dummy_taster", btn, (0.6, 0.6, 0.6)),
            _spec("dummy_c14", c14, (0.6, 0.6, 0.6))]


def build():
    return [board(), cooler(), gpu(), psu()] + keepouts()
