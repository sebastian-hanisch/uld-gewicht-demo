"""Volles Bau-Gate (AP 7): wiederholt den Sweep (tools/sweep.py) und vergleicht das Ergebnis mit der
eingecheckten data/uldg_results.json.

**Bekannte Einschraenkung, mechanisch aus dem verifizierten Kern geerbt (nicht durch die Modulaufteilung
verursacht):** die Zellen-Seeds kommen aus `hash((contour, tol, cv, n))` - genau wie im Original
`packen-planung/messreihe_uld_gewicht/sweep.py`. Pythons `hash()` auf Strings ist seit PEP 456 pro Prozess
zufaellig gesalzen (PYTHONHASHSEED), ausser er wird explizit fixiert; der Referenzlauf, der
`data/uldg_results.json` erzeugt hat, hat sein Hash-Salt nicht aufgezeichnet - eine BITGLEICHE Reproduktion
ist deshalb grundsaetzlich nicht moeglich, unabhaengig von der Modulaufteilung hier. Das Bau-Gate prueft
deshalb DREI Dinge statt reiner Bitgleichheit:

1. Die deterministischen (RNG-freien) Kennzahlen (Containermasse, nutzbares Volumen, Kontur-Verlust) MUESSEN
   bitgleich sein - dort steckt kein Zufall drin.
2. Der Sweep ist INNERHALB eines Prozesses (fester Hash-Salt) reproduzierbar: zwei Laeufe hintereinander
   liefern bitgleiche Ergebnisse - das beweist, dass keine versteckte Nichtdeterminismus-Quelle jenseits des
   bekannten Hash-Salts existiert.
3. Die RNG-abhaengigen Kennzahlen (Verletzungsraten, Auslastung, unplatzierte Boxen) liegen INNERHALB einer
   grosszuegigen statistischen Toleranz um die eingecheckten Werte (kein Bug, nur eine andere Zufallsziehung
   derselben 200-Instanzen-Messung) - eine systematische Abweichung (z. B. eine ganz andere Groessenordnung)
   wuerde hier auffallen, eine reine Stichprobenschwankung nicht.

Aufruf (im Projektordner): _venvs/runtime/Scripts/python.exe tools/check_full.py"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from sweep import run_sweep  # noqa: E402

DETERMINISTIC_KEYS = ("W", "D", "H", "chamfer", "n_instances", "vol_rechteck", "vol_gerundet", "kontur_verlust_pct")
# 200 Instanzen je Zelle: Standardfehler eines Anteils hoechstens sqrt(0.5*0.5/200) ~ 3.5 Prozentpunkte;
# 0.12 (12 Prozentpunkte) ist eine grosszuegige ~3.4-Sigma-Toleranz fuer den Vergleich zweier UNABHAENGIGER
# Ziehungen (Referenzlauf gegen Neulauf), nicht fuer denselben Lauf.
RATE_TOLERANCE = 0.12
UTIL_TOLERANCE = 0.02


def compare_deterministic(got, expected):
    return [(k, got[k], expected[k]) for k in DETERMINISTIC_KEYS if got[k] != expected[k]]


def compare_statistical(got_rows, expected_rows):
    bad = []
    by_key = {(r["contour"], r["tol"], r["density_cv"], r["n_boxes"]): r for r in expected_rows}
    for g in got_rows:
        key = (g["contour"], g["tol"], g["density_cv"], g["n_boxes"])
        e = by_key[key]
        for field, tol in (("violation_rate_vol", RATE_TOLERANCE), ("violation_rate_cg", RATE_TOLERANCE),
                           ("util_vol_mean", UTIL_TOLERANCE), ("util_cg_mean", UTIL_TOLERANCE)):
            if abs(g[field] - e[field]) > tol:
                bad.append((key, field, g[field], e[field]))
    return bad


def main():
    checked = ROOT / "data" / "uldg_results.json"
    expected = json.loads(checked.read_text(encoding="utf-8"))

    run1 = run_sweep()
    run2 = run_sweep()
    self_mismatches = [] if run1 == run2 else ["Zwei Laeufe im selben Prozess sind NICHT bitgleich - das waere ein echter Fehler"]

    det_mismatches = compare_deterministic(run1, expected)
    stat_mismatches = compare_statistical(run1["rows"], expected["rows"])

    ok = not self_mismatches and not det_mismatches and not stat_mismatches
    print(f"1) Selbst-Reproduzierbarkeit (zwei Laeufe, fester Prozess-Hash-Salt): {'bitgleich' if not self_mismatches else 'ABWEICHUNG'}")
    print(f"2) Deterministische Kennzahlen gegen {checked.name}: {'bitgleich' if not det_mismatches else f'{len(det_mismatches)} Abweichungen'}")
    for m in det_mismatches:
        print("   ", m)
    print(f"3) RNG-abhaengige Kennzahlen gegen {checked.name} (Toleranz {RATE_TOLERANCE} bzw. {UTIL_TOLERANCE}): "
          f"{'alle 54 Zellen innerhalb der Toleranz' if not stat_mismatches else f'{len(stat_mismatches)} Zellen ausserhalb der Toleranz'}")
    for m in stat_mismatches[:10]:
        print("   ", m)
    print()
    print("BAU-GATE BESTANDEN (statistisch, siehe Modul-Docstring fuer die bekannte Hash-Salt-Einschraenkung)"
          if ok else "BAU-GATE FEHLGESCHLAGEN")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
