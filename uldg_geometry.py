"""ULD-Beladung: Volumen gegen Schwerpunkt - Extreme-Point-Packverfahren.

Mechanisch aus `packen-planung/messreihe_uld_gewicht/uld.py` übernommen (dort gegen 25 Checks verifiziert,
siehe ERGEBNIS.md) - nur die Modulgrenze ist neu, die Logik ist unverändert. Enthält die
Extreme-Point-Heuristik (Crainic, Perboli, Tadei 2008) mit den beiden Packregeln H_vol (Baseline, ignoriert
Gewicht) und H_cg (schwerpunkt-bewusst) sowie die Zufallserzeugung der Boxen.
"""
from __future__ import annotations

import numpy as np

from uldg_model import Box, GERUNDET, Placed, RECHTECK, corners_ok


def _overlaps(a: Placed, b: Placed) -> bool:
    ax0, ax1 = a.x, a.x + a.box.w
    ay0, ay1 = a.y, a.y + a.box.d
    az0, az1 = a.z, a.z + a.box.h
    bx0, bx1 = b.x, b.x + b.box.w
    by0, by1 = b.y, b.y + b.box.d
    bz0, bz1 = b.z, b.z + b.box.h
    return not (
        ax1 <= bx0 + 1e-9 or bx1 <= ax0 + 1e-9
        or ay1 <= by0 + 1e-9 or by1 <= ay0 + 1e-9
        or az1 <= bz0 + 1e-9 or bz1 <= az0 + 1e-9
    )


def _seed_points(W: float, D: float, contour: str, chamfer: float) -> set[tuple[float, float, float]]:
    """Anfangs-Kandidaten am Boden: der Ursprung bei Rechteck-Kontur liegt bei einer gerundeten Kontur
    selbst außerhalb der Kontur (die Ecke ist ja gerade abgeschnitten) - der Extreme-Point-Algorithmus
    braucht dort die Eckpunkte der Kontur als Startpunkte, sonst wird nie etwas platziert (0/200 Instanzen
    beim ersten Lauf dieser Messreihe - Nullspalten-Signal, siehe check.py)."""
    if contour == RECHTECK:
        return {(0.0, 0.0, 0.0)}
    c = chamfer
    return {
        (c, 0.0, 0.0), (0.0, c, 0.0),
        (W - c, 0.0, 0.0), (W, c, 0.0),
        (0.0, D - c, 0.0), (c, D, 0.0),
        (W - c, D, 0.0), (W, D - c, 0.0),
    }


def _floor_grid(W: float, D: float, step: float = 20.0) -> set[tuple[float, float, float]]:
    """Zusätzliche Kandidatenpunkte am Boden (nicht nur an Boxkanten), damit eine Regel, die auf die Mitte
    zielt, dort auch tatsächlich ansetzen kann - ohne sie wären nur Randpunkte erreichbar."""
    xs = [i * step for i in range(int(W // step) + 1)]
    ys = [j * step for j in range(int(D // step) + 1)]
    return {(x, y, 0.0) for x in xs for y in ys}


def _candidate_points(placed: list[Placed], W: float, D: float, contour: str, chamfer: float,
                       with_floor_grid: bool) -> list[tuple[float, float, float]]:
    """Extreme-Points (Crainic et al. 2008): Start-/Bodenpunkte plus rechte/hintere/obere Kante jeder
    platzierten Box."""
    pts = set(_seed_points(W, D, contour, chamfer))
    if with_floor_grid:
        pts |= _floor_grid(W, D)
    for p in placed:
        pts.add((p.x + p.box.w, p.y, p.z))
        pts.add((p.x, p.y + p.box.d, p.z))
        pts.add((p.x, p.y, p.z + p.box.h))
    return sorted(pts, key=lambda t: (t[2], t[1], t[0]))  # unten vor hinten vor links


def try_place(box: Box, placed: list[Placed], W: float, D: float, H: float, contour: str, chamfer: float,
              target: tuple[float, float] | None = None, with_floor_grid: bool = False) -> Placed | None:
    """Erste zulässige Position (Extreme-Point); mit `target` die zulässige Position, deren Boxmitte den
    kleinsten Abstand zu `target` hat (für die schwerpunkt-bewusste Regel, mit erweitertem Kandidatenraster)."""
    best = None
    best_dist = None
    for (x, y, z) in _candidate_points(placed, W, D, contour, chamfer, with_floor_grid):
        if x + box.w > W + 1e-9 or y + box.d > D + 1e-9 or z + box.h > H + 1e-9:
            continue
        if not corners_ok(x, y, box.w, box.d, W, D, contour, chamfer):
            continue
        cand = Placed(box, x, y, z)
        if any(_overlaps(cand, p) for p in placed):
            continue
        if target is None:
            return cand
        tx, ty = target
        dist = (x + box.w / 2 - tx) ** 2 + (y + box.d / 2 - ty) ** 2
        if best is None or dist < best_dist:
            best, best_dist = cand, dist
    return best


def pack_greedy_volume(boxes: list[Box], W: float, D: float, H: float, contour: str, chamfer: float):
    """H_vol: reine Volumen-Heuristik, ignoriert Gewicht (Baseline wie in pack_demo)."""
    order = sorted(boxes, key=lambda b: b.w * b.d * b.h, reverse=True)
    placed: list[Placed] = []
    unplaced: list[Box] = []
    for b in order:
        p = try_place(b, placed, W, D, H, contour, chamfer)
        if p:
            placed.append(p)
        else:
            unplaced.append(b)
    return placed, unplaced


def pack_cg_aware(boxes: list[Box], W: float, D: float, H: float, contour: str, chamfer: float):
    """H_cg: schwere Boxen zuerst und mit Vorzug für Positionen nahe der geometrischen Mitte (erweiterter
    Bodenraster, damit dieser Vorzug überhaupt Kandidaten in der Mitte zur Auswahl hat), sonst dasselbe
    Verfahren wie H_vol."""
    if not boxes:
        return [], []
    med = float(np.median([b.weight for b in boxes]))
    heavy = sorted([b for b in boxes if b.weight >= med], key=lambda b: (-b.weight, -(b.w * b.d * b.h)))
    light = sorted([b for b in boxes if b.weight < med], key=lambda b: -(b.w * b.d * b.h))
    placed: list[Placed] = []
    unplaced: list[Box] = []
    for b in heavy:
        p = try_place(b, placed, W, D, H, contour, chamfer, target=(W / 2, D / 2), with_floor_grid=True)
        if p:
            placed.append(p)
        else:
            unplaced.append(b)
    for b in light:
        p = try_place(b, placed, W, D, H, contour, chamfer)
        if p:
            placed.append(p)
        else:
            unplaced.append(b)
    return placed, unplaced


def make_boxes(rng: np.random.Generator, n: int, density_cv: float,
               w_range=(20.0, 60.0), d_range=(20.0, 60.0), h_range=(15.0, 45.0)) -> list[Box]:
    boxes = []
    for _ in range(n):
        w = rng.uniform(*w_range)
        d = rng.uniform(*d_range)
        h = rng.uniform(*h_range)
        vol = w * d * h
        density = max(0.05, rng.normal(1.0, density_cv))
        weight = vol * density / 1000.0  # kg, willkürliche Skala (dm^3 * kg/dm^3 / 1000 -> handliche Größenordnung)
        boxes.append(Box(w, d, h, weight))
    return boxes
