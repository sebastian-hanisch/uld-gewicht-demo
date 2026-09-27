"""Reproduktion der Vorab-Messreihe (Detailplan AP 0/7): derselbe Sweep wie
packen-planung/messreihe_uld_gewicht/sweep.py, hier gegen die aufgeteilten Module uldg_model/uldg_geometry.
Schreibt data/uldg_results.json (nicht Teil der CI - Laufzeit rund 20-25 s, siehe Detailplan Abschnitt 10).
Vorlage für tools/check_full.py: dort wird dieselbe Rechnung gegen die eingecheckte Datei geprüft (AP 7,
Bau-Gate).

Die Zellen-Seeds kommen bewusst mechanisch unverändert aus `hash((contour, tol, cv, n))` (wie im Original
messreihe_uld_gewicht/sweep.py) - das macht den Sweep NICHT bit-reproduzierbar zwischen verschiedenen
Prozessen, weil Pythons String-`hash()` pro Prozess zufällig gesalzen ist (PYTHONHASHSEED, PEP 456), es sei
denn, man fixiert ihn ausdrücklich. Siehe tools/check_full.py für die Einordnung und den Ersatz-Nachweis
(Selbst-Reproduzierbarkeit + statistische Nähe statt Bitgleichheit)."""
from __future__ import annotations

import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from uldg_geometry import make_boxes, pack_cg_aware, pack_greedy_volume  # noqa: E402
from uldg_model import GERUNDET, RECHTECK, cg_offset, cg_violation, usable_volume, volume_utilization  # noqa: E402

W, D, H, CHAMFER = 160.0, 150.0, 160.0, 40.0
N_INSTANCES = 200
TOLS = [0.05, 0.10, 0.20]
DENSITY_CVS = [0.1, 0.3, 0.6]
N_BOXES = [10, 16, 24]


def run_sweep():
    rows = []
    for contour in (RECHTECK, GERUNDET):
        for tol in TOLS:
            for cv in DENSITY_CVS:
                for n in N_BOXES:
                    rng = np.random.default_rng(hash((contour, tol, cv, n)) % (2 ** 31))
                    vio_vol = vio_cg = 0
                    util_vol_list, util_cg_list = [], []
                    unplaced_vol_list, unplaced_cg_list = [], []
                    for _i in range(N_INSTANCES):
                        boxes = make_boxes(rng, n, cv)
                        pv, uv = pack_greedy_volume(boxes, W, D, H, contour, CHAMFER)
                        pc, uc = pack_cg_aware(boxes, W, D, H, contour, CHAMFER)
                        ox_v, oy_v = cg_offset(pv, W, D)
                        ox_c, oy_c = cg_offset(pc, W, D)
                        vio_vol += cg_violation(ox_v, oy_v, W, D, tol)
                        vio_cg += cg_violation(ox_c, oy_c, W, D, tol)
                        util_vol_list.append(volume_utilization(pv, W, D, H, contour, CHAMFER))
                        util_cg_list.append(volume_utilization(pc, W, D, H, contour, CHAMFER))
                        unplaced_vol_list.append(len(uv))
                        unplaced_cg_list.append(len(uc))
                    rows.append(dict(
                        contour=contour, tol=tol, density_cv=cv, n_boxes=n,
                        violation_rate_vol=vio_vol / N_INSTANCES,
                        violation_rate_cg=vio_cg / N_INSTANCES,
                        util_vol_mean=float(np.mean(util_vol_list)),
                        util_cg_mean=float(np.mean(util_cg_list)),
                        util_diff_mean=float(np.mean(np.array(util_cg_list) - np.array(util_vol_list))),
                        util_diff_se=float(np.std(np.array(util_cg_list) - np.array(util_vol_list), ddof=1) / np.sqrt(N_INSTANCES)),
                        unplaced_vol_mean=float(np.mean(unplaced_vol_list)),
                        unplaced_cg_mean=float(np.mean(unplaced_cg_list)),
                    ))
    vol_rechteck = usable_volume(W, D, H, RECHTECK, CHAMFER)
    vol_gerundet = usable_volume(W, D, H, GERUNDET, CHAMFER)
    return dict(
        W=W, D=D, H=H, chamfer=CHAMFER, n_instances=N_INSTANCES,
        vol_rechteck=vol_rechteck, vol_gerundet=vol_gerundet,
        kontur_verlust_pct=100.0 * (vol_rechteck - vol_gerundet) / vol_rechteck,
        rows=rows,
    )


def main():
    t0 = time.time()
    out = run_sweep()
    out_path = ROOT / "data" / "uldg_results.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out['rows'])} Zellen, {len(out['rows']) * N_INSTANCES * 2} Packungen, {time.time() - t0:.1f}s")
    print(f"Kontur-Verlust (Rechteck->gerundet, gleiche Außenhülle): {out['kontur_verlust_pct']:.1f}%")


if __name__ == "__main__":
    main()
