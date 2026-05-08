"""
Interactive 3D plot of Andesite Ridge soil thickness transect.
  • Surface points plotted at true elevation (lat/lon → local metres from centroid)
  • A vertical bar drops downward from each point; bar length = soil thickness (cm)
  • Bars are scaled ×10 for visibility (noted in title and hover text)
  • Both dots and bars are coloured by soil thickness (viridis scale)
Saved as standalone interactive HTML.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from parameters import ROOT, script_output_dir

DATA_PATH = ROOT / "raw" / "andesite_ridge_soil_thickness_curvature.xlsx"
BAR_SCALE  = 10   # display bar length = actual thickness × BAR_SCALE


# ── data ──────────────────────────────────────────────────────────────────────

def load_data(path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = df.dropna(subset=["latitude", "longitude", "elevation_m", "soil_thickness_cm"])
    df["_num"] = df["sample_name"].str.extract(r"(\d+)$")[0].astype(int)
    return df.sort_values("_num").reset_index(drop=True)


def to_local_m(df: pd.DataFrame):
    """Lat/lon → local easting/northing in metres (origin = centroid)."""
    lat0 = df["latitude"].mean()
    lon0 = df["longitude"].mean()
    x = (df["longitude"] - lon0) * (111_000 * np.cos(np.radians(lat0)))
    y = (df["latitude"]  - lat0) *  111_000
    return x.values, y.values


df    = load_data(DATA_PATH)
x, y  = to_local_m(df)
z     = df["elevation_m"].values
thick = df["soil_thickness_cm"].values
names = df["sample_name"].str.replace("andesite_", "", regex=False).values

# Per-point hex colours from viridis, normalised to thickness range
t_norm     = (thick - thick.min()) / (thick.max() - thick.min())
viridis    = cm.get_cmap("viridis")
hex_colors = [mcolors.to_hex(viridis(v)) for v in t_norm]


# ── figure ────────────────────────────────────────────────────────────────────

fig = go.Figure()

# 1. Hillslope profile line (connects samples in numeric order)
fig.add_trace(go.Scatter3d(
    x=x, y=y, z=z,
    mode="lines",
    line=dict(color="#888888", width=2),
    name="Hillslope profile",
    hoverinfo="skip",
))

# 2. Surface scatter dots (coloured + hover labels)
fig.add_trace(go.Scatter3d(
    x=x, y=y, z=z,
    mode="markers",
    marker=dict(
        size=6,
        color=thick,
        colorscale="Viridis",
        cmin=thick.min(),
        cmax=thick.max(),
        colorbar=dict(
            title=dict(text="Soil thickness (cm)", font=dict(size=11)),
            thickness=16,
            len=0.55,
            x=1.02,
            tickfont=dict(size=9),
        ),
        showscale=True,
        line=dict(color="white", width=0.5),
    ),
    text=[
        f"<b>{n}</b><br>"
        f"Elevation: {z_:.1f} m<br>"
        f"Soil thickness: {t} cm<br>"
        f"Easting: {xi:.1f} m  Northing: {yi:.1f} m"
        for n, z_, t, xi, yi in zip(names, z, thick, x, y)
    ],
    hovertemplate="%{text}<extra></extra>",
    name="Sample points",
))

# 3. Vertical bars (one trace per sample, coloured by thickness)
z_bottom_all = z - thick * BAR_SCALE / 100   # cm → m, then scale

for i in range(len(df)):
    fig.add_trace(go.Scatter3d(
        x=[x[i], x[i]],
        y=[y[i], y[i]],
        z=[z[i], z_bottom_all[i]],
        mode="lines",
        line=dict(color=hex_colors[i], width=8),
        showlegend=False,
        text=[
            f"<b>{names[i]}</b><br>"
            f"Soil thickness: {thick[i]} cm<br>"
            f"(bar shown at ×{BAR_SCALE} scale)"
        ] * 2,
        hovertemplate="%{text}<extra></extra>",
    ))

# ── layout ────────────────────────────────────────────────────────────────────

z_all = np.concatenate([z, z_bottom_all])
z_pad = (z_all.max() - z_all.min()) * 0.08

fig.update_layout(
    title=dict(
        text=(
            "<b>Andesite Ridge — Soil Thickness Transect</b><br>"
            f"<sup>Bars drop downward from surface elevation; "
            f"bar length = soil thickness × {BAR_SCALE} (for visibility)</sup>"
        ),
        font=dict(size=15),
        x=0.5,
    ),
    legend=dict(font=dict(size=10), x=0.01, y=0.97),
    scene=dict(
        xaxis=dict(
            title="Easting (m from centroid)",
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            title="Northing (m from centroid)",
            tickfont=dict(size=9),
        ),
        zaxis=dict(
            title="Elevation (m)",
            tickfont=dict(size=9),
            range=[z_all.min() - z_pad, z_all.max() + z_pad],
        ),
        camera=dict(eye=dict(x=1.6, y=-1.8, z=1.0)),
        aspectmode="manual",
        aspectratio=dict(x=1.8, y=1.0, z=1.0),
    ),
    width=1050, height=720,
    margin=dict(l=10, r=10, t=90, b=10),
)

out_dir = script_output_dir(__file__)
output  = out_dir / "soil_thickness_3d.html"
fig.write_html(str(output), include_plotlyjs="cdn")
print(f"Saved {output}")
