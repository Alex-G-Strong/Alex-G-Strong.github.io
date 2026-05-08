"""
Shared parameters for all erosion pin plots.
Edit this file to change settings that apply across all plots.
"""

import re
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.transforms import Bbox as _MplBbox

# ── paths ─────────────────────────────────────────────────────────────────────

ROOT     = Path(__file__).parent.parent
POST_DIR = ROOT / "post_bundle" / "content" / "posts" / "capps-slypark-field-report"

# ── exaggeration ──────────────────────────────────────────────────────────────
# Vertical exaggeration applied to deviations from the first visit.
# Used in: plot_pin_heights_all_years, plot_pin_heights_comparison, plot_3d_surface
# Formula: tip_base + (h_now - h_first) * EXAGGERATION_FACTOR / 100
# The /100 converts mm→m, so 1 cm of change appears as EXAGGERATION_FACTOR cm on
# the elevation axis. Total effective exaggeration = EXAGGERATION_FACTOR × 10.

EXAGGERATION_FACTOR = 30

# ── date colormap ─────────────────────────────────────────────────────────────
# Plasma colormap, oldest date = dark purple, newest = yellow.

COLORMAP      = plt.cm.plasma
COLORMAP_MIN  = 0.05   # value for the oldest date
COLORMAP_MAX  = 0.85   # value for the newest date


def date_colors_rgba(n: int) -> list:
    """Return n RGBA tuples from the date colormap (oldest → newest)."""
    return [COLORMAP(v) for v in np.linspace(COLORMAP_MIN, COLORMAP_MAX, n)]


def date_colors_hex(n: int) -> list:
    """Return n hex colour strings from the date colormap (oldest → newest)."""
    return [mcolors.to_hex(COLORMAP(v)) for v in np.linspace(COLORMAP_MIN, COLORMAP_MAX, n)]


# ── growth / loss point colours ───────────────────────────────────────────────

COLOR_GROWTH  = "#28a745"   # green  — pin grew since previous visit
COLOR_LOSS    = "#dc3545"   # red    — pin shrank since previous visit
COLOR_NEUTRAL = "grey"      # no prior measurement to compare against

# ── line colours ─────────────────────────────────────────────────────────────

COLOR_GREY_LINE       = "#555555"   # connecting lines between time slices / pins
COLOR_GREY_LINE_3D    = "#333333"   # slightly darker grey for 3-D pin traces

# ── hillslope / ground colours ────────────────────────────────────────────────

COLOR_HILL_FILL = "#C4A265"   # tan fill for hill background / baseline surface
COLOR_HILL_LINE = "#8B6914"   # dark tan for hill outline / dotted ground line

# ── table cell colours ────────────────────────────────────────────────────────

COLOR_TABLE_GROWTH  = "#d4edda"   # light green cell background
COLOR_TABLE_LOSS    = "#f8d7da"   # light red cell background
COLOR_TABLE_NEUTRAL = "#ffffff"
COLOR_TABLE_HEADER  = "#dee2e6"   # grey header row

# ── 3-D surface colours ───────────────────────────────────────────────────────

COLOR_GLASS_SURFACE = "#b8c8d8"   # steel blue-grey for the glass data sheet


# ── output helpers ────────────────────────────────────────────────────────────

def script_output_dir(script_file) -> Path:
    """Return (and create) processed/{script_stem}-images/ for a given script."""
    d = ROOT / "processed" / f"{Path(script_file).stem}-images"
    d.mkdir(parents=True, exist_ok=True)
    return d


def safe_filename(title: str) -> str:
    """Convert a plot title to a filesystem-safe filename (no extension)."""
    s = title.replace("\n", " ").replace("×", "x").strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s).lower().strip("_")
    return s[:80] or "panel"


def save_ax(fig, ax, path, dpi: int = 150) -> None:
    """Save a single axes (with its labels/title) as a PNG."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bbox = ax.get_tightbbox(renderer) or ax.get_window_extent(renderer)
    bbox_in = bbox.transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(str(path), bbox_inches=bbox_in, dpi=dpi)


def save_ax_group(fig, axes, path, dpi: int = 150) -> None:
    """Save a list of axes as one PNG (their bounding boxes are unioned)."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bboxes = [
        ax.get_tightbbox(renderer) or ax.get_window_extent(renderer)
        for ax in axes
    ]
    bboxes = [bb for bb in bboxes if bb is not None]
    if not bboxes:
        return
    x0 = min(bb.x0 for bb in bboxes)
    y0 = min(bb.y0 for bb in bboxes)
    x1 = max(bb.x1 for bb in bboxes)
    y1 = max(bb.y1 for bb in bboxes)
    bbox_in = _MplBbox([[x0, y0], [x1, y1]]).transformed(
        fig.dpi_scale_trans.inverted()
    )
    fig.savefig(str(path), bbox_inches=bbox_in, dpi=dpi)
