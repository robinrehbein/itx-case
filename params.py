"""Alle Maße in mm. Einzige Quelle für Maße – Bauteile lesen nur von hier.

Drei Varianten ohne Riser (LAYOUT=A, B oder C). Die Karte steckt direkt im Slot, Board,
Karte, Kühler und Netzteil bilden einen festen Block. Die Varianten stellen diesen Block
nur verschieden ins Gehäuse:
  A  liegend: Board flach auf dem Boden, Kühler nach oben, Karte steht senkrecht,
     GPU-Lüfter zur linken Seitenwand.
  B  stehend: Board an einem Träger vor der rechten Seitenwand, Bestückung nach links,
     Karte waagerecht, GPU-Lüfter zum Boden.
     B hat Lüftungsfelder als Reibe (wie Mac Pro 2019) in Rahmen mit Einlegern und Filter.
  C  wie B im Stil des NCase M3 Grater, mit vier Füßen statt Sockelring.

Gehäusekoordinaten (Innenraum):
  x: vorn -> hinten   (0 = Innenseite Frontwand)
  y: links -> rechts  (0 = Innenseite linke Seitenwand, von vorn gesehen)
  z: unten -> oben    (0 = Oberseite Boden)

Blockkoordinaten (u, v, w) für Board, Karte, Kühler und Netzteil:
  u = x
  v: quer zum Slot, 0 = Wand vor den GPU-Lüftern, die Slot-Kante des Boards liegt bei kleinem v
  w: Höhe über der Board-Ebene (Oberseite Boden bzw. Board-Träger)
  A: y = v, z = w
  B: y = Y_BASE - w, z = v   (Drehung um x um 90°, Händigkeit bleibt erhalten)

Achtung Händigkeit: x nach hinten, y nach rechts, z nach oben ist ein Linkssystem.
FreeCAD rechnet rechtshändig, dort zeigt +y von vorn gesehen nach links. build.py
spiegelt deshalb jedes Teil beim Export an der Ebene y = INNER_W / 2. Alle Maße hier
und in parts/ bleiben in Modellkoordinaten; im FreeCAD-Raum gilt y_fc = INNER_W - y.

Aus der Händigkeit echter Bauteile folgt: Liegt das Board mit der Bestückung nach oben
und der I/O-Kante hinten, dann liegt seine Slot-Kante links (A). Dreht man A um die
x-Achse auf die rechte Seite, entsteht B, ein gewöhnlicher Tower.
"""
import math as _math
import os as _os

# --------------------------------------------------------------------------
# Auswahl / Optionen
# --------------------------------------------------------------------------
LAYOUT = _os.environ.get("LAYOUT", "A").upper()            # "A" liegend | "B" stehend | "C" M3-Stil
GPU_PROFILE = _os.environ.get("GPU_PROFILE", "reaper")   # "reaper" | "max" (340x140x65)
PSU_TYPE = _os.environ.get("PSU_TYPE", "SFX")             # "SFX" | "SFX-L"
USB_C = False            # optionaler USB-C-Ausschnitt in der Front
COOLER_PROFILE = "NH-D15"  # Noctua NH-D15 (Original, 165 mm)
assert LAYOUT in ("A", "B", "C"), LAYOUT
LYING = LAYOUT == "A"          # A liegt, B und C stehen (gleiche Anordnung innen)
# B und C: alle sichtbaren Lüftungsfelder (Front, Deckel, Seiten, Rückwand) als Reibe in
# Rahmen mit Einlegern. Boden und Sockelring behalten Rundlöcher.
GRATER = LAYOUT in ("B", "C")  # Front mit Reiben-Einleger
GRATER_LID = GRATER            # Deckel
GRATER_SIDES = GRATER          # Seitenwände
GRATER_REAR = GRATER           # Rückwand
FEET = LAYOUT == "C"           # Füße statt Sockelring
# Versteckte Fugen: keine V-Nut, Hälften stumpf gestoßen und verklebt, enge Schraubenlöcher
# in den Flanschen richten sie bündig aus. Die Fugen laufen durch eine Lochspalte bzw. bei der
# Reibe durch eine Reihe aus Muldenmitten und Löchern.
HIDDEN_SEAMS = LAYOUT in ("B", "C")
FLANGE_BOLT_D = 3.15 if HIDDEN_SEAMS else 3.4

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
T_TRAY = 5.0        # Board-Träger (nur B)
# Eckradius außen. I/O-Blende und Slotblech brauchen zusammen gut 205 mm ebene Rückwand,
# mit 22 mm Radius müsste das Gehäuse rund 20 mm breiter werden.
CORNER_R = 12.0
LID_EDGE_R = 2.5    # Rundung Deckel-Oberkante
LID_EDGE_BED_CHAMFER = 1.0  # davon die äußersten 1 mm als 45°-Fase (liegt auf dem Druckbett)

# --------------------------------------------------------------------------
# Komponenten
# --------------------------------------------------------------------------
BOARD = 170.0
PCB_T = 1.6
STANDOFF = 8.0         # 6.35 wäre Standard; 8 lässt Platz für die Rückplatte des Kühlers

COOLERS = {
    # Höhe ab Platinenoberseite; Breite quer (v), Tiefe in Luftrichtung (u, Lüfter blasen +x)
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
GPU_SLOTS = GPU["slots"]
GPU_CABLE_BEND = 35.0          # Kabelbogen über der Karte (Stromstecker an der Oberkante)
GPU_CABLE_REAR_FREE = 30.0     # hinten frei von Steckern (Platz für die C14-Buchse)
GPU_PCB_FROM_BACKPLATE = 4.0   # Platinenebene hinter der Backplate
GPU_FINGER_FROM_BRACKET = 43.0 # Abstand Slotblech -> Beginn Kontaktfinger (CEM ~42-43)
GPU_FINGER_LEN = 89.0          # x16
GPU_FINGER_ABOVE_PCB = 3.0     # Unterkante Kontaktfinger über der Board-Oberseite (Annahme)
# Slotblech (PCIe CEM, Full Height) – UNSICHER, mit Passtest prüfen
BRACKET_LEN = 120.02           # Gesamtlänge Blech
BRACKET_TAB_ABOVE_FINGERS = 112.0  # Oberseite Lasche über Fingerunterkante
SLOT_PITCH = 20.32
GPU_RAIL_H = 6.0               # Leiste unter der Lasche (mit M3-Mutternkanal)
GPU_RAIL_DEPTH = 12.0

PSUS = {
    # w x h x d nach SFX-Norm; der Lüfter sitzt auf der Fläche w x d
    "SFX":   dict(w=125.0, h=63.5, d=100.0),
    "SFX-L": dict(w=125.0, h=63.5, d=130.0),
}
PSU = PSUS[PSU_TYPE]

# --------------------------------------------------------------------------
# Block (u, v, w) – gilt für A und B
# --------------------------------------------------------------------------
GPU_FAN_AIR = 17.0          # GPU-Lüfter -> Wand (A: linke Seitenwand, B: Boden)
COOLER_SIDE_AIR = 12.0      # Kühler -> Wand quer (Platz für Flansche und Magnetnasen)
COOLER_TOP_AIR = 5.0        # nur A: Kühler -> Deckel
COOLER_FAR_AIR = 12.0       # nur B: Kühler -> linke Seitenwand (Flansche, Magnetnasen)
TRAY_BACK = 11.0            # nur B: Kabelraum hinter dem Träger (Flansche der Seitenwand)
FRONT_GAP = 10.0            # Kartenvorderkante -> Front
BOARD_REAR_GAP = 4.0        # Platinenhinterkante -> Rückwand innen

GPU_V0 = GPU_FAN_AIR                         # Lüfterseite
GPU_V1 = GPU_V0 + GPU["T"]                   # Backplate, zeigt zum Board
GPU_PCB_V = GPU_V1 - GPU_PCB_FROM_BACKPLATE
PCIE_SLOT_FROM_EDGE = 10.0  # Kartenebene ab Slot-Kante des Boards – UNSICHER, Passtest
PCIE_SLOT_FROM_IO = 45.0
BOARD_V0 = GPU_PCB_V - PCIE_SLOT_FROM_EDGE   # Slot-Kante
BOARD_V1 = BOARD_V0 + BOARD
BOARD_W0 = STANDOFF                          # Rückseite Platine
BOARD_W1 = BOARD_W0 + PCB_T                  # Bestückungsseite

# Sockelmitte (Parameter: anpassen fürs neue Board)
SOCKET_FROM_IO = 90.0
SOCKET_FROM_SLOT_EDGE = 105.0
SOCKET_V = BOARD_V0 + SOCKET_FROM_SLOT_EDGE
CPU_BACKPLATE = dict(w=90.0, t=6.0)      # Rückplatte des Kühlers hinter dem Board (Annahme)
COOLER_KEEP_X = COOLER["d"] / 2          # ±80.5
COOLER_KEEP_V = COOLER["w"] / 2          # ±75
COOLER_W1 = BOARD_W1 + COOLER["h"]

GPU_W0 = BOARD_W1 + GPU_FINGER_ABOVE_PCB     # Unterkante Kontaktfinger
GPU_W1 = GPU_W0 + GPU["H"]
GPU_TAB_W = GPU_W0 + BRACKET_TAB_ABOVE_FINGERS
GPU_RAIL_W1 = GPU_TAB_W - 1.0
GPU_RAIL_W0 = GPU_RAIL_W1 - GPU_RAIL_H
BLOCK_W = max(COOLER_W1, GPU_W1 + GPU_CABLE_BEND)   # höchster Punkt über der Board-Ebene

INNER_V = max(SOCKET_V + COOLER_KEEP_V, BOARD_V1) + COOLER_SIDE_AIR
INNER_L = GPU["L"] + FRONT_GAP

# --------------------------------------------------------------------------
# Innenmaße je Variante
# --------------------------------------------------------------------------
if LYING:
    INNER_W = INNER_V
    INNER_H = float(_math.ceil(BLOCK_W + COOLER_TOP_AIR))
    Y_BASE = None
else:
    INNER_W = float(_math.ceil(BLOCK_W + COOLER_FAR_AIR + T_TRAY + TRAY_BACK))
    INNER_H = INNER_V
    Y_BASE = INNER_W - TRAY_BACK - T_TRAY    # Board-Seite des Trägers

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

# Sockel (Mac-Studio-Fuß). Bei B saugt die Karte durch den Boden, der Ring ist höher.
PLINTH_INSET = 16.0
# B: höher und gröber gelocht, die Karte saugt durch den Boden (Sockelring ist die Engstelle)
PLINTH_H = {"A": 12.0, "B": 26.0, "C": 20.0}[LAYOUT]
FOOT_H = 12.0          # C: Füße statt Sockelring
FOOT_D = 24.0
PLINTH_T = 3.0
PLINTH_LIP_W = 6.0     # Bodenlippe innen (Gummifüße)
PLINTH_LIP_T = 2.0
PLINTH_R = 8.0           # eigener Eckradius (das Gehäuse hat nur 12 mm, der Sockel ist 16 mm eingerückt)
PLINTH_TABS = [(100.0, "L"), (260.0, "L"), (100.0, "R"), (260.0, "R")]
PLINTH_POST_D = 11.0
PLINTH_POST_OFF = 9.5      # Pfostenmitte ab Ring-Innenfläche -> 4 mm Luft dahinter
PLINTH_FLANGE_GAP = 4.0    # Flansch ab Ring-Innenfläche

# --------------------------------------------------------------------------
# Lage im Block (abgeleitet)
# --------------------------------------------------------------------------
BOARD_X1 = INNER_L - BOARD_REAR_GAP     # I/O-Kante
BOARD_X0 = BOARD_X1 - BOARD
SOCKET_X = BOARD_X1 - SOCKET_FROM_IO

# Mini-ITX-Lochbild. d = Abstand zur I/O-Kante, l = Abstand zur Slot-Kante.
# Quelle: ATX 2.2 / microATX (Löcher C, F, H, J); C–F 6.1" (154.94) Richtung vorn,
# C–H/J 6.2" (157.48) quer, H 0.9" (22.86) weiter von der I/O-Kante als C.
# Kante-Abstände (10.16 / 6.17) aus Mini-ITX-Zeichnungen – mit Passtest-Platte prüfen.
ITX_HOLE_C = (10.16, 6.17)
ITX_HOLES = {
    "C": (ITX_HOLE_C[0], ITX_HOLE_C[1]),
    "F": (ITX_HOLE_C[0] + 154.94, ITX_HOLE_C[1]),
    "H": (ITX_HOLE_C[0] + 22.86, ITX_HOLE_C[1] + 157.48),
    "J": (ITX_HOLE_C[0] + 154.94, ITX_HOLE_C[1] + 157.48),
}

GPU_BRACKET_X0 = INNER_L - 2.0             # Blech liegt innen an der Rückwand
GPU_X0 = INNER_L - GPU["L"]
GPU_FINGER_X1 = GPU_BRACKET_X0 - GPU_FINGER_FROM_BRACKET
GPU_FINGER_X0 = GPU_FINGER_X1 - GPU_FINGER_LEN
BRACKET_SLOT_V0 = GPU_V1 - GPU_SLOTS * SLOT_PITCH
GPU_SLOT_CENTERS_V = [GPU_V1 - (i + 0.5) * SLOT_PITCH for i in range(GPU_SLOTS)]

# I/O-Blende (ATX 2.2, 3.3.5): 158.75 x 44.45, Unterkante 3.81 unter Platinenoberseite,
# Rückwand für Clip 0.94..1.32 dick, Ecken r<=0.99, Sperrzone 2.5 rundum.
# Lage entlang der Kante: direkt neben dem Slotblech (2 mm Steg ab Backplate-Ebene).
# Die Norm-Zeichnung dazu war nicht lesbar – UNSICHER, mit der Passtest-Platte prüfen.
IO_W = 158.75
IO_H = 44.45
IO_BELOW_PCB_TOP = 3.81
IO_V0 = GPU_V1 + 2.0
IO_V1 = IO_V0 + IO_W
IO_W0 = BOARD_W1 - IO_BELOW_PCB_TOP
IO_W1 = IO_W0 + IO_H
IO_PANEL_T = 1.2
IO_KEEPOUT = 2.5

# Netzteil steht hochkant vor dem Board: Lüfter zur Front, Rückseite (Anschlüsse,
# Abluft) zur Wand bei v = INNER_V. So bleiben vor dem D15 rund 65 mm Luft.
PSU_X0 = 12.0
PSU_X1 = PSU_X0 + PSU["h"]
PSU_BACK_GAP = 25.0    # Rückseite -> Wand (Winkel-C13, Modulstecker, Abluft)
PSU_V1 = INNER_V - PSU_BACK_GAP
PSU_V0 = PSU_V1 - PSU["d"]
LOW_BOSS_H = 3.0
CRADLE_T = 3.0          # Wandstärke/Bodenplatte Netzteil-Halter
CRADLE_H = 25.0         # Wandhöhe über der Bodenplatte
PSU_W0 = LOW_BOSS_H + CRADLE_T
PSU_W1 = PSU_W0 + PSU["w"]
PSU_BOSS = [(PSU_X0 + 10, PSU_V0 - 8), (PSU_X1 - 10, PSU_V0 - 8),
            (PSU_X0 + 10, PSU_V1 + 8), (PSU_X1 - 10, PSU_V1 + 8)]

# Front: Taster über dem Netzteil, eigene Leitung zum F_PANEL-Anschluss (PWR_SW)
BUTTON_D = 16.2        # 16-mm-Vandalismus-Taster
BUTTON_KEEP_R = 13.0   # lochfreier Kreis um den Taster (Auflage für Kragen und Mutter)
BUTTON_DEPTH = 28.0    # Körper hinter der Front
BUTTON_CABLE = 22.0    # dahinter frei für Anschlüsse und Kabelbogen
BUTTON_V = PSU_V1 - 30.0
BUTTON_W = PSU_W1 + 20.0
GRATER_TOP_BAND = 40.0      # C: Rahmen über dem Front-Einleger, darin der Taster
USBC_W, USBC_H = 9.4, 3.8

# Kaltgeräte-Buchse C14 in der Rückwand über der Karte
C14_W, C14_H = 27.5, 19.8   # Schnapp-Einbau-Ausschnitt (Typ mit Schnapphaken, 1..2 mm Wand)
C14_V = (GPU_V0 + GPU_V1) / 2
C14_W_POS = GPU_W1 + 4.0 + C14_H / 2
C14_PANEL_T = 2.0
C14_DEPTH = 22.0

# Slotblech-Öffnung (Block): zwischen Fingerunterkante und Leiste
GPU_OPEN_V = (BRACKET_SLOT_V0 + 1.5, GPU_V1 - 1.5)
GPU_OPEN_W = (GPU_W0 + 3.0, GPU_RAIL_W0 - 3.0)

# GPU-Stütze unter der Kartenvorderkante (Gehäusekoordinaten, siehe unten)
GPU_SUPPORT_ADJ = 15.0


def to_case(u, v, w):
    """Blockpunkt -> Gehäusepunkt."""
    if LYING:
        return u, v, w
    return u, Y_BASE - w, v


def rect_vw(v0, v1, w0, w1):
    """Rechteck im Block (v, w) -> Rechteck in der Rückwand/Front (y0, y1, z0, z1)."""
    if LYING:
        return v0, v1, w0, w1
    return Y_BASE - w1, Y_BASE - w0, v0, v1


if GRATER:   # Taster links oben im Rahmenband über dem Einleger
    BUTTON_V = INNER_H - GRATER_TOP_BAND / 2
    BUTTON_W = Y_BASE - 36.0
BUTTON_Y, BUTTON_Z = to_case(0, BUTTON_V, BUTTON_W)[1:]
USBC_Y, USBC_Z = BUTTON_Y, BUTTON_Z + 23.0

# --------------------------------------------------------------------------
# Befestigung
# --------------------------------------------------------------------------
INSERT_D = 4.1        # M3-Einschmelzmutter, Bohrung 4.0..4.2
INSERT_DEPTH = 5.5
M3_CLEAR = 3.4
M3_HEAD_D = 6.5
M3_NUT_AF = 5.7       # Schlüsselweite + Spiel
M3_NUT_T = 2.6
DOME_D = 9.0
DOME_H = 8.0          # Boden-/Deckeldome für Wandlaschen
TAB_W = 12.0
TAB_D = 10.0
TAB_T = 3.0
TAB_Z_BOT = (DOME_H, DOME_H + TAB_T)
TAB_Z_TOP = (INNER_H - DOME_H - TAB_T, INNER_H - DOME_H)

if LYING:
    # Front: eine Lasche zwischen Kabelbogen der Karte und Netzteil-Halter, eine rechts daneben
    _cradle_v0 = PSU_V0 - 0.5 - CRADLE_T
    _cradle_v1 = PSU_V1 + 0.5 + CRADLE_T
    FRONT_TABS_Y = [(GPU_V1 + _cradle_v0) / 2, _cradle_v1 + 1.0 + TAB_W / 2]
    REAR_TABS_Y_TOP = [40.0, 140.0, 200.0]
    REAR_TABS_Y_BOT = []
    # Rückwand unten: I/O-Blende und Slotblech reichen fast bis zum Boden. Zwei Nasen
    # neben den Ausschnitten, von unten durch den Boden verschraubt.
    REAR_LOW_BOSS_Y = [BRACKET_SLOT_V0 - 5.4, IO_V1 + 4.25]
    TRAY_TABS_X = []
    TRAY_TOP_TABS_X = []
else:
    # C: der Taster sitzt links oben im Rahmen, die Laschen weichen ihm aus
    FRONT_TABS_Y = [40.0, 140.0] if not GRATER else [90.0, 160.0]
    REAR_TABS_Y_TOP = [40.0, 140.0]
    REAR_TABS_Y_BOT = [40.0, 140.0]
    REAR_LOW_BOSS_Y = []
    TRAY_TABS_X = [35.0, 110.0, 200.0, 285.0]          # unten, zum Boden
    # oben, zum Deckel: auf der Rückseite des Trägers im Kabelraum, damit der Deckelrand so
    # schmal bleiben kann wie an Front und Seiten; zwischen den Magnetnasen der Seitenwand
    TRAY_TOP_TABS_X = [75.0, 150.0, 235.0]

# Seitenwände: unten Randfalz im Boden, oben Magnete 10x3
RIM_H = 3.0
RIM_W = 2.0
REAR_LOW_BOSS_H = GPU_W0 - 1.0 - RIM_H   # endet 1 mm unter der Kartenunterkante
MAGNET_D = 10.2
MAGNET_H = 3.2
MAGNET_FROM_OUTER = 6.9
MAGNET_BOSS_DEPTH = 9.0
MAGNET_BOSS_H = 7.0

# Trennstellen: vor dem Kühler, damit kein Flansch an Kühler, Board oder Rückplatte stößt
SPLIT_X = 130.0       # Boden, Deckel, Sockel, Seitenwände, Träger
FLANGE_T = 4.0
FLANGE_D = 10.0
VGROOVE = 0.8         # Fase je Seite -> V-Nut 1.6 breit, 0.8 tief
MAGNET_X = [FLAT_X0 + 20.0, SPLIT_X - 25.0, SPLIT_X + 40.0, FLAT_X1 - 20.0]

# --------------------------------------------------------------------------
# Lüftung: runde Löcher im Wabenraster
# --------------------------------------------------------------------------
# Optik wie Mac Studio: feine Löcher, dicht, große Felder mit runden Ecken, ohne Lücken.
VENT_D = 3.2
VENT_PITCH = 4.5       # Steg 1.3 mm, Feld theoretisch 45.9 % offen
VENT_EDGE = 1.0        # Mindeststeg zum Feldrand / zu Ausschnitten
# Alle Wandfelder beginnen und enden auf derselben Höhe (zwischen den Wandlaschen).
VENT_Z0 = TAB_Z_BOT[1] + 3.0
VENT_Z1 = TAB_Z_TOP[0] - 3.0
VENT_BLIND_SKIN = 0.6  # Löcher über Flanschen und Domen enden als Sackloch vor dieser Haut
# Felder über die Trennfuge haben eine Lochspalte genau auf SPLIT_X.
TOP_VENT = dict(x0=OUT_X0 + 16.0, x1=OUT_X1 - 16.0, y0=OUT_Y0 + 16.0, y1=OUT_Y1 - 16.0, r=10.0)
SIDE_VENT = dict(x0=FLAT_X0 + 4.0, x1=FLAT_X1 - 4.0, z0=VENT_Z0, z1=VENT_Z1, r=12.0)
REAR_VENT = dict(y0=FLAT_Y0 + 4.0, y1=FLAT_Y1 - 4.0, z0=VENT_Z0, z1=VENT_Z1, r=12.0)
REAR_RAIL_CLEAR = 6.0  # über der GPU-Leiste frei (Lasche + Schraubenköpfe)
FRONT_VENT = dict(y0=FLAT_Y0 + 4.0, y1=FLAT_Y1 - 4.0, z0=VENT_Z0, z1=VENT_Z1, r=12.0)
# Sockelring: etwas größere Löcher (Engstelle der Bodenzuluft), rundum
PLINTH_VENT_D = 4.4 if LAYOUT == "B" else 3.8
PLINTH_VENT_PITCH = 5.4 if LAYOUT == "B" else 5.0
PLINTH_VENT_EDGE = 0.6

# Reibe (nur C): Einleger von innen gegen eine Lippe im Rahmen, dazwischen Filtergewebe.
# Außen Kegelmulden (45°) im Wabenraster, die sich an Graten treffen; an jedem Treffpunkt
# von drei Mulden ein Loch, dazu ein kleines Loch in jeder Muldenspitze. Mit Sacklöchern
# (GR_HOLE_H < GR_T) entstehen nur Sicheln, dann sind bloß ca. 15 % offen.
GR_PITCH = 8.0         # Abstand der Mulden
GR_R = 4.8             # Muldenradius an der Außenfläche = Tiefe (45°)
GR_T = 4.0             # Dicke des Einlegers
GR_HOLE_D = 3.6        # Löcher an den Treffpunkten
GR_HOLE_H = GR_T       # durchgehend
GR_LIP = 1.5           # Lippe außen im Rahmen
GR_LAP = 7.0           # Einleger liegt so breit auf der Lippe auf (Magnete 6 x 1)
GR_CLEAR = 0.3         # Spiel rundum im Rahmen
GR_FILTER = 0.3        # Filtergewebe zwischen Lippe und Einleger
GR_MAG = (6.2, 1.1)    # Magnettasche Ø, Tiefe (Magnete 6 x 1 mm)
GR_EDGE = 4.0          # Rahmen außen neben der Einleger-Tasche (Front)
GR_SEAM_LAP = 20.0     # Deckel-Einleger überlappen an der Fuge stufenförmig (halbe Dicke)
GR_SEAM_GAP = 0.2

# --------------------------------------------------------------------------
# Board-Träger (nur B): Durchbrüche im Block (u0, u1, v0, v1)
# --------------------------------------------------------------------------
TRAY_CUTOUTS = [
    (SOCKET_X - 50.0, SOCKET_X + 50.0, SOCKET_V - 50.0, SOCKET_V + 50.0),   # Kühler-Rückplatte
    (PSU_X1 + 8.0, PSU_X1 + 48.0, PSU_V0, PSU_V1),                          # Netzteilkabel
    (PSU_X0 + 18.0, PSU_X1 - 18.0, PSU_V1 + 2.0, INNER_V - 6.0),            # hinter dem Netzteil
]

# Leitblech (nur stehend): Platte zwischen Backplate der Karte und Unterseite des D15. Die
# warme Luft der Karte steigt sonst direkt in die Lamellen des Kühlers; so zieht sie zur
# linken Seitenwand ab. Über dem Board erst ab w = BAFFLE_W0 (Bauteile auf der Platine).
BAFFLE_V0 = GPU_V1 + 5.0
BAFFLE_T = 2.5
BAFFLE_W0 = 30.0
BAFFLE_W1 = GPU_W1 - 5.0
BAFFLE_U = (GPU_X0, min(SOCKET_X + COOLER_KEEP_X, BOARD_X1 - 26.0))   # endet vor dem I/O-Block
BAFFLE_RIBS_U = [40.0, 135.0, 210.0, 280.0]     # Rippen quer, auf der Oberseite
BAFFLE_RIB_H = 5.0
BAFFLE_POSTS_U = [30.0, 110.0]                  # Stützen zum Träger, vor dem Board, neben dem Fugenflansch
BAFFLE_POST_V = BAFFLE_V0 + BAFFLE_T + 3.5     # Schraubachse über der Platte (Zugang von links)

# Kabelwege (nur stehend), Annahmen fürs aktuelle Board, mit dem neuen Board prüfen:
# 24-Pin an der Vorderkante, EPS an der Oberkante nahe der I/O-Seite, Strom der Karte an
# ihrer Oberkante (Reaper: 2 x 8-Pin).
ATX24_V = BOARD_V0 + 140.0
EPS_U = BOARD_X1 - 30.0
GPU_POWER_U = GPU_X0 + 200.0

# GPU-Stütze: Pfosten vom Boden bis knapp unter die tiefste Kartenfläche
if LYING:
    GPU_SUPPORT = dict(x=GPU_X0 + 12.0, y=(GPU_V0 + GPU_V1) / 2, ztop=GPU_W0 - 1.0)
else:
    GPU_SUPPORT = dict(x=GPU_X0 + 12.0, y=Y_BASE - (GPU_W0 + 30.0), ztop=GPU_V0 - 1.0)


def summary():
    return {
        "Variante": {"A": "A liegend", "B": "B stehend", "C": "C stehend, M3-Stil"}[LAYOUT],
        "Außen L x B x H (ohne Sockel)": (OUT_L, OUT_W, OUT_H),
        "Außen H mit Sockel bzw. Füßen": OUT_H + (FOOT_H if FEET else PLINTH_H),
        "Innen L x B x H": (INNER_L, INNER_W, INNER_H),
        "Luft Kühler -> Wand oben/seitlich": round(
            (INNER_H - COOLER_W1) if LYING else (Y_BASE - COOLER_W1), 2),
        "Sockel-Mitte (x, v)": (SOCKET_X, SOCKET_V),
        "GPU-Profil": GPU_PROFILE,
        "GPU Luft Lüfter -> Wand": GPU_V0,
        "Luft Netzteil -> Kühler": round(SOCKET_X - COOLER_KEEP_X - PSU_X1, 1),
        "Netzteil": PSU_TYPE,
    }
