"""
Scatter plots of erosion pin heights over time for Capps Crossing and Sly Park.
Outputs one PNG per site to processed/.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).parent.parent

SITES = {
    "Capps Crossing": ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx",
    "Sly Park":       ROOT / "raw" / "sly_park_erosion_pins_compiled.xlsx",
}


def load_site(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    return df


def plot_site(df: pd.DataFrame, site_name: str, ax: plt.Axes) -> None:
    pins = sorted(df["Pin_number"].unique(), key=lambda p: int(p.split()[-1]))
    colors = plt.cm.tab10.colors

    for i, pin in enumerate(pins):
        subset = df[df["Pin_number"] == pin].sort_values("Date_measured")
        color = colors[i % len(colors)]
        ax.plot(
            subset["Date_measured"],
            subset["pin_height_mean_cm"],
            color=color,
            linewidth=0.8,
            linestyle="--",
            alpha=0.5,
        )
        ax.scatter(
            subset["Date_measured"],
            subset["pin_height_mean_cm"],
            label=pin,
            color=color,
            s=60,
            zorder=3,
        )

    ax.set_title(site_name, fontsize=13, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Mean pin height (cm)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.tick_params(axis="x", rotation=30)
    ax.legend(title="Pin", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    ax.grid(True, linestyle=":", alpha=0.4)


fig, axes = plt.subplots(2, 1, figsize=(11, 10), constrained_layout=True)

for ax, (site_name, path) in zip(axes, SITES.items()):
    df = load_site(path)
    plot_site(df, site_name, ax)

fig.suptitle("Erosion Pin Heights Over Time", fontsize=15, fontweight="bold", y=1.01)

output = ROOT / "processed" / "pin_heights_over_time.png"
fig.savefig(output, dpi=150, bbox_inches="tight")
print(f"Plot saved to {output}")
plt.show()
