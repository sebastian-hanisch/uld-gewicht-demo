"""Korrektheits-Checks für uldg_geometry.py - übernommen aus
packen-planung/messreihe_uld_gewicht/check.py (dort als Skript, hier als pytest), Checks 7-10, 12-14
(Ueberlappung, Zufallspackungen, Grenzfälle, die beiden PFLICHT-Regressionstests, Determinismus)."""
from __future__ import annotations

import numpy as np
import pytest

from uldg_geometry import _floor_grid, _overlaps, make_boxes, pack_cg_aware, pack_greedy_volume, try_place
from uldg_model import Box, GERUNDET, Placed, RECHTECK, cg_offset, corners_ok, volume_utilization

W, D, H, CHAMFER = 160.0, 150.0, 160.0, 40.0


def test_ueberlappung_gleiche_position_ueberlappt():
    """Check 7a."""
    pa = Placed(Box(30, 30, 30, 1), 0, 0, 0)
    pb = Placed(Box(30, 30, 30, 1), 0, 0, 0)
    assert _overlaps(pa, pb)


def test_ueberlappung_kante_an_kante_ueberlappt_nicht():
    """Check 7b."""
    pa = Placed(Box(30, 30, 30, 1), 0, 0, 0)
    pc = Placed(Box(30, 30, 30, 1), 30, 0, 0)
    assert not _overlaps(pa, pc)


def test_viele_zufallspackungen_ohne_fehler():
    """Check 8: Gewichtserhaltung und keine Ueberlappung über viele Zufallsinstanzen, beide Heuristiken,
    beide Konturen (300 Instanzen x 2 Konturen x 2 Regeln = 1200 Packungen, wie im Original)."""
    rng = np.random.default_rng(1)
    n_checked = 0
    overlap_found = False
    weight_mismatch = False
    contour_violation = False
    for _trial in range(300):
        boxes = make_boxes(rng, int(rng.integers(4, 16)), float(rng.uniform(0.05, 0.6)))
        total_w = sum(b.weight for b in boxes)
        for contour in (RECHTECK, GERUNDET):
            for packer in (pack_greedy_volume, pack_cg_aware):
                placed, unplaced = packer(boxes, W, D, H, contour, CHAMFER)
                n_checked += 1
                if abs(sum(p.box.weight for p in placed) + sum(b.weight for b in unplaced) - total_w) > 1e-6:
                    weight_mismatch = True
                for i in range(len(placed)):
                    for j in range(i + 1, len(placed)):
                        if _overlaps(placed[i], placed[j]):
                            overlap_found = True
                    if not corners_ok(placed[i].x, placed[i].y, placed[i].box.w, placed[i].box.d, W, D, contour, CHAMFER):
                        contour_violation = True
    assert n_checked == 1200
    assert not overlap_found
    assert not weight_mismatch
    assert not contour_violation


def test_keine_boxen_leere_packung():
    """Check 9a."""
    placed, unplaced = pack_greedy_volume([], W, D, H, RECHTECK, CHAMFER)
    assert placed == [] and unplaced == []


def test_keine_boxen_auslastung_null():
    """Check 9b."""
    assert volume_utilization([], W, D, H, RECHTECK, CHAMFER) == 0.0


def test_wuerfel_gleich_container_fuellt_rechteck_voll():
    """Check 10a: ein Würfel exakt so groß wie der Container füllt ihn zu 100 % (Rechteck-Kontur)."""
    big = Box(W, D, H, 1)
    placed, unplaced = pack_greedy_volume([big], W, D, H, RECHTECK, CHAMFER)
    assert len(placed) == 1 and unplaced == []
    assert abs(volume_utilization(placed, W, D, H, RECHTECK, CHAMFER) - 1.0) < 1e-9


def test_wuerfel_passt_nicht_in_gerundete_kontur():
    """Check 10b: derselbe Würfel passt NICHT in die gerundete Kontur (Ecken ragen heraus)."""
    big = Box(W, D, H, 1)
    placed, unplaced = pack_greedy_volume([big], W, D, H, GERUNDET, CHAMFER)
    assert len(placed) == 0 and len(unplaced) == 1


def test_regression_gerundete_kontur_platziert_wieder_etwas():
    """Check 12 - PFLICHT-Regressionstest für den beim Bauen gefundenen Bug: die gerundete Kontur schneidet
    genau den Ursprung ab; die Extreme-Point-Heuristik startete anfangs nur dort, wodurch 0 von 200 Instanzen
    überhaupt etwas platzierten (Nullspalten-Signal, siehe feedback_all_zero_result_column_is_a_bug_signal).
    Behoben durch eigene Start-Kandidaten an den Eckpunkten der Kontur (uldg_geometry._seed_points)."""
    rng = np.random.default_rng(7)
    placed_any = False
    for _ in range(20):
        boxes = make_boxes(rng, 16, 0.3)
        pv, _ = pack_greedy_volume(boxes, W, D, H, GERUNDET, CHAMFER)
        if pv:
            placed_any = True
            break
    assert placed_any


def test_regression_schwerpunktregel_senkt_offset_messbar():
    """Check 13 - PFLICHT-Regressionstest (Nullspalten-Falle, Zweig-Test je Regel): die schwerpunkt-bewusste
    Regel H_cg muss auf einer konstruierten Instanz (eine schwere Box + viele leichte) den Offset messbar
    kleiner machen als H_vol - sonst wirkt der Bodenraster-Regler nicht (die Regel hatte anfangs sogar
    HOEHERE Verletzungsraten, weil der ersten, schwersten Box nur der Ursprung als Kandidat zur Verfügung
    stand; behoben durch das zusätzliche Bodenraster in uldg_geometry._floor_grid)."""
    heavy_light = [Box(30, 30, 30, 500)] + [Box(15, 15, 15, 1) for _ in range(10)]
    pv, _ = pack_greedy_volume(heavy_light, W, D, H, RECHTECK, CHAMFER)
    pc, _ = pack_cg_aware(heavy_light, W, D, H, RECHTECK, CHAMFER)
    ox_v, oy_v = cg_offset(pv, W, D)
    ox_c, oy_c = cg_offset(pc, W, D)
    off_v = (ox_v ** 2 + oy_v ** 2) ** 0.5
    off_c = (ox_c ** 2 + oy_c ** 2) ** 0.5
    assert off_c < off_v - 1.0


def test_determinismus_gleicher_seed_gleiche_boxen():
    """Check 14."""
    r1 = np.random.default_rng(42)
    r2 = np.random.default_rng(42)
    b_a = make_boxes(r1, 10, 0.3)
    b_b = make_boxes(r2, 10, 0.3)
    assert all((a.w, a.d, a.h, a.weight) == (b.w, b.d, b.h, b.weight) for a, b in zip(b_a, b_b))


def test_floor_grid_enthaelt_den_letzten_erreichbaren_schritt_in_y():
    """D = 150 ist KEIN Vielfaches von step = 20 (150 // 20 = 7, Rest 10): der letzte Gitterpunkt bei
    y = 140 ist ein echter, von einer Box erreichbarer Innenpunkt (anders als der x-Randpunkt bei
    x = W = 160, den keine Box mit positiver Breite je erreichen kann) - er darf nicht fehlen."""
    pts = _floor_grid(160.0, 150.0, step=20.0)
    ys = {y for (_x, y, _z) in pts}
    assert 140.0 in ys and 160.0 not in ys  # 150 selbst ist kein Vielfaches von 20, 140 ist der letzte Schritt


def test_try_place_tie_break_bevorzugt_den_zuerst_gefundenen_kandidaten():
    """Kandidatenlisten-Reihenfolge kann einen scheinbaren Vorteil vortäuschen (Bestfit-Tiebreak-Fall,
    siehe feedback_bestfit_tiebreak_order_artefact) - hier ausdrücklich geprüft: bei einem EXAKTEN
    Distanz-Gleichstand zwischen zwei Kandidaten muss `try_place` den in der sortierten Kandidatenliste
    ZUERST auftretenden wählen (deterministisch, kein Sich-selbst-Ueberschreiben durch spätere Gleichstände).
    Konstruierte Instanz: target=(60, 70), Box 20x20x20 -> die Kandidaten (x=40, y=60) und (x=60, y=60) sind
    beide exakt 100 (Boxmitte-Distanz-Quadrat) von target entfernt und die nächstgelegenen überhaupt;
    (x=40, y=60) kommt in der sortierten Kandidatenliste (Schlüssel z, y, x) zuerst."""
    box = Box(20, 20, 20, 5)
    p = try_place(box, [], 160.0, 150.0, 160.0, RECHTECK, 40.0, target=(60.0, 70.0), with_floor_grid=True)
    assert (p.x, p.y, p.z) == (40.0, 60.0, 0.0)


def test_make_boxes_gewichtsformel_volumen_mal_dichte_durch_1000():
    """Die Gewichtsformel `w * d * h * density / 1000.0` direkt gegen einen Fall prüfen, in dem die Dichte
    deterministisch 1,0 ist (Dichtestreuung CV = 0 -> keine Zufallsstreuung um den Mittelwert 1,0)."""
    rng = np.random.default_rng(5)
    boxes = make_boxes(rng, 1, 0.0)
    b = boxes[0]
    assert b.weight == pytest.approx(b.w * b.d * b.h * 1.0 / 1000.0, rel=1e-12)


class _FixedRNG:
    """Test-Doppel mit derselben Schnittstelle wie np.random.Generator (nur `uniform`/`normal`), damit der
    Dichte-Bodenwert 0,05 gezielt und ohne Zufalls-Suche getroffen werden kann."""

    def __init__(self, normal_value):
        self._normal_value = normal_value

    def uniform(self, lo, hi):
        return (lo + hi) / 2.0

    def normal(self, _mean, _std):
        return self._normal_value


def test_make_boxes_dichte_bodenwert_ist_005():
    """Eine sehr niedrige (auch negative) gezogene Dichte wird auf den Bodenwert 0,05 begrenzt, nie auf 0
    oder negativ (sonst gäbe es Boxen mit Gewicht <= 0)."""
    rng = _FixedRNG(normal_value=-10.0)
    boxes = make_boxes(rng, 1, 0.5)
    b = boxes[0]
    assert b.weight == pytest.approx(b.w * b.d * b.h * 0.05 / 1000.0, rel=1e-12)


@pytest.mark.parametrize("contour", [RECHTECK, GERUNDET])
def test_h_cg_unterscheidet_sich_von_h_vol_auf_frischer_instanz(contour):
    """Zusätzlicher Zweig-Test (Nullspalten-Falle): H_cg muss auf einer frischen Zufallsinstanz eine andere
    Platzierung liefern als H_vol (sonst wäre der Regler 'Schwerpunkt-bewusste Regel' ein wirkungsloser
    Regler, siehe DEMO-PLAYBOOK Abschnitt 3)."""
    rng = np.random.default_rng(123)
    boxes = make_boxes(rng, 16, 0.3)
    pv, _ = pack_greedy_volume(boxes, W, D, H, contour, CHAMFER)
    pc, _ = pack_cg_aware(boxes, W, D, H, contour, CHAMFER)
    positions_v = sorted((round(p.x, 3), round(p.y, 3), round(p.z, 3)) for p in pv)
    positions_c = sorted((round(p.x, 3), round(p.y, 3), round(p.z, 3)) for p in pc)
    assert positions_v != positions_c
