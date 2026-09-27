"""Jede Zahl aus dem README wird hier gegen data/uldg_results.json nachgerechnet (DEMO-PLAYBOOK Abschnitt 4:
erst messen, dann Text schreiben - keine Behauptung ohne Test)."""
import pytest

import uldg_results as R

D = R.load_results()
REF = R.find_cell(D, "rechteck", 0.10, 0.3, 16)
REF_G = R.find_cell(D, "gerundet", 0.10, 0.3, 16)
TIGHT = R.find_cell(D, "rechteck", 0.05, 0.3, 16)
LOSE = R.find_cell(D, "rechteck", 0.20, 0.3, 16)
MANY = R.find_cell(D, "gerundet", 0.10, 0.6, 24)


def test_befund_reine_volumen_packung_verletzt_meistens():
    assert REF["violation_rate_vol"] == pytest.approx(0.745)


def test_befund_schwerpunktregel_senkt_deutlich():
    assert REF["violation_rate_cg"] == pytest.approx(0.380)
    assert R.gain_pp(REF) == pytest.approx(36.5)


def test_befund_enge_toleranz_reicht_nicht():
    assert TIGHT["violation_rate_vol"] == pytest.approx(0.955)
    assert TIGHT["violation_rate_cg"] == pytest.approx(0.775)


def test_befund_lose_toleranz_fast_unkritisch():
    assert LOSE["violation_rate_vol"] == pytest.approx(0.095)


def test_befund_volumenpreis_vernachlaessigbar():
    s = R.util_price_summary(D)
    assert round(100 * s["min"], 1) == pytest.approx(-1.6)
    assert round(100 * s["max"], 1) == pytest.approx(0.1)
    assert round(100 * s["mean"], 2) == pytest.approx(-0.17)


def test_befund_unplatzierte_boxen_zeigen_den_preis():
    assert MANY["unplaced_vol_mean"] == pytest.approx(0.045)
    assert MANY["unplaced_cg_mean"] == pytest.approx(0.82)


def test_befund_kontur_kostet_volumen():
    s = R.kontur_summary(D)
    assert s["verlust_pct"] == pytest.approx(13.333333333333334, rel=1e-9)
    assert round(s["verlust_pct"], 1) == pytest.approx(13.3)
    assert s["vol_rechteck"] / 1e6 == pytest.approx(3.84)
    assert s["vol_gerundet"] / 1e6 == pytest.approx(3.328, rel=1e-3)


def test_befund_regel_hilft_nicht_in_jeder_zelle():
    assert any(R.gain_pp(c) < 0 for c in R.cells(D))


def test_urteilsverteilung_13_27_14():
    rows = R.regime_rows(D)
    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    assert counts[R.STATE_DEUTLICH] == 13
    assert counts[R.STATE_NICHT_AUSREICHEND] == 27
    assert counts[R.STATE_UNKRITISCH] == 14


def test_gerundete_kontur_hat_niedrigere_verletzungsrate_bei_gleicher_einstellung():
    assert REF_G["violation_rate_vol"] == pytest.approx(0.365)
    assert REF_G["violation_rate_vol"] < REF["violation_rate_vol"]
