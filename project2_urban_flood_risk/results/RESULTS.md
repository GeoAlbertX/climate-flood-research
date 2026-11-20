# Project 2 Results — Lagos Metropolitan Area, Nigeria, 2005–2024

*Produced by `analysis.py`. Rainfall: NASA POWER (PRECTOTCORR). Catchment 25.0 km², drainage capacity 40 mm/day, CN pervious 74 / impervious 98. Impervious fraction 55 % → 55 % (GHSL built-up surface, set in `config.yaml`).*

## 1. Flood-trend statistics

| Variable | Scenario | Mean | Sen's slope /yr | % change over period | MK p | Result |
|---|---|---|---|---|---|---|
| Flood days/yr | Climate + urban | 0.45 | +0 | +0.0 % | 0.871 | no significant trend |
| Flood days/yr | Climate only | 0.45 | +0 | +0.0 % | 0.871 | no significant trend |
| Excess volume (m³/yr) | Climate + urban | 2.72e+05 | +0 | +0.0 % | 1.000 | no significant trend |
| Excess volume (m³/yr) | Climate only | 2.71e+05 | +0 | +0.0 % | 1.000 | no significant trend |
| Runoff coefficient | Climate + urban | 0.308 | +0.000613 | +3.8 % | 0.770 | no significant trend |
| Runoff coefficient | Climate only | 0.308 | +0.000573 | +3.5 % | 0.770 | no significant trend |
| Max daily runoff (mm) | Climate + urban | 41.7 | -0.00783 | -0.4 % | 1.000 | no significant trend |
| Max daily runoff (mm) | Climate only | 41.6 | -0.0133 | -0.6 % | 0.974 | no significant trend |

**Poisson regression of flood days (climate + urban):** IRR = 1.012 (95 % CI 0.903–1.133), p = 0.840, dispersion = 1.35. This means the expected number of flood days changes by **+1.2 % per year**, i.e. ×1.25 over 19 years.
With land use frozen at 2005, the same model gives IRR = 1.012 (p = 0.840).

## 2. Attribution — how much is climate, how much is urban growth?

Change in the average of 2015–2024 compared with 2005–2014:

| Quantity | Total change | Due to rainfall change | Due to urban growth | Urban share |
|---|---|---|---|---|
| flood_days | +0.3 | +0.3 | +0 | 0 % |
| excess_volume_m3 | +1.71e+05 | +1.69e+05 | +2.07e+03 | 1 % |
| runoff_mm | +0.0616 | -1.18 | +1.24 | n/a (total change close to zero) |

*Method: run the model twice — once with real land-use growth, once with land use frozen at 2005. The difference between the two runs is the effect of urbanisation.*

## 3. Sustainable drainage (SuDS) scenarios

Each scenario applies 2024 land use to all 20 years of observed rainfall.

| Scenario | Flood days/yr | Excess m³/yr | Runoff coeff. | Flood-day reduction | Volume reduction |
|---|---|---|---|---|---|
| Business as usual | 0.45 | 272,742 | 0.309 | 0 % | 0 % |
| Green roofs | 0.35 | 244,786 | 0.282 | 22 % | 10 % |
| Rain gardens + permeable paving | 0.35 | 190,557 | 0.269 | 22 % | 30 % |
| Drain upgrade (grey only) | 0.30 | 180,835 | 0.309 | 33 % | 34 % |
| Integrated green + grey | 0.10 | 112,643 | 0.243 | 78 % | 59 % |

**Best performing strategy:** Integrated green + grey (59 % less floodwater).

## 4. Sensitivity analysis

| Parameter varied | Flood days/yr (low) | Flood days/yr (high) |
|---|---|---|
| Drainage capacity ±20 % | 0.90 | 0.30 |
| Impervious fraction ±10 % | 0.35 | 0.55 |
| Initial abstraction ratio 0.05 vs 0.30 | 0.55 | 0.45 |
| Pervious CN ±5 % | 0.45 | 0.55 |

The result is most sensitive to **drainage capacity** — this is the parameter most worth measuring carefully.

## Figures

![01_scs_runoff_curves](figures/01_scs_runoff_curves.png)

![02_impervious_and_runoff_coefficient](figures/02_impervious_and_runoff_coefficient.png)

![03_flood_days_per_year](figures/03_flood_days_per_year.png)

![04_excess_flood_volume](figures/04_excess_flood_volume.png)

![05_suds_scenarios](figures/05_suds_scenarios.png)

![06_sensitivity_tornado](figures/06_sensitivity_tornado.png)
