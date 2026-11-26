"""Compare annual rainfall and the wettest day of each year for central Lagos,
1981-2024, from three datasets (CHIRPS, ERA5, NASA POWER).

Run from the repository root after the three long-record runs (see LONG_RECORD_CHECK.md):
    python project1_rainfall_trends/compare_datasets.py
Writes project1_rainfall_trends/results_chirps_1981_2024/figures/three_datasets.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FILES = {
    "CHIRPS (gauge-based)": RAW / "chirps_lagos_daily_1981_2024.csv",
    "ERA5": RAW / "rainfall_open_meteo_6.5244_3.3792_1980_2024.csv",
    "NASA POWER": RAW / "rainfall_nasa_power_6.5244_3.3792_1981_2024.csv",
}
COLOURS = {"CHIRPS (gauge-based)": "#111111", "ERA5": "#1f78b4", "NASA POWER": "#e6550d"}


def sen_line(years, values):
    slopes = [(values[j] - values[i]) / (years[j] - years[i])
              for i in range(len(years)) for j in range(i + 1, len(years))]
    s = np.median(slopes)
    b = np.median(values - s * years)
    return s, b


fig, axs = plt.subplots(1, 2, figsize=(14, 4.6))
for name, path in FILES.items():
    s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    s = s.where(s >= 0)["1981":"2024"]
    for ax, series, unit in [(axs[0], s.groupby(s.index.year).sum(), "mm per year"),
                             (axs[1], s.groupby(s.index.year).max(), "mm in one day")]:
        yrs = series.index.values.astype(float)
        vals = series.values.astype(float)
        slope, icpt = sen_line(yrs, vals)
        ax.plot(yrs, vals, color=COLOURS[name], lw=1.2, alpha=0.55)
        ax.plot(yrs, icpt + slope * yrs, color=COLOURS[name], lw=2.4,
                label=f"{name}: {round(slope, 1) + 0.0:+.1f} {unit.split(' ')[0]}/yr")
axs[0].set(title="Total rainfall per year", ylabel="mm per year", xlabel="Year")
axs[1].set(title="Wettest single day of each year", ylabel="mm in one day", xlabel="Year")
for ax in axs:
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(alpha=0.25)
fig.suptitle("Central Lagos, 1981–2024: three datasets, three different trends (thin = yearly values, "
             "thick = Sen's slope)", fontsize=12, fontweight="bold", x=0.01, ha="left")
fig.text(0.01, -0.02, "Data: CHIRPS v2.0 (Climate Hazards Center, UCSB), ERA5 (ECMWF/Copernicus, via Open-Meteo), "
         "NASA POWER. Analysis: Atta Albert, 2026.", fontsize=8, color="#444444")
fig.tight_layout()
out = ROOT / "project1_rainfall_trends" / "results_chirps_1981_2024" / "figures" / "three_datasets.png"
fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
print("saved", out)
