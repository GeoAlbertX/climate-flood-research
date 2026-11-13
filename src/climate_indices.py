"""
climate_indices.py
------------------
Annual and monthly rainfall indices following the WMO Expert Team on Climate Change
Detection and Indices (ETCCDI) definitions, plus the Precipitation Concentration Index.

Index      Meaning                                               Unit
---------  ----------------------------------------------------  -------
ANNUAL     total rainfall in the year (all days)                 mm
PRCPTOT    total rainfall on wet days (>= 1 mm)                  mm
WETDAYS    number of wet days                                    days
SDII       simple daily intensity = PRCPTOT / WETDAYS            mm/day
Rx1day     wettest single day                                    mm
Rx5day     wettest 5-day spell                                   mm
R10mm      days with >= 10 mm (heavy)                            days
R20mm      days with >= 20 mm (very heavy)                       days
R50mm      days with >= 50 mm (flood-producing in many cities)   days
R95p       rain falling on days above the 95th percentile        mm
R95pTOT    share of the year's rain from those extreme days      %
CDD        longest dry spell (consecutive days < 1 mm)           days
CWD        longest wet spell (consecutive days >= 1 mm)          days
PCI        precipitation concentration index (Oliver, 1980)      -
"""
import numpy as np
import pandas as pd


def _max_run(mask):
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def precipitation_concentration_index(monthly_totals):
    """PCI = 100 * sum(p_i^2) / (sum p_i)^2  over the 12 months.
    <=10 uniform | 11-15 moderately seasonal | 16-20 seasonal | >20 strongly irregular"""
    p = np.asarray(monthly_totals, float)
    tot = p.sum()
    return 100 * np.sum(p ** 2) / tot ** 2 if tot > 0 else np.nan


def wet_day_percentile(daily, q=0.95, wet=1.0):
    return float(daily[daily >= wet].quantile(q))


def annual_indices(daily, wet=1.0, max_missing=0.10, p95=None):
    if p95 is None:
        p95 = wet_day_percentile(daily, 0.95, wet)
    rows = []
    for year, g in daily.groupby(daily.index.year):
        miss = g.isna().mean()
        row = {"year": year, "missing_frac": miss}
        if miss > max_missing:
            rows.append(row)          # all indices stay NaN for incomplete years
            continue
        gv = g.fillna(0.0)
        wetd = gv[gv >= wet]
        prcptot = wetd.sum()
        r95 = gv[gv > p95].sum()
        monthly = gv.groupby(gv.index.month).sum().reindex(range(1, 13), fill_value=0)
        row.update({
            "ANNUAL": gv.sum(),
            "PRCPTOT": prcptot,
            "WETDAYS": len(wetd),
            "SDII": prcptot / len(wetd) if len(wetd) else np.nan,
            "Rx1day": gv.max(),
            "Rx5day": gv.rolling(5).sum().max(),
            "R10mm": int((gv >= 10).sum()),
            "R20mm": int((gv >= 20).sum()),
            "R50mm": int((gv >= 50).sum()),
            "R95p": r95,
            "R95pTOT": 100 * r95 / prcptot if prcptot else np.nan,
            "CDD": _max_run((gv < wet).values),
            "CWD": _max_run((gv >= wet).values),
            "PCI": precipitation_concentration_index(monthly.values),
        })
        rows.append(row)
    return pd.DataFrame(rows).set_index("year")


def monthly_table(daily):
    """Year x Month matrix of monthly rainfall totals (mm)."""
    m = daily.resample("MS").sum(min_count=20)
    df = pd.DataFrame({"year": m.index.year, "month": m.index.month, "mm": m.values})
    return df.pivot(index="year", columns="month", values="mm")


INDEX_INFO = {
    "ANNUAL": ("Annual rainfall", "mm"),
    "PRCPTOT": ("Wet-day rainfall total", "mm"),
    "WETDAYS": ("Number of wet days", "days"),
    "SDII": ("Rain per wet day (intensity)", "mm/day"),
    "Rx1day": ("Wettest day of the year", "mm"),
    "Rx5day": ("Wettest 5-day spell", "mm"),
    "R10mm": ("Heavy-rain days (>=10 mm)", "days"),
    "R20mm": ("Very heavy days (>=20 mm)", "days"),
    "R50mm": ("Extreme days (>=50 mm)", "days"),
    "R95p": ("Rain from extreme days (>P95)", "mm"),
    "R95pTOT": ("Share of rain from extreme days", "%"),
    "CDD": ("Longest dry spell", "days"),
    "CWD": ("Longest wet spell", "days"),
    "PCI": ("Precipitation Concentration Index", "-"),
}
