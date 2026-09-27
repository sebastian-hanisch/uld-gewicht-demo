# 📦 ULD-Beladung: Volumen gegen Schwerpunkt

**[→ Demo live ausprobieren](https://sebastianhanisch-uld-gewicht-demo.streamlit.app/)**

Ausbau von [`pack_demo`](https://github.com/sebastian-hanisch/pack_demo) (Extreme-Point-Verfahren für Luftfracht-ULDs, hebt dessen Annahme
"keine Gewichtsverteilung" gezielt auf): ein ULD wird nach Volumen gepackt, ohne auf das Gewicht der Boxen zu achten - hält das automatisch
den **Schwerpunkt** in der zulässigen Toleranz um die geometrische Mitte? Und was kostet eine an die Rumpfkontur angepasste Grundfläche
(LD3-artig, an den Ecken abgeschnitten) an nutzbarem Volumen gegenüber einer Palette? Die Demo zeigt live **eine Instanz** mit zwei Regeln
(H_vol, ignoriert Gewicht; H_cg, schwerpunkt-bewusst) auf zwei Konturen und vorgerechnet die Messreihe über **200 Instanzen je Zelle** (54
Zellen), die die Aussage trägt.

## Warum dieses Problem

Bei Luftfracht-ULDs gilt eine reale Vorschrift: der Schwerpunkt der beladenen Einheit muss in einem Toleranzfenster um die geometrische
Mitte liegen (IATA-Größenordnung), sonst darf sie nicht ohne Zusatzprüfung geladen werden. `pack_demo` packt bewusst rein nach Volumen
und nennt "Gewichtsverteilung" ausdrücklich als eigene, nicht eingelöste Erweiterungsidee. Dieses Stück löst genau das ein - als eigenes
Repo mit eigenem Programmcode, nicht als Nachrüstung des bestehenden. Zusätzlich: ein LD3 hat keine rechteckige, sondern eine an den
Rumpf angepasste, an den vier Ecken abgeschnittene Grundfläche - eine zweite, unabhängige Frage nach dem Volumenpreis der Kontur.

## Modell

- **Container:** 160 × 150 × 160 cm (Größenordnung LD3), zwei Konturen: **Rechteck** (Palette/PMC-artig, volle Grundfläche) und
  **gerundet** (LD3-artig, an allen vier Ecken um 40 cm Kathete abgeschnitten - ein einfaches, aber geometrisch geprüftes Achteck-Modell,
  nicht die reale 3D-Rumpfkontur).
- **Boxen:** Grundfläche 20-60 cm je Kante, Höhe 15-45 cm, **feste Orientierung** (keine Rotation, wie bei Luftfracht mit vorgegebenem
  "diese Seite oben" üblich). Gewicht = Volumen × Dichte, Dichte ~ Normal(1,0; Dichtestreuung) mit der Dichtestreuung als Regler.
- **Platzierung:** Extreme-Point-Heuristik (Crainic, Perboli, Tadei 2008) wie `pack_demo`, mit eigenen Start-Kandidaten an den Eckpunkten
  der gerundeten Kontur (siehe Abschnitt "Befunde beim Bauen") und einem zusätzlichen Bodenraster (20-cm-Schritte) für die
  schwerpunkt-bewusste Regel.
- **Schwerpunkt:** gewichtetes Mittel der Boxmitten, Offset zur geometrischen Mitte in x und y; eine Packung verletzt das Fenster, wenn
  |Offset| die Toleranz (5/10/20 %) in x **oder** y überschreitet. Formale Beschreibung im Expander "📐 Mathematische Formulierung" der App.
- **Zwei Regeln:** **H_vol** (größte Box zuerst, ignoriert Gewicht - die Baseline aus `pack_demo`) gegen **H_cg** (schwere Boxen zuerst,
  mit Vorzug für die zulässige Position nahe der Container-Mitte; leichte Boxen wie H_vol).

Boxgrößen, Dichteverteilung, Containermasse und Fase sind erfunden, nicht kalibriert. Die Schwerpunkt-Toleranz orientiert sich an der
Größenordnung realer ULD-Schwerpunktgrenzen (IATA ULD Technical Manual), ist aber **keine Uebernahme einer konkreten Tabelle**.

## Befunde beim Bauen (Vorab-Messreihe, siehe `packen-planung/messreihe_uld_gewicht/ERGEBNIS.md`)

Drei Bugs wurden gefunden (zwei beim Bauen, einer erst vom Nutzer an der laufenden App) und mit Regressionstests abgesichert (siehe
`tests/test_geometry.py`):

- **Nullspalten-Signal:** die gerundete Kontur schneidet genau den Ursprung ab; die Extreme-Point-Heuristik startete anfangs nur dort, wodurch
  0 von 200 Instanzen überhaupt etwas platzierten. Behoben durch eigene Start-Kandidaten an den acht Eckpunkten der Kontur
  (`uldg_geometry._seed_points`).
- **Wirkungslose Zielregel:** die schwerpunkt-bewusste Regel hatte anfangs **höhere** Verletzungsraten als die reine Volumen-Regel, weil der
  ersten, schwersten Box nur der Ursprung als Kandidat zur Verfügung stand - die "Vorzug Mitte"-Regel griff ins Leere. Behoben durch ein
  zusätzliches Bodenraster (`uldg_geometry._floor_grid`).
- **Schwebende/kippende Boxen (nach dem Deploy vom Nutzer gemeldet):** das Platzierungsverfahren prüfte nur Überlappung und Kontur, nie ob
  die gesamte Grundfläche einer Box tatsächlich aufliegt (Boden oder Oberkante bereits platzierter Boxen) - ein Extreme-Point aus der
  oberen Kante einer kleineren Box erlaubte, eine größere Box teilweise oder ganz darüber schweben zu lassen. Gemessen an 100
  Zufallsinstanzen vor der Behebung: **2,3 %** der platzierten Boxen hatten **0 %** Auflage, **4,3 %** unter 50 % Auflage. Behoben durch
  eine `_fully_supported()`-Prüfung (Boden **oder** lückenlose Deckung durch tieferliegende Boxoberkanten) in `uldg_geometry.try_place()`,
  mit vier neuen Checks und der kompletten Messreihe neu gerechnet - **alle Zahlen unten sind bereits die korrigierte Fassung.** Mit der
  zusätzlichen Nebenbedingung "vollständig aufgelegt" landen Boxen seltener zufällig in einer schwerpunkt-zentrierenden Position, darum
  liegen die Verletzungsraten unten durchweg höher als vor der Behebung.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen aus `data/uldg_results.json` (54 Zellen × 200 gepaarte Instanzen), nachgerechnet in `tests/test_claims.py`.

| Frage | Befund |
|---|---|
| Verletzt eine reine Volumen-Packung das Schwerpunktfenster? | Ja, meistens: Rechteck-Kontur, 16 Boxen, Dichtestreuung 0,3, Toleranz 10 % - **90,5 %** der Instanzen verletzt. |
| Hilft die schwerpunkt-bewusste Regel? | Deutlich, aber nicht bis auf null: senkt auf **26,0 %** (−64,5 Prozentpunkte) in derselben Zelle. |
| Reicht sie bei enger Toleranz (5 %)? | **Nein:** bleibt bei **73,0 %** (von 98,0 % bei H_vol) - eine einfache Platzierungsregel allein reicht dort nicht. |
| Verschwindet der Unterschied bei loser Toleranz (20 %)? | Fast: H_vol verletzt nur noch **23,5 %**, H_cg senkt das in dieser Zelle auf **0 %**. |
| Was kostet die Schwerpunktregel an Volumen? | Klein, aber seit dem Auflage-Fix messbar: Auslastungsdifferenz H_cg gegen H_vol über alle 54 Zellen zwischen **−4,2 %** und **≈0 Prozentpunkten** (Mittel −0,96 pp) - vor der Behebung war sie mit −1,6 bis +0,1 pp praktisch vernachlässigbar. |
| Wo zeigt sich der Preis dann? | Bei vielen Boxen und hoher Dichtestreuung in unplatzierten Boxen: gerundet, 24 Boxen, Dichtestreuung 0,6, Toleranz 10 % - **8,71** unplatzierte Boxen im Mittel bei H_cg gegen **6,73** bei H_vol. |
| Was kostet die gerundete Kontur? | **13,3 %** nutzbares Volumen bei gleicher Außenhülle (3,84 gegen 3,33 Mio. cm³) - unverändert durch den Auflage-Fix, hängt nicht von der Platzierungsregel ab. |
| Hilft die Regel in jeder Zelle? | In dieser (neu gerechneten) Messreihe **ja** - anders als vor dem Auflage-Fix ist der Gewinn in allen 54 Zellen positiv (kleinster Wert 1,5 Prozentpunkte); vor der Behebung gab es Zellen mit negativem Gewinn, das war selbst ein damals dokumentierter Bug (siehe "Befunde beim Bauen"). Kein Beweis, dass das für jede denkbare Instanz gilt - nur der gemessene Befund dieser Stichprobe (siehe `tests/test_results.py::test_gain_pp_ist_in_dieser_messreihe_nie_negativ`). |

Verteilung des Urteils über alle 54 gemessenen Zellen: **25** "Schwerpunktregel hilft deutlich", **22** "hilft, reicht aber nicht", **7**
"Toleranz ohnehin unkritisch" (siehe `uldg_results.py`, App-Abschnitt "Regime").

## Ehrliche Grenzen

- **Kein exaktes Optimum:** 3D-Packen mit Kontur ist für einen ILP-Vergleich aufwendig, nicht Teil dieser Version.
- **Feste Orientierung je Box** vereinfacht gegenüber `pack_demo` (dort sechs Rotationen).
- **Die schwerpunkt-bewusste Regel reicht bei enger Toleranz nicht aus** - ein dritter, reparierender Schritt (Tausch schwerer Boxen, wie in
  `stauplanung-demo`s Reparatur-Heuristik) wäre eine Ausbauidee, ist hier bewusst nicht umgesetzt.
- **Die gerundete Kontur senkt die Verletzungsrate über einen Nebeneffekt** (das Bodenraster ist dort stärker zur Mitte hin konzentriert),
  nicht weil die Kontur selbst beim Zentrieren "hilft" - im Text und in der App ausdrücklich als Artefakt der Rasterwahl eingeordnet, nicht
  als physikalische Aussage über gerundete ULDs.
- **Kein bit-reproduzierbarer Sweep:** die Zellen-Seeds kommen aus `hash((contour, tol, cv, n))`, mechanisch unverändert aus dem
  verifizierten Vorab-Messreihen-Skript übernommen. Pythons `hash()` auf Strings ist pro Prozess zufällig gesalzen (PEP 456,
  `PYTHONHASHSEED`); der einmalige Referenzlauf hat sein Salt nicht aufgezeichnet. `tools/check_full.py` weist stattdessen
  Selbst-Reproduzierbarkeit (zwei Läufe im selben Prozess sind bitgleich) und statistische Nähe zur eingecheckten Datei nach - siehe die
  Docstrings dort und in `tools/sweep.py`.

## Verwandte Demos mit demselben mathematischen Modell

Kernmodell: **gewichtete Positionierung mit Schwerpunkt-/Momentengrenze**, hier als kontinuierliches 3D-Packen mit einem zweiachsigen
Toleranzfenster um die geometrische Mitte, plus eine Container-**Kontur** als zweite, unabhängige Frage.

- **[`pack_demo`](https://github.com/sebastian-hanisch/pack_demo):** derselbe Extreme-Point-Kern, dieselbe Kulisse (Luftfracht-ULD) - `pack_demo`
  nennt Gewichtsverteilung selbst als "bewusst nicht enthalten"; dieses Stück ist die nachgeholte Erweiterung, als eigenes Repo statt
  Nachrüstung.
- **[`stauplanung-demo`](https://github.com/sebastian-hanisch/stauplanung-demo):** echte Verwandtschaft im Muster "gewichtete Objekte
  positionieren, dabei eine Momentengrenze einhalten, Heuristik gegen Optimum" (dort: Schwerpunkt-Grenze und Seitenneigung beim Stauen
  eines Containerschiff-Bays). Unterschied: dort diskrete Stapel in einem festen Bay-Raster (Sequenz-/Umstau-Problem, ALLE Container werden
  gestaut, Ziel = Reshuffles minimieren) gegen kontinuierliches 3D-Packen unregelmäßiger Boxen in einen einzelnen Behälter mit
  zweiachsigem Toleranzfenster hier (kein Stapel-Raster, kein Umstauen) - gemeinsame Sprache ("Schwerpunkt"), andere Kulisse und andere
  Entscheidung (wo genau eine Box liegt, statt in welcher Reihenfolge Stapel abgebaut werden).

## Tests

116 Tests, Laufzeit unter 10 s (`_venvs/test/Scripts/python.exe -m pytest tests -v`):

- `tests/test_model_units.py`, `tests/test_geometry.py` - die 29 Korrektheits-Checks aus `messreihe_uld_gewicht/check.py` (Handinstanzen,
  Kontur-Grenzfälle, Monte-Carlo-Volumenschätzung, 1200 Zufallspackungen ohne Ueberlappung/Gewichtsfehler/Konturverletzung/fehlende
  Auflage), plus drei PFLICHT-Regressionstests für die drei beim Bauen bzw. nach dem Deploy gefundenen Bugs (Nullspalte, wirkungslose
  Zielregel, schwebende/kippende Boxen) und zusätzliche Grenzfall-/Tiebreak-Tests, die die Fehler-Einbau-Prüfung aufgedeckt hat.
- `tests/test_frozen_reference.py` - vier eingefrorene Boxlisten (feste Zahlenwerte, keine Zufallsziehung zur Testzeit), CI-robust gegen
  NumPy-Versionsdrift.
- `tests/test_results.py`, `tests/test_format.py` - Zell-Zuordnung (AP 0: alle 54 Reglerkombinationen liegen exakt auf einer gemessenen
  Zelle), Urteilslogik in drei Zuständen, Zahlenformate.
- `tests/test_visualization.py`, `tests/test_pdf_export.py` - Plotly-Figuren und PDF-Export bauen ohne Fehler.
- `tests/test_presets.py`, `tests/test_stories.py` - Permalink-Parsing, alle fünf Presets bestehen ihre Abnahmekriterien gegen die
  Messreihe.
- `tests/test_claims.py` - jede Zahl aus dem README-Abschnitt "Befunde" gegen `data/uldg_results.json` nachgerechnet.
- `tests/test_app.py` - AppTest: Skelett, Footer, jedes Preset, Permalink, alle Regler an Min/Max, alle drei Urteilszustände, keine
  wirkungslosen Regler, PDF-Download, keine toten Datei-Links.

Zusätzlich: `tools/mutation_check.py` (Fehler-Einbau-Test für `uldg_model.py`/`uldg_geometry.py`, 37 handverlesene Mutanten, siehe
`tools/mutants.py` für die Einordnung der sechs gleichwertigen Ueberlebenden) und `tools/check_full.py` (volles Bau-Gate: Wiederholung der
Messreihe gegen `data/uldg_results.json`, siehe "Ehrliche Grenzen" oben).

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Einstiegspunkt |
| `uldg_constants.py` | Reglerstufen, Presets, Farben, feste Parameter |
| `uldg_presets.py` | Reglerspezifikation, Permalink, Presets, Seed-Knopf |
| `uldg_model.py` | Datentypen (Box, Placed), Kontur-/Volumen-Geometrie, Schwerpunkt-Kennzahlen (aus `uld.py` übernommen) |
| `uldg_geometry.py` | Extreme-Point-Packverfahren, beide Regeln (aus `uld.py` übernommen) |
| `uldg_results.py` | Laden und Auswerten von `data/uldg_results.json`, Urteilslogik |
| `uldg_format.py` | Zahlenformate mit deutschem Dezimalkomma |
| `uldg_visualization.py` | 3D-Ansicht (Mesh3d, Kontur), Verletzungsrate-/Kontur-Volumen-/Regime-Grafik |
| `uldg_stories.py` | Abnahmekriterien der Presets |
| `uldg_pdf_export.py` | Packplan-PDF |
| `tools/sweep.py` | Reproduktion der Messreihe (rund 20-25 s, nicht in CI) |
| `tools/check_full.py` | Volles Bau-Gate (siehe "Ehrliche Grenzen") |
| `tools/mutants.py`, `tools/mutation_check.py` | Fehler-Einbau-Test der Kernmodule |
| `data/uldg_results.json` | Messreihe: 54 Zellen × 200 gepaarte Instanzen |
| `tests/` | Testsuite |

## Bewusst nicht umgesetzt

Rotation der Boxen, Stapelbarkeit/"diese Seite oben" als eigene Regel (die Orientierung ist fix), mehrere Container gleichzeitig, ein
dritter Reparatur-Algorithmus gegen enge Toleranzen, eine echte IATA-Schwerpunkttabelle, die reale Rumpfkontur (nur das Achteck-Modell),
ein exaktes Optimum als Vergleichsmassstab.

## Lokal ausführen

```
pip install -r requirements-dev.txt
streamlit run app.py
```

---

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.
