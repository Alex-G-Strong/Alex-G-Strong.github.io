"""
All-years erosion pin profile comparison.
Three panels per site:
  Col 0: Absolute elevation  — y = ground_elev (m) + pin_height (mm) / 1000
  Col 1: Pin height (mm)     — y = raw pin height above ground
  Col 2: Exaggerated         — Apr 09 baseline at true elevation; each
                               subsequent visit's deviation from the first
                               measurement is scaled by EXAGGERATION_FACTOR
                               so cm changes appear at metre scale.
Each measurement date has a distinct base colour (plasma colormap, old→new).
Lighter shade = pin grew since the previous visit.
Darker shade  = pin shrank since the previous visit.
Outputs one PNG to processed/.
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
    COLOR_GREY_LINE,
    COLOR_TABLE_GROWTH, COLOR_TABLE_LOSS, COLOR_TABLE_HEADER,
    script_output_dir, safe_filename, save_ax, save_ax_group,
)

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

def load_all(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    return df


def load_elevations(path: Path) -> pd.Series:
    df = pd.read_excel(path).dropna(subset=["sample_name"])
    df = df[df["sample_name"].str.startswith("pin_")]
    df["Pin_number"] = df["sample_name"].str.replace("pin_", "Pin ", regex=False)
    return df.set_index("Pin_number")["elevation_m"]


def build_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Rows = pins (numeric order), columns = dates (chronological)."""
    pivot = df.pivot_table(
        index="Pin_number", columns="Date_measured",
        values="pin_height_mean_cm", aggfunc="first",
    )
    pivot.index.name = "Pin"
    pivot = pivot.sort_index(key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    return pivot


# ── colour helpers ────────────────────────────────────────────────────────────

_date_colors = date_colors_rgba


def _tint(color, amount: float = 0.45):
    """Blend toward white (growth)."""
    c = np.array(mcolors.to_rgb(color))
    return tuple(c + (1 - c) * amount)


def _shade(color, amount: float = 0.45):
    """Blend toward black (loss)."""
    c = np.array(mcolors.to_rgb(color))
    return tuple(c * (1 - amount))


def _seg_color(base, h_now, h_prev):
    """Pick tinted, shaded, or base colour for a single point/segment."""
    if h_prev is None or pd.isna(h_prev) or h_now is None or pd.isna(h_now):
        return base
    if h_now > h_prev:
        return _tint(base)
    if h_now < h_prev:
        return _shade(base)
    return base


# ── core drawing ──────────────────────────────────────────────────────────────

def _marker(h_now, h_prev):
    """Circle if surface gained material, square if surface lost material."""
    if h_prev is None or pd.isna(h_prev) or h_now is None or pd.isna(h_now):
        return "o"
    if h_now > h_prev:   # pin more exposed = surface eroded = loss
        return "s"
    return "o"


def _draw_profile(ax, x, y_pos, h_now, h_prev, base_color):
    """
    Draw one date's profile line.
      y_pos  — actual y coordinates to plot
      h_now  — raw pin heights (mm) for this date, used for marker selection
      h_prev — raw pin heights (mm) for previous date (or None for first date)
    Colour is uniform (base_color); shape encodes growth (○) vs loss (□).
    """
    for i in range(len(x)):
        if y_pos[i] is None or pd.isna(y_pos[i]):
            continue
        hp = h_prev[i] if h_prev is not None else None
        ax.scatter(x[i], y_pos[i], color=base_color, s=40, zorder=5,
                   marker=_marker(h_now[i], hp))

        if i < len(x) - 1 and y_pos[i + 1] is not None and pd.notna(y_pos[i + 1]):
            ax.plot([x[i], x[i + 1]], [y_pos[i], y_pos[i + 1]],
                    color=base_color, linewidth=1.5, zorder=4)


def _make_legend(ax, dates, colors, exag: bool = False, first_date=None):
    elements = [
        Line2D([0], [0], color=c, linewidth=2, label=d.strftime("%b %d, '%y"))
        for d, c in zip(dates, colors)
    ]
    elements += [
        Line2D([0], [0], color="none", label=""),
        Line2D([0], [0], marker="o", color="grey", markerfacecolor="grey",
               linestyle="none", markersize=7, label="Surface gained material"),
        Line2D([0], [0], marker="s", color="grey", markerfacecolor="grey",
               linestyle="none", markersize=7, label="Surface lost material"),
    ]
    if exag:
        fd_label = first_date.strftime("%b %d, '%y") if first_date is not None else "first visit"
        elements += [
            Patch(facecolor=COLOR_HILL_FILL, edgecolor="black", linewidth=1.2,
                  linestyle="--", label=f"Hill = {fd_label} pin profile"),
            Line2D([0], [0], color="none",
                   label=f"⚠ ×{EXAGGERATION_FACTOR} (factor) × 10 (mm→cm)\n   = ×{EXAGGERATION_FACTOR * 10} total exaggeration"),
        ]
    ax.legend(handles=elements, fontsize=6.5, loc="best", framealpha=0.85)


def _nan_list(vals):
    return [v if pd.notna(v) else None for v in vals]


# ── Panel 0: absolute elevation ───────────────────────────────────────────────

def plot_absolute_all(pivot, elevations, site_name, ax, y_min=None):
    pins   = [p for p in pivot.index if p in elevations.index]
    x      = list(range(len(pins)))
    ground = [elevations[p] for p in pins]
    dates  = list(pivot.columns)
    colors = _date_colors(len(dates))

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
    _make_legend(ax, dates, colors)


# ── Panel 1: pin height (mm) ──────────────────────────────────────────────────

def plot_height_all(pivot, site_name, ax):
    pins   = list(pivot.index)
    x      = list(range(len(pins)))
    dates  = list(pivot.columns)
    colors = _date_colors(len(dates))

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
    _make_legend(ax, dates, colors)


# ── Panel 2: exaggerated (deviation from first measurement) ───────────────────

def plot_exaggerated_all(pivot, elevations, site_name, ax, y_min=None):
    pins   = [p for p in pivot.index if p in elevations.index]
    x      = list(range(len(pins)))
    ground = [elevations[p] for p in pins]
    dates  = list(pivot.columns)
    colors = _date_colors(len(dates))

    # Baseline from first measurement
    h_base   = _nan_list(pivot.loc[pins, dates[0]].values)
    tip_base = [ground[j] - h_base[j] / 1000 if h_base[j] is not None else None
                for j in range(len(pins))]

    # Hill = first-visit pin-tip profile (not just bare ground)
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

    bottom = y_min if y_min is not None else min(ground) - 0.5
    y_range = max(all_y) - bottom
    ax.set_ylim(bottom=bottom, top=max(all_y) + y_range * 0.08)
    ax.set_xticks(x)
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Pin")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(f"{site_name} — {EXAGGERATION_FACTOR * 10}× exaggeration\n(deviation from first visit)",
                 fontsize=10, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)
    _make_legend(ax, dates, colors, exag=True, first_date=dates[0])


# ── Panel 3: per-pin interval change bar charts ───────────────────────────────

def plot_interval_changes(pivot: pd.DataFrame, site_name: str,
                          fig: plt.Figure, gs) -> None:
    """Horizontal bar chart per pin showing Δmm between consecutive visits.
    Time runs top-to-bottom on the y-axis; x-axis is change in mm."""
    pins  = list(pivot.index)
    dates = list(pivot.columns)

    # Interval end-date labels (abbreviated)
    end_labels = [d.strftime("%b '%y") for d in dates[1:]]

    # Global x range for shared axis
    all_deltas = []
    for pin in pins:
        for i in range(1, len(dates)):
            h0, h1 = pivot.loc[pin, dates[i - 1]], pivot.loc[pin, dates[i]]
            if pd.notna(h0) and pd.notna(h1):
                all_deltas.append(h1 - h0)
    x_lim = max(abs(v) for v in all_deltas) * 1.2 if all_deltas else 10

    axes_list = []
    for i, pin in enumerate(pins):
        ax = fig.add_subplot(gs[i, 0],
                             sharex=axes_list[0] if axes_list else None)
        axes_list.append(ax)

        changes, colors, labels = [], [], []
        for j in range(1, len(dates)):
            h0 = pivot.loc[pin, dates[j - 1]]
            h1 = pivot.loc[pin, dates[j]]
            if pd.notna(h0) and pd.notna(h1):
                delta = h1 - h0
                changes.append(delta)
                colors.append(COLOR_LOSS if delta > 0 else COLOR_GROWTH)
                labels.append(end_labels[j - 1])

        y_pos = list(range(len(changes)))
        ax.barh(y_pos, changes, color=colors, edgecolor="none", height=0.7,
                zorder=3)
        ax.axvline(0, color="black", linewidth=0.6, zorder=4)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=5.5)
        ax.tick_params(axis="y", length=0, pad=2)
        ax.tick_params(axis="x", labelsize=6)
        ax.set_xlim(-x_lim, x_lim)
        ax.grid(True, axis="x", linestyle=":", alpha=0.4, zorder=0)
        ax.invert_yaxis()   # oldest interval at top

        # Pin label on the right
        ax.yaxis.set_label_position("right")
        ax.set_ylabel(pin, fontsize=7, rotation=0, ha="left", va="center",
                      labelpad=4)

        if i == 0:
            ax.set_title(f"{site_name}\nInterval Δ (mm)",
                         fontsize=10, fontweight="bold")
        if i < len(pins) - 1:
            plt.setp(ax.get_xticklabels(), visible=False)
        else:
            ax.set_xlabel("Change (mm)", fontsize=8)

        ax.spines[["top", "right"]].set_visible(False)

    return axes_list


# ── layout — one figure per site ─────────────────────────────────────────────

SITE_OUTPUTS = {
    "Capps Crossing": ROOT / "processed" / "pin_heights_all_years_capps_crossing.png",
    "Sly Park":       ROOT / "processed" / "pin_heights_all_years_sly_park.png",
}

for (site_name, paths), output in zip(SITES.items(), SITE_OUTPUTS.values()):
    df         = load_all(paths["pins"])
    elevations = load_elevations(paths["landscape"])
    pivot      = build_pivot(df)
    y_min      = paths.get("y_min")
    n_pins     = len(pivot.index)

    fig = plt.figure(figsize=(26, 5))
    gs_main = gridspec.GridSpec(
        1, 4, figure=fig,
        width_ratios=[1.2, 1.0, 1.2, 0.9],
        left=0.05, right=0.97, top=0.88, bottom=0.14,
        wspace=0.35,
    )

    ax_abs  = fig.add_subplot(gs_main[0, 0])
    ax_cm   = fig.add_subplot(gs_main[0, 1])
    ax_exag = fig.add_subplot(gs_main[0, 2])
    gs_bars = gs_main[0, 3].subgridspec(n_pins, 1, hspace=0.08)

    plot_absolute_all(pivot, elevations, site_name, ax_abs, y_min=y_min)
    plot_height_all(pivot, site_name, ax_cm)
    plot_exaggerated_all(pivot, elevations, site_name, ax_exag, y_min=y_min)
    bar_axes = plot_interval_changes(pivot, site_name, fig, gs_bars)

    fig.suptitle(f"Erosion Pin Heights — All Years: {site_name}",
                 fontsize=14, fontweight="bold", y=0.98)

    # ── save combined sheet ───────────────────────────────────────────────────
    out_dir = script_output_dir(__file__)
    fig.savefig(out_dir / output.name, dpi=150, bbox_inches="tight")
    fig.savefig(POST_DIR / output.name, dpi=150, bbox_inches="tight")
    print(f"Sheet saved to {out_dir / output.name}")

    # ── save individual panels ───────────────────────────────────────────────
    slug = site_name.lower().replace(" ", "_")
    for ax, label in [
        (ax_abs,  f"{slug}_absolute_elevation"),
        (ax_cm,   f"{slug}_pin_height_mm"),
        (ax_exag, f"{slug}_exaggerated"),
    ]:
        save_ax(fig, ax, out_dir / f"{label}.png")

    save_ax_group(fig, bar_axes, out_dir / f"{slug}_interval_changes.png")

    plt.close(fig)
