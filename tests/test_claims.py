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
    assert REF["violation_rate_vol"] == pytest.approx(0.905)


def test_befund_schwerpunktregel_senkt_deutlich():
    assert REF["violation_rate_cg"] == pytest.approx(0.26)
    assert R.gain_pp(REF) == pytest.approx(64.5)


def test_befund_enge_toleranz_reicht_nicht():
    assert TIGHT["violation_rate_vol"] == pytest.approx(0.98)
    assert TIGHT["violation_rate_cg"] == pytest.approx(0.73)


def test_befund_lose_toleranz_fast_unkritisch():
    assert LOSE["violation_rate_vol"] == pytest.approx(0.235)


def test_befund_volumenpreis_klein_aber_messbar():
    """Nach dem Auflage-Fix (siehe ERGEBNIS.md Nachtrag) ist der Volumenpreis nicht mehr vernachlässigbar wie
    vor der Behebung (damals -1,6 bis +0,1 pp), aber weiterhin klein."""
    s = R.util_price_summary(D)
    assert round(100 * s["min"], 1) == pytest.approx(-4.2)
    assert round(100 * s["max"], 1) == pytest.approx(-0.0)
    assert round(100 * s["mean"], 2) == pytest.approx(-0.96)


def test_befund_unplatzierte_boxen_zeigen_den_preis():
    assert MANY["unplaced_vol_mean"] == pytest.approx(6.73)
    assert MANY["unplaced_cg_mean"] == pytest.approx(8.71)


def test_befund_kontur_kostet_volumen():
    s = R.kontur_summary(D)
    assert s["verlust_pct"] == pytest.approx(13.333333333333334, rel=1e-9)
    assert round(s["verlust_pct"], 1) == pytest.approx(13.3)
    assert s["vol_rechteck"] / 1e6 == pytest.approx(3.84)
    assert s["vol_gerundet"] / 1e6 == pytest.approx(3.328, rel=1e-3)


def test_befund_regel_hilft_in_jeder_gemessenen_zelle():
    """Vor dem Auflage-Fix gab es Zellen mit negativem Gewinn (siehe ERGEBNIS.md 'Bug beim Bauen': die
    schwerpunkt-bewusste Regel war anfangs stellenweise schlechter). Nach der Behebung und der neu gerechneten
    Messreihe ist der Gewinn in allen 54 gemessenen Zellen positiv - das ist selbst ein Befund der neuen
    Messreihe, keine allgemeingültige Garantie."""
    assert all(R.gain_pp(c) >= 0 for c in R.cells(D))
    assert min(R.gain_pp(c) for c in R.cells(D)) == pytest.approx(1.5)


def test_urteilsverteilung_25_22_7():
    rows = R.regime_rows(D)
    counts = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    assert counts[R.STATE_DEUTLICH] == 25
    assert counts[R.STATE_NICHT_AUSREICHEND] == 22
    assert counts[R.STATE_UNKRITISCH] == 7


def test_gerundete_kontur_hat_niedrigere_verletzungsrate_bei_gleicher_einstellung():
    assert REF_G["violation_rate_vol"] == pytest.approx(0.64)
    assert REF_G["violation_rate_vol"] < REF["violation_rate_vol"]
