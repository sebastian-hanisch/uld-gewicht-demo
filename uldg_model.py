"""ULD-Beladung: Volumen gegen Schwerpunkt - Kerndatentypen und Kennzahlen.

Mechanisch aus `packen-planung/messreihe_uld_gewicht/uld.py` übernommen (dort gegen 25 Checks verifiziert,
siehe ERGEBNIS.md) - nur die Modulgrenze ist neu, die Logik ist unverändert. Dieses Modul enthält die
Datentypen (Box, Placed), die Kontur-/Volumen-Geometrie ohne Packalgorithmus und die Schwerpunkt-Kennzahlen.
Das Extreme-Point-Packverfahren selbst steht in `uldg_geometry.py`.
"""
from __future__ import annotations

from dataclasses import dataclass

RECHTECK = "rechteck"
GERUNDET = "gerundet"


@dataclass
class Box:
    w: float
    d: float
    h: float
    weight: float


@dataclass
class Placed:
    box: Box
    x: float
    y: float
    z: float


def corners_ok(x: float, y: float, w: float, d: float, W: float, D: float, contour: str, chamfer: float) -> bool:
    """Prüft die vier Grundflächen-Ecken einer Box gegen die Kontur."""
    pts = [(x, y), (x + w, y), (x, y + d), (x + w, y + d)]
    for px, py in pts:
        if px < -1e-9 or px > W + 1e-9 or py < -1e-9 or py > D + 1e-9:
            return False
        if contour == GERUNDET:
            if px + py < chamfer - 1e-9:
                return False
            if (W - px) + py < chamfer - 1e-9:
                return False
            if px + (D - py) < chamfer - 1e-9:
                return False
            if (W - px) + (D - py) < chamfer - 1e-9:
                return False
    return True


def usable_volume(W: float, D: float, H: float, contour: str, chamfer: float) -> float:
    if contour == RECHTECK:
        return W * D * H
    return (W * D - 2.0 * chamfer * chamfer) * H  # vier rechtwinklige Dreiecke der Kathete `chamfer`


def cg_offset(placed: list[Placed], W: float, D: float) -> tuple[float, float]:
    tw = sum(p.box.weight for p in placed)
    if tw <= 0:
        return 0.0, 0.0
    cx = sum(p.box.weight * (p.x + p.box.w / 2) for p in placed) / tw
    cy = sum(p.box.weight * (p.y + p.box.d / 2) for p in placed) / tw
    return cx - W / 2, cy - D / 2


def volume_utilization(placed: list[Placed], W: float, D: float, H: float, contour: str, chamfer: float) -> float:
    used = sum(p.box.w * p.box.d * p.box.h for p in placed)
    uv = usable_volume(W, D, H, contour, chamfer)
    return used / uv if uv > 0 else 0.0


def cg_violation(offset_x: float, offset_y: float, W: float, D: float, tol: float) -> bool:
    return abs(offset_x) > tol * (W / 2) + 1e-9 or abs(offset_y) > tol * (D / 2) + 1e-9
