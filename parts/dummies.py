"""Dummy-Komponenten für Kollisionsprüfung und Montageansicht."""
import params as P
from parts.common import Spec, box, cyl_x, fuse_all
from parts.panels import io_window


def board():
    pcb = box(P.BOARD_X0, P.BOARD_X1, P.BOARD_Y0, P.BOARD_Y1, P.BOARD_Z0, P.BOARD_Z1)
    iy0, iy1, iz0, iz1 = io_window()
    io = box(P.BOARD_X1 - 24, P.INNER_L, P.BOARD_Y1, iy1 - 1.5, iz0 + 1.5, iz1 - 1.5)
    return Spec("dummy_board", pcb.fuse(io), (0.10, 0.45, 0.20), group="dummy", printable=False)


def cooler():
    s = box(P.SOCKET_X - P.COOLER_KEEP_X, P.SOCKET_X + P.COOLER_KEEP_X,
            P.BOARD_Y1, P.BOARD_Y1 + P.COOLER["h"],
            P.SOCKET_Z - P.COOLER_KEEP_Z, P.SOCKET_Z + P.COOLER_KEEP_Z)
    return Spec("dummy_nhd15", s, (0.55, 0.40, 0.30), group="dummy", printable=False)


def gpu():
    g = P.GPU
    body = box(P.GPU_X0, P.GPU_BRACKET_X0, P.GPU_Y0, P.GPU_Y1, P.GPU_Z0, P.GPU_Z0 + g["H"])
    # Freiraum unter der Lasche (Leiste): Karte nahe am Blech nur bis Leistenunterkante
    notch = box(P.INNER_L - P.GPU_RAIL_DEPTH - 1, P.INNER_L, P.GPU_Y0 - 1, P.GPU_Y1 + 1,
                P.GPU_RAIL_Z0, 999)
    body = body.cut(notch)
    bz0 = P.GPU_TAB_Z - P.BRACKET_LEN
    bracket = box(P.GPU_BRACKET_X0, P.INNER_L, P.GPU_Y1 - g["slots"] * P.SLOT_PITCH, P.GPU_Y1,
                  bz0, P.GPU_RAIL_Z0)
    cables = box(P.GPU_X0, P.INNER_L - P.GPU_RAIL_DEPTH - 1, P.GPU_Y0, P.GPU_Y1,
                 P.GPU_Z0 + g["H"], P.GPU_Z0 + g["H"] + P.GPU_CABLE_BEND)
    return Spec("dummy_gpu", fuse_all([body, bracket, cables]), (0.75, 0.10, 0.10),
                group="dummy", printable=False)


def psu():
    s = box(P.PSU_X0, P.PSU_X1, P.PSU_Y0, P.PSU_Y1, P.PSU_Z0, P.PSU_Z1)
    return Spec("dummy_netzteil", s, (0.15, 0.15, 0.15), group="dummy", printable=False)


def riser():
    x0, x1 = P.BOARD_X1 - P.PCIE_SLOT_FROM_IO - P.PCIE_SLOT_LEN, P.BOARD_X1 - P.PCIE_SLOT_FROM_IO
    zs = P.BOARD_Z0 + P.PCIE_SLOT_FROM_BOTTOM
    plug = box(x0, x1, P.BOARD_Y1, P.BOARD_Y1 + 14, zs - 6, zs + 6)
    drop = box(x0, x1, P.MID_Y1 + 1.5, P.BOARD_Y1 + 14, 1.0, zs - 6)
    through = box(x0, x1, 72.0, P.MID_Y1 + 1.5, 1.0, 8.5)
    fx0, fx1 = P.GPU_FINGER_X0 - 4, P.GPU_FINGER_X1 + 4
    pcb = box(fx0 - 6, fx1 + 6, 68.0, 84.0, 12.0, 13.6)
    sock = box(fx0, fx1, P.GPU_PCB_Y - 5.5, P.GPU_PCB_Y + 5.5, 13.6, P.GPU_Z0 + 8)
    return Spec("dummy_riser", fuse_all([plug, drop, through, pcb, sock]), (0.85, 0.75, 0.10),
                group="dummy", printable=False)


def keepouts():
    # Körper + Mutter, dahinter Raum für Anschlüsse und Leitung zum Mainboard (F_PANEL)
    btn = cyl_x(P.BUTTON_Y, P.BUTTON_Z, 0, P.BUTTON_DEPTH, 11.0).fuse(
        cyl_x(P.BUTTON_Y, P.BUTTON_Z, P.BUTTON_DEPTH, P.BUTTON_DEPTH + P.BUTTON_CABLE, 7.0))
    c14 = box(P.INNER_L - P.C14_DEPTH, P.INNER_L, P.C14_Y - 15, P.C14_Y + 15,
              P.C14_Z - 12, P.C14_Z + 12)
    return [Spec("dummy_taster", btn, (0.6, 0.6, 0.6), group="dummy", printable=False),
            Spec("dummy_c14", c14, (0.6, 0.6, 0.6), group="dummy", printable=False)]


def build():
    return [board(), cooler(), gpu(), psu(), riser()] + keepouts()
