"""
Compute pin height change rate (mm/day) between consecutive measurement dates.
Rows = pins, columns = intervals (labelled with end date and duration).
Outputs one CSV per site to processed/.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent

SITES = {
    "capps_crossing": ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx",
    "sly_park":       ROOT / "raw" / "sly_park_erosion_pins_compiled.xlsx",
}

for site_slug, path in SITES.items():
    df = pd.read_excel(path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])

    pivot = df.pivot_table(
        index="Pin_number", columns="Date_measured",
        values="pin_height_mean_cm", aggfunc="first",
    )
    pivot = pivot.sort_index(key=lambda s: s.str.extract(r"(\d+)")[0].astype(int))
    dates = sorted(pivot.columns)

    # Build rate table: one column per interval
    rates = {}
    for i in range(1, len(dates)):
        d0, d1 = dates[i - 1], dates[i]
        days   = (d1 - d0).days
        s0, s1 = d0.strftime("%b %d '%y"), d1.strftime("%b %d '%y")
        label  = f"{s0} to {s1} ({days} d)"
        delta  = pivot[d1] - pivot[d0]
        rates[label] = (delta / days).round(4)

    out = pd.DataFrame(rates, index=pivot.index)
    out.index.name = "Pin"

    csv_path = ROOT / "processed" / f"{site_slug}_height_change_rate_mm_per_day.csv"
    out.to_csv(csv_path)
    print(f"Saved {csv_path}")
    print(out.to_string())
    print()
