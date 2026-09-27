"""Korrektheits-Checks für uldg_model.py - übernommen aus
packen-planung/messreihe_uld_gewicht/check.py (dort als Skript, hier als pytest), Checks 1-6 und 11
(Datentypen, Kontur-Geometrie, Volumen, Schwerpunkt-Kennzahlen ohne Packalgorithmus)."""
from __future__ import annotations

import numpy as np

from uldg_model import Box, GERUNDET, Placed, RECHTECK, cg_offset, cg_violation, corners_ok, usable_volume, volume_utilization

W, D, H, CHAMFER = 160.0, 150.0, 160.0, 40.0


def test_handinstanz_symmetrische_boxen_offset_null():
    """Check 1: zwei identische Boxen symmetrisch platziert -> Schwerpunkt exakt in der Mitte."""
    b1, b2 = Box(40, 40, 40, 10), Box(40, 40, 40, 10)
    placed = [Placed(b1, 0, 0, 0), Placed(b2, W - 40, D - 40, 0)]
    cx, cy = cg_offset(placed, W, D)
    assert abs(cx) < 1e-6 and abs(cy) < 1e-6


def test_handinstanz_box_in_ecke_offset_von_hand():
    """Check 2: eine Box in einer Ecke -> Offset von Hand nachgerechnet."""
    b3 = Box(20, 20, 20, 5)
    placed = [Placed(b3, 0, 0, 0)]
    cx, cy = cg_offset(placed, W, D)
    want_cx, want_cy = 10 - W / 2, 10 - D / 2
    assert abs(cx - want_cx) < 1e-9 and abs(cy - want_cy) < 1e-9


def test_leere_platzierung_offset_null_kein_nenner_null_fehler():
    """Check 3: leere Platzierung -> Offset (0, 0), kein Fehler durch Division durch 0."""
    assert cg_offset([], W, D) == (0.0, 0.0)


def test_rechteck_kontur_lehnt_nur_ausserhalb_ab():
    """Check 4: Rechteck-Kontur lehnt nur Boxen außerhalb der Außenmaße ab, nie wegen der Ecken."""
    assert corners_ok(0, 0, 5, 5, W, D, RECHTECK, CHAMFER)
    assert not corners_ok(W - 4, 0, 5, 5, W, D, RECHTECK, CHAMFER)


def test_gerundete_kontur_lehnt_abgeschnittene_ecke_ab():
    """Check 5a: Box exakt in der abgeschnittenen Ecke wird abgelehnt."""
    assert not corners_ok(0, 0, 5, 5, W, D, GERUNDET, CHAMFER)


def test_gerundete_kontur_akzeptiert_zentrierte_box():
    """Check 5b: dieselbe Box zentriert ist zulässig."""
    assert corners_ok(W / 2 - 2.5, D / 2 - 2.5, 5, 5, W, D, GERUNDET, CHAMFER)


def test_gerundete_kontur_chamfer_kante_ist_zulaessig():
    """Check 5c: eine Box, die die Chamfer-Linie exakt berührt, ist noch zulässig (>=), keine Ecke ragt raus."""
    assert corners_ok(CHAMFER, 0, 1e-6, 1e-6, W, D, GERUNDET, CHAMFER)


def test_gerundete_kontur_chamfer_kante_ecke_unten_rechts():
    """Die gerundete Kontur schneidet alle VIER Ecken ab, nicht nur (0, 0) - jede eigene Bedingung
    (px+py, (W-px)+py, px+(D-py), (W-px)+(D-py)) einzeln auf der Chamfer-Linie prüfen. Ecke unten rechts
    (W, 0): die Bedingung (W-px)+py>=chamfer. Die Box liegt knapp INNERHALB (tuckt sich Richtung Mitte ein),
    ihre äußerste Ecke berührt die Chamfer-Linie exakt - eine Box, die stattdessen über die Linie hinaus
    wächst, würde zu Recht abgelehnt (siehe corners_ok-Logik: jede der vier Boxecken wird geprüft)."""
    assert corners_ok(W - CHAMFER - 1e-6, 0, 1e-6, 1e-6, W, D, GERUNDET, CHAMFER)


def test_gerundete_kontur_chamfer_kante_ecke_oben_links():
    """Ecke oben links (0, D): die Bedingung px+(D-py)>=chamfer, Box knapp innerhalb, äußerste Ecke
    berührt die Chamfer-Linie."""
    assert corners_ok(0, D - CHAMFER - 1e-6, 1e-6, 1e-6, W, D, GERUNDET, CHAMFER)


def test_gerundete_kontur_chamfer_kante_ecke_oben_rechts():
    """Ecke oben rechts (W, D): die Bedingung (W-px)+(D-py)>=chamfer, Box knapp innerhalb, äußerste Ecke
    berührt die Chamfer-Linie."""
    assert corners_ok(W - CHAMFER - 1e-6, D - 1e-6, 1e-6, 1e-6, W, D, GERUNDET, CHAMFER)


def test_monte_carlo_flaeche_trifft_formel():
    """Check 6a: nutzbares Volumen der gerundeten Kontur per Monte-Carlo-Flächenschätzung (400.000 Punkte)
    gegen die geschlossene Formel, auf 1 % Toleranz."""
    rng = np.random.default_rng(0)
    n_mc = 400_000
    xs = rng.uniform(0, W, n_mc)
    ys = rng.uniform(0, D, n_mc)
    inside = (
        (xs + ys >= CHAMFER) & ((W - xs) + ys >= CHAMFER)
        & (xs + (D - ys) >= CHAMFER) & ((W - xs) + (D - ys) >= CHAMFER)
    )
    area_mc = inside.mean() * W * D
    area_formula = W * D - 2 * CHAMFER * CHAMFER
    assert abs(area_mc - area_formula) / area_formula < 0.01


def test_usable_volume_gerundet_nutzt_dieselbe_formel_mal_h():
    """Check 6b."""
    area_formula = W * D - 2 * CHAMFER * CHAMFER
    assert abs(usable_volume(W, D, H, GERUNDET, CHAMFER) - area_formula * H) < 1e-6


def test_usable_volume_rechteck_ist_w_mal_d_mal_h():
    """Check 6c."""
    assert usable_volume(W, D, H, RECHTECK, CHAMFER) == W * D * H


def test_usable_volume_gerundet_kleiner_als_rechteck():
    """Check 6d."""
    assert usable_volume(W, D, H, GERUNDET, CHAMFER) < usable_volume(W, D, H, RECHTECK, CHAMFER)


def test_volume_utilization_division_guard_bei_null_volumen():
    """Division-durch-0-Schutz in volume_utilization(): bei einem Container ohne Volumen (uv == 0) muss die
    Funktion 0.0 zurückgeben statt eine ZeroDivisionError auszulösen - der Zweig `if uv > 0` ist ein
    ECHTES '>' (strikt), nicht '>='."""
    assert volume_utilization([], 0.0, 0.0, 0.0, RECHTECK, CHAMFER) == 0.0


def test_cg_violation_toleranzgrenze_exakt_keine_verletzung():
    """Check 11a: Toleranzgrenze exakt getroffen -> keine Verletzung."""
    assert not cg_violation(0.1 * W / 2, 0.0, W, D, 0.1)


def test_cg_violation_knapp_darueber_ist_verletzung():
    """Check 11b: knapp über der Toleranzgrenze -> Verletzung."""
    assert cg_violation(0.1 * W / 2 + 0.01, 0.0, W, D, 0.1)


def test_cg_violation_exakt_auf_dem_epsilon_x_keine_verletzung():
    """Grenzfall exakt auf der `+ 1e-9`-Schwelle in x: die Verletzung ist ein ECHTES '>' (strikt), nicht '>='
    - exakt auf der Schwelle zählt noch nicht als Verletzung."""
    assert not cg_violation(0.1 * (W / 2) + 1e-9, 0.0, W, D, 0.1)


def test_cg_violation_exakt_auf_dem_epsilon_y_keine_verletzung():
    """Derselbe Grenzfall für die y-Achse."""
    assert not cg_violation(0.0, 0.1 * (D / 2) + 1e-9, W, D, 0.1)
