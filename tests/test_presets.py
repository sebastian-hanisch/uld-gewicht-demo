"""Tests fuer uldg_presets.py: Permalink-Parsing, Einrasten auf Stufen, Presets."""
import uldg_constants as C
import uldg_presets as P


def test_alle_presets_haben_gueltige_werte():
    for name, p in C.PRESETS.items():
        assert p["contour"] in C.CONTOUR_OPTIONS
        assert p["boxes"] in C.BOXES_OPTIONS
        assert p["cv"] in C.CV_OPTIONS
        assert p["tol"] in C.TOL_OPTIONS
        assert C.SEED_RANGE[0] <= p["seed"] <= C.SEED_RANGE[1]


def test_parse_setting_rastet_zahl_auf_naechste_stufe_ein():
    spec = P.SETTING_SPECS["tol_slider"]
    assert P.parse_setting(spec, "0.11") == 0.10
    assert P.parse_setting(spec, "0.17") == 0.20


def test_parse_setting_text_nur_bei_exaktem_treffer():
    spec = P.SETTING_SPECS["contour_select"]
    assert P.parse_setting(spec, "gerundet") == "gerundet"
    assert P.parse_setting(spec, "achteck") is None


def test_parse_setting_seed_wird_begrenzt():
    spec = P.SETTING_SPECS["seed_input"]
    assert P.parse_setting(spec, "500") == C.SEED_RANGE[1]
    assert P.parse_setting(spec, "-5") == C.SEED_RANGE[0]


def test_parse_setting_ungueltige_zahl_gibt_none():
    spec = P.SETTING_SPECS["tol_slider"]
    assert P.parse_setting(spec, "abc") is None
    assert P.parse_setting(spec, "nan") is None
    assert P.parse_setting(spec, "inf") is None


def test_bounds_liefert_lo_hi_fuer_seed():
    lo, hi = P.bounds("seed_input")
    assert (lo, hi) == C.SEED_RANGE
