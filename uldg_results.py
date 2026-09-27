"""ULD-Beladung: Volumen gegen Schwerpunkt - Laden und Auswerten der vorgerechneten Messreihe
(data/uldg_results.json, 54 Zellen x 200 gepaarte Instanzen, aus messreihe_uld_gewicht/sweep.py).

Die drei Regler (Kontur, Boxzahl, Dichtestreuung) bilden zusammen mit der Schwerpunkt-Toleranz genau die vier
Sweep-Dimensionen ab (AP 0 bestätigt: alle 54 Kombinationen liegen exakt auf einer gemessenen Zelle, siehe
tests/test_results.py::test_alle_reglerkombinationen_liegen_auf_einer_gemessenen_zelle) - `find_cell` ist
deshalb ein exakter Treffer, keine Näherung auf die nächstliegende Zelle wie bei anderen Fall-Demos."""
from __future__ import annotations

import functools
import json
import pathlib

from uldg_format import fmt_num, fmt_pct

DATA_PATH = pathlib.Path(__file__).parent / "data" / "uldg_results.json"

CONTOURS = ("rechteck", "gerundet")
TOL_OPTIONS = (0.05, 0.10, 0.20)
CV_OPTIONS = (0.1, 0.3, 0.6)
N_BOXES_OPTIONS = (10, 16, 24)

# Urteilsschwellen (Kernabschnitt, drei Zustände wie im Detailplan Abschnitt 6 vorgesehen). Mit 200 Instanzen
# je Zelle liegt die Stichprobenstreuung einer Anteilsschätzung (Standardfehler sqrt(p(1-p)/200)) bei
# höchstens rund 3,5 Prozentpunkten - alle drei Schwellen liegen klar darüber, kein Rauschartefakt.
UNKRITISCH_VOL_MAX = 0.15   # H_vol verletzt ohnehin selten: die Toleranz ist in dieser Zelle kaum ein Thema
DEUTLICH_MIN_GAIN = 0.15    # H_vol minus H_cg (Anteil, nicht Prozentpunkte): Mindest-Reduktion für "hilft deutlich"
DEUTLICH_MAX_CG = 0.40      # UND die Regel muss die Restverletzung auf einen überschaubaren Wert senken - sonst
                             # zählt eine große relative Reduktion allein nicht als "deutlich" (die enge-Toleranz-Zelle
                             # senkt z. B. von 95,5 % auf 77,5 %, eine große Reduktion, bleibt aber untragbar hoch:
                             # das ist der Befund "reicht nicht", nicht "hilft deutlich" - siehe ERGEBNIS.md Befund 2)

STATE_UNKRITISCH = "unkritisch"
STATE_DEUTLICH = "deutlich"
STATE_NICHT_AUSREICHEND = "nicht_ausreichend"

STATE_LABEL = {
    STATE_UNKRITISCH: "Toleranz ohnehin unkritisch",
    STATE_DEUTLICH: "Schwerpunktregel hilft deutlich",
    STATE_NICHT_AUSREICHEND: "Schwerpunktregel hilft, reicht aber nicht",
}


@functools.lru_cache(maxsize=1)
def load_results(path: pathlib.Path | None = None) -> dict:
    p = path or DATA_PATH
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def cells(data: dict) -> list[dict]:
    return data["rows"]


def find_cell(data: dict, contour: str, tol: float, cv: float, n_boxes: int) -> dict:
    """Exakter Treffer (AP 0: die Reglerstufen SIND die gemessenen Zellen)."""
    for r in cells(data):
        if r["contour"] == contour and abs(r["tol"] - tol) < 1e-9 and abs(r["density_cv"] - cv) < 1e-9 and r["n_boxes"] == n_boxes:
            return r
    raise KeyError((contour, tol, cv, n_boxes))


def gain_pp(cell: dict) -> float:
    """H_vol minus H_cg in Prozentpunkten Verletzungsrate: positiv = die Regel senkt die Verletzungsrate."""
    return 100.0 * (cell["violation_rate_vol"] - cell["violation_rate_cg"])


def judgment(cell: dict) -> str:
    """Drei Zustände (Kernabschnitt). Fällt der Gewinn negativ aus (H_cg schlechter als H_vol - kommt in
    dieser Messreihe in mehreren Zellen vor, siehe ERGEBNIS.md-Nebenbefunde), zählt das ausdrücklich zu
    „hilft, reicht aber nicht": die Regel ist dort keine verlässliche Verbesserung."""
    if cell["violation_rate_vol"] < UNKRITISCH_VOL_MAX:
        return STATE_UNKRITISCH
    if gain_pp(cell) >= 100.0 * DEUTLICH_MIN_GAIN and cell["violation_rate_cg"] <= DEUTLICH_MAX_CG:
        return STATE_DEUTLICH
    return STATE_NICHT_AUSREICHEND


def judgment_text(cell: dict) -> str:
    state = judgment(cell)
    g = gain_pp(cell)
    vol, cg = fmt_pct(cell["violation_rate_vol"]), fmt_pct(cell["violation_rate_cg"])
    gtxt = fmt_num(g, 1, signed=True)
    if state == STATE_UNKRITISCH:
        return f"{STATE_LABEL[state]}: schon die reine Volumen-Packung verletzt das Schwerpunktfenster nur in {vol} der Instanzen."
    if state == STATE_DEUTLICH:
        return f"{STATE_LABEL[state]}: {vol} auf {cg} ({gtxt} Prozentpunkte)."
    if g < 0:
        return f"{STATE_LABEL[state]}: die schwerpunkt-bewusste Regel ist hier sogar schlechter ({vol} auf {cg}, {gtxt} Prozentpunkte)."
    return f"{STATE_LABEL[state]}: {vol} auf {cg} ({gtxt} Prozentpunkte) - reicht bei dieser Toleranz nicht."


def regime_rows(data: dict) -> list[dict]:
    """Alle 54 Zellen mit Urteil, für die Regime-Tabelle."""
    out = []
    for c in cells(data):
        out.append({
            "contour": c["contour"], "tol": c["tol"], "cv": c["density_cv"], "n_boxes": c["n_boxes"],
            "violation_vol": c["violation_rate_vol"], "violation_cg": c["violation_rate_cg"],
            "gain_pp": gain_pp(c), "state": judgment(c), "label": STATE_LABEL[judgment(c)],
            "util_diff": c["util_diff_mean"], "unplaced_vol": c["unplaced_vol_mean"], "unplaced_cg": c["unplaced_cg_mean"],
        })
    return out


def tol_rows(data: dict, contour: str, cv: float, n_boxes: int) -> list[dict]:
    """Verletzungsrate über die Toleranz (für die Kerngrafik), feste Kontur/CV/Boxzahl."""
    return [find_cell(data, contour, tol, cv, n_boxes) for tol in TOL_OPTIONS]


def util_price_summary(data: dict) -> dict:
    """Auslastungsdifferenz H_cg minus H_vol über alle 54 Zellen (Beleg: Volumenpreis vernachlässigbar)."""
    diffs = [c["util_diff_mean"] for c in cells(data)]
    return {"min": min(diffs), "max": max(diffs), "mean": sum(diffs) / len(diffs)}


def kontur_summary(data: dict) -> dict:
    return {"vol_rechteck": data["vol_rechteck"], "vol_gerundet": data["vol_gerundet"], "verlust_pct": data["kontur_verlust_pct"]}
