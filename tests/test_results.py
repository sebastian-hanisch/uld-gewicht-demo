"""Tests fuer uldg_results.py: exakte Zell-Zuordnung (AP 0), Urteilslogik in drei Zustaenden, Kennzahlen."""
from __future__ import annotations

from itertools import product

import pytest

import uldg_results as R

D = R.load_results()


def test_alle_reglerkombinationen_liegen_auf_einer_gemessenen_zelle():
    """AP 0: die drei Regler (Kontur, Boxzahl, Dichtestreuung) bilden zusammen mit der Toleranz genau die
    vier Sweep-Dimensionen ab - 2 x 3 x 3 x 3 = 54 Kombinationen, keine Naeherung noetig."""
    combos = list(product(R.CONTOURS, R.TOL_OPTIONS, R.CV_OPTIONS, R.N_BOXES_OPTIONS))
    assert len(combos) == 54
    for contour, tol, cv, n in combos:
        cell = R.find_cell(D, contour, tol, cv, n)
        assert cell["contour"] == contour and cell["n_boxes"] == n


def test_unbekannte_kombination_wirft_key_error():
    with pytest.raises(KeyError):
        R.find_cell(D, "rechteck", 0.15, 0.3, 16)


def test_54_zellen_insgesamt_ohne_duplikate():
    seen = set()
    for c in R.cells(D):
        key = (c["contour"], c["tol"], c["density_cv"], c["n_boxes"])
        assert key not in seen
        seen.add(key)
    assert len(seen) == 54


@pytest.mark.parametrize("name,args,expected_state", [
    ("Standard", ("rechteck", 0.10, 0.3, 16), R.STATE_DEUTLICH),
    ("Enge Toleranz", ("rechteck", 0.05, 0.3, 16), R.STATE_NICHT_AUSREICHEND),
    ("Lose Toleranz", ("rechteck", 0.20, 0.3, 16), R.STATE_UNKRITISCH),
    ("Gerundetes ULD", ("gerundet", 0.10, 0.3, 16), R.STATE_DEUTLICH),
    ("Viele gemischte Boxen", ("gerundet", 0.10, 0.6, 24), R.STATE_DEUTLICH),
])
def test_presets_liefern_das_im_plan_beschriebene_urteil(name, args, expected_state):
    cell = R.find_cell(D, *args)
    assert R.judgment(cell) == expected_state, name


def test_alle_drei_urteilszustaende_kommen_in_der_messreihe_vor():
    """Kein Zustand ist ein toter Zweig (Nullspalten-Signal): jeder der drei Zustaende muss unter den 54
    Zellen mindestens einmal auftreten, sonst waere die App-Meldung nie in diesem Zustand zu sehen."""
    states = {R.judgment(c) for c in R.cells(D)}
    assert states == {R.STATE_UNKRITISCH, R.STATE_DEUTLICH, R.STATE_NICHT_AUSREICHEND}


def test_gain_pp_vorzeichen():
    """gain_pp ist H_vol minus H_cg: positiv, wenn die Regel die Verletzungsrate senkt."""
    cell = R.find_cell(D, "rechteck", 0.10, 0.3, 16)
    assert R.gain_pp(cell) == pytest.approx(100.0 * (cell["violation_rate_vol"] - cell["violation_rate_cg"]))


def test_gain_pp_kann_negativ_sein_regel_hilft_nicht_immer():
    """Ehrlichkeitskultur: die schwerpunkt-bewusste Regel ist nicht in jeder Zelle besser als die reine
    Volumen-Regel (siehe ERGEBNIS.md); mindestens eine gemessene Zelle muss das zeigen."""
    assert any(R.gain_pp(c) < 0 for c in R.cells(D))


def test_regime_rows_deckt_alle_54_zellen_ab():
    rows = R.regime_rows(D)
    assert len(rows) == 54
    for row in rows:
        assert row["state"] in R.STATE_LABEL
        assert row["label"] == R.STATE_LABEL[row["state"]]


def test_tol_rows_liefert_alle_drei_toleranzstufen_derselben_zelle():
    rows = R.tol_rows(D, "rechteck", 0.3, 16)
    assert [r["tol"] for r in rows] == list(R.TOL_OPTIONS)
    assert all(r["contour"] == "rechteck" and r["n_boxes"] == 16 and abs(r["density_cv"] - 0.3) < 1e-9 for r in rows)


def test_util_price_summary_liegt_im_gemessenen_bereich():
    """ERGEBNIS.md Befund 3: Auslastungsdifferenz zwischen -0,016 und +0,001 ueber alle 54 Zellen."""
    s = R.util_price_summary(D)
    assert -0.02 < s["min"] < 0 <= s["max"] < 0.01
    assert -0.005 < s["mean"] < 0.0


def test_kontur_summary_stimmt_mit_ergebnis_md_ueberein():
    s = R.kontur_summary(D)
    assert s["vol_rechteck"] == pytest.approx(3_840_000.0)
    assert s["vol_gerundet"] == pytest.approx(3_328_000.0)
    assert s["verlust_pct"] == pytest.approx(13.333333333333334, rel=1e-9)


def test_judgment_text_enthaelt_die_gemessenen_prozentzahlen():
    cell = R.find_cell(D, "rechteck", 0.10, 0.3, 16)
    text = R.judgment_text(cell)
    assert "74,5" in text  # 0.745 -> Prozentanzeige mit deutschem Komma
    assert R.STATE_LABEL[R.STATE_DEUTLICH] in text
