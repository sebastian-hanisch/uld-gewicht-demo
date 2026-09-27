"""Rauchtests fuer uldg_visualization.py: Figuren bauen ohne Fehler, mit der erwarteten Spurenzahl, und alle
2D-Achsen sind fixedrange (Plotly-Fallstricke, DEMO-PLAYBOOK Abschnitt 3)."""
import numpy as np
import plotly.graph_objects as go

import uldg_results as R
import uldg_visualization as V
from uldg_geometry import make_boxes, pack_cg_aware, pack_greedy_volume
from uldg_model import GERUNDET, RECHTECK

W, D, H, CHAMFER = 160.0, 150.0, 160.0, 40.0
DATA = R.load_results()


def _sample_placed():
    rng = np.random.default_rng(1)
    boxes = make_boxes(rng, 16, 0.3)
    placed, _ = pack_greedy_volume(boxes, W, D, H, RECHTECK, CHAMFER)
    return placed


def test_packing_figure_hat_eine_spur_je_box_plus_kontur():
    placed = _sample_placed()
    fig = V.packing_figure(placed, W, D, H, RECHTECK, CHAMFER)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == len(placed) + 1  # + Kontur-Drahtgitter


def test_packing_figure_leere_packung_hat_nur_die_kontur():
    fig = V.packing_figure([], W, D, H, RECHTECK, CHAMFER)
    assert len(fig.data) == 1


def test_packing_figure_funktioniert_fuer_beide_konturen():
    placed = _sample_placed()
    for contour in (RECHTECK, GERUNDET):
        fig = V.packing_figure(placed, W, D, H, contour, CHAMFER)
        assert isinstance(fig, go.Figure)


def test_violation_rate_figure_hat_zwei_balkenspuren_und_fixedrange():
    rows = R.tol_rows(DATA, "rechteck", 0.3, 16)
    fig = V.violation_rate_figure(rows)
    assert len(fig.data) == 2
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_kontur_volume_figure_baut_ohne_fehler():
    s = R.kontur_summary(DATA)
    fig = V.kontur_volume_figure(s["vol_rechteck"], s["vol_gerundet"])
    assert isinstance(fig, go.Figure)
    assert fig.layout.yaxis.fixedrange


def test_regime_figure_deckt_alle_54_zellen_ab():
    rows = R.regime_rows(DATA)
    fig = V.regime_figure(rows)
    assert len(fig.data[0].x) == 54
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
