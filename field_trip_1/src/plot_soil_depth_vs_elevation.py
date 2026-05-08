"""
Scatter plot of soil thickness (cm) vs. elevation (m) for the Andesite Ridge transect.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from parameters import ROOT, POST_DIR, script_output_dir, save_ax

DATA_PATH = ROOT / "raw" / "andesite_ridge_soil_thickness_curvature.xlsx"

df = pd.read_excel(DATA_PATH).dropna(subset=["elevation_m", "soil_thickness_cm"])
df["label"] = df["sample_name"].str.replace("andesite_", "", regex=False)

fig, ax = plt.subplots(figsize=(8, 6))

ax.scatter(df["elevation_m"], df["soil_thickness_cm"],
           color="#2c7bb6", edgecolors="white", linewidths=0.6,
           s=70, zorder=3)

for _, row in df.iterrows():
    ax.annotate(row["label"],
                xy=(row["elevation_m"], row["soil_thickness_cm"]),
                xytext=(4, 3), textcoords="offset points",
                fontsize=7, color="#333333")

# Linear fit excluding the two lowest-elevation points
upper_df = df.nlargest(len(df) - 2, "elevation_m")
m1, b1 = np.polyfit(upper_df["elevation_m"], upper_df["soil_thickness_cm"], 1)
x1 = np.linspace(upper_df["elevation_m"].min(), upper_df["elevation_m"].max(), 200)
ax.plot(x1, m1 * x1 + b1, color="#28a745", linewidth=1.8, linestyle="--", zorder=4, alpha=0.5,
        label=f"Upper fit (excl. 2 lowest)\n y = {m1:.2f}x + {b1:.1f}")

# Linear fit for the two lowest-elevation points only
lower_df = df.nsmallest(2, "elevation_m")
m2, b2 = np.polyfit(lower_df["elevation_m"], lower_df["soil_thickness_cm"], 1)
st18_elev = df.loc[df["label"] == "ST18", "elevation_m"].iloc[0]
x2 = np.linspace(lower_df["elevation_m"].min() - 4, st18_elev, 200)
ax.plot(x2, m2 * x2 + b2, color="#e07c2a", linewidth=1.8, linestyle="--", zorder=4, alpha=0.5,
        label=f"Lower fit (2 lowest)\n y = {m2:.2f}x + {b2:.1f}")

ax.legend(fontsize=9, loc="upper right")

ax.set_xlabel("Elevation (m)", fontsize=12)
ax.set_ylabel("Soil thickness (cm)", fontsize=12)
ax.set_title("Andesite Ridge — Soil Thickness vs. Elevation",
             fontsize=13, fontweight="bold")
ax.invert_xaxis()
ax.grid(True, linestyle=":", alpha=0.4)
ax.tick_params(labelsize=10)

plt.tight_layout()

out_dir = script_output_dir(__file__)
fig.savefig(out_dir / "soil_depth_vs_elevation.png", dpi=150, bbox_inches="tight")
save_ax(fig, ax, out_dir / "soil_depth_vs_elevation_panel.png")
save_ax(fig, ax, POST_DIR / "soil_depth_vs_elevation.png")
print(f"Saved to {out_dir / 'soil_depth_vs_elevation.png'}")

plt.show()
