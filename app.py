"""
ULD-Beladung: Volumen gegen Schwerpunkt - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ausbau von pack_demo: eine reine Volumen-Packung ignoriert das Gewicht der Boxen. Bei Luftfracht-ULDs muss der
Schwerpunkt der beladenen Einheit aber in einem Toleranzfenster um die geometrische Mitte liegen. Live: eine
Instanz mit beiden Regeln (H_vol, H_cg) auf zwei Konturen. Vorgerechnet: die Messreihe ueber 200 Instanzen je
Zelle (data/uldg_results.json), die die Aussage traegt.

Lauffaehig mit: streamlit run app.py
"""
import numpy as np
import streamlit as st

import uldg_constants as C
import uldg_results as R
import uldg_stories as S
import uldg_visualization as V
from uldg_format import fmt_num, fmt_pct
from uldg_geometry import make_boxes, pack_cg_aware, pack_greedy_volume
from uldg_model import GERUNDET, RECHTECK, cg_offset, cg_violation, volume_utilization
from uldg_pdf_export import generate_uldg_pdf
from uldg_presets import (SETTING_SPECS, apply_preset, bounds, init_session_state_defaults, load_permalink_settings,
                          randomize_seed, sync_query_params)

st.set_page_config(page_title="ULD-Beladung – Sebastian Hanisch", layout="wide")

DATA = R.load_results()


@st.cache_data(show_spinner=False, max_entries=256)
def _live(contour, n_boxes, cv, tol, seed):
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


st.title("📦 ULD-Beladung: Volumen gegen Schwerpunkt")
st.markdown(
    """
Ein ULD (Luftfracht-Ladeeinheit) wird nach Volumen gepackt - haelt das automatisch den **Schwerpunkt** in der
zulaessigen Toleranz um die geometrische Mitte? Und was kostet es, das gezielt einzuhalten? Zusaetzlich sind
ULDs nicht alle rechteckig: ein LD3 hat eine an die Rumpfkontur angepasste, an den Ecken abgeschnittene
Grundflaeche - wie viel **nutzbares Volumen** kostet das? Die Demo zeigt live **eine Instanz** mit beiden Regeln
(**H_vol**, ignoriert Gewicht, wie `pack_demo`; **H_cg**, schwerpunkt-bewusst) auf beiden Konturen, und
vorgerechnet die Messreihe ueber **200 Instanzen je Zelle**, die die Aussage traegt. Das Platzierungsverfahren
(Extreme-Point-Heuristik) kennt man aus `pack_demo`; die Schwerpunkt-/Momentengrenze als Nebenbedingung ist mit
`stauplanung-demo` verwandt (dort ein diskretes Stapel-Raster statt kontinuierlichem 3D-Packen). Wie das Modell
funktioniert, steht im Expander „Wie funktioniert diese Demo?" weiter unten, die formale Beschreibung im
Expander „📐 Mathematische Formulierung".
"""
)

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_names = list(C.PRESETS)
for row in (preset_names[:3], preset_names[3:]):
    cols = st.columns(len(row))
    for col, name in zip(cols, row):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Container**")
    contour = st.selectbox("ULD-Kontur", options=list(C.CONTOUR_OPTIONS), key="contour_select",
                           format_func=lambda v: C.CONTOUR_LABEL[v],
                           help="Rechteck = Palette/PMC-artig, volle Grundflaeche nutzbar. Gerundet = LD3-artig, "
                                "an allen vier Ecken um 40 cm Kathete abgeschnitten.")
    st.markdown("**Ladung**")
    n_boxes = st.select_slider("Anzahl Boxen", options=list(C.BOXES_OPTIONS), key="boxes_slider",
                               help="Gemessene Stufen der Messreihe (10 / 16 / 24).")
    cv = st.select_slider("Dichtestreuung", options=list(C.CV_OPTIONS), key="cv_slider",
                          help="Variationskoeffizient der Boxdichte: 0,1 = homogene Ladung, 0,6 = stark gemischt "
                               "(z. B. Maschinenteile neben Styropor).")
    st.markdown("**Schwerpunkt**")
    tol = st.select_slider("Toleranz", options=list(C.TOL_OPTIONS), key="tol_slider",
                           help="Erlaubter Schwerpunkt-Offset zur geometrischen Mitte, in Prozent der halben "
                                "Kantenlaenge (IATA-Groessenordnung, kein Zitat einer konkreten Tabelle).")
    st.markdown("**Gezeigte Instanz**")
    seed = st.number_input("Seed", *bounds("seed_input"), key="seed_input", step=1,
                           help="Nummer der gezeigten Instanz.")
    st.button("🎲 Neue Instanz", width="stretch", on_click=randomize_seed, help="Wuerfelt einen neuen Seed.")

sync_query_params({key: st.session_state[key] for key in SETTING_SPECS})
n_boxes, seed = int(n_boxes), int(seed)
cv, tol = float(cv), float(tol)

cell = R.find_cell(DATA, contour, tol, cv, n_boxes)
live = _live(contour, n_boxes, cv, tol, seed)

# ---------------------------------------------------------------------------------------------------
# Hauptansicht (Kernabschnitt ①, live: eine Instanz)
# ---------------------------------------------------------------------------------------------------
st.markdown("## 📦 Haelt eine Volumen-Packung den Schwerpunkt ein?")
st.caption(f"Live-Instanz (eine Instanz): Seed {seed}, {n_boxes} Boxen, Dichtestreuung {fmt_num(cv, 1)}, "
           f"Kontur {C.CONTOUR_LABEL[contour]}, Toleranz {fmt_pct(tol, 0)}. Beide Regeln laufen bei jeder "
           "Einstellung neu (unter 0,01 s, je Einstellung zwischengespeichert). Eine einzelne Instanz – die "
           "vorgerechnete Messreihe unten traegt die Aussage.")

m1, m2 = st.columns(2)
with m1:
    st.markdown("**📦 H_vol (Volumen, ignoriert Gewicht)**")
    st.plotly_chart(V.packing_figure(live["placed_vol"], C.W, C.D, C.H, contour, C.CHAMFER), width="stretch", key="main_vol")
with m2:
    st.markdown("**⚖️ H_cg (schwerpunkt-bewusst)**")
    st.plotly_chart(V.packing_figure(live["placed_cg"], C.W, C.D, C.H, contour, C.CHAMFER), width="stretch", key="main_cg")

k1, k2, k3, k4 = st.columns(4)
off_v = (live["offset_vol"][0] ** 2 + live["offset_vol"][1] ** 2) ** 0.5
off_c = (live["offset_cg"][0] ** 2 + live["offset_cg"][1] ** 2) ** 0.5
k1.metric("Schwerpunkt-Offset H_vol", f"{off_v:.1f} cm", delta="verletzt" if live["violation_vol"] else "im Fenster",
          delta_color="off")
k2.metric("Schwerpunkt-Offset H_cg", f"{off_c:.1f} cm", delta="verletzt" if live["violation_cg"] else "im Fenster",
          delta_color="off")
k3.metric("Auslastung H_vol / H_cg", f"{fmt_pct(live['util_vol'])} / {fmt_pct(live['util_cg'])}")
k4.metric("Unplatzierte Boxen H_vol / H_cg", f"{len(live['unplaced_vol'])} / {len(live['unplaced_cg'])}")

st.info(R.judgment_text(cell))
st.caption("Ehrliche Grenze: eine Instanz zeigt nur einen von 200 moeglichen Zufallsfaellen; die Meldung oben "
           "stuetzt sich auf die Messreihe (200 Instanzen dieser Zelle), nicht auf diese eine Instanz.")

pdf_slot = st.container()

st.markdown("---")

# ---------------------------------------------------------------------------------------------------
# Kernabschnitt ② (vorgerechnet): was die Messreihe zeigt
# ---------------------------------------------------------------------------------------------------
st.markdown("### 📐 Was die Messreihe über 200 Instanzen zeigt")
st.markdown(
    f"""
Kernfrage: Wie oft verletzt eine reine Volumen-Packung das Schwerpunktfenster, und was kostet es, das gezielt
einzuhalten? Die Antwort steht auf **200 gepaarten Instanzen je Zelle** (dieselben Boxen fuer H_vol und H_cg),
vorgerechnet und **nie live** gerechnet. Gezeigt wird die exakt gemessene Zelle Ihrer Einstellung (die drei
Regler bilden genau die vier Sweep-Dimensionen ab, keine Naeherung noetig).
"""
)

st.markdown("**1 · Verletzungsrate ueber die Toleranz** (feste Kontur/Dichtestreuung/Boxzahl Ihrer Einstellung)")
tol_rows = R.tol_rows(DATA, contour, cv, n_boxes)
st.plotly_chart(V.violation_rate_figure(tol_rows), width="stretch", key="core_violation")
st.caption("H_vol ignoriert das Gewicht komplett, H_cg bevorzugt Positionen nahe der Mitte fuer die schwereren "
           "Boxen. Bei loser Toleranz (20 %) verschwindet der Unterschied fast, bei enger Toleranz (5 %) bleibt "
           "auch H_cg mehrheitlich ausserhalb des Fensters.")

st.markdown("**2 · Kontur-Volumenverlust** – wie viel nutzbares Volumen kostet die Rumpfkontur bei gleicher Aussenhuelle?")
ks = R.kontur_summary(DATA)
c1, c2 = st.columns([2, 3])
with c1:
    st.plotly_chart(V.kontur_volume_figure(ks["vol_rechteck"], ks["vol_gerundet"]), width="stretch", key="core_kontur")
with c2:
    st.markdown(f"Die gerundete Kontur kostet **{fmt_num(ks['verlust_pct'], 1)} %** nutzbares Volumen bei gleicher "
                "Aussenhuelle 160 × 150 × 160 cm. Interessant: sie senkt dabei auch die Verletzungsrate "
                f"({fmt_pct(R.find_cell(DATA, 'gerundet', tol, cv, n_boxes)['violation_rate_vol'])} statt "
                f"{fmt_pct(R.find_cell(DATA, 'rechteck', tol, cv, n_boxes)['violation_rate_vol'])} bei H_vol, "
                "gleiche Toleranz/Dichtestreuung/Boxzahl) - nicht weil die Kontur beim Zentrieren hilft, sondern "
                "weil sie das Bodenraster staerker zur Mitte hin konzentriert (Nebeneffekt der Rasterwahl, keine "
                "physikalische Aussage ueber gerundete ULDs).")
    util_price = R.util_price_summary(DATA)
    st.markdown(f"**Volumenpreis der Schwerpunktregel:** Auslastungsdifferenz H_cg gegen H_vol ueber alle 54 "
                f"Zellen zwischen {fmt_num(util_price['min'] * 100, 1, True)} und {fmt_num(util_price['max'] * 100, 1, True)} "
                "Prozentpunkten - vernachlaessigbar. Der Preis zeigt sich stattdessen in mehr unplatzierten "
                "Boxen bei hoher Dichtestreuung und vielen Boxen.")

st.markdown("**3 · Regime** – wo hilft die Schwerpunktregel deutlich, wo reicht sie nicht, wo ist die Toleranz ohnehin unkritisch? (alle 54 gemessenen Zellen)")
regime = R.regime_rows(DATA)
st.plotly_chart(V.regime_figure(regime), width="stretch", key="core_regime")
_counts = {}
for r in regime:
    _counts[r["state"]] = _counts.get(r["state"], 0) + 1
_state_text = (
    f"„{R.STATE_LABEL[R.STATE_DEUTLICH]}“ ({_counts.get(R.STATE_DEUTLICH, 0)} von 54 Zellen), "
    f"„{R.STATE_LABEL[R.STATE_NICHT_AUSREICHEND]}“ ({_counts.get(R.STATE_NICHT_AUSREICHEND, 0)}), "
    f"„{R.STATE_LABEL[R.STATE_UNKRITISCH]}“ ({_counts.get(R.STATE_UNKRITISCH, 0)})"
)
st.caption(f"Urteil in drei Zustaenden (wie die Meldung oben): {_state_text}. Die schwerpunkt-bewusste Regel "
           "ist NICHT in jeder Zelle besser als die reine Volumen-Regel - in mehreren Zellen ist der Gewinn "
           "negativ (die Regel schadet leicht); das ist ein gemessener Befund, keine Ausnahme, die verschwiegen wird.")

with pdf_slot:
    st.download_button(
        "📄 Packplan als PDF herunterladen",
        data=generate_uldg_pdf(dict(contour=contour, n_boxes=n_boxes, cv=cv, tol=tol, seed=seed), live, cell),
        file_name="uld_beladung_packplan.pdf", mime="application/pdf", key="primary_pdf_download",
        help="Einstellungen, Kennzahlen beider Regeln und die Meldung der gezeigten Instanz.")

st.markdown("---")

# ---------------------------------------------------------------------------------------------------
# Ansichten
# ---------------------------------------------------------------------------------------------------
with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich"):
    tabs = st.tabs(["📦 3D-Vergleich", "📊 Regeln", "📈 Messreihe"])
    with tabs[0]:
        st.markdown("Beide Packungen nebeneinander, Kontur eingezeichnet (Drahtgitter). Jede Box in einer eigenen "
                     "Farbe, Groesse und Gewicht als Tooltip. Die Ansicht dreht frei (Maus/Touch ziehen).")
        st.plotly_chart(V.packing_figure(live["placed_vol"], C.W, C.D, C.H, contour, C.CHAMFER), width="stretch", key="tab_vol")
        st.plotly_chart(V.packing_figure(live["placed_cg"], C.W, C.D, C.H, contour, C.CHAMFER), width="stretch", key="tab_cg")
    with tabs[1]:
        st.markdown("Beide Regeln auf **dieser** Instanz, Kennzahlen nebeneinander:")
        st.dataframe(
            {
                "Kennzahl": ["Auslastung", "Unplatzierte Boxen", "Offset x (cm)", "Offset y (cm)", "Verletzung"],
                "H_vol": [fmt_pct(live["util_vol"]), str(len(live["unplaced_vol"])), f"{live['offset_vol'][0]:.1f}",
                          f"{live['offset_vol'][1]:.1f}", "ja" if live["violation_vol"] else "nein"],
                "H_cg": [fmt_pct(live["util_cg"]), str(len(live["unplaced_cg"])), f"{live['offset_cg'][0]:.1f}",
                         f"{live['offset_cg'][1]:.1f}", "ja" if live["violation_cg"] else "nein"],
            },
            width="stretch", hide_index=True,
        )
        st.caption(f"Zum Vergleich die Messreihe dieser Zelle (200 Instanzen): {R.judgment_text(cell)}")
    with tabs[2]:
        st.markdown("Alle 54 gemessenen Zellen als Tabelle (Kontur, Toleranz, Dichtestreuung, Boxzahl, "
                     "Verletzungsrate beider Regeln, Gewinn, Urteil):")
        st.dataframe(
            {
                "Kontur": [r["contour"] for r in regime], "Toleranz": [fmt_pct(r["tol"], 0) for r in regime],
                "Dichtestreuung": [fmt_num(r["cv"], 1) for r in regime], "Boxen": [r["n_boxes"] for r in regime],
                "H_vol": [fmt_pct(r["violation_vol"]) for r in regime], "H_cg": [fmt_pct(r["violation_cg"]) for r in regime],
                "Gewinn (pp)": [fmt_num(r["gain_pp"], 1, True) for r in regime], "Urteil": [r["label"] for r in regime],
            },
            width="stretch", hide_index=True, height=360,
        )

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        f"""
**Instanz.** Container 160 × 150 × 160 cm (Groessenordnung LD3), zwei Konturen: Rechteck (volle Grundflaeche)
und gerundet (LD3-artig, an allen vier Ecken um 40 cm Kathete abgeschnitten). Boxen mit Grundflaeche 20-60 cm
je Kante, Hoehe 15-45 cm, **feste Orientierung** (keine Rotation). Gewicht = Volumen × Dichte, Dichte ~
Normal(1,0; Dichtestreuung).

**Platzierung.** Extreme-Point-Heuristik (Crainic, Perboli, Tadei 2008) wie `pack_demo`, mit eigenen
Start-Kandidaten an den Eckpunkten der gerundeten Kontur (ohne sie wuerde nie etwas platziert - der Ursprung
selbst liegt bei der gerundeten Kontur ausserhalb) und einem zusaetzlichen Bodenraster (20-cm-Schritte) fuer
die schwerpunkt-bewusste Regel.

**Die Regeln.** **H_vol:** groesste Box zuerst, ignoriert Gewicht (die Baseline, identisch zur
Volumen-Heuristik aus `pack_demo`). **H_cg:** Boxen ueber dem Median-Gewicht zuerst, mit Vorzug fuer die
zulaessige Position, deren Mitte der Container-Mitte am naechsten liegt (erweitertes Kandidatenraster);
leichte Boxen wie H_vol.

**Schwerpunkt.** Gewichtetes Mittel der Boxmitten, Offset zur geometrischen Mitte in x und y; eine Packung
verletzt das Fenster, wenn |Offset| die Toleranz in x **oder** y ueberschreitet.

**Warum der Volumenpreis der Schwerpunktregel praktisch null ist.** H_cg bevorzugt zentrumsnahe Positionen,
aendert aber nicht, WELCHE Boxen platziert werden - nur WO. Der Preis zeigt sich stattdessen in mehr
unplatzierten Boxen: die zentrumsnahen Bodenfelder werden von schweren Boxen belegt, spaeter ankommenden
Boxen fehlt dort Platz.

**Warum die gerundete Kontur die Verletzungsrate senkt, obwohl sie Volumen kostet.** Ein Nebeneffekt der
Rasterwahl: das Bodenraster ist bei der gerundeten Kontur staerker zur Mitte hin konzentriert (die Randfelder
in den abgeschnittenen Ecken fehlen), was indirekt zentrumsnahe Platzierung beguenstigt - keine physikalische
Aussage ueber gerundete ULDs.

**Grenzen dieses Modells** (bewusst so gewaehlt, damit die Aussage ehrlich bleibt):

- Boxgroessen, Dichteverteilung, Containermasse und Fase erfunden, nicht kalibriert. Die Schwerpunkt-Toleranz
  orientiert sich an der Groessenordnung realer ULD-Schwerpunktgrenzen (IATA ULD Technical Manual), ist aber
  keine Uebernahme einer konkreten Tabelle.
- Feste Orientierung je Box vereinfacht gegenueber `pack_demo` (sechs Rotationen).
- Kein Vergleich gegen ein exaktes Optimum: 3D-Packen mit Kontur ist fuer einen ILP-Vergleich aufwendig.
- Die schwerpunkt-bewusste Regel reicht bei enger Toleranz (5 %) nicht aus (Restverletzung bleibt hoch); ein
  dritter, reparierender Schritt (Tausch schwerer Boxen, wie in `stauplanung-demo`s Reparatur-Heuristik) waere
  eine Ausbauidee, ist aber nicht Teil dieser Demo.
- **Nicht Teil dieser Demo:** Rotation der Boxen, Stapelbarkeit als Regel, mehrere Container gleichzeitig, ein
  dritter Reparatur-Algorithmus, eine echte IATA-Schwerpunkttabelle, die reale Rumpfkontur (nur das
  Achteck-Modell).
        """
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Kontur (gerundet).** Punkt $(x, y)$ zulaessig $\iff$ $x+y \ge c \,\land\, (W-x)+y \ge c \,\land\, x+(D-y) \ge c \,\land\, (W-x)+(D-y) \ge c$,
mit Fase $c$ = 40 cm.

**Schwerpunkt.** $(c_x, c_y) = \sum_i w_i \cdot (\text{Boxmitte}_i) \,/\, \sum_i w_i$; Verletzung $\iff$
$|c_x - W/2| > \tau \cdot W/2 \,\lor\, |c_y - D/2| > \tau \cdot D/2$, mit Toleranz $\tau$.

**Nutzbares Volumen gerundet.** $(W \cdot D - 2c^2) \cdot H$ (vier rechtwinklige Dreiecke der Kathete $c$
abgeschnitten).

**H_vol.** Boxreihenfolge nach Volumen $w \cdot d \cdot h$ absteigend, erste zulaessige Extreme-Point-Position.

**H_cg.** Boxen ueber dem Median-Gewicht zuerst (bei Gleichstand nach Volumen), mit Zielposition
$(W/2, D/2)$: unter allen zulaessigen Kandidaten die mit minimalem $(x + w/2 - W/2)^2 + (y + d/2 - D/2)^2$;
danach die leichten Boxen wie H_vol.

Implementiert in `uldg_model.py` (Datentypen, Kontur-/Volumen-Geometrie, Schwerpunkt-Kennzahlen),
`uldg_geometry.py` (Extreme-Point-Verfahren, beide Regeln) und `uldg_results.py` (Messreihe, Urteil).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
