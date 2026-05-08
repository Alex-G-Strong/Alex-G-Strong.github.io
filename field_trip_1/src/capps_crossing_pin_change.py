"""
Capps Crossing Erosion Pin Analysis
Computes change in pin height over time from compiled measurements.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent
INPUT_FILE = ROOT / "raw" / "Capps_Crossing_Erosion_pins_Compiled.xlsx"

df = pd.read_excel(INPUT_FILE)

df["Date_measured"] = pd.to_datetime(df["Date_measured"])
df = df.sort_values(["Pin_number", "Date_measured"]).reset_index(drop=True)

# --- Change from baseline (first measurement per pin) ---
baseline = (
    df.groupby("Pin_number", sort=False)
    .first()
    .reset_index()[["Pin_number", "Date_measured", "pin_height_mean_cm"]]
    .rename(columns={"Date_measured": "baseline_date", "pin_height_mean_cm": "baseline_mean_cm"})
)

df = df.merge(baseline, on="Pin_number")
df["change_from_baseline_cm"] = df["pin_height_mean_cm"] - df["baseline_mean_cm"]
df["days_since_baseline"] = (df["Date_measured"] - df["baseline_date"]).dt.days
df["erosion_rate_cm_per_day"] = df.apply(
    lambda r: r["change_from_baseline_cm"] / r["days_since_baseline"]
    if r["days_since_baseline"] > 0 else None,
    axis=1,
)

# --- Change between consecutive measurements per pin ---
df["prev_date"] = df.groupby("Pin_number")["Date_measured"].shift(1)
df["prev_mean_cm"] = df.groupby("Pin_number")["pin_height_mean_cm"].shift(1)
df["interval_change_cm"] = df["pin_height_mean_cm"] - df["prev_mean_cm"]
df["interval_days"] = (df["Date_measured"] - df["prev_date"]).dt.days
df["interval_rate_cm_per_day"] = df["interval_change_cm"] / df["interval_days"]

# Helper: get last two measurements per pin
def get_last_two_pin_heights(df, pin=None, subtract_pins=None):
    """Return a DataFrame with the last and previous measurement for each pin.

    Columns: Pin_number, last_date, last_mean_cm, prev_date, prev_mean_cm,
    interval_change_cm, interval_days, interval_rate_cm_per_day
    If `pin` is provided, return only that pin's row.
    """
    grouped = df.sort_values(["Pin_number", "Date_measured"]).groupby("Pin_number")

    def last_two(series):
        if len(series) == 0:
            return None
        last = series.iloc[-1]
        prev = series.iloc[-2] if len(series) >= 2 else None
        last_date = last["Date_measured"]
        last_mean = last["pin_height_mean_cm"]
        if prev is None:
            return pd.Series({
                "last_date": last_date,
                "last_mean_cm": last_mean,
                "prev_date": pd.NaT,
                "prev_mean_cm": None,
                "interval_change_cm": None,
                "interval_days": None,
                "interval_rate_cm_per_day": None,
            })
        prev_date = prev["Date_measured"]
        prev_mean = prev["pin_height_mean_cm"]
        days = (last_date - prev_date).days
        rate = (last_mean - prev_mean) / days if days and days > 0 else None
        return pd.Series({
            "last_date": last_date,
            "last_mean_cm": last_mean,
            "prev_date": prev_date,
            "prev_mean_cm": prev_mean,
            "interval_change_cm": last_mean - prev_mean,
            "interval_days": days,
            "interval_rate_cm_per_day": rate,
        })

    out = grouped.apply(lambda g: last_two(g)).reset_index()
    if pin is not None:
        out = out[out["Pin_number"] == pin]

    # If subtract_pins is provided, return a single-row DataFrame with the
    # last/prev values for each pin and their difference (pin_a - pin_b).
    if subtract_pins is not None:
        if not (isinstance(subtract_pins, (list, tuple)) and len(subtract_pins) == 2):
            raise ValueError("subtract_pins must be a (pin_a, pin_b) tuple of length 2")
        pin_a, pin_b = subtract_pins
        if pin_a not in out["Pin_number"].values or pin_b not in out["Pin_number"].values:
            raise KeyError(f"One or both pins not found: {pin_a}, {pin_b}")

        ra = out[out["Pin_number"] == pin_a].iloc[0]
        rb = out[out["Pin_number"] == pin_b].iloc[0]

        prev_diff = None
        if pd.notnull(ra.get("prev_mean_cm")) and pd.notnull(rb.get("prev_mean_cm")):
            prev_diff = ra.get("prev_mean_cm") - rb.get("prev_mean_cm")

        result = pd.DataFrame([
            {
                "pin_a": pin_a,
                "pin_b": pin_b,
                "last_date_a": ra.get("last_date"),
                "last_mean_a": ra.get("last_mean_cm"),
                "prev_date_a": ra.get("prev_date"),
                "prev_mean_a": ra.get("prev_mean_cm"),
                "last_date_b": rb.get("last_date"),
                "last_mean_b": rb.get("last_mean_cm"),
                "prev_date_b": rb.get("prev_date"),
                "prev_mean_b": rb.get("prev_mean_cm"),
                "last_diff_cm": ra.get("last_mean_cm") - rb.get("last_mean_cm"),
                "prev_diff_cm": prev_diff,
            }
        ])
        return result

    return out

# --- Print summary ---
cols_display = [
    "Pin_number",
    "Date_measured",
    "pin_height_mean_cm",
    "change_from_baseline_cm",
    "days_since_baseline",
    "erosion_rate_cm_per_day",
    "interval_change_cm",
    "interval_days",
    "interval_rate_cm_per_day",
]

print("=== Capps Crossing Erosion Pin Height Change ===\n")
for pin, group in df.groupby("Pin_number"):
    print(f"--- {pin} (baseline: {group['baseline_date'].iloc[0].date()}, "
          f"height: {group['baseline_mean_cm'].iloc[0]:.3f} cm) ---")
    print(
        group[cols_display]
        .to_string(index=False, float_format=lambda x: f"{x:.3f}")
    )
    print()

# --- Save to CSV ---
output_csv = ROOT / "processed" / "capps_crossing_pin_change.csv"
df[cols_display].to_csv(output_csv, index=False)
print(f"Results saved to {output_csv}")

# --- Last-two measurements summary ---
last_two = get_last_two_pin_heights(df)
print("\n=== Last-two Measurements Per Pin ===")
last_two_print = last_two.copy()
last_two_print["last_date"] = last_two_print["last_date"].dt.strftime("%Y-%m-%d")
last_two_print["prev_date"] = last_two_print["prev_date"].dt.strftime("%Y-%m-%d").fillna("")
print(last_two_print.to_string(index=False, float_format=lambda v: f"{v:.3f}" if pd.notnull(v) else ""))

# --- Per-pin overall summary ---
print("\n=== Overall Change Summary (baseline to most recent) ===")
summary = df.groupby("Pin_number").last()[
    ["baseline_mean_cm", "pin_height_mean_cm", "change_from_baseline_cm",
     "days_since_baseline", "erosion_rate_cm_per_day"]
].rename(columns={
    "baseline_mean_cm": "first_mean_cm",
    "pin_height_mean_cm": "last_mean_cm",
    "change_from_baseline_cm": "total_change_cm",
    "days_since_baseline": "total_days",
    "erosion_rate_cm_per_day": "mean_rate_cm_per_day",
})
print(summary.to_string(float_format=lambda x: f"{x:.4f}"))
