"""
2D hillslope profile for the Andesite Ridge soil-thickness transect.

X axis — distance along the best-fit transect line (metres).
         Each sample's (easting, northing) is projected onto the first
         principal component of the point cloud.
Y axis — elevation (m).
Coloured downward bars — soil thickness (cm), scaled ×BAR_SCALE for visibility,
         viridis colormap (matches the 3D plot).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

from parameters import ROOT, POST_DIR, script_output_dir, save_ax

DATA_PATH = ROOT / "raw" / "andesite_ridge_soil_thickness_curvature.xlsx"
BAR_SCALE  = 10   # display bar = actual thickness × BAR_SCALE


# ── data helpers (identical to 3D script) ─────────────────────────────────────

def load_data(path):
    df = pd.read_excel(path)
    df = df.dropna(subset=["latitude", "longitude", "elevation_m", "soil_thickness_cm"])
    df["_num"] = df["sample_name"].str.extract(r"(\d+)$")[0].astype(int)
    return df.sort_values("_num").reset_index(drop=True)


def to_local_m(df):
    lat0 = df["latitude"].mean()
    lon0 = df["longitude"].mean()
    x = (df["longitude"] - lon0) * (111_000 * np.cos(np.radians(lat0)))
    y = (df["latitude"]  - lat0) *  111_000
    return x.values, y.values


def pca_projection(x, y):
    """Project (x, y) onto the first principal component.
    Returns 1-D distance along the transect for each point.
    Orient so that the uphill (high-elevation) end is on the right."""
    xy = np.column_stack([x, y])
    mean = xy.mean(axis=0)
    _, _, Vt = np.linalg.svd(xy - mean, full_matrices=False)
    axis = Vt[0]                          # unit vector along max-variance direction
    proj = (xy - mean) @ axis             # signed scalar projection
    return proj, axis, mean


# ── load & project ─────────────────────────────────────────────────────────────

df    = load_data(DATA_PATH)
x, y  = to_local_m(df)
z     = df["elevation_m"].values
thick = df["soil_thickness_cm"].values
names = df["sample_name"].str.replace("andesite_", "", regex=False).values

proj, axis, mean_xy = pca_projection(x, y)

# Orient: make the higher-elevation end positive
if np.corrcoef(proj, z)[0, 1] < 0:
    proj = -proj

# Per-point viridis colours (normalised to thickness range)
norm_thick  = Normalize(vmin=thick.min(), vmax=thick.max())
viridis     = cm.get_cmap("viridis")
colors      = [viridis(norm_thick(t)) for t in thick]

# Display bar bottoms
z_bot = z - thick * BAR_SCALE / 100      # cm → m, then scale


# ── plot ───────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(14, 6))

# Profile line connecting samples in projection order
order = np.argsort(proj)
ax.plot(proj[order], z[order],
        color="#888888", linewidth=1.2, zorder=2, label="Hillslope profile")

# Coloured downward bars + surface dots
for i in range(len(df)):
    c = colors[i]
    # Bar
    ax.plot([proj[i], proj[i]], [z[i], z_bot[i]],
            color=c, linewidth=5, solid_capstyle="butt", zorder=3)
    # Surface dot (white outline for contrast)
    ax.scatter(proj[i], z[i], color=c, s=60, zorder=5,
               edgecolors="white", linewidths=0.8)

# Sample-name labels above each dot
for i in range(len(df)):
    ax.text(proj[i], z[i] + 0.6, names[i],
            ha="center", va="bottom", fontsize=6.5,
            rotation=70, color="#333333")

# Colorbar
sm   = ScalarMappable(cmap="viridis", norm=norm_thick)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, pad=0.01, fraction=0.025)
cbar.set_label("Soil thickness (cm)", fontsize=10)
cbar.ax.tick_params(labelsize=9)

ax.set_xlabel("Distance along transect (m, projected onto principal axis)", fontsize=11)
ax.set_ylabel("Elevation (m)", fontsize=11)
ax.set_title(
    "Andesite Ridge — Hillslope Profile & Soil Thickness\n"
    f"(bars scaled ×{BAR_SCALE} for visibility; true max = {thick.max()} cm)",
    fontsize=12, fontweight="bold",
)
ax.grid(True, linestyle=":", alpha=0.4)
ax.legend(fontsize=9, loc="upper left")
ax.tick_params(labelsize=10)

plt.tight_layout()

out_dir = script_output_dir(__file__)
fig.savefig(out_dir / "soil_profile_2d.png", dpi=150, bbox_inches="tight")
print(f"Saved {out_dir / 'soil_profile_2d.png'}")

save_ax(fig, ax, out_dir / "soil_profile_2d_panel.png")
save_ax(fig, ax, POST_DIR / "soil_profile_2d_panel.png")

plt.show()
