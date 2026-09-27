"""AppTest: Skelett und Footer, jedes Preset, Permalink, alle Regler an Min und Max, alle drei Urteilszustände,
keine wirkungslosen Regler, PDF, Texte. Deckt DEMO-PLAYBOOK Abschnitt 5 (Browser-Verifikation reicht AppTest
allein nicht, ergänzt in AP 7 mit einem echten Browser-Durchlauf)."""
import pathlib
import re

import pytest
from streamlit.testing.v1 import AppTest

import uldg_constants as C
import uldg_results as R
from uldg_presets import PRESET_STATE_KEYS, SETTING_SPECS

APP = str(pathlib.Path(__file__).resolve().parent.parent / "app.py")
DATA = R.load_results()
FOOTER = ("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
          "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
          "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)")


def fresh(**query):
    at = AppTest.from_file(APP, default_timeout=180)
    for k, v in query.items():
        at.query_params[k] = v
    at.run()
    assert not at.exception, at.exception
    return at


def set_and_run(at, **values):
    for key, value in values.items():
        if key == "seed_input":
            at.number_input(key=key).set_value(value)
        elif key == "contour_select":
            at.selectbox(key=key).set_value(value)
        else:
            at.select_slider(key=key).set_value(value)
    at.run()
    assert not at.exception, at.exception
    return at


def click(at, label):
    next(b for b in at.button if b.label == label).click().run()
    assert not at.exception, at.exception
    return at


def state_values(at):
    return {key: at.session_state[key] for key in SETTING_SPECS}


# ---------------------------------------------------------------------------------------------------
# Skelett
# ---------------------------------------------------------------------------------------------------
def test_skeleton_and_footer():
    at = fresh()
    assert [h.value for h in at.sidebar.header] == ["⚙️ Einstellungen"]
    assert len(at.title) == 1 and at.title[0].value == "📦 ULD-Beladung: Volumen gegen Schwerpunkt"
    assert any(v.value.startswith("## 📦 Hält eine Volumen-Packung den Schwerpunkt ein?") for v in at.markdown)
    assert any(v.value.startswith("### 📐 Was die Messreihe über 200 Instanzen zeigt") for v in at.markdown)
    assert [e.label for e in at.expander] == ["🔧 Wie wir das erreichen – vollständiger Methodenvergleich",
                                                "Wie funktioniert diese Demo?", "📐 Mathematische Formulierung"]
    assert any(c.value == FOOTER for c in at.caption)
    presets = [b.label for b in at.button if b.label in C.PRESETS]
    assert presets == list(C.PRESETS)
    assert len(at.sidebar.header) == 1 and len(at.sidebar.subheader) == 0


def test_preset_buttons_have_help_text():
    at = fresh()
    buttons = [b for b in at.button if b.label in C.PRESETS]
    assert all(b.help and len(b.help) > 15 for b in buttons)
    assert [b.help for b in buttons] == [C.PRESET_HELP[n] for n in C.PRESETS]


def test_no_dead_controls():
    """Nur die dokumentierten Widgets, keine Checkboxen/Toggles/blinden Regler."""
    at = fresh()
    assert not at.sidebar.checkbox and not at.sidebar.toggle and not at.checkbox and not at.toggle
    assert not at.slider  # nur select_slider/selectbox/number_input


def test_sliders_have_the_measured_stages_and_seed_bounds():
    at = fresh()
    assert list(at.select_slider(key="boxes_slider").options) == [str(v) for v in C.BOXES_OPTIONS]
    assert list(at.select_slider(key="cv_slider").options) == [str(v) for v in C.CV_OPTIONS]
    assert list(at.select_slider(key="tol_slider").options) == [str(v) for v in C.TOL_OPTIONS]
    assert list(at.selectbox(key="contour_select").options) == [C.CONTOUR_LABEL[v] for v in C.CONTOUR_OPTIONS]
    seed = at.number_input(key="seed_input")
    assert (seed.min, seed.max, seed.step, seed.value) == (C.SEED_RANGE[0], C.SEED_RANGE[1], 1, C.SEED_DEFAULT)


def test_default_state_and_permalink_written_to_the_address_bar():
    at = fresh()
    assert state_values(at) == dict(contour_select=C.CONTOUR_DEFAULT, boxes_slider=C.BOXES_DEFAULT,
                                     cv_slider=C.CV_DEFAULT, tol_slider=C.TOL_DEFAULT, seed_input=C.SEED_DEFAULT)
    qp = {k: (v[0] if isinstance(v, list) else v) for k, v in dict(at.query_params).items()}
    assert qp["contour"] == C.CONTOUR_DEFAULT and qp["seed"] == str(C.SEED_DEFAULT)


# ---------------------------------------------------------------------------------------------------
# Presets, Permalink, Regler
# ---------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_sets_all_controls_and_runs_without_exception(name):
    at = fresh()
    click(at, name)
    p = C.PRESETS[name]
    assert state_values(at) == {PRESET_STATE_KEYS[k]: v for k, v in p.items()}
    cell = R.find_cell(DATA, p["contour"], p["tol"], p["cv"], p["boxes"])
    assert any(R.judgment_text(cell) in i.value for i in at.info)


def test_permalink_sets_the_controls_and_snaps_to_stages():
    at = fresh(contour="gerundet", n="24", cv="0.6", tol="0.05", seed="17")
    assert state_values(at) == dict(contour_select="gerundet", boxes_slider=24, cv_slider=0.6, tol_slider=0.05, seed_input=17)
    at = fresh(contour="achteck", n="15", cv="0.4", tol="0.5", seed="-4")
    vals = state_values(at)
    assert vals["contour_select"] == C.CONTOUR_DEFAULT  # ungültiger Text: Standard
    assert vals["boxes_slider"] in C.BOXES_OPTIONS and vals["cv_slider"] in C.CV_OPTIONS and vals["tol_slider"] in C.TOL_OPTIONS
    assert vals["seed_input"] == C.SEED_RANGE[0]  # -4 wird auf die Untergrenze begrenzt


def test_all_controls_at_min_and_max_run_without_exception():
    at = fresh()
    for key, options in (("boxes_slider", C.BOXES_OPTIONS), ("cv_slider", C.CV_OPTIONS), ("tol_slider", C.TOL_OPTIONS)):
        for v in (options[0], options[-1]):
            set_and_run(at, **{key: v})
            assert state_values(at)[key] == v
    for v in ("rechteck", "gerundet"):
        set_and_run(at, contour_select=v)
        assert state_values(at)["contour_select"] == v
    for v in C.SEED_RANGE:
        set_and_run(at, seed_input=v)
        assert state_values(at)["seed_input"] == v


def test_new_instance_button_rolls_a_new_seed(monkeypatch):
    import uldg_presets as P
    frozen = iter([3, 5, C.SEED_DEFAULT, 3])
    monkeypatch.setattr(P.random, "randint", lambda lo, hi: next(frozen))
    at = fresh()
    seen = {at.session_state["seed_input"]}
    for _ in range(3):
        click(at, "🎲 Neue Instanz")
        seen.add(at.session_state["seed_input"])
        assert C.SEED_RANGE[0] <= at.session_state["seed_input"] <= C.SEED_RANGE[1]
    assert seen == {C.SEED_DEFAULT, 3, 5}


# ---------------------------------------------------------------------------------------------------
# Urteilszustände, Kennzahlen, Texte
# ---------------------------------------------------------------------------------------------------
def test_all_three_judgment_states_are_reachable_through_the_controls():
    at = fresh(contour="rechteck", n="16", cv="0.3", tol="0.10")  # Standard: "deutlich"
    assert R.STATE_LABEL[R.STATE_DEUTLICH] in " ".join(i.value for i in at.info)
    at = fresh(contour="rechteck", n="16", cv="0.3", tol="0.05")  # eng: "nicht ausreichend"
    assert R.STATE_LABEL[R.STATE_NICHT_AUSREICHEND] in " ".join(i.value for i in at.info)
    at = fresh(contour="rechteck", n="16", cv="0.3", tol="0.20")  # lose: "unkritisch"
    assert R.STATE_LABEL[R.STATE_UNKRITISCH] in " ".join(i.value for i in at.info)


def test_main_metrics_are_present_and_four():
    at = fresh()
    assert len(at.metric) == 4


def test_pdf_download_button_is_present_and_named():
    at = fresh()
    buttons = at.get("download_button")
    assert len(buttons) == 1 and buttons[0].proto.label == "📄 Packplan als PDF herunterladen"


def test_all_plotly_charts_render_with_unique_keys():
    at = fresh()
    charts = at.get("plotly_chart")
    assert len(charts) >= 6
    ids = [c.proto.id for c in charts]
    assert len(set(ids)) == len(ids)


def test_no_dead_file_links_in_markdown():
    at = fresh()
    for md in list(at.markdown) + list(at.caption):
        for target in re.findall(r"\]\(([^)]+)\)", md.value):
            assert target.startswith("https://"), (target, md.value[:80])


def test_real_umlauts_present():
    at = fresh()
    text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert "schwerpunkt" in text.lower() and "Größenordnung" in text or "Größenordnung" in text


def test_regime_dataframe_is_not_a_dead_column():
    """Nullspalten-Signal: keine Spalte der Regime-Tabelle ist überall gleich."""
    at = fresh()
    regime_frame = next(d.value for d in at.dataframe if "Urteil" in d.value.columns)
    assert len(regime_frame) == 54
    for col in ("H_vol", "H_cg", "Urteil"):
        assert regime_frame[col].astype(str).nunique() > 1


def test_expander_texts_state_the_limits():
    at = fresh()
    how = next(m.value for m in at.markdown if "Nicht Teil dieser Demo" in m.value)
    for needle in ("Extreme-Point-Heuristik", "feste Orientierung", "Grenzen dieses Modells", "erfunden, nicht kalibriert",
                   "enger Toleranz", "stauplanung-demo", "pack_demo"):
        assert needle in how, needle
    math = next(m.value for m in at.markdown if "Kontur (gerundet)" in m.value)
    for needle in ("uldg_model.py", "uldg_geometry.py", "uldg_results.py"):
        assert needle in math, needle
