"""
Run all erosion pin plotting scripts in sequence.
Execute from the project root:  python run_all.py
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    "src/capps_crossing_pin_change.py",
    "src/erosion_pin_change_apr2026.py",
    "src/plot_pin_heights_apr2026.py",
    "src/plot_pin_heights_comparison.py",
    "src/plot_pin_heights_all_years.py",
    "src/plot_pin_heights_all_years_over_time.py",
    "src/plot_3d_surface.py",
]

for script in SCRIPTS:
    print(f"\n{'='*60}")
    print(f"Running {script}")
    print('='*60)
    result = subprocess.run([sys.executable, script], cwd=Path(__file__).parent)
    if result.returncode != 0:
        print(f"\n*** {script} failed with exit code {result.returncode} ***")
        sys.exit(result.returncode)

print("\nAll scripts completed successfully.")
