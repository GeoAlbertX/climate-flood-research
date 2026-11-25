# Long-record check: is Lagos rainfall really changing? (1981–2024, three datasets)

*Atta Albert, November 2026*

## Why I did this

The main study (2005–2024, NASA POWER) found no statistically significant trend in any rainfall index, though the heaviest days pointed upwards. Twenty years is short, so I reran the same analysis on 44–45-year records from three independent datasets.

| Run | Data | What it is | Years | Results |
|---|---|---|---|---|
| A | ERA5 (Open-Meteo archive) | Weather-model reanalysis | 1980–2024 | [`results_era5_1980_2024/RESULTS.md`](results_era5_1980_2024/RESULTS.md) |
| B | NASA POWER (PRECTOTCORR) | Reanalysis, bias-corrected with satellite data | 1981–2024 | [`results_nasapower_1981_2024/RESULTS.md`](results_nasapower_1981_2024/RESULTS.md) |
| C | CHIRPS v2.0 daily | Satellite estimates blended with rain-gauge records | 1981–2024 | [`results_chirps_1981_2024/RESULTS.md`](results_chirps_1981_2024/RESULTS.md) |

All three use the same point in central Lagos (6.5244° N, 3.3792° E), the same code and the same tests (Mann-Kendall, Sen's slope, Pettitt, Gumbel). CHIRPS was exported from Google Earth Engine with [`tools/gee_chirps_lagos_daily.js`](../tools/gee_chirps_lagos_daily.js).

```
python project1_rainfall_trends/analysis.py --source open_meteo --start 1980 --end 2024 --out results_era5_1980_2024
python project1_rainfall_trends/analysis.py --source nasa_power --start 1981 --end 2024 --out results_nasapower_1981_2024
python project1_rainfall_trends/analysis.py --csv data/raw/chirps_lagos_daily_1981_2024.csv --start 1981 --end 2024 --out results_chirps_1981_2024
```

## Results (all for 1981–2024)

| Trend (Sen's slope, Mann-Kendall p) | ERA5 | NASA POWER | CHIRPS |
|---|---|---|---|
| Annual rainfall | −9.4 mm/yr, p = 0.001 (**down**) | +7.7 mm/yr, p = 0.028 (**up**) | +4.5 mm/yr, p = 0.13 (no trend) |
| Wettest day of the year | +0.40 mm/yr, p = 0.14 (no trend) | +0.42 mm/yr, p = 0.034 (**up**) | −0.01 mm/yr, p = 0.96 (no trend) |
| Days with ≥ 20 mm | +0.07 days/yr, p = 0.13 (no trend) | 0.00 days/yr, p = 0.64 (no trend) | +0.19 days/yr, p = 0.007 (**up**) |
| 1-in-10-year storm of the first half, in the second half | 1-in-8.4 years | 1-in-3.1 years | 1-in-27 years |

**How well do the datasets agree year by year?** (correlation of yearly values)

| | ERA5–POWER | ERA5–CHIRPS | POWER–CHIRPS |
|---|---|---|---|
| Annual totals | 0.21 | 0.39 | **0.71** |
| Wettest day of the year | 0.14 | −0.11 | −0.03 |

## What this means

1. **Total rainfall: no reliable evidence of a big change.** ERA5 is the odd one out. It is the only dataset showing a decline, and it agrees poorly with the other two. NASA POWER and CHIRPS, which agree fairly well (r = 0.71), both lean towards slightly more rain, but only one of them is significant.
2. **The heaviest single days: no consistent trend.** NASA POWER shows a rise and CHIRPS, the gauge-based dataset, shows none. The three datasets don't even agree on *which years* had the biggest storms (correlations near zero). Gridded products blur short, local downpours, so none of them captures single-day extremes at a point in a city well.
3. **This changes my earlier reading.** The 2005–2024 result that "the 1-in-10-year storm now behaves like a 1-in-3.7-year storm" comes from one dataset and a short record. It does not hold up in the longer, gauge-based record (CHIRPS gives the opposite). I now treat it as unconfirmed.
4. **What it means for flooding in Lagos:** there is no consistent evidence that the rain itself has changed enough to explain worsening floods. That points the attention back to the ground: built-up area, lost wetlands and drainage. Study 2 found a measurable effect there (Lekki–Ajah runoff share +32 %, p = 0.048).

## Limitations and next steps

- All three are gridded products (about 5–50 km), and rain-gauge coverage in Lagos is sparse, so even CHIRPS can miss local trends.
- The real test is station data: NiMet daily records for Ikeja or Oshodi, if they can be obtained.
- Sub-daily (hourly) intensity matters most for urban drains and can't be seen in daily data.
