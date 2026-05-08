"""
Erosion Pin Change: 2026-04-09 vs 2026-04-18
Computes the difference in mean pin height between the two most recent
field visits for both Capps Crossing and Sly Park sites.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent

DATE_A = pd.Timestamp("2026-04-09")
DATE_B = pd.Timestamp("2026-04-18")

SITES = {
    "Capps Crossing": ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx",
    "Sly Park":       ROOT / "raw" / "sly_park_erosion_pins_compiled.xlsx",
}


def load_site(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df["Date_measured"] = pd.to_datetime(df["Date_measured"])
    return df


def pin_change(df: pd.DataFrame, date_a: pd.Timestamp, date_b: pd.Timestamp) -> pd.DataFrame:
    a = df[df["Date_measured"] == date_a][["Pin_number", "pin_height_mean_cm"]].rename(
        columns={"pin_height_mean_cm": f"mean_cm_{date_a.strftime('%Y-%m-%d')}"}
    )
    b = df[df["Date_measured"] == date_b][["Pin_number", "pin_height_mean_cm"]].rename(
        columns={"pin_height_mean_cm": f"mean_cm_{date_b.strftime('%Y-%m-%d')}"}
    )
    merged = a.merge(b, on="Pin_number")
    col_a = f"mean_cm_{date_a.strftime('%Y-%m-%d')}"
    col_b = f"mean_cm_{date_b.strftime('%Y-%m-%d')}"
    merged["change_cm"] = merged[col_b] - merged[col_a]
    interval_days = (date_b - date_a).days
    merged["rate_cm_per_day"] = merged["change_cm"] / interval_days
    return merged


results = {}
for site, path in SITES.items():
    df = load_site(path)
    results[site] = pin_change(df, DATE_A, DATE_B)

# --- Print ---
interval_days = (DATE_B - DATE_A).days
print(f"Erosion pin change: {DATE_A.date()} to {DATE_B.date()} ({interval_days} days)\n")

for site, tbl in results.items():
    print(f"=== {site} ===")
    print(tbl.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print()

# --- Save ---
output_csv = ROOT / "processed" / "erosion_pin_change_apr2026.csv"
combined = pd.concat(
    [tbl.assign(site=site) for site, tbl in results.items()],
    ignore_index=True,
)
col_order = ["site", "Pin_number"] + [c for c in combined.columns if c not in ("site", "Pin_number")]
combined[col_order].to_csv(output_csv, index=False)
print(f"Results saved to {output_csv}")
