"""
Bar chart + elevation profile of pin height change from first to last measurement.
Three panels per site:
  Col 0: elevation profile (first measurement grey dashed, last coloured green/red)
  Col 1: bar chart of net change (green = grew, red = shrank)
  Col 2: summary table (first | last | delta)
Outputs one PNG to processed/.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from parameters import (
    ROOT, POST_DIR,
    COLOR_GROWTH, COLOR_LOSS,
    COLOR_HILL_FILL, COLOR_HILL_LINE,
    COLOR_TABLE_GROWTH, COLOR_TABLE_LOSS, COLOR_TABLE_NEUTRAL, COLOR_TABLE_HEADER,
    script_output_dir, save_ax,
)

SITES = {
    "Capps Crossing": {
        "pins":      ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx",
        "landscape": ROOT / "raw" / "capps_crossing_landscape_attributes.xlsx",
    },
    "Sly Park": {
        "pins":      ROOT / "raw" / "sly_park_erosion_pins_compiled.xlsx",
        "landscape": ROOT / "raw" / "sly_park_landscape_attributes.xlsx",
    },
}


def load_all(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    return df


def load_elevations(path: Path) -> pd.Series:
    df = pd.read_excel(path).dropna(subset=["sample_name"])
    df = df[df["sample_name"].str.startswith("pin_")]
    df["Pin_number"] = df["sample_name"].str.replace("pin_", "Pin ", regex=False)
    return df.set_index("Pin_number")["elevation_m"]


def build_first_last(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("Date_measured")
    grp = df.groupby("Pin_number")
    out = pd.DataFrame({
        "first_date":  grp["Date_measured"].first(),
        "last_date":   grp["Date_measured"].last(),
        "first_mm":    grp["pin_height_mean_cm"].first(),
        "last_mm":     grp["pin_height_mean_cm"].last(),
    })
    out["change_mm"] = out["last_mm"] - out["first_mm"]
    out = out.sort_index(key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))
    return out


def plot_profile(tbl: pd.DataFrame, elevations: pd.Series,
                 site_name: str, ax: plt.Axes) -> None:
    pins = [p for p in tbl.index if p in elevations.index]
    x = list(range(len(pins)))

    ground  = [elevations[p] for p in pins]
    h_first = [tbl.loc[p, "first_mm"] for p in pins]
    h_last  = [tbl.loc[p, "last_mm"]  for p in pins]

    tip_first = [g - h / 1000 if pd.notna(h) else None for g, h in zip(ground, h_first)]
    tip_last  = [g - h / 1000 if pd.notna(h) else None for g, h in zip(ground, h_last)]

    first_label = tbl["first_date"].iloc[0].strftime("%b %d, '%y")
    last_label  = tbl["last_date"].iloc[0].strftime("%b %d, '%y")

    # Ground surface
    ax.plot(x, ground, color=COLOR_HILL_LINE, linewidth=1.2, linestyle=":", zorder=2)
    ax.fill_between(x, min(ground) - 0.5, ground, color=COLOR_HILL_FILL, alpha=0.25, zorder=1)

    # First visit — grey dashed reference
    ax.plot(x, tip_first, color="grey", linewidth=1.5, linestyle="--", zorder=3)
    ax.scatter(x, tip_first, color="grey", s=50, zorder=4)

    # Last visit — coloured dots and segments
    for i in range(len(pins)):
        if tip_last[i] is None:
            continue
        dot_color = (
            COLOR_GROWTH if tip_last[i] > tip_first[i]
            else COLOR_LOSS if tip_last[i] < tip_first[i]
            else "grey"
        ) if tip_first[i] is not None else "grey"
        ax.scatter(x[i], tip_last[i], color=dot_color, s=50, zorder=5)

        if i < len(pins) - 1 and tip_last[i + 1] is not None:
            seg_color = (
                COLOR_GROWTH if tip_last[i + 1] > tip_first[i + 1]
                else COLOR_LOSS if tip_last[i + 1] < tip_first[i + 1]
                else "grey"
            ) if tip_first[i + 1] is not None else "grey"
            ax.plot([x[i], x[i + 1]], [tip_last[i], tip_last[i + 1]],
                    color=seg_color, linewidth=1.8, zorder=4)

    ax.set_ylim(bottom=min(ground) - 0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)

    legend_elements = [
        Line2D([0], [0], color=COLOR_HILL_LINE, linewidth=1.2, linestyle=":", label="Ground surface"),
        Line2D([0], [0], color="grey",       linewidth=1.5, linestyle="--", label=first_label),
        Line2D([0], [0], color=COLOR_GROWTH, linewidth=1.8, label=f"{last_label} (grew)"),
        Line2D([0], [0], color=COLOR_LOSS,   linewidth=1.8, label=f"{last_label} (shrank)"),
    ]
    ax.legend(handles=legend_elements, fontsize=7, loc="best")
    ax.set_xlabel("Pin")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(f"{site_name} — elevation profile\n({first_label} → {last_label})",
                 fontsize=11, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)


def plot_bar(tbl: pd.DataFrame, site_name: str, ax: plt.Axes) -> None:
    pins   = list(tbl.index)
    x      = range(len(pins))
    colors = [COLOR_LOSS if c > 0 else COLOR_GROWTH for c in tbl["change_mm"]]

    bars = ax.bar(x, tbl["change_mm"], color=colors, edgecolor="white",
                  linewidth=0.5, zorder=3)
    ax.axhline(0, color="black", linewidth=0.8, zorder=4)

    for bar, val in zip(bars, tbl["change_mm"]):
        ypos = bar.get_height() + (1 if val >= 0 else -3)
        ax.text(bar.get_x() + bar.get_width() / 2, ypos,
                f"{val:+.1f}", ha="center", va="bottom", fontsize=7)

    first_date = tbl["first_date"].iloc[0].strftime("%b %d, '%y")
    last_date  = tbl["last_date"].iloc[0].strftime("%b %d, '%y")

    ax.set_xticks(list(x))
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=9)
    ax.set_xlabel("Pin")
    ax.set_ylabel("Change in pin height (mm)")
    ax.set_title(f"{site_name}\n{first_date} → {last_date}",
                 fontsize=11, fontweight="bold")
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)


def render_table(tbl: pd.DataFrame, site_name: str, ax: plt.Axes) -> None:
    ax.axis("off")

    first_label = tbl["first_date"].iloc[0].strftime("%b %d, '%y")
    last_label  = tbl["last_date"].iloc[0].strftime("%b %d, '%y")

    cell_text = []
    for _, row in tbl.iterrows():
        cell_text.append([
            f"{row['first_mm']:.1f}",
            f"{row['last_mm']:.1f}",
            f"{row['change_mm']:+.1f}",
        ])

    col_labels = [f"{first_label} (mm)", f"{last_label} (mm)", "Change (mm)"]
    table = ax.table(
        cellText=cell_text,
        rowLabels=list(tbl.index),
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)

    for i, row in enumerate(tbl.itertuples()):
        delta = row.change_mm
        color = COLOR_TABLE_LOSS if delta > 0 else COLOR_TABLE_GROWTH if delta < 0 else COLOR_TABLE_NEUTRAL
        table[i + 1, 2].set_facecolor(color)

    for j in range(len(col_labels)):
        table[0, j].set_text_props(fontweight="bold")
        table[0, j].set_facecolor(COLOR_TABLE_HEADER)

    ax.set_title(f"{site_name} — summary", fontsize=11, fontweight="bold")


fig, axes = plt.subplots(
    2, 3, figsize=(20, 9),
    gridspec_kw={"width_ratios": [1.2, 1.4, 0.9]},
    constrained_layout=True,
)

for row_axes, (site_name, paths) in zip(axes, SITES.items()):
    ax_prof, ax_bar, ax_tbl = row_axes
    df         = load_all(paths["pins"])
    elevations = load_elevations(paths["landscape"])
    tbl        = build_first_last(df)
    plot_profile(tbl, elevations, site_name, ax_prof)
    plot_bar(tbl, site_name, ax_bar)
    render_table(tbl, site_name, ax_tbl)

fig.suptitle("Erosion Pin Height Change: First vs. Last Measurement",
             fontsize=14, fontweight="bold")

out_dir = script_output_dir(__file__)
fig.savefig(out_dir / "pin_heights_first_last_change.png", dpi=150, bbox_inches="tight")
fig.savefig(POST_DIR / "pin_heights_first_last_change.png", dpi=150, bbox_inches="tight")
print(f"Sheet saved to {out_dir / 'pin_heights_first_last_change.png'}")

for row_axes, (site_name, _) in zip(axes, SITES.items()):
    ax_prof, ax_bar, ax_tbl = row_axes
    slug = site_name.lower().replace(" ", "_")
    save_ax(fig, ax_prof, out_dir / f"{slug}_elevation_profile.png")
    save_ax(fig, ax_bar,  out_dir / f"{slug}_first_last_bar.png")
    save_ax(fig, ax_tbl,  out_dir / f"{slug}_first_last_table.png")

plt.show()
