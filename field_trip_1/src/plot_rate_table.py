"""
Graphic table of pin height change rate (mm/day) for both sites.
Rows = pins, columns = measurement intervals.
Seven discrete colour bins on a red–white–green diverging scale centred at 0.
Rate values are printed in each cell.
Capps Crossing (left) · Sly Park (right).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch

from parameters import ROOT, POST_DIR, COLOR_GROWTH, COLOR_LOSS, script_output_dir, save_ax

CSVS = {
    "Capps Crossing": ROOT / "processed" / "capps_crossing_height_change_rate_mm_per_day.csv",
    "Sly Park":       ROOT / "processed" / "sly_park_height_change_rate_mm_per_day.csv",
}

# ── discrete colour bins (mm/day) ─────────────────────────────────────────────
BOUNDS = [-3.0, -0.50, -0.10, -0.02, 0.02, 0.10, 0.50, 3.0]
# Negative rate = pin getting shorter = surface gaining material = GROWTH (green)
# Positive rate = pin getting longer = surface losing material = LOSS (red)
BIN_LABELS = [
    "< −0.50  strong growth",
    "−0.50 to −0.10  moderate growth",
    "−0.10 to −0.02  slow growth",
    "−0.02 to +0.02  stable",
    "+0.02 to +0.10  slow loss",
    "+0.10 to +0.50  moderate loss",
    "> +0.50  strong loss",
]
BIN_COLORS = [
    "#145228",    # dark green  – strong growth
    COLOR_GROWTH, # green       – moderate growth
    "#a8d9b8",    # light green – slow growth
    "#ebebeb",    # light grey  – stable
    "#f4b8be",    # light red   – slow loss
    COLOR_LOSS,   # red         – moderate loss
    "#7b0d13",    # dark red    – strong loss
]
NAN_COLOR = "#f7f7f7"


def _txt_color(hex_color: str) -> str:
    r, g, b = mcolors.to_rgb(hex_color)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return "white" if lum < 0.55 else "#222222"


TXT_COLORS = [_txt_color(c) for c in BIN_COLORS]


def _bin_idx(val: float) -> int:
    for k in range(len(BOUNDS) - 1):
        if val < BOUNDS[k + 1]:
            return k
    return len(BOUNDS) - 2


def draw_table(ax: plt.Axes, df: pd.DataFrame, site_name: str) -> None:
    """Draw df with rows=pins, columns=intervals."""
    n_rows, n_cols = df.shape
    data = df.values.astype(float)

    for r in range(n_rows):
        for c in range(n_cols):
            val = data[r, c]
            if np.isnan(val):
                fc, txt, tc = NAN_COLOR, "—", "#888888"
            else:
                b   = _bin_idx(val)
                fc  = BIN_COLORS[b]
                txt = f"{val:+.3f}"
                tc  = TXT_COLORS[b]

            ax.add_patch(plt.Rectangle(
                (c - 0.5, r - 0.5), 1, 1,
                facecolor=fc, edgecolor="white", linewidth=1.2,
            ))
            ax.text(c, r, txt, ha="center", va="center",
                    fontsize=10, color=tc, fontweight="bold")

    ax.set_xlim(-0.5, n_cols - 0.5)
    ax.set_ylim(n_rows - 0.5, -0.5)   # Pin 1 at top

    # x-axis: interval labels at bottom, rotated
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(df.columns, rotation=40, ha="right", fontsize=10)
    ax.tick_params(axis="x", which="both", length=0, pad=3)

    # y-axis: pin names on left
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(df.index, fontsize=11)
    ax.tick_params(axis="y", which="both", length=0, pad=4)

    ax.set_title(site_name, fontsize=13, fontweight="bold", pad=10)

    for spine in ax.spines.values():
        spine.set_visible(False)


# ── load (pins = rows, intervals = columns) ───────────────────────────────────

tables = {site: pd.read_csv(path, index_col="Pin") for site, path in CSVS.items()}

site_list  = list(tables.items())
n_capps    = site_list[0][1].shape[1]   # 7 intervals
n_slypark  = site_list[1][1].shape[1]   # 6 intervals

# Width proportional to interval count; height generous for 10-pin Sly Park rows
fig, axes = plt.subplots(
    1, 2,
    figsize=(13, 5),
    gridspec_kw={"width_ratios": [n_capps, n_slypark], "wspace": 0.18},
    constrained_layout=False,
)
fig.subplots_adjust(left=0.10, right=0.97, top=0.90, bottom=0.30, wspace=0.18)

for ax, (site_name, df) in zip(axes, tables.items()):
    draw_table(ax, df, site_name)

# Shared discrete legend below the figure
legend_patches = [
    Patch(facecolor=c, edgecolor="#cccccc", linewidth=0.8, label=lbl)
    for c, lbl in zip(BIN_COLORS, BIN_LABELS)
]
legend_patches.append(
    Patch(facecolor=NAN_COLOR, edgecolor="#cccccc", linewidth=0.8, label="No data")
)
fig.legend(
    handles=legend_patches,
    title="Rate (mm / day)",
    title_fontsize=9,
    fontsize=8.5,
    loc="lower center",
    ncol=4,
    bbox_to_anchor=(0.5, -0.04),
    framealpha=0.95,
    edgecolor="#cccccc",
)

fig.suptitle(
    "Pin Height Change Rate (mm / day) — consecutive measurement intervals",
    fontsize=13, fontweight="bold",
)

out_dir = script_output_dir(__file__)
fig.savefig(out_dir / "height_change_rate_table.png", dpi=150, bbox_inches="tight")
fig.savefig(POST_DIR / "height_change_rate_table.png", dpi=150, bbox_inches="tight")
print(f"Saved {out_dir / 'height_change_rate_table.png'}")

for ax, (site_name, _) in zip(axes, tables.items()):
    slug = site_name.lower().replace(" ", "_")
    save_ax(fig, ax, out_dir / f"{slug}_rate_table.png")

plt.show()
