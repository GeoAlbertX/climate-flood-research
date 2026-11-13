"""
data_loader.py
--------------
Downloads (or loads) DAILY rainfall for the study point and period.

Sources (all free, no API key):
  * NASA POWER   - https://power.larc.nasa.gov  (parameter PRECTOTCORR, mm/day)
  * Open-Meteo   - https://open-meteo.com      (ERA5 reanalysis, precipitation_sum, mm/day)
  * CSV          - your own rain-gauge file with columns: date, precip_mm

Downloaded data are cached in data/raw/ so the analysis is reproducible offline.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(path=None):
    path = Path(path) if path else ROOT / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Downloaders
# ---------------------------------------------------------------------------
def _fetch_nasa_power(lat, lon, start_year, end_year):
    import requests

    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point"
        f"?parameters=PRECTOTCORR&community=AG&longitude={lon}&latitude={lat}"
        f"&start={start_year}0101&end={end_year}1231&format=JSON"
    )
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    values = r.json()["properties"]["parameter"]["PRECTOTCORR"]
    s = pd.Series(values, dtype=float)
    s.index = pd.to_datetime(s.index, format="%Y%m%d")
    return s


def _fetch_open_meteo(lat, lon, start_year, end_year):
    import requests

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start_year}-01-01&end_date={end_year}-12-31"
        "&daily=precipitation_sum&timezone=UTC"
    )
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    d = r.json()["daily"]
    return pd.Series(d["precipitation_sum"], index=pd.to_datetime(d["time"]), dtype=float)


def _load_csv(path):
    df = pd.read_csv(ROOT / path)
    df.columns = [c.strip().lower() for c in df.columns]
    if not {"date", "precip_mm"}.issubset(df.columns):
        raise ValueError("CSV must have the columns: date, precip_mm")
    return pd.Series(df["precip_mm"].values, index=pd.to_datetime(df["date"]), dtype=float)


# ---------------------------------------------------------------------------
# Synthetic demo data (ONLY for testing that the code runs - never report it)
# ---------------------------------------------------------------------------
def make_demo_series(start_year, end_year, seed=42):
    """Bimodal West-African-style rainfall with a small built-in intensification.
    This is FAKE data used only to test the pipeline offline."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(f"{start_year}-01-01", f"{end_year}-12-31", freq="D")
    doy = days.dayofyear.values
    # two rainy peaks (~June and ~October), dry Dec-Feb
    season = 0.08 + 0.55 * np.exp(-((doy - 170) / 35) ** 2) + 0.35 * np.exp(-((doy - 285) / 25) ** 2)
    trend = 1 + 0.012 * (days.year.values - start_year)          # +1.2 %/yr intensity
    wet = rng.random(len(days)) < np.clip(season, 0, 0.9)
    amount = rng.gamma(shape=0.75, scale=17.0, size=len(days)) * trend
    return pd.Series(np.where(wet, np.round(amount, 1), 0.0), index=days)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def load_rainfall(cfg, demo=False, verbose=True):
    """Return a clean daily rainfall Series (mm/day, DatetimeIndex, NaN = missing)."""
    sa, per, dc = cfg["study_area"], cfg["period"], cfg["data"]
    y0, y1 = per["start_year"], per["end_year"]

    if demo:
        s = make_demo_series(y0, y1)
        source = "SYNTHETIC DEMO DATA (not real)"
    else:
        src = dc["source"].lower()
        cache = ROOT / "data" / "raw" / f"rainfall_{src}_{sa['latitude']}_{sa['longitude']}_{y0}_{y1}.csv"
        if src == "csv":
            s = _load_csv(dc["csv_path"])
        elif cache.exists():
            s = pd.read_csv(cache, index_col=0, parse_dates=True).iloc[:, 0]
            if verbose:
                print(f"  Loaded cached data: {cache.relative_to(ROOT)}")
        else:
            if verbose:
                print(f"  Downloading daily rainfall from {src} ...")
            fetch = {"nasa_power": _fetch_nasa_power, "open_meteo": _fetch_open_meteo}[src]
            s = fetch(sa["latitude"], sa["longitude"], y0, y1)
            cache.parent.mkdir(parents=True, exist_ok=True)
            s.rename("precip_mm").to_csv(cache, index_label="date")
            if verbose:
                print(f"  Saved raw data to {cache.relative_to(ROOT)}")
        source = {"nasa_power": "NASA POWER (PRECTOTCORR)",
                  "open_meteo": "Open-Meteo ERA5 archive",
                  "csv": f"Local file {dc['csv_path']}"}[src]

    # --- quality control ---------------------------------------------------
    s = s.sort_index()
    s = s[(s.index.year >= y0) & (s.index.year <= y1)]
    s = s.where(s >= 0)                           # -999 fill values and negatives -> NaN
    full = pd.date_range(f"{y0}-01-01", f"{y1}-12-31", freq="D")
    s = s.reindex(full)                           # make missing days explicit
    s.name = "precip_mm"
    s.attrs["source"] = source
    if verbose:
        print(f"  Source: {source}")
        print(f"  Days: {len(s)}, missing: {int(s.isna().sum())} ({100 * s.isna().mean():.2f} %)")
    return s
