"""Orakel-Regressionstest (ULD-Beladung): fertige Packungen mit unabhängig gerechneter Geometrie nachprüfen.

Anders als `test_geometry.py` (dort prüft `corners_ok` und eine Kopie der Auflage-Formel sich selbst) rechnet dieses Orakel neu:
- Kontur: Rechteck bzw. Achteck als Polygon, jede Boxecke per Kreuzprodukt gegen alle Kanten (bei konvexem Polygon genügt das);
- Auflage: exakte Deckung der Grundfläche durch die Oberseiten darunterliegender Boxen per Koordinatenkompression;
- Überlappung über das Schnittvolumen, Schwerpunkt-Offset mit `fractions.Fraction`, nutzbares Volumen über die Polygonfläche;
- jede Box ist entweder platziert oder unplatziert (kein Verlust, keine Doppelung)."""
from __future__ import annotations

from fractions import Fraction

import numpy as np

from uldg_geometry import make_boxes, pack_cg_aware, pack_greedy_volume
from uldg_model import GERUNDET, RECHTECK, cg_offset, cg_violation, usable_volume, volume_utilization

W, D, H, C = 160.0, 150.0, 160.0, 40.0
OCT = [(C, 0), (W - C, 0), (W, C), (W, D - C), (W - C, D), (C, D), (0, D - C), (0, C)]
RECT = [(0, 0), (W, 0), (W, D), (0, D)]


def _in_poly(pt, poly):
    x, y = pt
    return all((poly[(k + 1) % len(poly)][0] - poly[k][0]) * (y - poly[k][1])
               - (poly[(k + 1) % len(poly)][1] - poly[k][1]) * (x - poly[k][0]) >= -1e-7 for k in range(len(poly)))


def _area(poly):
    return abs(sum(poly[k][0] * poly[(k + 1) % len(poly)][1] - poly[(k + 1) % len(poly)][0] * poly[k][1] for k in range(len(poly)))) / 2


def _supported(p, others):
    if p.z <= 1e-9:
        return True
    tops = [q for q in others if abs(q.z + q.box.h - p.z) < 1e-6]
    xs = sorted({p.x, p.x + p.box.w} | {v for q in tops for v in (q.x, q.x + q.box.w) if p.x < v < p.x + p.box.w})
    ys = sorted({p.y, p.y + p.box.d} | {v for q in tops for v in (q.y, q.y + q.box.d) if p.y < v < p.y + p.box.d})
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if not any(q.x <= cx <= q.x + q.box.w and q.y <= cy <= q.y + q.box.d for q in tops):
                return False
    return True


def _overlap_volume(a, b):
    ox = min(a.x + a.box.w, b.x + b.box.w) - max(a.x, b.x)
    oy = min(a.y + a.box.d, b.y + b.box.d) - max(a.y, b.y)
    oz = min(a.z + a.box.h, b.z + b.box.h) - max(a.z, b.z)
    return max(0, ox) * max(0, oy) * max(0, oz)


def test_packings_checked_with_independent_geometry():
    assert abs(_area(OCT) * H - usable_volume(W, D, H, GERUNDET, C)) < 1e-6
    assert abs(_area(RECT) * H - usable_volume(W, D, H, RECHTECK, C)) < 1e-6
    rng = np.random.default_rng(99)
    for _ in range(40):
        boxes = make_boxes(rng, int(rng.integers(1, 26)), float(rng.choice([0.1, 0.3, 0.6])))
        for contour, poly in ((RECHTECK, RECT), (GERUNDET, OCT)):
            for packer in (pack_greedy_volume, pack_cg_aware):
                placed, unplaced = packer(boxes, W, D, H, contour, C)
                assert sorted(map(id, [p.box for p in placed] + unplaced)) == sorted(map(id, boxes))
                for i, p in enumerate(placed):
                    b = p.box
                    assert -1e-9 <= p.x and -1e-9 <= p.y and -1e-9 <= p.z
                    assert p.x + b.w <= W + 1e-9 and p.y + b.d <= D + 1e-9 and p.z + b.h <= H + 1e-9
                    assert all(_in_poly(c, poly) for c in [(p.x, p.y), (p.x + b.w, p.y), (p.x, p.y + b.d), (p.x + b.w, p.y + b.d)])
                    assert _supported(p, placed[:i] + placed[i + 1:])
                    assert all(_overlap_volume(p, q) <= 1e-6 for q in placed[i + 1:])
                tw = sum(Fraction(p.box.weight) for p in placed)
                ox = oy = 0.0
                if tw > 0:
                    ox = float(sum(Fraction(p.box.weight) * (Fraction(p.x) + Fraction(p.box.w) / 2) for p in placed) / tw - Fraction(W) / 2)
                    oy = float(sum(Fraction(p.box.weight) * (Fraction(p.y) + Fraction(p.box.d) / 2) for p in placed) / tw - Fraction(D) / 2)
                dx, dy = cg_offset(placed, W, D)
                assert abs(dx - ox) < 1e-9 and abs(dy - oy) < 1e-9
                for tol in (0.05, 0.10, 0.20):
                    if abs(abs(ox) - tol * W / 2) > 1e-6 and abs(abs(oy) - tol * D / 2) > 1e-6:
                        assert cg_violation(dx, dy, W, D, tol) == (abs(ox) > tol * W / 2 or abs(oy) > tol * D / 2)
                used = sum(p.box.w * p.box.d * p.box.h for p in placed)
                assert abs(volume_utilization(placed, W, D, H, contour, C) - used / (_area(poly) * H)) < 1e-12
