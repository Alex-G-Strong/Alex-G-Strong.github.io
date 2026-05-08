"""
Soil production function for the Andesite Ridge transect.
P = P₀ · e^(-h/h*)
  P₀ = 36 m Myr⁻¹  (maximum production rate)
  h* = 0.5 m        (e-folding depth scale)
Y axis (log scale): soil production rate P (m Myr⁻¹)
X axis: soil thickness (cm)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from parameters import ROOT, POST_DIR, script_output_dir, save_ax

DATA_PATH = ROOT / "raw" / "andesite_ridge_soil_thickness_curvature.xlsx"

P0     = 36.0   # maximum soil production rate (m Myr⁻¹)
H_STAR = 0.5    # e-folding depth scale (m)

# ── data ──────────────────────────────────────────────────────────────────────

df = pd.read_excel(DATA_PATH).dropna(subset=["elevation_m", "soil_thickness_cm"])
df["h_m"]     = df["soil_thickness_cm"] / 100
df["P_m_myr"] = P0 * np.exp(-df["h_m"] / H_STAR)

# ── plot ───────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(7, 6))

# Smooth model curve
h_range = np.linspace(0, df["h_m"].max() * 1.1, 300)
ax.plot(h_range * 100, P0 * np.exp(-h_range / H_STAR),
        color="#888888", linewidth=1.5, linestyle="--",
        label=f"P = {P0:.0f} · e$^{{-h/{H_STAR}}}$")

# Measured samples
ax.scatter(df["soil_thickness_cm"], df["P_m_myr"],
           color="#2c7bb6", edgecolors="white", linewidths=0.6,
           s=65, zorder=3, label="Measurements")

ax.set_yscale("log")
ax.set_xlabel("Soil thickness (cm)", fontsize=12)
ax.set_ylabel("Soil production P (m Myr⁻¹)", fontsize=12)
ax.set_title(
    f"Soil Production Function\n(P₀ = {P0:.0f} m Myr⁻¹, h* = {H_STAR} m)",
    fontsize=13, fontweight="bold",
)
ax.legend(fontsize=10)
ax.grid(True, linestyle=":", alpha=0.4, which="both")
ax.tick_params(labelsize=10)

plt.tight_layout()

out_dir = script_output_dir(__file__)
fig.savefig(out_dir / "soil_production.png", dpi=150, bbox_inches="tight")
save_ax(fig, ax, out_dir / "soil_production_panel.png")
save_ax(fig, ax, POST_DIR / "soil_production.png")
print(f"Saved to {out_dir / 'soil_production.png'}")

plt.show()
