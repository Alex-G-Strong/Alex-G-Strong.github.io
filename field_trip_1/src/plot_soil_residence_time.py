"""
Soil residence time for the Andesite Ridge transect.
τ_res = h / E, where h is soil thickness (m) and E is the long-term
erosion rate for Mehrten andesites (24 m Myr⁻¹).

Figure layout:
  Col 0: summary table  (sample | thickness cm | elevation m | τ_res kyr)
  Col 1: elevation vs τ_res — linear axes
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from parameters import ROOT, POST_DIR, script_output_dir, save_ax

DATA_PATH = ROOT / "raw" / "andesite_ridge_soil_thickness_curvature.xlsx"

E_M_PER_MYR = 24.0   # long-term erosion rate for Mehrten andesites (m Myr⁻¹)
P0          = 36.0   # maximum soil production rate (m Myr⁻¹)
H_STAR      = 0.5    # characteristic depth scale (m)


# ── data ──────────────────────────────────────────────────────────────────────

df = pd.read_excel(DATA_PATH).dropna(subset=["elevation_m", "soil_thickness_cm"])
df["_num"] = df["sample_name"].str.extract(r"(\d+)$")[0].astype(int)
df = df.sort_values("_num").reset_index(drop=True)

df["label"]        = df["sample_name"].str.replace("andesite_", "", regex=False)
df["h_m"]          = df["soil_thickness_cm"] / 100          # cm → m
df["tau_res_kyr"]  = df["h_m"] / E_M_PER_MYR * 1_000       # Myr → kyr
df["P_m_myr"]      = P0 * np.exp(-df["h_m"] / H_STAR)      # soil production rate (m Myr⁻¹)


# ── figure ─────────────────────────────────────────────────────────────────────

fig, (ax_tbl, ax_lin) = plt.subplots(
    1, 2,
    figsize=(13, 7),
    gridspec_kw={"width_ratios": [1.1, 1.3]},
    constrained_layout=True,
)

# ── Col 0: table ──────────────────────────────────────────────────────────────

ax_tbl.axis("off")

col_labels = ["Sample", "Thickness\n(cm)", "Elevation\n(m)", "τ_res\n(kyr)"]
cell_text  = [
    [row["label"],
     f"{row['soil_thickness_cm']}",
     f"{row['elevation_m']:.1f}",
     f"{row['tau_res_kyr']:.2f}"]
    for _, row in df.iterrows()
]

table = ax_tbl.table(
    cellText=cell_text,
    colLabels=col_labels,
    loc="center",
    cellLoc="center",
)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.5)

for j in range(len(col_labels)):
    table[0, j].set_text_props(fontweight="bold")
    table[0, j].set_facecolor("#dee2e6")

ax_tbl.set_title(
    f"Residence time  τ = h / E\n(E = {E_M_PER_MYR:.0f} m Myr⁻¹)",
    fontsize=11, fontweight="bold", pad=20,
)


# ── shared scatter helper ─────────────────────────────────────────────────────

def _scatter(ax, loglog=False):
    ax.scatter(df["elevation_m"], df["tau_res_kyr"],
               color="#2c7bb6", edgecolors="white", linewidths=0.6,
               s=65, zorder=3)
    if loglog:
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.invert_xaxis()   # high elevation on the left
    ax.set_xlabel("Elevation (m)", fontsize=11)
    ax.set_ylabel("Residence time τ_res (kyr)", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.4, which="both")
    ax.tick_params(labelsize=9)


# ── Col 1: linear ─────────────────────────────────────────────────────────────

_scatter(ax_lin, loglog=False)
ax_lin.set_title("Residence time vs. Elevation", fontsize=11, fontweight="bold")


# ── suptitle & save ───────────────────────────────────────────────────────────

fig.suptitle(
    "Andesite Ridge — Soil Residence Time",
    fontsize=14, fontweight="bold",
)

out_dir = script_output_dir(__file__)
fig.savefig(out_dir / "soil_residence_time.png", dpi=150, bbox_inches="tight")
fig.savefig(POST_DIR / "soil_residence_time.png", dpi=150, bbox_inches="tight")
print(f"Saved to {out_dir / 'soil_residence_time.png'}")

for ax, name in [
    (ax_tbl, "residence_table"),
    (ax_lin, "residence_linear"),
]:
    save_ax(fig, ax, out_dir / f"{name}.png")

plt.show()
