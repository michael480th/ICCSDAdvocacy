"""Run the full liquidity-stress pipeline in order."""
import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
STEPS = [
    "01_build_dataset.py",
    "02_compute_metrics.py",
    "03_dictionary_and_tables.py",
    "04_build_charts.py",
    "05_build_workbook.py",
    "06_build_narratives.py",
]
for step in STEPS:
    print(f"\n=== {step} ===")
    runpy.run_path(str(Path(__file__).resolve().parent / step), run_name="__main__")
print("\nAll steps complete.")
