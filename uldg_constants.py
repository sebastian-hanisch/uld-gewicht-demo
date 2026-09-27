"""ULD-Beladung: Volumen gegen Schwerpunkt - feste Annahmen, Reglerstufen, Presets, Farben."""
from uldg_model import GERUNDET, RECHTECK

# Container (Größenordnung LD3), siehe messreihe_uld_gewicht/ERGEBNIS.md
W, D, H, CHAMFER = 160.0, 150.0, 160.0, 40.0

CONTOUR_OPTIONS = (RECHTECK, GERUNDET)
CONTOUR_DEFAULT = RECHTECK
CONTOUR_LABEL = {RECHTECK: "Rechteck (Palette)", GERUNDET: "gerundet (LD3)"}

BOXES_OPTIONS = (10, 16, 24)
BOXES_DEFAULT = 16

CV_OPTIONS = (0.1, 0.3, 0.6)
CV_DEFAULT = 0.3

TOL_OPTIONS = (0.05, 0.10, 0.20)
TOL_DEFAULT = 0.10

SEED_RANGE = (0, 199)
SEED_DEFAULT = 0

COLOR_VOL = "#2a6fb0"
COLOR_CG = "#9fc2e6"

PRESETS = {
    "Standard": dict(contour=RECHTECK, boxes=16, cv=0.3, tol=0.10, seed=0),
    "Enge Toleranz": dict(contour=RECHTECK, boxes=16, cv=0.3, tol=0.05, seed=0),
    "Lose Toleranz": dict(contour=RECHTECK, boxes=16, cv=0.3, tol=0.20, seed=0),
    "Gerundetes ULD": dict(contour=GERUNDET, boxes=16, cv=0.3, tol=0.10, seed=0),
    "Viele, gemischte Boxen": dict(contour=GERUNDET, boxes=24, cv=0.6, tol=0.10, seed=0),
}

PRESET_HELP = {
    "Standard": "Rechteck, 16 Boxen, Dichtestreuung 0,3, Toleranz 10 %: reine Volumen-Packung verletzt das Schwerpunktfenster meistens, die Gegenregel hilft deutlich.",
    "Enge Toleranz": "Toleranz 5 %: hier reicht die einfache schwerpunkt-bewusste Regel allein nicht mehr.",
    "Lose Toleranz": "Toleranz 20 %: der Unterschied zwischen den Regeln verschwindet fast.",
    "Gerundetes ULD": "gerundete Kontur, sonst wie Standard: kostet Volumen, hilft aber überraschend beim Zentrieren (Bodenraster-Effekt).",
    "Viele, gemischte Boxen": "24 Boxen, Dichtestreuung 0,6: hier zeigt sich der eigentliche Preis der Schwerpunktregel - unplatzierte Boxen statt Volumen.",
}
