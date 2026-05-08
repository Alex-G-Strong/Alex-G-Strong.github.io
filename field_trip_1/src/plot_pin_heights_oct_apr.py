"""
Three-date comparison: Oct 25, 2025 | Apr 09, 2026 | Apr 18, 2026.
Layout mirrors pin_heights_all_years: four panels per site.
  Col 0: Absolute elevation
  Col 1: Pin height (mm)
  Col 2: Exaggerated deviations from Oct 25, 2025 baseline
  Col 3: Interval change bar charts (one sub-panel per pin)

Colours are drawn from each site's full plasma sequence so they
match the all-years figures exactly.
Row 0: Capps Crossing    Row 1: Sly Park
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from parameters import (
    ROOT, POST_DIR, EXAGGERATION_FACTOR,
    date_colors_rgba,
    COLOR_GROWTH, COLOR_LOSS,
    COLOR_HILL_FILL, COLOR_HILL_LINE,
    script_output_dir, save_ax, save_ax_group,
)

COMPARE_DATES = [
    pd.Timestamp("2025-10-25"),
    pd.Timestamp("2026-04-09"),
    pd.Timestamp("2026-04-18"),
]
DATE_LABELS = ["Oct 25, '25", "Apr 09, '26", "Apr 18, '26"]

SITES = {
    "Capps Crossing": {
        "pins":      ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx",
        "landscape": ROOT / "raw" / "capps_crossing_landscape_attributes.xlsx",
        "y_min":     1500,
    },
    "Sly Park": {
        "pins":      ROOT / "raw" / "sly_park_erosion_pins_compiled.xlsx",
        "landscape": ROOT / "raw" / "sly_park_landscape_attributes.xlsx",
        "y_min":     1080,
    },
}


# ── data helpers ──────────────────────────────────────────────────────────────

def load_site(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    return df[df["Date_measured"].isin(COMPARE_DATES)]


def load_elevations(path: Path) -> pd.Series:
    df = pd.read_excel(path).dropna(subset=["sample_name"])
    df = df[df["sample_name"].str.startswith("pin_")]
    df["Pin_number"] = df["sample_name"].str.replace("pin_", "Pin ", regex=False)
    return df.set_index("Pin_number")["elevation_m"]


def build_pivot(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(
        index="Pin_number", columns="Date_measured",
        values="pin_height_mean_cm", aggfunc="first",
    )
    pivot.index.name = "Pin"
    pivot = pivot.sort_index(key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))
    return pivot.reindex(sorted(pivot.columns), axis=1)


def site_date_colors(pins_path: Path) -> list:
    """Return plasma colours for the 3 target dates using the site's full sequence."""
    df = pd.read_excel(pins_path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    all_dates = sorted(df["Date_measured"].unique())
    all_colors = date_colors_rgba(len(all_dates))
    result = []
    for target in COMPARE_DATES:
        idx = next((i for i, d in enumerate(all_dates) if pd.Timestamp(d) == target), None)
        result.append(all_colors[idx] if idx is not None else (0.5, 0.5, 0.5, 1.0))
    return result


# ── drawing helpers ───────────────────────────────────────────────────────────

def _nan_list(vals):
    return [v if pd.notna(v) else None for v in vals]


def _marker(h_now, h_prev):
    if h_prev is None or pd.isna(h_prev) or h_now is None or pd.isna(h_now):
        return "o"
    return "s" if h_now > h_prev else "o"   # more exposed = surface eroded = square


def _draw_profile(ax, x, y_pos, h_now, h_prev, color):
    for i in range(len(x)):
        if y_pos[i] is None or pd.isna(y_pos[i]):
            continue
        hp = h_prev[i] if h_prev is not None else None
        ax.scatter(x[i], y_pos[i], color=color, s=40, zorder=5,
                   marker=_marker(h_now[i], hp))
        if i < len(x) - 1 and y_pos[i + 1] is not None and pd.notna(y_pos[i + 1]):
            ax.plot([x[i], x[i + 1]], [y_pos[i], y_pos[i + 1]],
                    color=color, linewidth=1.5, zorder=4)


def _make_legend(ax, colors, exag=False):
    elements = [
        Line2D([0], [0], color=c, linewidth=2, label=lbl)
        for c, lbl in zip(colors, DATE_LABELS)
    ]
    elements += [
        Line2D([0], [0], color="none", label=""),
        Line2D([0], [0], marker="o", color="grey", markerfacecolor="grey",
               linestyle="none", markersize=7, label="Surface gained material"),
        Line2D([0], [0], marker="s", color="grey", markerfacecolor="grey",
               linestyle="none", markersize=7, label="Surface lost material"),
    ]
    if exag:
        elements += [
            Patch(facecolor=COLOR_HILL_FILL, edgecolor="black", linewidth=1.2,
                  linestyle="--", label=f"Hill = {DATE_LABELS[0]} pin profile"),
            Line2D([0], [0], color="none",
                   label=(f"⚠ ×{EXAGGERATION_FACTOR} (factor) × 10 (mm→cm)\n"
                          f"   = ×{EXAGGERATION_FACTOR * 10} total exaggeration")),
        ]
    ax.legend(handles=elements, fontsize=6.5, loc="best", framealpha=0.85)


# ── Col 0: absolute elevation ─────────────────────────────────────────────────

def plot_absolute(pivot, elevations, site_name, ax, colors, y_min=None):
    pins   = [p for p in pivot.index if p in elevations.index]
    x      = list(range(len(pins)))
    ground = [elevations[p] for p in pins]
    dates  = list(pivot.columns)

    ax.plot(x, ground, color=COLOR_HILL_LINE, linewidth=1.0, linestyle=":", zorder=2)
    ax.fill_between(x, y_min if y_min is not None else min(ground) - 0.5, ground,
                    color=COLOR_HILL_FILL, alpha=0.2, zorder=1)

    for i, date in enumerate(dates):
        h_now  = _nan_list(pivot.loc[pins, date].values)
        h_prev = _nan_list(pivot.loc[pins, dates[i - 1]].values) if i > 0 else None
        y_pos  = [ground[j] - h_now[j] / 1000 if h_now[j] is not None else None
                  for j in range(len(pins))]
        _draw_profile(ax, x, y_pos, h_now, h_prev, colors[i])

    ax.set_ylim(bottom=y_min if y_min is not None else min(ground) - 0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Pin")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(f"{site_name} — absolute elevation", fontsize=10, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)
    _make_legend(ax, colors)


# ── Col 1: pin height (mm) ────────────────────────────────────────────────────

def plot_height(pivot, site_name, ax, colors):
    pins  = list(pivot.index)
    x     = list(range(len(pins)))
    dates = list(pivot.columns)

    ax.axhline(0, color=COLOR_HILL_LINE, linewidth=1.0, linestyle=":", zorder=2)

    for i, date in enumerate(dates):
        h_now  = _nan_list(pivot.loc[pins, date].values)
        h_prev = _nan_list(pivot.loc[pins, dates[i - 1]].values) if i > 0 else None
        _draw_profile(ax, x, h_now, h_now, h_prev, colors[i])

    ax.set_xticks(x)
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Pin")
    ax.set_ylabel("Pin height above ground (mm)")
    ax.set_title(f"{site_name} — pin height (mm)", fontsize=10, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)
    _make_legend(ax, colors)


# ── Col 2: exaggerated deviations ────────────────────────────────────────────

def plot_exaggerated(pivot, elevations, site_name, ax, colors, y_min=None):
    pins   = [p for p in pivot.index if p in elevations.index]
    x      = list(range(len(pins)))
    ground = [elevations[p] for p in pins]
    dates  = list(pivot.columns)

    h_base   = _nan_list(pivot.loc[pins, dates[0]].values)
    tip_base = [ground[j] - h_base[j] / 1000 if h_base[j] is not None else None
                for j in range(len(pins))]

    ax.plot(x, tip_base, color=COLOR_HILL_LINE, linewidth=1.0, linestyle=":", zorder=2)
    fill_bottom = y_min if y_min is not None else min(ground) - 0.5
    ax.fill_between(x, fill_bottom, tip_base, color=COLOR_HILL_FILL, alpha=0.2, zorder=1)

    all_y = [v for v in tip_base if v is not None]

    for i, date in enumerate(dates):
        h_now  = _nan_list(pivot.loc[pins, date].values)
        h_prev = _nan_list(pivot.loc[pins, dates[i - 1]].values) if i > 0 else None

        if i == 0:
            y_pos = tip_base
        else:
            y_pos = [
                tip_base[j] - (h_now[j] - h_base[j]) * EXAGGERATION_FACTOR / 100
                if h_now[j] is not None and h_base[j] is not None else None
                for j in range(len(pins))
            ]

        all_y.extend(v for v in y_pos if v is not None)
        _draw_profile(ax, x, y_pos, h_now, h_prev, colors[i])

    bottom  = y_min if y_min is not None else min(ground) - 0.5
    y_range = max(all_y) - bottom
    ax.set_ylim(bottom=bottom, top=max(all_y) + y_range * 0.08)
    ax.set_xticks(x)
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Pin")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(
        f"{site_name} — {EXAGGERATION_FACTOR * 10}× exaggeration\n"
        f"(deviation from {DATE_LABELS[0]})",
        fontsize=10, fontweight="bold",
    )
    ax.grid(True, linestyle=":", alpha=0.4)
    _make_legend(ax, colors, exag=True)


# ── Col 3: interval change bars ───────────────────────────────────────────────

def plot_interval_changes(pivot, site_name, fig, gs):
    pins       = list(pivot.index)
    dates      = list(pivot.columns)
    end_labels = [d.strftime("%b '%y") for d in dates[1:]]

    all_deltas = []
    for pin in pins:
        for i in range(1, len(dates)):
            h0, h1 = pivot.loc[pin, dates[i - 1]], pivot.loc[pin, dates[i]]
            if pd.notna(h0) and pd.notna(h1):
                all_deltas.append(h1 - h0)
    x_lim = max(abs(v) for v in all_deltas) * 1.2 if all_deltas else 10

    axes_list = []
    for i, pin in enumerate(pins):
        ax = fig.add_subplot(gs[i, 0], sharex=axes_list[0] if axes_list else None)
        axes_list.append(ax)

        changes, bar_colors, labels = [], [], []
        for j in range(1, len(dates)):
            h0 = pivot.loc[pin, dates[j - 1]]
            h1 = pivot.loc[pin, dates[j]]
            if pd.notna(h0) and pd.notna(h1):
                delta = h1 - h0
                changes.append(delta)
                bar_colors.append(COLOR_LOSS if delta > 0 else COLOR_GROWTH)
                labels.append(end_labels[j - 1])

        y_pos = list(range(len(changes)))
        ax.barh(y_pos, changes, color=bar_colors, edgecolor="none", height=0.7, zorder=3)
        ax.axvline(0, color="black", linewidth=0.6, zorder=4)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=5.5)
        ax.tick_params(axis="y", length=0, pad=2)
        ax.tick_params(axis="x", labelsize=6)
        ax.set_xlim(-x_lim, x_lim)
        ax.grid(True, axis="x", linestyle=":", alpha=0.4, zorder=0)
        ax.invert_yaxis()
        ax.yaxis.set_label_position("right")
        ax.set_ylabel(pin, fontsize=7, rotation=0, ha="left", va="center", labelpad=4)

        if i == 0:
            ax.set_title(f"{site_name}\nInterval Δ (mm)", fontsize=10, fontweight="bold")
        if i < len(pins) - 1:
            plt.setp(ax.get_xticklabels(), visible=False)
        else:
            ax.set_xlabel("Change (mm)", fontsize=8)

        ax.spines[["top", "right"]].set_visible(False)

    return axes_list


# ── main figure ───────────────────────────────────────────────────────────────

site_list = list(SITES.items())

fig = plt.figure(figsize=(26, 10))
gs_main = gridspec.GridSpec(
    len(site_list), 4, figure=fig,
    width_ratios=[1.2, 1.0, 1.2, 0.9],
    left=0.05, right=0.97, top=0.92, bottom=0.10,
    hspace=0.50, wspace=0.35,
)

out_dir = script_output_dir(__file__)
saved_axes = {}

for row, (site_name, paths) in enumerate(site_list):
    df         = load_site(paths["pins"])
    elevations = load_elevations(paths["landscape"])
    pivot      = build_pivot(df)
    colors     = site_date_colors(paths["pins"])
    y_min      = paths.get("y_min")
    n_pins     = len(pivot.index)

    ax_abs  = fig.add_subplot(gs_main[row, 0])
    ax_cm   = fig.add_subplot(gs_main[row, 1])
    ax_exag = fig.add_subplot(gs_main[row, 2])
    gs_bars = gs_main[row, 3].subgridspec(n_pins, 1, hspace=0.08)

    plot_absolute(pivot, elevations, site_name, ax_abs, colors, y_min=y_min)
    plot_height(pivot, site_name, ax_cm, colors)
    plot_exaggerated(pivot, elevations, site_name, ax_exag, colors, y_min=y_min)
    bar_axes = plot_interval_changes(pivot, site_name, fig, gs_bars)

    saved_axes[site_name] = (ax_abs, ax_cm, ax_exag, bar_axes)

fig.suptitle(
    "Erosion Pin Heights: Oct 25, 2025 | Apr 09, 2026 | Apr 18, 2026",
    fontsize=14, fontweight="bold", y=0.97,
)

fig.savefig(out_dir / "pin_heights_oct_apr.png", dpi=150, bbox_inches="tight")
fig.savefig(POST_DIR / "pin_heights_oct_apr.png", dpi=150, bbox_inches="tight")
print(f"Sheet saved to {out_dir / 'pin_heights_oct_apr.png'}")

for site_name, (ax_abs, ax_cm, ax_exag, bar_axes) in saved_axes.items():
    slug = site_name.lower().replace(" ", "_")
    save_ax(fig, ax_abs,  out_dir / f"{slug}_absolute_elevation.png")
    save_ax(fig, ax_cm,   out_dir / f"{slug}_pin_height_mm.png")
    save_ax(fig, ax_exag, out_dir / f"{slug}_exaggerated.png")
    save_ax_group(fig, bar_axes, out_dir / f"{slug}_interval_changes.png")

plt.show()
