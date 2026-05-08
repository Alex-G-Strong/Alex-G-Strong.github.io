"""
April 2026 erosion pin figure with three panels per site:
  Col 0: scatter plot (height vs date, one series per pin)
  Col 1: profile chart (pin height vs actual ground elevation; Apr 09 grey,
          Apr 18 segments coloured green if height rose vs Apr 09, red if fell)
  Col 2: summary table (Apr 09 | Apr 18 | delta)
Outputs one PNG to processed/.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

from parameters import (
    ROOT, POST_DIR,
    COLOR_GROWTH, COLOR_LOSS, COLOR_NEUTRAL,
    COLOR_HILL_FILL, COLOR_HILL_LINE,
    COLOR_TABLE_GROWTH, COLOR_TABLE_LOSS, COLOR_TABLE_NEUTRAL, COLOR_TABLE_HEADER,
    script_output_dir, save_ax,
)

SITES = {
    "Capps Crossing": {
        "pins":       ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx",
        "landscape":  ROOT / "raw" / "capps_crossing_landscape_attributes.xlsx",
    },
    "Sly Park": {
        "pins":       ROOT / "raw" / "sly_park_erosion_pins_compiled.xlsx",
        "landscape":  ROOT / "raw" / "sly_park_landscape_attributes.xlsx",
    },
}

APR_DATES = [pd.Timestamp("2026-04-09"), pd.Timestamp("2026-04-18")]
DATE_LABELS = ["Apr 09, 2026", "Apr 18, 2026"]


def load_site(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    return df[df["Date_measured"].isin(APR_DATES)]


def load_all(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    return df


def build_long_term_change(df: pd.DataFrame) -> pd.DataFrame:
    """First vs last measurement per pin, returning change in cm."""
    df = df.sort_values("Date_measured")
    first = df.groupby("Pin_number")["pin_height_mean_cm"].first()
    last  = df.groupby("Pin_number")["pin_height_mean_cm"].last()
    first_date = df.groupby("Pin_number")["Date_measured"].first()
    last_date  = df.groupby("Pin_number")["Date_measured"].last()
    out = pd.DataFrame({"first_cm": first, "last_cm": last,
                        "first_date": first_date, "last_date": last_date})
    out["change_cm"] = out["last_cm"] - out["first_cm"]
    out.index = pd.Index(out.index, name="Pin_number")
    out = out.sort_index(key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))
    return out


def load_elevations(path: Path) -> pd.Series:
    """Return a Series mapping 'Pin N' -> elevation_m."""
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


def plot_scatter(df: pd.DataFrame, site_name: str, ax: plt.Axes) -> None:
    pins = sorted(df["Pin_number"].unique(), key=lambda p: int(p.split()[-1]))
    colors = plt.cm.tab10.colors

    for i, pin in enumerate(pins):
        subset = df[df["Pin_number"] == pin].sort_values("Date_measured")
        color = colors[i % len(colors)]
        ax.plot(
            subset["Date_measured"], subset["pin_height_mean_cm"],
            color=color, linewidth=0.8, linestyle="--", alpha=0.5,
        )
        ax.scatter(
            subset["Date_measured"], subset["pin_height_mean_cm"],
            label=pin, color=color, s=60, zorder=3,
        )

    ax.set_title(site_name, fontsize=11, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Mean pin height (mm)")
    ax.set_xticks(APR_DATES)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d, %Y"))
    ax.tick_params(axis="x", rotation=15)
    ax.legend(title="Pin", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=7)
    ax.grid(True, linestyle=":", alpha=0.4)


def plot_profile(tbl: pd.DataFrame, elevations: pd.Series,
                 site_name: str, ax: plt.Axes) -> None:
    """Profile chart: pin numbers on x, pin-tip elevation (m) on y.

    y = ground_elevation_m + pin_height_cm / 100.
    Ground surface drawn as a reference. Y-axis starts 0.5 m below the
    lowest pin's ground elevation.
    """
    pins = [p for p in tbl.index if p in elevations.index]
    x = list(range(len(pins)))

    ground  = [elevations[p] for p in pins]
    h_early = [tbl.loc[p, DATE_LABELS[0]] for p in pins]
    h_late  = [tbl.loc[p, DATE_LABELS[1]] for p in pins]

    tip_early = [g - h / 1000 if pd.notna(h) else None for g, h in zip(ground, h_early)]
    tip_late  = [g - h / 1000 if pd.notna(h) else None for g, h in zip(ground, h_late)]

    # --- Ground surface reference ---
    ax.plot(x, ground, color=COLOR_HILL_LINE, linewidth=1.2, linestyle=":", zorder=2,
            label="Ground surface")
    ax.fill_between(x, min(ground) - 0.5, ground, color=COLOR_HILL_FILL, alpha=0.25, zorder=1)

    # --- Apr 09 pin tips (grey) ---
    ax.plot(x, tip_early, color="grey", linewidth=1.5, linestyle="--", zorder=3)
    ax.scatter(x, tip_early, color="grey", s=50, zorder=4)

    # --- Apr 18 pin tips: coloured segments ---
    for i in range(len(pins)):
        if tip_late[i] is None:
            continue
        dot_color = (
            COLOR_GROWTH if tip_late[i] > tip_early[i]
            else COLOR_LOSS if tip_late[i] < tip_early[i]
            else "grey"
        ) if tip_early[i] is not None else "grey"
        ax.scatter(x[i], tip_late[i], color=dot_color, s=50, zorder=5)

        if i < len(pins) - 1 and tip_late[i + 1] is not None:
            seg_color = (
                COLOR_GROWTH if tip_late[i + 1] > tip_early[i + 1]
                else COLOR_LOSS if tip_late[i + 1] < tip_early[i + 1]
                else "grey"
            ) if tip_early[i + 1] is not None else "grey"
            ax.plot([x[i], x[i + 1]], [tip_late[i], tip_late[i + 1]],
                    color=seg_color, linewidth=1.8, zorder=4)

    ax.set_ylim(bottom=min(ground) - 0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)

    legend_elements = [
        Line2D([0], [0], color=COLOR_HILL_LINE, linewidth=1.2, linestyle=":", label="Ground surface"),
        Line2D([0], [0], color="grey",    linewidth=1.5, linestyle="--", label=DATE_LABELS[0]),
        Line2D([0], [0], color=COLOR_GROWTH, linewidth=1.8, label=f"{DATE_LABELS[1]} (up)"),
        Line2D([0], [0], color=COLOR_LOSS, linewidth=1.8, label=f"{DATE_LABELS[1]} (down)"),
        Line2D([0], [0], color="grey",    linewidth=1.8, marker="o", markersize=5,
               label=f"{DATE_LABELS[1]} (no prior measurement)"),
    ]
    ax.legend(handles=legend_elements, fontsize=7, loc="best")
    ax.set_xlabel("Pin")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(f"{site_name} — elevation profile", fontsize=11, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.4)


def plot_long_term_change(tbl: pd.DataFrame, site_name: str, ax: plt.Axes) -> None:
    """Bar chart of pin-height change (cm) between the two April 2026 visits."""
    pins = list(tbl.index)
    x = range(len(pins))
    changes = tbl["Delta (mm)"].values
    colors = [COLOR_LOSS if c > 0 else COLOR_GROWTH if c < 0 else "grey"
              for c in changes]

    ax.bar(x, changes, color=colors, edgecolor="white", linewidth=0.5, zorder=3)
    ax.axhline(0, color="black", linewidth=0.8, zorder=4)

    ax.set_xticks(list(x))
    ax.set_xticklabels(pins, rotation=30, ha="right", fontsize=8)
    ax.set_xlabel("Pin")
    ax.set_ylabel("Elevation change (mm)")
    ax.set_title(f"{site_name} — change\n({DATE_LABELS[0]} to {DATE_LABELS[1]})",
                 fontsize=11, fontweight="bold")
    ax.grid(True, axis="y", linestyle=":", alpha=0.4)


def render_table(tbl: pd.DataFrame, ax: plt.Axes, site_name: str) -> None:
    ax.axis("off")

    cell_text = []
    for _, row in tbl.iterrows():
        cell_text.append([
            f"{row[DATE_LABELS[0]]:.2f}" if pd.notna(row[DATE_LABELS[0]]) else "—",
            f"{row[DATE_LABELS[1]]:.2f}" if pd.notna(row[DATE_LABELS[1]]) else "—",
            f"{row['Delta (mm)']:+.2f}"  if pd.notna(row["Delta (mm)"])   else "—",
        ])

    col_labels = [DATE_LABELS[0], DATE_LABELS[1], "Delta (mm)"]
    row_labels = list(tbl.index)

    table = ax.table(
        cellText=cell_text,
        rowLabels=row_labels,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)

    for i, row in enumerate(tbl.itertuples()):
        delta = row._3
        if pd.notna(delta):
            color = COLOR_TABLE_LOSS if delta > 0 else COLOR_TABLE_GROWTH if delta < 0 else COLOR_TABLE_NEUTRAL
            table[i + 1, 2].set_facecolor(color)

    for j in range(len(col_labels)):
        table[0, j].set_text_props(fontweight="bold")
        table[0, j].set_facecolor(COLOR_TABLE_HEADER)

    ax.set_title(f"{site_name} — summary", fontsize=11, fontweight="bold")


fig, axes = plt.subplots(
    2, 3, figsize=(18, 9),
    gridspec_kw={"width_ratios": [1.4, 0.9, 1.0]},
    constrained_layout=True,
)

for row_axes, (site_name, paths) in zip(axes, SITES.items()):
    ax_profile, ax_table, ax_lt = row_axes
    df         = load_site(paths["pins"])
    elevations = load_elevations(paths["landscape"])
    tbl        = build_table(df)
    plot_profile(tbl, elevations, site_name, ax_profile)
    render_table(tbl, ax_table, site_name)
    plot_long_term_change(tbl, site_name, ax_lt)

fig.suptitle("Erosion Pin Heights: April 2026", fontsize=15, fontweight="bold")

out_dir = script_output_dir(__file__)
fig.savefig(out_dir / "pin_heights_apr2026.png", dpi=150, bbox_inches="tight")
fig.savefig(POST_DIR / "pin_heights_apr2026.png", dpi=150, bbox_inches="tight")
print(f"Sheet saved to {out_dir / 'pin_heights_apr2026.png'}")

for row_axes, (site_name, _) in zip(axes, SITES.items()):
    ax_profile, ax_table, ax_lt = row_axes
    slug = site_name.lower().replace(" ", "_")
    save_ax(fig, ax_profile, out_dir / f"{slug}_elevation_profile.png")
    save_ax(fig, ax_table,   out_dir / f"{slug}_summary_table.png")
    save_ax(fig, ax_lt,      out_dir / f"{slug}_change_bar.png")
plt.show()
