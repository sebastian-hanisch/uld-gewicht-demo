"""Tests fuer uldg_format.py (deutsches Dezimalkomma)."""
from uldg_format import fmt_num, fmt_pct, fmt_pp


def test_fmt_num_verwendet_komma():
    assert fmt_num(74.5) == "74,5"


def test_fmt_num_vorzeichen():
    assert fmt_num(3.2, signed=True) == "+3,2"
    assert fmt_num(-3.2, signed=True) == "-3,2"


def test_fmt_pct_multipliziert_mit_100():
    assert fmt_pct(0.745) == "74,5 %"
    assert fmt_pct(0.0) == "0,0 %"
    assert fmt_pct(1.0) == "100,0 %"


def test_fmt_pp_haengt_einheit_an():
    assert fmt_pp(36.5) == "+36,5 Prozentpunkte"
    assert fmt_pp(-4.0) == "-4,0 Prozentpunkte"
