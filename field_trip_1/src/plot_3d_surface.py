"""
Interactive 3D lattice plot of pin heights over time.
  X axis — measurement date
  Y axis — ground elevation (m), so pin spacing reflects hillslope geometry
  Z axis — elevation (m):  tip_base + (h_now − h_first) × EXAGGERATION_FACTOR / 100
           where tip_base = ground_elev + h_first / 1000
           Deviations from the first visit are scaled ×EXAGGERATION_FACTOR (same
           formula as the exaggeration panels in the other plots).

Elements:
  • Glass data surface   — semi-transparent sheet through all data points
  • Baseline plane       — first date's tip elevations extruded along date axis;
                           ribbons above/below show exaggerated change from baseline
  • Date ribbons         — one coloured line per date (plasma scale); circles = grew,
                           squares = shrank since previous visit
  • Pin traces           — dark grey lines connecting each pin through time
  • Ground reference     — tan line at floor showing terrain rise

Saved as standalone interactive HTML; embeds in Jupyter with fig.show().
"""

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from parameters import (
    ROOT, EXAGGERATION_FACTOR,
    date_colors_hex,
    COLOR_GROWTH, COLOR_LOSS,
    COLOR_GREY_LINE_3D,
    COLOR_HILL_FILL, COLOR_HILL_LINE,
    COLOR_GLASS_SURFACE,
    script_output_dir,
)

SITES = {
    "Capps Crossing": {
        "pins":      ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx",
        "landscape": ROOT / "raw" / "capps_crossing_landscape_attributes.xlsx",
        "output":    ROOT / "processed" / "3d_pin_heights_capps_crossing.html",
    },
    "Sly Park": {
        "pins":      ROOT / "raw" / "sly_park_erosion_pins_compiled.xlsx",
        "landscape": ROOT / "raw" / "sly_park_landscape_attributes.xlsx",
        "output":    ROOT / "processed" / "3d_pin_heights_sly_park.html",
    },
}


# ── data helpers ──────────────────────────────────────────────────────────────

def load_all(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    return df


def build_pivot(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(
        index="Pin_number", columns="Date_measured",
        values="pin_height_mean_cm", aggfunc="first",
    )
    pivot.index.name = "Pin"
    pivot = pivot.sort_index(key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))
    return pivot.reindex(sorted(pivot.columns), axis=1)


def load_elevations(path: Path) -> pd.Series:
    df = pd.read_excel(path).dropna(subset=["sample_name"])
    df = df[df["sample_name"].str.startswith("pin_")]
    df["Pin_number"] = df["sample_name"].str.replace("pin_", "Pin ", regex=False)
    return df.set_index("Pin_number")["elevation_m"]


plasma_hex = date_colors_hex


def exag_z(ground, h_now, h_first):
    """Surface elevation with exaggerated deviation from first visit.
    Higher pin exposure = more erosion = surface lower."""
    tip_base = ground - h_first / 1000
    return tip_base - (h_now - h_first) * EXAGGERATION_FACTOR / 100


# ── build figures ─────────────────────────────────────────────────────────────

for site_name, cfg in SITES.items():
    df         = load_all(cfg["pins"])
    elevations = load_elevations(cfg["landscape"])
    pivot      = build_pivot(df)

    dates       = list(pivot.columns)
    pins        = [p for p in pivot.index if p in elevations.index]
    date_labels = [d.strftime("%b %d, '%y") for d in dates]
    colors      = plasma_hex(len(dates))

    # X axis: months elapsed since first measurement (linear time)
    t0     = dates[0]
    x_months = [(d - t0).days / 30.4375 for d in dates]

    # Generate tick marks every 6 months across the full span
    total_months = (dates[-1] - t0).days / 30.4375
    tick_months  = [i * 6 for i in range(int(total_months / 6) + 2)
                    if i * 6 <= total_months + 1]
    tick_labels  = [(t0 + pd.Timedelta(days=m * 30.4375)).strftime("%b '%y")
                    for m in tick_months]

    # Y axis: simple pin index (1, 2, 3 …) — ground elev kept separately for Z
    ground = [elevations[p] for p in pins]
    y_pin  = list(range(1, len(pins) + 1))

    # First-visit heights and baseline tip elevations per pin
    h_first  = np.array([
        pivot.loc[p, dates[0]] if pd.notna(pivot.loc[p, dates[0]]) else np.nan
        for p in pins
    ], dtype=float)
    tip_base = np.array([ground[j] + h_first[j] / 1000 for j in range(len(pins))])

    # Full z grid [n_pins × n_dates] using exaggerated elevation formula
    z_grid = np.array([
        [
            exag_z(ground[j], pivot.loc[p, d], h_first[j])
            if pd.notna(pivot.loc[p, d]) and not np.isnan(h_first[j]) else np.nan
            for d in dates
        ]
        for j, p in enumerate(pins)
    ], dtype=float)

    fig = go.Figure()

    # ── 1. Glass data surface ─────────────────────────────────────────────────
    fig.add_trace(go.Surface(
        x=x_months,
        y=y_pin,
        z=z_grid,
        colorscale=[[0, COLOR_GLASS_SURFACE], [1, COLOR_GLASS_SURFACE]],
        showscale=False,
        opacity=0.28,
        lighting=dict(
            ambient=0.15,
            diffuse=0.25,
            specular=2.0,
            roughness=0.02,
            fresnel=2.0,
        ),
        lightposition=dict(x=1500, y=500, z=2000),
        contours=dict(x=dict(show=False), y=dict(show=False), z=dict(show=False)),
        name="Data surface",
        showlegend=True,
        hoverinfo="skip",
    ))

    # ── 2. Baseline plane (first-visit tip elevations extruded) ───────────────
    z_baseline = np.tile(tip_base.reshape(-1, 1), (1, len(dates)))

    fig.add_trace(go.Surface(
        x=x_months,
        y=y_pin,
        z=z_baseline,
        colorscale=[[0, COLOR_HILL_FILL], [1, COLOR_HILL_FILL]],
        showscale=False,
        opacity=0.55,
        lighting=dict(ambient=0.5, diffuse=0.7, specular=0.1, roughness=0.8),
        name=f"Baseline ({date_labels[0]})",
        showlegend=True,
        hoverinfo="skip",
    ))

    # ── 3. Dark-grey pin traces (time-series slices) ──────────────────────────
    for j, (pin, y_val, g_val) in enumerate(zip(pins, y_pin, ground)):
        entries = [
            (xm, exag_z(g_val, pivot.loc[pin, d], h_first[j]))
            for xm, d in zip(x_months, dates)
            if pd.notna(pivot.loc[pin, d]) and not np.isnan(h_first[j])
        ]
        if len(entries) < 2:
            continue
        vx, vz = zip(*entries)
        fig.add_trace(go.Scatter3d(
            x=list(vx), y=[y_val] * len(vx), z=list(vz),
            mode="lines",
            line=dict(color=COLOR_GREY_LINE_3D, width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ── 4. Coloured date ribbons with circle/square markers ───────────────────
    for i, (xm, date, label, color) in enumerate(zip(x_months, dates, date_labels, colors)):
        h_now  = [pivot.loc[p, date] for p in pins]
        h_prev = [pivot.loc[p, dates[i - 1]] for p in pins] if i > 0 else [None] * len(pins)

        entries = []
        for j, (y_val, g_val, h, hp, p) in enumerate(zip(y_pin, ground, h_now, h_prev, pins)):
            if not pd.notna(h) or np.isnan(h_first[j]):
                continue
            z_val  = exag_z(g_val, h, h_first[j])
            symbol = ("square"
                      if hp is not None and pd.notna(hp) and h > hp
                      else "circle")   # more exposed = surface eroded = square
            entries.append((y_val, z_val, p, h, symbol))

        if not entries:
            continue

        vy, vz, vp, vh, vsym = zip(*entries)
        hover = [
            f"<b>{label}</b><br>{p}<br>"
            f"Height: {h:.1f} mm<br>Elev: {z:.3f} m"
            for p, h, z in zip(vp, vh, vz)
        ]

        fig.add_trace(go.Scatter3d(
            x=[xm] * len(vy), y=list(vy), z=list(vz),
            mode="lines+markers",
            line=dict(color=color, width=5),
            marker=dict(color=color, size=6, symbol=list(vsym)),
            name=label,
            text=hover,
            hovertemplate="%{text}<extra></extra>",
        ))

    # ── 5. Ground elevation reference line ────────────────────────────────────
    z_floor = float(np.nanmin(z_grid)) - 0.3
    for xm in [x_months[0], x_months[-1]]:
        fig.add_trace(go.Scatter3d(
            x=[xm] * len(y_pin), y=y_pin, z=[z_floor] * len(y_pin),
            mode="lines",
            line=dict(color=COLOR_HILL_FILL, width=3),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ── layout ────────────────────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=(f"<b>{site_name} — Pin Heights Over Time</b><br>"
                  f"<sup>Z axis: elevation (m), deviations from first visit "
                  f"×{EXAGGERATION_FACTOR} exaggerated</sup>"),
            font=dict(size=16), x=0.5,
        ),
        legend=dict(title="Legend", font=dict(size=10), x=0.02, y=0.95),
        scene=dict(
            xaxis=dict(
                title="Date (months since first visit)",
                tickvals=tick_months,
                ticktext=tick_labels,
                tickfont=dict(size=9),
            ),
            yaxis=dict(
                title="Pin number",
                tickvals=y_pin,
                ticktext=[str(n) for n in y_pin],
                tickfont=dict(size=9),
            ),
            zaxis=dict(
                title=f"Elevation (m, ×{EXAGGERATION_FACTOR} exag.)",
                tickfont=dict(size=9),
            ),
            camera=dict(eye=dict(x=1.8, y=-1.6, z=0.9)),
            aspectmode="manual",
            aspectratio=dict(x=1.6, y=1.0, z=0.9),
        ),
        width=980, height=720,
        margin=dict(l=10, r=10, t=80, b=10),
    )

    out_dir = script_output_dir(__file__)
    output  = out_dir / cfg["output"].name
    fig.write_html(str(output), include_plotlyjs="cdn")
    print(f"Saved {output}")
