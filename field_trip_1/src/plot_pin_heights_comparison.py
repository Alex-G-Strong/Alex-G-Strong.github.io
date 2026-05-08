"""
Side-by-side comparison of three elevation profile styles.
Reference date : Oct 25, 2025 (coloured with its plasma colour from the full record)
Comparison date: Apr 18, 2026 (segments green = grew, red = shrank vs reference)
  Col 0: Absolute elevation
  Col 1: Pin height (mm)
  Col 2: Exaggerated deviations from reference
  Col 3: Summary table
Outputs one PNG to processed/.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from parameters import (
    ROOT, EXAGGERATION_FACTOR,
    date_colors_rgba,
    COLOR_GROWTH, COLOR_LOSS, COLOR_NEUTRAL,
    COLOR_HILL_FILL, COLOR_HILL_LINE,
    COLOR_TABLE_GROWTH, COLOR_TABLE_LOSS, COLOR_TABLE_NEUTRAL, COLOR_TABLE_HEADER,
    script_output_dir, safe_filename, save_ax,
)

SITES = {
    "Capps Crossing": {
        "pins":      ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx",
        "landscape": ROOT / "raw" / "capps_crossing_landscape_attributes.xlsx",
        "y_min":     1520,
    },
    "Sly Park": {
        "pins":      ROOT / "raw" / "sly_park_erosion_pins_compiled.xlsx",
        "landscape": ROOT / "raw" / "sly_park_landscape_attributes.xlsx",
        "y_min":     None,
    },
}

COMPARE_DATES = [pd.Timestamp("2025-10-25"), pd.Timestamp("2026-04-18")]
DATE_LABELS   = ["Oct 25, 2025", "Apr 18, 2026"]


def site_date_color(pins_path: Path) -> tuple:
    """Return the plasma colour for Oct 25, 2025 using each site's full date sequence."""
    df = pd.read_excel(pins_path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    dates = sorted(df["Date_measured"].unique())
    idx   = next(i for i, d in enumerate(dates) if pd.Timestamp(d) == COMPARE_DATES[0])
    return date_colors_rgba(len(dates))[idx]



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


def build_table(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(
        index="Pin_number", columns="Date_measured",
        values="pin_height_mean_cm", aggfunc="first",
    )
    pivot.columns = DATE_LABELS
    pivot.index.name = "Pin"
    pivot["Delta (mm)"] = pivot[DATE_LABELS[1]] - pivot[DATE_LABELS[0]]
    pivot = pivot.sort_index(key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))
    return pivot


# ── shared helpers ────────────────────────────────────────────────────────────

def _pin_color(val_late, val_early, invert=False):
    """Green if surface rose, red if surface fell.
    invert=True for raw-mm charts where higher value = more erosion."""
    if val_early is None:
        return "grey"
    rose = (val_late < val_early) if invert else (val_late > val_early)
    fell = (val_late > val_early) if invert else (val_late < val_early)
    if rose:
        return COLOR_GROWTH
    if fell:
        return COLOR_LOSS
    return "grey"


def _draw_late_line(ax, x, y_late, y_early, invert_color=False):
    """Draw comparison dots and segments coloured by change direction."""
    for i in range(len(x)):
        if y_late[i] is None:
            continue
        color = _pin_color(y_late[i], y_early[i], invert=invert_color)
        ax.scatter(x[i], y_late[i], color=color, s=50, zorder=5)
        if i < len(x) - 1 and y_late[i + 1] is not None:
            seg_color = _pin_color(y_late[i + 1], y_early[i + 1], invert=invert_color)
            ax.plot([x[i], x[i + 1]], [y_late[i], y_late[i + 1]],
                    color=seg_color, linewidth=1.8, zorder=4)


def _std_legend(ax, ref_color, extra=None):
    elements = [
        Line2D([0], [0], color=COLOR_HILL_LINE, linewidth=1.2, linestyle=":",
               label="Ground surface"),
        Line2D([0], [0], color=ref_color, linewidth=1.5, linestyle="--",
               label=DATE_LABELS[0]),
        Line2D([0], [0], color=COLOR_GROWTH, linewidth=1.8,
               label=f"{DATE_LABELS[1]} (up)"),
        Line2D([0], [0], color=COLOR_LOSS, linewidth=1.8,
               label=f"{DATE_LABELS[1]} (down)"),
        Line2D([0], [0], color=COLOR_NEUTRAL, linewidth=1.8, marker="o", markersize=5,
               label=f"{DATE_LABELS[1]} (no prior measurement)"),
    ]
    if extra:
        elements.append(extra)
    ax.legend(handles=elements, fontsize=6.5, loc="upper left")


# ── Col 0: absolute elevation ─────────────────────────────────────────────────

def plot_absolute(tbl, elevations, site_name, ax, ref_color, y_min=None):
    pins = [p for p in tbl.index if p in elevations.index]
    x = list(range(len(pins)))
    ground   = [elevations[p] for p in pins]
    h_early  = [tbl.loc[p, DATE_LABELS[0]] for p in pins]
    h_late   = [tbl.loc[p, DATE_LABELS[1]] for p in pins]
    tip_early = [g - h / 1000 if pd.notna(h) else None for g, h in zip(ground, h_early)]
    tip_late  = [g - h / 1000 if pd.notna(h) else None for g, h in zip(ground, h_late)]

    ax.plot(x, ground, color=COLOR_HILL_LINE, linewidth=1.2, linestyle=":", zorder=2)
    ax.fill_between(x, min(ground) - 0.5, ground, color=COLOR_HILL_FILL, alpha=0.25, zorder=1)
    ax.plot(x, tip_early, color=ref_color, linewidth=1.5, linestyle="--", zorder=3)
    ax.scatter(x, tip_early, color=ref_color, s=50, zorder=4)
    _draw_late_line(ax, x, tip_late, tip_early)

    ax.set_ylim(bottom=y_min if y_min is not None else min(ground) - 0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Pin")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(f"{site_name}\nAbsolute elevation", fontsize=10, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)
    _std_legend(ax, ref_color)


# ── Col 1: raw pin height (mm) ────────────────────────────────────────────────

def plot_pin_height(tbl, site_name, ax, ref_color):
    pins = list(tbl.index)
    x = list(range(len(pins)))
    h_early = [tbl.loc[p, DATE_LABELS[0]] for p in pins]
    h_late  = [tbl.loc[p, DATE_LABELS[1]] for p in pins]

    ax.axhline(0, color=COLOR_HILL_LINE, linewidth=1.2, linestyle=":", zorder=2,
               label="Ground surface (y=0)")
    ax.fill_between(x, min(v for v in h_early if pd.notna(v)) * -0.05, 0,
                    color=COLOR_HILL_FILL, alpha=0.25, zorder=1)

    ax.plot(x, h_early, color=ref_color, linewidth=1.5, linestyle="--", zorder=3)
    ax.scatter(x, h_early, color=ref_color, s=50, zorder=4)
    _draw_late_line(ax, x, h_late, h_early, invert_color=True)

    ax.set_xticks(x)
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Pin")
    ax.set_ylabel("Pin height above ground (mm)")
    ax.set_title(f"{site_name}\nPin height (mm)", fontsize=10, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)
    _std_legend(ax, ref_color)


# ── Col 2: 100× exaggerated differences ──────────────────────────────────────

def plot_exaggerated(tbl, elevations, site_name, ax, ref_color, y_min=None):
    """Oct 25 2025 line at true elevation. Apr 18 2026 deviations exaggerated."""
    pins = [p for p in tbl.index if p in elevations.index]
    x = list(range(len(pins)))
    ground   = [elevations[p] for p in pins]
    h_early  = [tbl.loc[p, DATE_LABELS[0]] for p in pins]
    h_late   = [tbl.loc[p, DATE_LABELS[1]] for p in pins]

    tip_early = [g - h / 1000 if pd.notna(h) else None for g, h in zip(ground, h_early)]
    # Comparison tip: reference tip, minus mm deviation scaled for visibility
    tip_late_exag = []
    for te, hl in zip(tip_early, h_late):
        if te is None or not pd.notna(hl):
            tip_late_exag.append(None)
        else:
            idx = tip_early.index(te)
            he = h_early[idx]
            if pd.notna(he):
                tip_late_exag.append(te - (hl - he) * EXAGGERATION_FACTOR / 100)
            else:
                tip_late_exag.append(None)

    ax.plot(x, ground, color=COLOR_HILL_LINE, linewidth=1.2, linestyle=":", zorder=2)
    ax.fill_between(x, min(ground) - 0.5, ground, color=COLOR_HILL_FILL, alpha=0.25, zorder=1)
    ax.plot(x, tip_early, color=ref_color, linewidth=1.5, linestyle="--", zorder=3)
    ax.scatter(x, tip_early, color=ref_color, s=50, zorder=4)
    _draw_late_line(ax, x, tip_late_exag, tip_early)

    all_vals = [v for v in tip_early + tip_late_exag if v is not None]
    ax.set_ylim(bottom=y_min if y_min is not None else min(ground) - 0.5,
                top=max(all_vals) + 0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Pin")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(f"{site_name}\n{EXAGGERATION_FACTOR * 10}× exaggeration",
                 fontsize=10, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)
    exag_note = Line2D([0], [0], color="none",
                       label=f"⚠ ×{EXAGGERATION_FACTOR} (factor) × 10 (mm→cm)\n   = ×{EXAGGERATION_FACTOR * 10} total exaggeration")
    _std_legend(ax, ref_color, extra=exag_note)


# ── Col 3: summary table ──────────────────────────────────────────────────────

def render_table(tbl, site_name, ax):
    ax.axis("off")
    cell_text = []
    for _, row in tbl.iterrows():
        cell_text.append([
            f"{row[DATE_LABELS[0]]:.2f}" if pd.notna(row[DATE_LABELS[0]]) else "—",
            f"{row[DATE_LABELS[1]]:.2f}" if pd.notna(row[DATE_LABELS[1]]) else "—",
            f"{row['Delta (mm)']:+.2f}"  if pd.notna(row["Delta (mm)"])   else "—",
        ])
    col_labels = [DATE_LABELS[0], DATE_LABELS[1], "Delta (mm)"]
    table = ax.table(
        cellText=cell_text, rowLabels=list(tbl.index),
        colLabels=col_labels, loc="center", cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    for i, row in enumerate(tbl.itertuples()):
        delta = row._3
        if pd.notna(delta):
            color = COLOR_TABLE_GROWTH if delta > 0 else COLOR_TABLE_LOSS if delta < 0 else COLOR_TABLE_NEUTRAL
            table[i + 1, 2].set_facecolor(color)
    for j in range(len(col_labels)):
        table[0, j].set_text_props(fontweight="bold")
        table[0, j].set_facecolor(COLOR_TABLE_HEADER)
    ax.set_title(f"{site_name} — summary", fontsize=10, fontweight="bold")


# ── layout ────────────────────────────────────────────────────────────────────

fig, axes = plt.subplots(
    2, 4, figsize=(22, 9),
    gridspec_kw={"width_ratios": [1.2, 1.0, 1.2, 0.8]},
    constrained_layout=True,
)

for row_axes, (site_name, paths) in zip(axes, SITES.items()):
    ax_abs, ax_cm, ax_exag, ax_tbl = row_axes
    df         = load_site(paths["pins"])
    elevations = load_elevations(paths["landscape"])
    tbl        = build_table(df)
    ref_color  = site_date_color(paths["pins"])
    y_min      = paths.get("y_min")
    plot_absolute(tbl, elevations, site_name, ax_abs, ref_color, y_min=y_min)
    plot_pin_height(tbl, site_name, ax_cm, ref_color)
    plot_exaggerated(tbl, elevations, site_name, ax_exag, ref_color, y_min=y_min)
    render_table(tbl, site_name, ax_tbl)

fig.suptitle("Erosion Pin Heights: Oct 2025 vs Apr 2026 — Profile Comparison", fontsize=14, fontweight="bold")

out_dir = script_output_dir(__file__)
fig.savefig(out_dir / "pin_heights_comparison.png", dpi=150, bbox_inches="tight")
print(f"Sheet saved to {out_dir / 'pin_heights_comparison.png'}")

for row_axes, (site_name, _) in zip(axes, SITES.items()):
    ax_abs, ax_cm, ax_exag, ax_tbl = row_axes
    slug = site_name.lower().replace(" ", "_")
    save_ax(fig, ax_abs,  out_dir / f"{slug}_absolute_elevation.png")
    save_ax(fig, ax_cm,   out_dir / f"{slug}_pin_height_mm.png")
    save_ax(fig, ax_exag, out_dir / f"{slug}_exaggerated.png")
    save_ax(fig, ax_tbl,  out_dir / f"{slug}_summary_table.png")

plt.show()
