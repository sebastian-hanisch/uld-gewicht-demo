"""Eingefrorene Instanzen (tests/data/uldg_frozen.json): 4 feste Boxlisten (Zahlenwerte, keine Zufallsziehung
zur Testzeit), mit denen beide Packregeln auf beiden Konturen reproduzierbare Kennzahlen liefern muessen.

Nach DEMO-PLAYBOOK Abschnitt 4 (NumPy-Version-Drift) haengt kein Test hier von `np.random.default_rng` ab:
die Boxen selbst sind als Zahlen im JSON eingefroren (einmalig mit Seeds 11/22/33/44 erzeugt und dann fest
gespeichert), nur das Packverfahren (reine Python-Schleifen plus ein `np.median` ueber eine feste, kurze
Liste) laeuft bei jedem Testlauf neu. Ganzzahlige Kennzahlen (platzierte/unplatzierte Boxen) muessen exakt
stimmen, Gleitkommasummen mit `pytest.approx`."""
from __future__ import annotations

import json
import pathlib

import pytest

from uldg_geometry import pack_cg_aware, pack_greedy_volume
from uldg_model import Box, GERUNDET, RECHTECK, cg_offset, volume_utilization

DATA = json.loads((pathlib.Path(__file__).parent / "data" / "uldg_frozen.json").read_text(encoding="utf-8"))
W, D, H, CHAMFER = 160.0, 150.0, 160.0, 40.0
CONTOURS = {"rechteck": RECHTECK, "gerundet": GERUNDET}


def _ids():
    return [f"seed{c['seed']}-n{c['n']}-cv{c['cv']}" for c in DATA]


@pytest.mark.parametrize("case", DATA, ids=_ids())
@pytest.mark.parametrize("contour_key", ["rechteck", "gerundet"])
def test_frozen_instance_reproduces_measured_metrics(case, contour_key):
    contour = CONTOURS[contour_key]
    boxes = [Box(*b) for b in case["boxes"]]
    exp = case[contour_key]

    pv, uv = pack_greedy_volume(boxes, W, D, H, contour, CHAMFER)
    pc, uc = pack_cg_aware(boxes, W, D, H, contour, CHAMFER)

    assert len(pv) == exp["n_placed_vol"] and len(uv) == exp["n_unplaced_vol"]
    assert len(pc) == exp["n_placed_cg"] and len(uc) == exp["n_unplaced_cg"]
    assert volume_utilization(pv, W, D, H, contour, CHAMFER) == pytest.approx(exp["util_vol"], rel=1e-9, abs=1e-9)
    assert volume_utilization(pc, W, D, H, contour, CHAMFER) == pytest.approx(exp["util_cg"], rel=1e-9, abs=1e-9)

    ox_v, oy_v = cg_offset(pv, W, D)
    ox_c, oy_c = cg_offset(pc, W, D)
    assert [ox_v, oy_v] == pytest.approx(exp["offset_vol"], rel=1e-9, abs=1e-9)
    assert [ox_c, oy_c] == pytest.approx(exp["offset_cg"], rel=1e-9, abs=1e-9)


def test_the_frozen_set_covers_boxzahl_and_cv_stufen():
    """Die eingefrorenen Faelle decken alle drei Boxzahl-Stufen (10/16/24) und mehrere Dichtestreuungen ab."""
    ns = {c["n"] for c in DATA}
    cvs = {c["cv"] for c in DATA}
    assert ns == {10, 16, 24}
    assert cvs >= {0.1, 0.3, 0.6}
    assert len(DATA) == 4
