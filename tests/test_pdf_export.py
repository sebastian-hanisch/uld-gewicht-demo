"""Tests fuer uldg_pdf_export.py: das PDF muss ohne Fehler entstehen (keine der abstuerzenden Sonderzeichen
Gedankenstrich/Euro, siehe DEMO-PLAYBOOK Abschnitt 7) und ein plausibles PDF-Objekt sein."""
import numpy as np

import uldg_constants as C
import uldg_results as R
from uldg_geometry import make_boxes, pack_cg_aware, pack_greedy_volume
from uldg_model import cg_offset, cg_violation, volume_utilization
from uldg_pdf_export import generate_uldg_pdf

DATA = R.load_results()


def _live(contour="rechteck", n_boxes=16, cv=0.3, tol=0.10, seed=0):
    rng = np.random.default_rng(seed)
    boxes = make_boxes(rng, n_boxes, cv)
    placed_vol, unplaced_vol = pack_greedy_volume(boxes, C.W, C.D, C.H, contour, C.CHAMFER)
    placed_cg, unplaced_cg = pack_cg_aware(boxes, C.W, C.D, C.H, contour, C.CHAMFER)
    ox_v, oy_v = cg_offset(placed_vol, C.W, C.D)
    ox_c, oy_c = cg_offset(placed_cg, C.W, C.D)
    return dict(
        boxes=boxes, placed_vol=placed_vol, unplaced_vol=unplaced_vol, placed_cg=placed_cg, unplaced_cg=unplaced_cg,
        offset_vol=(ox_v, oy_v), offset_cg=(ox_c, oy_c),
        violation_vol=cg_violation(ox_v, oy_v, C.W, C.D, tol), violation_cg=cg_violation(ox_c, oy_c, C.W, C.D, tol),
        util_vol=volume_utilization(placed_vol, C.W, C.D, C.H, contour, C.CHAMFER),
        util_cg=volume_utilization(placed_cg, C.W, C.D, C.H, contour, C.CHAMFER),
    )


def test_pdf_wird_erzeugt_und_beginnt_mit_pdf_signatur():
    live = _live()
    cell = R.find_cell(DATA, "rechteck", 0.10, 0.3, 16)
    data = generate_uldg_pdf(dict(contour="rechteck", n_boxes=16, cv=0.3, tol=0.10, seed=0), live, cell)
    assert isinstance(data, (bytes, bytearray))
    assert data[:5] == b"%PDF-"
    assert len(data) > 500


def test_pdf_funktioniert_ohne_platzierte_boxen():
    """Grenzfall: eine Instanz, in der (fast) nichts platziert wurde, darf das PDF nicht zum Absturz bringen."""
    live = _live(n_boxes=10, cv=0.1, seed=3)
    cell = R.find_cell(DATA, "rechteck", 0.10, 0.1, 10)
    data = generate_uldg_pdf(dict(contour="rechteck", n_boxes=10, cv=0.1, tol=0.10, seed=3), live, cell)
    assert data[:5] == b"%PDF-"


def test_pdf_funktioniert_fuer_gerundete_kontur():
    live = _live(contour="gerundet")
    cell = R.find_cell(DATA, "gerundet", 0.10, 0.3, 16)
    data = generate_uldg_pdf(dict(contour="gerundet", n_boxes=16, cv=0.3, tol=0.10, seed=0), live, cell)
    assert data[:5] == b"%PDF-"
