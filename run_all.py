"""
Run both research projects in one go.

    python run_all.py           # downloads real rainfall (internet needed the first time)
    python run_all.py --demo    # offline test with synthetic data (results are NOT real)
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "project1_rainfall_trends"))
sys.path.insert(0, str(ROOT / "project2_urban_flood_risk"))

import importlib.util  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    demo = ap.parse_args().demo
    _load(ROOT / "project1_rainfall_trends" / "analysis.py", "p1").run(demo=demo)
    _load(ROOT / "project2_urban_flood_risk" / "analysis.py", "p2").run(demo=demo)
    print("\nAll done. Open the RESULTS.md file inside each project's results folder.")
