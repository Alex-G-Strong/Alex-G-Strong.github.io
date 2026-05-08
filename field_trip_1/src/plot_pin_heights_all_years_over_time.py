"""
Per-pin time-series: pin height (mm) vs date, one panel per pin.
Pin 1 is top-left, last pin is bottom-right.
Points coloured by date (plasma colormap, oldest→newest).
Connecting lines are dark grey.
Outputs two PNGs to processed/.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

from parameters import ROOT, date_colors_hex, COLOR_GREY_LINE, script_output_dir, save_ax

SITES = {
    "Capps Crossing": {
        "pins":   ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx",
        "layout": (2, 3),
        "output": ROOT / "processed" / "pin_heights_all_years_over_time_capps_crossing.png",
    },
    "Sly Park": {
        "pins":   ROOT / "raw" / "sly_park_erosion_pins_compiled.xlsx",
        "layout": (2, 5),
        "output": ROOT / "processed" / "pin_heights_all_years_over_time_sly_park.png",
    },
}


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
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    return pivot


_date_colors = date_colors_hex


for site_name, cfg in SITES.items():
    df    = load_all(cfg["pins"])
    pivot = build_pivot(df)
    pins  = list(pivot.index)
    dates = list(pivot.columns)
    colors = _date_colors(len(dates))

    nrows, ncols = cfg["layout"]
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(ncols * 3.5 + 1.4, nrows * 3.2),
        constrained_layout=False,
        sharey=False,
    )
    fig.subplots_adjust(left=0.18, right=0.97, top=0.90, bottom=0.12,
                        hspace=0.55, wspace=0.45)
    axes_flat = axes.flatten()

    x_min = min(dates) - pd.Timedelta(days=60)
    x_max = max(dates) + pd.Timedelta(days=60)

    for i, pin in enumerate(pins):
        ax = axes_flat[i]

        valid = [(d, pivot.loc[pin, d]) for d in dates if pd.notna(pivot.loc[pin, d])]
        if not valid:
            ax.set_visible(False)
            continue

        v_dates, v_heights = zip(*valid)

        # Dark grey connecting line
        ax.plot(v_dates, v_heights, color=COLOR_GREY_LINE, linewidth=1.2, zorder=2)

        # Coloured dot per date
        for d, h, c in zip(dates, [pivot.loc[pin, d] for d in dates], colors):
            if pd.notna(h):
                ax.scatter(d, h, color=c, s=55, zorder=3)

        ax.set_title(pin, fontsize=10, fontweight="bold")
        ax.set_ylabel("Pin height (mm)", fontsize=8)
        ax.set_xlim(x_min, x_max)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=5))
        ax.tick_params(axis="x", rotation=40, labelsize=7)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(True, linestyle=":", alpha=0.4)

    # Hide unused panels
    for j in range(len(pins), len(axes_flat)):
        axes_flat[j].set_visible(False)

    # Shared legend for date colours
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=c,
               markersize=7, label=d.strftime("%b %d, '%y"))
        for d, c in zip(dates, colors)
    ]
    fig.legend(handles=legend_elements, title="Date", fontsize=7, title_fontsize=8,
               loc="center left", bbox_to_anchor=(0.01, 0.5),
               bbox_transform=fig.transFigure, framealpha=0.9)

    fig.suptitle(f"{site_name} — Pin Heights Over Time", fontsize=13, fontweight="bold")

    out_dir = script_output_dir(__file__)
    sheet_name = cfg["output"].name
    fig.savefig(out_dir / sheet_name, dpi=150, bbox_inches="tight")
    print(f"Sheet saved to {out_dir / sheet_name}")

    slug = site_name.lower().replace(" ", "_")
    for i, pin in enumerate(pins):
        ax = axes_flat[i]
        if ax.get_visible():
            pin_slug = pin.lower().replace(" ", "_")
            save_ax(fig, ax, out_dir / f"{slug}_{pin_slug}.png")

    plt.close(fig)
