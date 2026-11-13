"""Alle Maße in mm. Einzige Quelle für Maße – Bauteile lesen nur von hier.

Koordinaten (Innenraum):
  x: vorn -> hinten   (0 = Innenseite Frontwand)
  y: links -> rechts  (0 = Innenseite linke Seitenwand, von vorn gesehen)
  z: unten -> oben    (0 = Oberseite Boden)
"""

# --------------------------------------------------------------------------
# Auswahl / Optionen
# --------------------------------------------------------------------------
import os as _os

GPU_PROFILE = _os.environ.get("GPU_PROFILE", "reaper")   # "reaper" (PowerColor RX 9070 XT Reaper) | "max" (340x140x65)
GPU_SLOTS = 3            # Slotöffnung in der Rückwand: 3 (Standard) | 4 (Option, siehe README)
PSU_TYPE = _os.environ.get("PSU_TYPE", "SFX")         # "SFX" | "SFX-L"
USB_C = False            # optionaler USB-C-Ausschnitt in der Front
COOLER_PROFILE = "NH-D15"  # Noctua NH-D15 (Original, 165 mm)

# --------------------------------------------------------------------------
# Drucker (Voron 2.4 300)
# --------------------------------------------------------------------------
BED = (290.0, 290.0, 270.0)

# --------------------------------------------------------------------------
# Wände
# --------------------------------------------------------------------------
T_WALL = 4.0        # Seitenwände, Front, Rückwand
T_FLOOR = 5.0
T_LID = 5.0
T_MID = 5.0         # Mittelwand
CORNER_R = 22.0     # Grundriss-Eckradius außen
LID_EDGE_R = 2.5    # Rundung Deckel-Oberkante
LID_EDGE_BED_CHAMFER = 1.0  # davon die äußersten 1 mm als 45°-Fase (liegt auf dem Druckbett)

# --------------------------------------------------------------------------
# Komponenten
# --------------------------------------------------------------------------
BOARD = 170.0
PCB_T = 1.6
STANDOFF = 6.0

COOLERS = {
    # Höhe ab Platinenoberseite; Breite in z, Tiefe in x (Lüfter blasen +x)
    "NH-D15": dict(h=165.0, w=150.0, d=161.0),
    "NH-D15 G2": dict(h=168.0, w=150.0, d=161.0),
}
COOLER = COOLERS[COOLER_PROFILE]

GPUS = {
    # L inkl. Slotblech, H ab Unterkante Kontaktfinger, T = Dicke, slots = belegte Slots
    # Reaper: Händlerangaben 289x111x41 (Karte) / 304x127x42 (mit Blech) – konservativ
    "reaper": dict(L=304.0, H=127.0, T=42.0, slots=2),
    "max":    dict(L=340.0, H=140.0, T=65.0, slots=3),
}
GPU = GPUS[GPU_PROFILE]
GPU_THICK_MAX = 65.0
GPU_CABLE_BEND = 35.0          # Kabelbogen über der Karte (Stromstecker oben)
GPU_PCB_FROM_BACKPLATE = 4.0   # Platinenebene hinter der Backplate
GPU_FINGER_FROM_BRACKET = 43.0 # Abstand Slotblech -> Beginn Kontaktfinger (CEM ~42-43)
GPU_FINGER_LEN = 89.0          # x16
GPU_Z0 = 25.0                  # Unterkante Kontaktfinger über Boden (Riser-Halter Mitte)
# Slotblech (PCIe CEM, Full Height) – UNSICHER, mit Passtest prüfen
BRACKET_LEN = 120.02           # Gesamtlänge Blech
BRACKET_TAB_ABOVE_FINGERS = 112.0  # Oberseite Lasche über Fingerunterkante
BRACKET_TAB_DEPTH = 11.43      # Lasche ragt so weit nach innen
SLOT_PITCH = 20.32
GPU_RAIL_H = 6.0               # Leiste unter der Lasche (mit M3-Mutternkanal)

PSUS = {
    "SFX":   dict(w=125.0, h=63.5, d=100.0),
    "SFX-L": dict(w=125.0, h=63.5, d=130.0),
}
PSU = PSUS[PSU_TYPE]
PSU_X0 = 30.0          # Vorderkante Netzteil
PSU_BACK_GAP = 25.0    # Rückseite -> Seitenwand (Platz für Winkel-C13 + Abluft)
PSU_LIFT = 11.0        # Unterkante Netzteil über Boden (Lüfter-Ansaugspalt)

# --------------------------------------------------------------------------
# Innenmaße (Layout: Sandwich mit Mittelwand)
# --------------------------------------------------------------------------
INNER_L = 358.0
INNER_H = 210.0
GPU_AIR_WALL = 3.0     # Backplate -> Mittelwand
GPU_FAN_AIR = 17.0     # Lüfter -> Seitenwand (bei 65 mm Karte)
GPU_CHAMBER = GPU_AIR_WALL + GPU_THICK_MAX + GPU_FAN_AIR      # 85
BOARD_CHAMBER = 181.0
INNER_W = GPU_CHAMBER + T_MID + BOARD_CHAMBER                  # 271

# --------------------------------------------------------------------------
# Außen
# --------------------------------------------------------------------------
OUT_X0, OUT_X1 = -T_WALL, INNER_L + T_WALL
OUT_Y0, OUT_Y1 = -T_WALL, INNER_W + T_WALL
OUT_L = OUT_X1 - OUT_X0
OUT_W = OUT_Y1 - OUT_Y0
OUT_H = T_FLOOR + INNER_H + T_LID
CORNER_RI = CORNER_R - T_WALL          # Innenradius der Eckbögen
FLAT_Y0 = OUT_Y0 + CORNER_R            # Front/Rückwand eben zwischen FLAT_Y0..FLAT_Y1
FLAT_Y1 = OUT_Y1 - CORNER_R
FLAT_X0 = OUT_X0 + CORNER_R            # Seitenwand gerade zwischen FLAT_X0..FLAT_X1
FLAT_X1 = OUT_X1 - CORNER_R

# Sockel (Mac-Studio-Fuß)
PLINTH_INSET = 16.0
PLINTH_H = 12.0
PLINTH_T = 3.0
PLINTH_LIP_W = 6.0     # Bodenlippe innen (Gummifüße)
PLINTH_LIP_T = 2.0
PLINTH_R = CORNER_R - PLINTH_INSET
PLINTH_TABS = [(100.0, "L"), (260.0, "L"), (100.0, "R"), (260.0, "R")]
# Schraubpfosten und Fugenflansche stehen frei hinter dem Ring (Löcher bleiben durchgängig)
PLINTH_POST_D = 11.0
PLINTH_POST_OFF = 9.5      # Pfostenmitte ab Ring-Innenfläche -> 4 mm Luft dahinter
PLINTH_FLANGE_GAP = 4.0    # Flansch ab Ring-Innenfläche

# --------------------------------------------------------------------------
# Lage der Komponenten
# --------------------------------------------------------------------------
MID_Y0 = GPU_CHAMBER
MID_Y1 = GPU_CHAMBER + T_MID
BOARD_Y0 = MID_Y1 + STANDOFF            # Rückseite Platine
BOARD_Y1 = BOARD_Y0 + PCB_T             # Bestückungsseite
BOARD_REAR_GAP = 4.0                    # Platinenhinterkante -> Rückwand innen
BOARD_X1 = INNER_L - BOARD_REAR_GAP     # I/O-Kante
BOARD_X0 = BOARD_X1 - BOARD
BOARD_Z0 = 22.0                         # Unterkante Platine (Riser-Bogen)
BOARD_Z1 = BOARD_Z0 + BOARD

# Sockelmitte (Parameter: anpassen fürs neue Board)
SOCKET_FROM_IO = 90.0
SOCKET_FROM_BOTTOM = 105.0
SOCKET_X = BOARD_X1 - SOCKET_FROM_IO
SOCKET_Z = BOARD_Z0 + SOCKET_FROM_BOTTOM
COOLER_KEEP_X = COOLER["d"] / 2          # ±80.5
COOLER_KEEP_Z = COOLER["w"] / 2          # ±75
COOLER_AIR = BOARD_CHAMBER - STANDOFF - PCB_T - COOLER["h"]

# Mini-ITX-Lochbild. d = Abstand zur I/O-Kante, l = Abstand zur Slot-Kante (unten).
# Quelle: ATX 2.2 / microATX (Löcher C, F, H, J); C–F 6.1" (154.94) Richtung vorn,
# C–H/J 6.2" (157.48) quer, H 0.9" (22.86) weiter von der I/O-Kante als C.
# Kante-Abstände (10.16 / 6.35) aus Mini-ITX-Zeichnungen – mit Passtest-Platte prüfen.
ITX_HOLE_C = (10.16, 6.17)
ITX_HOLES = {
    "C": (ITX_HOLE_C[0], ITX_HOLE_C[1]),
    "F": (ITX_HOLE_C[0] + 154.94, ITX_HOLE_C[1]),
    "H": (ITX_HOLE_C[0] + 22.86, ITX_HOLE_C[1] + 157.48),
    "J": (ITX_HOLE_C[0] + 154.94, ITX_HOLE_C[1] + 157.48),
}
# PCIe-x16-Slot auf dem Board (für Riser-Stecker)
PCIE_SLOT_FROM_IO = 45.0
PCIE_SLOT_LEN = 89.0
PCIE_SLOT_FROM_BOTTOM = 10.0

# I/O-Blende (ATX 2.2, 3.3.5): 158.75 x 44.45, Unterkante 3.81 unter Platinenoberseite,
# Rückwand für Clip 0.94..1.32 dick, Ecken r<=0.99, Sperrzone 2.5 rundum.
IO_W = 158.75
IO_H = 44.45
IO_BELOW_PCB_TOP = 3.81
IO_FROM_BOTTOM = 5.6         # Lage entlang der Kante – UNSICHER, Passtest
IO_PANEL_T = 1.2
IO_KEEPOUT = 2.5

# --------------------------------------------------------------------------
# GPU-Lage (abgeleitet)
# --------------------------------------------------------------------------
GPU_Y1 = MID_Y0 - GPU_AIR_WALL            # Backplate
GPU_Y0 = GPU_Y1 - GPU["T"]
GPU_PCB_Y = GPU_Y1 - GPU_PCB_FROM_BACKPLATE
GPU_BRACKET_X0 = INNER_L - 2.0             # Blech liegt innen an der Rückwand
GPU_X0 = INNER_L - GPU["L"]
GPU_TAB_Z = GPU_Z0 + BRACKET_TAB_ABOVE_FINGERS
GPU_RAIL_Z1 = GPU_TAB_Z - 1.0
GPU_RAIL_Z0 = GPU_RAIL_Z1 - GPU_RAIL_H
GPU_RAIL_DEPTH = 12.0
GPU_FINGER_X1 = GPU_BRACKET_X0 - GPU_FINGER_FROM_BRACKET
GPU_FINGER_X0 = GPU_FINGER_X1 - GPU_FINGER_LEN
BRACKET_SLOT_Y0 = GPU_Y1 - GPU_SLOTS * SLOT_PITCH   # Slotöffnung (für GPU_SLOTS)
GPU_SLOT_CENTERS_Y = [GPU_Y1 - (i + 0.5) * SLOT_PITCH for i in range(GPU_SLOTS)]

# Netzteil (abgeleitet)
PSU_Y1 = INNER_W - PSU_BACK_GAP
PSU_Y0 = PSU_Y1 - PSU["d"]
PSU_X1 = PSU_X0 + PSU["w"]
PSU_Z0 = PSU_LIFT
PSU_Z1 = PSU_Z0 + PSU["h"]

# --------------------------------------------------------------------------
# Befestigung
# --------------------------------------------------------------------------
INSERT_D = 4.1        # M3-Einschmelzmutter, Bohrung 4.0..4.2
INSERT_DEPTH = 5.5
M3_CLEAR = 3.4
M3_NUT_AF = 5.7       # Schlüsselweite + Spiel
M3_NUT_T = 2.6
DOME_D = 9.0
DOME_H = 8.0          # Boden-/Deckeldome für Wandlaschen
TAB_W = 12.0
TAB_D = 10.0
TAB_T = 3.0
TAB_Z_BOT = (DOME_H, DOME_H + TAB_T)
TAB_Z_TOP = (INNER_H - DOME_H - TAB_T, INNER_H - DOME_H)

FRONT_TABS_Y = [40.0, 135.0, 230.0]
REAR_TABS_Y_BOT = [40.0, 135.0, 230.0]
REAR_TABS_Y_TOP = [135.0, 230.0]           # GPU-Kammer oben: Kabelbogen
MID_TABS_X_BOT = [30.0, 140.0, 195.0, 335.0]
MID_TABS_X_TOP = [30.0, 140.0, 351.0]      # außerhalb des Kühlers

# Seitenwände: unten Randfalz im Boden, oben Magnete 10x3
RIM_H = 3.0
RIM_W = 2.0
MAGNET_D = 10.2
MAGNET_H = 3.2
MAGNET_FROM_OUTER = 6.9
MAGNET_X = [40.0, 140.0, 200.0, 310.0]
MAGNET_BOSS_DEPTH = 9.0
MAGNET_BOSS_H = 7.0

# Trennstellen
SPLIT_X = 175.0       # Boden, Deckel, Sockel, Mittelwand, Seitenwände
FLANGE_T = 4.0
FLANGE_D = 10.0
VGROOVE = 0.8         # Fase je Seite -> V-Nut 1.6 breit, 0.8 tief

# --------------------------------------------------------------------------
# Lüftung: runde Löcher im Wabenraster
# --------------------------------------------------------------------------
# Optik wie Mac Studio: feine Löcher, dicht, große Felder mit runden Ecken, ohne Lücken.
VENT_D = 3.2
VENT_PITCH = 4.5       # Steg 1.3 mm, Feld theoretisch 45.9 % offen
VENT_EDGE = 1.0        # Mindeststeg zum Feldrand / zu Ausschnitten
# Felder, die über die Trennfuge laufen, liegen symmetrisch zu SPLIT_X (Spalte auf der Fuge)
TOP_VENT = dict(x0=19.0, x1=331.0, y0=12.0, y1=80.0, r=14.0)   # Deckel über GPU
GPU_SIDE_VENT = dict(x0=19.0, x1=331.0, z0=20.0, z1=184.0, r=14.0)
PSU_VENT = dict(x0=PSU_X0 + 2, x1=PSU_X1 - 2, z0=PSU_Z0 + 2, z1=PSU_Z1 - 1, r=8.0)
# Rückwand: ein Feld über die ganze ebene Fläche, Ausschnitte darin ausgespart
REAR_VENT = dict(y0=FLAT_Y0 + 4.0, y1=FLAT_Y1 - 4.0, z0=TAB_Z_BOT[1] + 3.0,
                 z1=TAB_Z_TOP[0] - 3.0, r=12.0)
REAR_RAIL_CLEAR = 6.0  # über der GPU-Leiste frei (Lasche + Schraubenköpfe)
# Sockelring: etwas größere Löcher (Engstelle der Bodenzuluft), drei Höhen, rundum
PLINTH_VENT_D = 3.8
PLINTH_VENT_PITCH = 5.0
PLINTH_VENT_EDGE = 0.6

# --------------------------------------------------------------------------
# Front / Rückwand
# --------------------------------------------------------------------------
BUTTON_D = 16.2        # 16-mm-Vandalismus-Taster
BUTTON_Y = FLAT_Y1 - 20.0
# Taster sitzt frei über dem Netzteil (nicht davor): eigener Bauraum, Leitung zum
# F_PANEL-Anschluss (PWR_SW) des Mainboards. Unten rechts wäre direkt am Netzteil.
BUTTON_Z = INNER_H / 2
BUTTON_DEPTH = 28.0    # Körper hinter der Front
BUTTON_CABLE = 22.0    # dahinter frei für Anschlüsse und Kabelbogen
USBC_W, USBC_H = 9.4, 3.8
USBC_Z = BUTTON_Z + 23.0

C14_W, C14_H = 27.5, 19.8   # Schnapp-Einbau-Ausschnitt (Typ mit Schnapphaken, 1..2 mm Wand)
C14_Y = 225.0
C14_Z = 27.0
C14_PANEL_T = 2.0
C14_DEPTH = 22.0

GPU_OPEN = dict(y0=BRACKET_SLOT_Y0 + 1.5, y1=GPU_Y1 - 1.5, z0=GPU_Z0 + 3.0, z1=GPU_RAIL_Z0 - 3.0)

# Mittelwand-Durchführungen
RISER_PASS = dict(x0=212.0, x1=315.0, z0=0.0, z1=21.0)
CABLE_PASS = dict(x0=25.0, x1=85.0, z0=160.0, z1=195.0)

# --------------------------------------------------------------------------
# Extra-Teile
# --------------------------------------------------------------------------
RISER_BOSS = [(200.0, 63.0), (337.0, 63.0)]
RISER_ADJ = 8.0
PSU_BOSS = [(PSU_X0 + 6, PSU_Y0 - 3), (PSU_X1 - 6, PSU_Y0 - 3),
            (PSU_X0 + 6, PSU_Y1 + 3), (PSU_X1 - 6, PSU_Y1 + 3)]
GPU_SUPPORT_X = GPU_X0 + 12.0     # Stütze unter der Kartenvorderkante
GPU_SUPPORT_Y = 60.0
GPU_SUPPORT_ADJ = 15.0
LOW_BOSS_H = 3.0


def summary():
    return {
        "Außen L x B x H (ohne Sockel)": (OUT_L, OUT_W, OUT_H),
        "Außen H mit Sockel": OUT_H + PLINTH_H,
        "Innen L x B x H": (INNER_L, INNER_W, INNER_H),
        "GPU-Kammer": GPU_CHAMBER,
        "Board-Kammer": BOARD_CHAMBER,
        "Luft über Kühler": round(COOLER_AIR, 2),
        "Sockel-Mitte (x, z)": (SOCKET_X, SOCKET_Z),
        "GPU-Profil": GPU_PROFILE,
        "GPU Luft Lüfter->Seitenwand": GPU_Y0,
        "Netzteil": PSU_TYPE,
    }
