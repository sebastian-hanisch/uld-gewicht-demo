"""Handverlesene Mutantenliste fuer die beiden Kernmodule (uldg_model.py, uldg_geometry.py): jede alte Stelle
kommt im jeweiligen Modul genau einmal vor. Anders als bei den grossen Fall-Demos (dort maschinell erzeugt,
siehe tools/gen_mutants.py der Vorbild-Repos) sind es hier nur zwei kleine, mechanisch aus uld.py uebernommene
Module - eine handverlesene Liste deckt jede Vergleichsoperation, jede Vorzeichen-/Faktor-Stelle und jede
Sortierordnung ab, ohne die Maschinerie eines Generators zu brauchen.

EQUIVALENT_NOTES wird nach dem ersten vollen Lauf mit der tatsaechlichen Einordnung der Ueberlebenden gefuellt
(siehe tools/mutation_check.py und den Bericht im Abschluss-Kommentar)."""
EQUIVALENT_NOTES = """Stand nach zwei Laeufen (37 handverlesene Mutanten): Lauf 1 fand 21, 16 ueberlebten;
nach dem Schliessen von 10 echten Testluecken (tests/test_model_units.py: drei weitere Chamfer-Eckfaelle,
die exakte Epsilon-Schwelle von cg_violation in x/y, der Divisions-Schutz von volume_utilization bei
Volumen 0; tests/test_geometry.py: der Gitterpunkt y=140 in _floor_grid, der Distanz-Gleichstand-Tiebreak in
try_place, die Gewichtsformel und der Dichte-Bodenwert in make_boxes) fand Lauf 2 31 von 37, 6 ueberlebten.
Alle sechs sind gleichwertig (kein durch echte Geometrie erreichbarer Verhaltensunterschied), derselben
Klasse wie die 'Vergleich am Massnullpunkt'-Faelle anderer Demos (siehe irp/bw tools/mutants.py):

(1) Aeussere Rand-Ecke von corners_ok, x und y (`px < -1e-9` bzw. `py < -1e-9` gegen `<=`): der Unterschied
    zeigt sich nur, wenn eine Boxecke exakt bei -1e-9 liegt - Box-Koordinaten entstehen in diesem Modell
    ausschliesslich aus Container-Kanten (>= 0) und Boxkanten-Summen, nie aus einer Subtraktion, die exakt
    -1e-9 ergeben koennte.
(2) `_overlaps`: die drei Achsenvergleiche `<=` gegen `<` (x, y, z) mit derselben 1e-9-Toleranz: der
    Unterschied zeigt sich nur bei einem Achsenabstand von EXAKT 1e-9 zwischen zwei Boxkanten - bei
    Kante-an-Kante-Platzierung (der einzige in diesem Modell erzeugte Beruehrungsfall) ist der Abstand
    exakt 0, nicht 1e-9; ein Testfall mit exaktem 1e-9-Abstand waere reine Rundungs-Simulation, kein
    Modellverhalten.
(3) `_floor_grid`: die x-Randstufe `range(int(W // step) + 1)` gegen `range(int(W // step))`: W = 160 ist
    ein exaktes Vielfaches von step = 20, der zusaetzliche Punkt liegt exakt bei x = W = 160 - eine Box mit
    positiver Breite kann dort nie beginnen (`x + box.w > W + 1e-9` schlaegt immer fehl). Die spiegelbildliche
    y-Stufe (D = 150 ist KEIN Vielfaches von 20, der Punkt liegt bei y = 140, einem echten Innenpunkt) ist
    dagegen KEIN gleichwertiger Mutant und wird von test_floor_grid_enthaelt_den_letzten_erreichbaren_schritt_in_y
    gefangen - die Asymmetrie zwischen x und y ist beabsichtigt, kein Uebersehen."""

MUTANTS = [
    # --- uldg_model.py --------------------------------------------------------------------------------
    ("uldg_model.py", "px < -1e-9 or px > W", "px <= -1e-9 or px > W"),
    ("uldg_model.py", "or py < -1e-9 or py > D", "or py <= -1e-9 or py > D"),
    ("uldg_model.py", "if px + py < chamfer - 1e-9:", "if px + py < chamfer + 1e-9:"),
    ("uldg_model.py", "if (W - px) + py < chamfer - 1e-9:", "if (W - px) + py < chamfer + 1e-9:"),
    ("uldg_model.py", "if px + (D - py) < chamfer - 1e-9:", "if px + (D - py) < chamfer + 1e-9:"),
    ("uldg_model.py", "if (W - px) + (D - py) < chamfer - 1e-9:", "if (W - px) + (D - py) < chamfer + 1e-9:"),
    ("uldg_model.py", "return W * D * H", "return W * D * H * 1.01"),
    ("uldg_model.py", "2.0 * chamfer * chamfer", "2.0 * chamfer * chamfer * 1.01"),
    ("uldg_model.py", "if tw <= 0:", "if tw < 0:"),
    ("uldg_model.py", "p.x + p.box.w / 2)", "p.x + p.box.w / 3)"),
    ("uldg_model.py", "p.y + p.box.d / 2)", "p.y + p.box.d / 3)"),
    ("uldg_model.py", "return cx - W / 2, cy - D / 2", "return cx - W / 2, cy + D / 2"),
    ("uldg_model.py", "used = sum(p.box.w * p.box.d * p.box.h for p in placed)",
     "used = sum(p.box.w * p.box.d * p.box.h * 1.01 for p in placed)"),
    ("uldg_model.py", "return used / uv if uv > 0 else 0.0", "return used / uv if uv >= 0 else 0.0"),
    ("uldg_model.py", "abs(offset_x) > tol * (W / 2) + 1e-9", "abs(offset_x) >= tol * (W / 2) + 1e-9"),
    ("uldg_model.py", "abs(offset_y) > tol * (D / 2) + 1e-9", "abs(offset_y) >= tol * (D / 2) + 1e-9"),
    # --- uldg_geometry.py -------------------------------------------------------------------------------
    ("uldg_geometry.py", "ax1 <= bx0 + 1e-9 or bx1 <= ax0 + 1e-9", "ax1 < bx0 + 1e-9 or bx1 <= ax0 + 1e-9"),
    ("uldg_geometry.py", "or ay1 <= by0 + 1e-9 or by1 <= ay0 + 1e-9", "or ay1 < by0 + 1e-9 or by1 <= ay0 + 1e-9"),
    ("uldg_geometry.py", "or az1 <= bz0 + 1e-9 or bz1 <= az0 + 1e-9", "or az1 <= bz0 + 1e-9 or bz1 < az0 + 1e-9"),
    ("uldg_geometry.py", "return {(0.0, 0.0, 0.0)}", "return {(0.0, 0.0, 1.0)}"),
    ("uldg_geometry.py", "(c, 0.0, 0.0), (0.0, c, 0.0),", "(c, 0.0, 0.0), (0.0, c, 1.0),"),
    ("uldg_geometry.py", "xs = [i * step for i in range(int(W // step) + 1)]",
     "xs = [i * step for i in range(int(W // step))]"),
    ("uldg_geometry.py", "ys = [j * step for j in range(int(D // step) + 1)]",
     "ys = [j * step for j in range(int(D // step))]"),
    ("uldg_geometry.py", "pts.add((p.x + p.box.w, p.y, p.z))", "pts.add((p.x + p.box.w + 1.0, p.y, p.z))"),
    ("uldg_geometry.py", "pts.add((p.x, p.y + p.box.d, p.z))", "pts.add((p.x, p.y + p.box.d + 1.0, p.z))"),
    ("uldg_geometry.py", "pts.add((p.x, p.y, p.z + p.box.h))", "pts.add((p.x, p.y, p.z + p.box.h + 1.0))"),
    ("uldg_geometry.py", "key=lambda t: (t[2], t[1], t[0])", "key=lambda t: (t[1], t[2], t[0])"),
    ("uldg_geometry.py", "if x + box.w > W + 1e-9 or y + box.d > D + 1e-9 or z + box.h > H + 1e-9:",
     "if x + box.w > W - 1e-9 or y + box.d > D + 1e-9 or z + box.h > H + 1e-9:"),
    ("uldg_geometry.py", "dist = (x + box.w / 2 - tx) ** 2 + (y + box.d / 2 - ty) ** 2",
     "dist = (x + box.w / 2 - tx) ** 2 + (y + box.d / 3 - ty) ** 2"),
    ("uldg_geometry.py", "if best is None or dist < best_dist:", "if best is None or dist <= best_dist:"),
    ("uldg_geometry.py", "order = sorted(boxes, key=lambda b: b.w * b.d * b.h, reverse=True)",
     "order = sorted(boxes, key=lambda b: b.w * b.d * b.h, reverse=False)"),
    ("uldg_geometry.py", "med = float(np.median([b.weight for b in boxes]))",
     "med = float(np.median([b.weight for b in boxes])) * 1.01"),
    ("uldg_geometry.py", "heavy = sorted([b for b in boxes if b.weight >= med]",
     "heavy = sorted([b for b in boxes if b.weight > med]"),
    ("uldg_geometry.py", "light = sorted([b for b in boxes if b.weight < med]",
     "light = sorted([b for b in boxes if b.weight <= med]"),
    ("uldg_geometry.py", "target=(W / 2, D / 2), with_floor_grid=True)",
     "target=(W / 2, D / 3), with_floor_grid=True)"),
    ("uldg_geometry.py", "weight = vol * density / 1000.0", "weight = vol * density / 1001.0"),
    ("uldg_geometry.py", "density = max(0.05, rng.normal(1.0, density_cv))",
     "density = max(0.06, rng.normal(1.0, density_cv))"),
]
