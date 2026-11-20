# Rainfall, urban growth and flood risk in Lagos, Nigeria (2005–2024)

Flooding in Lagos seems to get worse every rainy season, and people usually blame either "heavier rain" or "too much building". I wanted to see what the data actually says. This repository contains two connected studies that look at the question from both sides:

| | Study | Question | Main methods |
|---|---|---|---|
| 1 | [Is the rain changing?](project1_rainfall_trends/README.md) | Has rainfall amount, intensity, seasonality or the size of extreme storms changed between 2005 and 2024? | ETCCDI climate indices, Mann-Kendall, Sen's slope, Pettitt test, Welch and Mann-Whitney tests, Gumbel extreme-value analysis |
| 2 | [Concrete, climate and floods](project2_urban_flood_risk/README.md) | How much of the flood risk comes from urban growth rather than rainfall, and which drainage strategy reduces it most? | SCS Curve Number runoff model, GHSL built-up area, Poisson regression, counterfactual attribution, SuDS scenarios, sensitivity analysis |

The first study describes the hazard (the rain). The second turns that rain into runoff and flooding for an urban catchment and tests possible solutions.

## Main findings

- **Rainfall.** Annual rainfall averaged about 1,590 mm with no statistically significant trend in any of the 14 indices. The extremes are moving upwards, though: the wettest day of the year was about 25 % higher in 2015–2024 than in 2005–2014. Under the Gumbel model, the storm that was a 1-in-10-year event in the first decade behaves more like a 1-in-4-year event in the second. With only 20 years of data these changes can't yet be confirmed statistically.
- **Flood risk.** As the built-up area grows, the share of rain that turns into runoff rises significantly (+26 %, p = 0.004). With land use held at 2005 levels, it barely changes. Of the strategies tested, combining green infrastructure with drain upgrades cut modelled flood volume the most (about 60 %).
- Full numbers, tables and figures are in each study's `results/RESULTS.md`.

Note: the built-up fractions used in study 2 are still provisional estimates. They will be replaced with values measured from GHSL (see [`tools/gee_impervious_ghsl.js`](tools/gee_impervious_ghsl.js)).

## Data

- **Rainfall:** NASA POWER daily precipitation (PRECTOTCORR) for central Lagos (6.52° N, 3.38° E). ERA5 via Open-Meteo can be used as an alternative source.
- **Built-up area:** Global Human Settlement Layer (GHS-BUILT-S R2023A), processed in Google Earth Engine.
- The downloaded rainfall series is saved in `data/raw/` so the results can be reproduced exactly.

## Repository layout

```
config.yaml                    study area, period and model settings
run_all.py                     runs both studies
src/                           shared code (data download, indices, statistics, hydrology, plots)
project1_rainfall_trends/      report, analysis script and results for study 1
project2_urban_flood_risk/     report, analysis script and results for study 2
tools/gee_impervious_ghsl.js   Earth Engine script for built-up area
data/                          rainfall data and a template for recorded flood events
tests/test_stats.py            checks of the statistics against worked examples
```

## Running it

You need Python 3.9 or newer.

```bash
git clone https://github.com/GeoAlbertX/climate-flood-research.git
cd climate-flood-research
pip install -r requirements.txt
python tests/test_stats.py
python run_all.py
```

It also runs in Google Colab:

```python
!git clone https://github.com/GeoAlbertX/climate-flood-research.git
%cd climate-flood-research
!pip install -q -r requirements.txt
!python run_all.py
```

`python run_all.py --demo` runs everything on synthetic rainfall, which is useful for checking the code without internet access. Demo outputs go to `results_demo/` folders, are marked "DEMO DATA", and are not part of the findings.

To study another city, change the name and coordinates in `config.yaml` (and, for study 2, the built-up fractions).

## Limitations

Twenty years is a short record for climate trends, gridded rainfall products underestimate local extremes, and the flood model works at a daily time step for a single lumped catchment. Each report discusses its limitations in more detail.

## Licence

Code is released under the MIT License (see [`LICENSE`](LICENSE)). The data remain under the terms of their providers: NASA POWER, Copernicus/ECMWF ERA5 and the European Commission JRC (GHSL).

## Author

Atta Albert, BSc Geography. Contact: albertsecurx@gmail.com
