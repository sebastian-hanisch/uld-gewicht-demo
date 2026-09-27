"""ULD-Beladung: Volumen gegen Schwerpunkt - Plotly-Figuren.

3D-Packansicht (go.Mesh3d, Quader-Dreiecksmuster mechanisch aus pack_demo/pack_visualization.py uebernommen -
dort bereits geometrisch verifiziert, siehe die Herleitung im dortigen Kommentar: alle 12 Dreiecke haben nach
aussen zeigende Normalen) plus die vorgerechneten Grafiken (Verletzungsrate ueber Toleranz, Kontur-Volumen).
Alle Achsen der 2D-Grafiken sind `fixedrange` (Touch-Scrollen soll nicht am Chart haengen bleiben); die
3D-Ansicht dreht bewusst frei (das ist der Sinn der Ansicht).
"""
from __future__ import annotations

import plotly.graph_objects as go

from uldg_model import GERUNDET

COLOR_VOL = "#2a6fb0"
COLOR_CG = "#9fc2e6"
BOX_COLORS = ["#e07a5f", "#3d5a80", "#81b29a", "#f2cc8f", "#98c1d9", "#ee6c4d", "#c9ada7", "#6d6875"]

# Quader-Eckpunkt-Reihenfolge und Dreiecke fuer go.Mesh3d (siehe pack_demo/pack_visualization.py fuer die
# Herleitung: alle 12 Dreiecke zeigen nach aussen).
_BOX_TRIANGLES_I = [0, 0, 4, 4, 0, 0, 3, 3, 0, 0, 1, 1]
_BOX_TRIANGLES_J = [2, 3, 5, 6, 1, 5, 6, 7, 7, 4, 2, 6]
_BOX_TRIANGLES_K = [1, 2, 6, 7, 5, 4, 2, 6, 3, 7, 6, 5]


def _box_mesh_trace(pos, dim, color, name):
    x0, y0, z0 = pos
    dx, dy, dz = dim
    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz
    xs = [x0, x1, x1, x0, x0, x1, x1, x0]
    ys = [y0, y0, y1, y1, y0, y0, y1, y1]
    zs = [z0, z0, z0, z0, z1, z1, z1, z1]
    return go.Mesh3d(
        x=xs, y=ys, z=zs, i=_BOX_TRIANGLES_I, j=_BOX_TRIANGLES_J, k=_BOX_TRIANGLES_K,
        color=color, opacity=1.0, flatshading=True,
        lighting=dict(ambient=0.55, diffuse=0.7, specular=0.35, roughness=0.6, fresnel=0.1),
        lightposition=dict(x=100, y=-100, z=200),
        name=name, hovertext=name, hoverinfo="text", showlegend=False,
    )


def _contour_outline(W: float, D: float, contour: str, chamfer: float):
    """Bodenkontur als geschlossenes Vieleck (Rechteck oder Achteck mit vier abgeschnittenen Ecken)."""
    if contour == GERUNDET:
        c = chamfer
        pts = [(c, 0), (W - c, 0), (W, c), (W, D - c), (W - c, D), (c, D), (0, D - c), (0, c), (c, 0)]
    else:
        pts = [(0, 0), (W, 0), (W, D), (0, D), (0, 0)]
    return pts


def _container_wireframe_trace(W: float, D: float, H: float, contour: str, chamfer: float):
    base = _contour_outline(W, D, contour, chamfer)
    xs, ys, zs = [], [], []
    for z in (0.0, H):
        for (px, py) in base:
            xs.append(px)
            ys.append(py)
            zs.append(z)
        xs.append(None)
        ys.append(None)
        zs.append(None)
    for (px, py) in base[:-1]:
        xs += [px, px, None]
        ys += [py, py, None]
        zs += [0.0, H, None]
    return go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=dict(color="rgba(60,60,60,0.6)", width=3),
                         name="Kontur", hoverinfo="skip", showlegend=False)


def packing_figure(placed, W: float, D: float, H: float, contour: str, chamfer: float):
    """3D-Ansicht einer Packung (eine Regel): Kontur-Drahtgitter plus jede platzierte Box als massiver Quader."""
    fig = go.Figure()
    fig.add_trace(_container_wireframe_trace(W, D, H, contour, chamfer))
    for i, p in enumerate(placed):
        color = BOX_COLORS[i % len(BOX_COLORS)]
        label = f"Box {i + 1} ({p.box.w:.0f}x{p.box.d:.0f}x{p.box.h:.0f} cm, {p.box.weight:.1f} kg)"
        fig.add_trace(_box_mesh_trace((p.x, p.y, p.z), (p.box.w, p.box.d, p.box.h), color, label))
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="Breite (cm)", range=[0, W]),
            yaxis=dict(title="Tiefe (cm)", range=[0, D]),
            zaxis=dict(title="Hoehe (cm)", range=[0, H]),
            aspectmode="data", camera=dict(eye=dict(x=1.5, y=-1.5, z=1.0)),
        ),
        height=460, margin=dict(l=0, r=0, t=20, b=0), showlegend=False,
    )
    return fig


def violation_rate_figure(rows: list[dict]):
    """Verletzungsrate H_vol gegen H_cg ueber die drei Toleranzstufen (feste Kontur/CV/Boxzahl, 3 Balkenpaare)."""
    tols = [f"{r['tol'] * 100:.0f} %" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tols, y=[r["violation_rate_vol"] * 100 for r in rows], name="H_vol (Volumen)",
                          marker_color=COLOR_VOL, text=[f"{r['violation_rate_vol'] * 100:.1f} %" for r in rows], textposition="outside"))
    fig.add_trace(go.Bar(x=tols, y=[r["violation_rate_cg"] * 100 for r in rows], name="H_cg (schwerpunkt-bewusst)",
                          marker_color=COLOR_CG, text=[f"{r['violation_rate_cg'] * 100:.1f} %" for r in rows], textposition="outside"))
    fig.update_layout(
        barmode="group", height=340, margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(title="Schwerpunkt-Toleranz", fixedrange=True),
        yaxis=dict(title="Verletzungsrate (%)", range=[0, 108], fixedrange=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def kontur_volume_figure(vol_rechteck: float, vol_gerundet: float):
    fig = go.Figure(go.Bar(
        x=["Rechteck", "Gerundet"], y=[vol_rechteck / 1e6, vol_gerundet / 1e6],
        marker_color=[COLOR_VOL, COLOR_CG],
        text=[f"{vol_rechteck / 1e6:.2f} Mio. cm³", f"{vol_gerundet / 1e6:.2f} Mio. cm³"], textposition="outside",
    ))
    fig.update_layout(
        height=300, margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(title=None, fixedrange=True),
        yaxis=dict(title="Nutzbares Volumen (Mio. cm³)", range=[0, vol_rechteck / 1e6 * 1.15], fixedrange=True),
        showlegend=False,
    )
    return fig


def regime_figure(rows: list[dict], current_key: tuple | None = None):
    """Gewinn (H_vol minus H_cg, Prozentpunkte) ueber alle 54 Zellen, gefaerbt nach Urteil."""
    color_map = {"deutlich": "#3d8b5f", "nicht_ausreichend": "#c9a227", "unkritisch": "#7a7a7a"}
    xs = [f"{r['contour'][:4]}/{r['tol']:.2f}/{r['cv']:.1f}/{r['n_boxes']}" for r in rows]
    ys = [r["gain_pp"] for r in rows]
    colors = [color_map[r["state"]] for r in rows]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=colors, hovertext=[r["label"] for r in rows], hoverinfo="text+y"))
    fig.update_layout(
        height=340, margin=dict(l=10, r=10, t=20, b=90),
        xaxis=dict(title="Kontur / Toleranz / Dichtestreuung / Boxzahl", tickangle=90, fixedrange=True, tickfont=dict(size=8)),
        yaxis=dict(title="Gewinn H_vol - H_cg (Prozentpunkte)", fixedrange=True),
        showlegend=False,
    )
    return fig
