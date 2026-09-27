"""Abnahmekriterien der fünf Presets (Detailplan Abschnitt 7) - jedes einzeln gegen die vorgerechnete
Messreihe (data/uldg_results.json) prüfbar, damit ein Preset nie eine Geschichte erzählt, die die Zahlen
nicht tragen."""
from __future__ import annotations

import uldg_constants as C
import uldg_results as R
from uldg_format import fmt_pct


def _cell_for(name: str, data: dict) -> dict:
    p = C.PRESETS[name]
    return R.find_cell(data, p["contour"], p["tol"], p["cv"], p["boxes"])


def check_standard(data: dict) -> tuple[bool, str]:
    cell = _cell_for("Standard", data)
    vol, cg = cell["violation_rate_vol"], cell["violation_rate_cg"]
    ok = vol >= 0.60 and cg <= vol / 2.0 + 0.05
    return ok, f"H_vol {fmt_pct(vol)} (>= 60 % erwartet), H_cg {fmt_pct(cg)} (<= etwa die Hälfte von H_vol erwartet)"


def check_enge_toleranz(data: dict) -> tuple[bool, str]:
    cell = _cell_for("Enge Toleranz", data)
    cg = cell["violation_rate_cg"]
    ok = cg >= 0.60
    return ok, f"H_cg {fmt_pct(cg)} (>= 60 % erwartet: die einfache Regel reicht bei enger Toleranz nicht)"


def check_lose_toleranz(data: dict) -> tuple[bool, str]:
    cell = _cell_for("Lose Toleranz", data)
    vol = cell["violation_rate_vol"]
    ok = vol <= 0.30
    return ok, f"H_vol {fmt_pct(vol)} (<= 30 % erwartet: der Unterschied zwischen den Regeln verschwindet fast)"


def check_gerundetes_uld(data: dict) -> tuple[bool, str]:
    cell_g = _cell_for("Gerundetes ULD", data)
    cell_r = R.find_cell(data, "rechteck", cell_g["tol"], cell_g["density_cv"], cell_g["n_boxes"])
    ok = cell_g["violation_rate_vol"] < cell_r["violation_rate_vol"]
    return ok, (f"H_vol gerundet {fmt_pct(cell_g['violation_rate_vol'])} gegen Rechteck {fmt_pct(cell_r['violation_rate_vol'])} "
                "(gerundet niedriger erwartet)")


def check_viele_gemischte_boxen(data: dict) -> tuple[bool, str]:
    cell = _cell_for("Viele, gemischte Boxen", data)
    ok = cell["unplaced_cg_mean"] > cell["unplaced_vol_mean"]
    return ok, f"unplatzierte Boxen H_cg {cell['unplaced_cg_mean']:.2f} gegen H_vol {cell['unplaced_vol_mean']:.2f} (H_cg größer erwartet)"


CHECKS = {
    "Standard": check_standard,
    "Enge Toleranz": check_enge_toleranz,
    "Lose Toleranz": check_lose_toleranz,
    "Gerundetes ULD": check_gerundetes_uld,
    "Viele, gemischte Boxen": check_viele_gemischte_boxen,
}


def check_all(data: dict) -> dict[str, tuple[bool, str]]:
    return {name: fn(data) for name, fn in CHECKS.items()}
