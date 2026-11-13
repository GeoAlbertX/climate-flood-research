"""Unit tests — checks the statistics against hand-calculated / textbook values.
Run with:  python -m pytest -q   (or  python tests/test_stats.py)"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import hydrology as hy  # noqa: E402
from src import stats_tools as st  # noqa: E402
from src.climate_indices import precipitation_concentration_index  # noqa: E402


def test_mann_kendall_perfect_increase():
    r = st.mann_kendall(np.arange(10))
    assert r["S"] == 45 and abs(r["tau"] - 1) < 1e-12 and r["p"] < 0.001


def test_mann_kendall_hand_example():
    # x = [1, 3, 2, 4]: pairs: +1 +1 +1 -1 +1 +1 -> S = 4 ; Var = 4*3*13/18 = 8.667
    r = st.mann_kendall([1, 3, 2, 4])
    assert r["S"] == 4
    assert abs(r["var_S"] - 8.6667) < 1e-3
    assert abs(r["Z"] - 3 / np.sqrt(8.6667)) < 1e-3


def test_sens_slope_exact_line():
    t = np.arange(2005, 2025)
    r = st.sens_slope(t, 3.0 * t + 7)
    assert abs(r["slope"] - 3.0) < 1e-9


def test_pettitt_finds_step():
    x = np.r_[np.full(10, 1.0), np.full(10, 5.0)] + np.linspace(0, 0.01, 20)
    r = st.pettitt(x)
    assert r["last_index_before_change"] == 9 and r["p"] < 0.01


def test_gumbel_roundtrip():
    u, a = 80.0, 20.0
    x100 = st.gumbel_return_level(u, a, 100)
    assert abs(st.gumbel_return_period(u, a, x100) - 100) < 1e-6
    assert abs(x100 - (80 - 20 * np.log(-np.log(0.99)))) < 1e-9


def test_pci_uniform_and_single_month():
    assert abs(precipitation_concentration_index(np.ones(12)) - 100 / 12) < 1e-9
    assert abs(precipitation_concentration_index([12] + [0] * 11) - 100) < 1e-9


def test_scs_textbook():
    # CN=80 -> S=63.5 mm, Ia=12.7 mm; P=100 mm -> Q=(87.3^2)/(150.8)=50.54 mm
    q = float(hy.scs_runoff(100.0, 80))
    assert abs(q - 50.54) < 0.05
    assert float(hy.scs_runoff(10.0, 80)) == 0.0


def test_poisson_recovers_rate():
    rng = np.random.default_rng(0)
    t = np.arange(200, dtype=float)
    lam = np.exp(1.0 + 0.01 * (t - t.mean()))
    r = st.poisson_trend(t, rng.poisson(lam))
    assert abs(r["b1"] - 0.01) < 0.003


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
