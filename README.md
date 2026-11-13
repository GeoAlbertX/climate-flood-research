# 🌧️ Climate, Flooding & Sustainable Urban Planning — Lagos, Nigeria (2005–2024)

Two linked, fully reproducible research projects that use **20 years of daily rainfall data**, **statistics** and **urban hydrology** to answer one question:

> **Why is flooding getting worse in fast-growing tropical cities — and what can planners do about it?**

| | Project | Core question | Main methods |
|---|---|---|---|
| 1 | [**Is the Rain Changing?**](project1_rainfall_trends/README.md) | How have rainfall amount, intensity, seasonality and extremes changed from 2005 to 2024? | 14 ETCCDI climate indices, Mann-Kendall, Sen's slope, Pettitt change point, Welch & Mann-Whitney tests, Gumbel extreme-value analysis |
| 2 | [**Concrete, Climate and Floods**](project2_urban_flood_risk/README.md) | How do urban growth and rainfall change drive flood risk, and which sustainable drainage strategy works best? | SCS Curve Number runoff model, GHSL built-up data, Poisson regression, climate-vs-urban attribution, SuDS scenarios, sensitivity analysis |

Project 1 describes **the hazard** (the rain). Project 2 turns that rain into **flood risk** for the city and tests **solutions**.

---

## ✨ Highlights

* **Real, open data** — NASA POWER and ERA5 daily rainfall downloaded automatically; GHSL satellite-derived built-up area via Google Earth Engine.
* **Transparent mathematics** — every equation in the reports maps to a commented function in [`src/`](src/), and core statistics are verified against hand calculations in [`tests/`](tests/).
* **Plain-English explanations** next to every method, for non-specialist readers.
* **Auto-generated results** — running the code writes a `RESULTS.md` report with tables, interpretation sentences and 13 figures.
* **Portable** — change the coordinates in [`config.yaml`](config.yaml) to analyse any city in the world.

## 📁 Repository structure

```
├── config.yaml                     ← study area, period and model settings
├── run_all.py                      ← runs both projects
├── requirements.txt
├── src/                            ← shared, documented toolkit
│   ├── data_loader.py              ← downloads & quality-controls daily rainfall
│   ├── climate_indices.py          ← ETCCDI indices + Precipitation Concentration Index
│   ├── stats_tools.py              ← Mann-Kendall, Sen, Pettitt, Gumbel, Poisson…
│   ├── hydrology.py                ← SCS Curve Number urban runoff model
│   └── plotting.py
├── project1_rainfall_trends/
│   ├── README.md                   ← full research report (methods + equations)
│   ├── analysis.py
│   └── results/                    ← figures, CSV tables, RESULTS.md (created by the code)
├── project2_urban_flood_risk/
│   ├── README.md                   ← full research report
│   ├── analysis.py
│   └── results/
├── tools/gee_impervious_ghsl.js    ← Google Earth Engine script for built-up area
├── data/                           ← raw downloads cached here; flood-event template
└── tests/test_stats.py             ← checks of the statistics against known answers
```

## 🚀 How to run

**Option A — on your computer** (Python 3.9+):

```bash
git clone https://github.com/<your-username>/climate-flood-research.git
cd climate-flood-research
pip install -r requirements.txt
python tests/test_stats.py        # check the maths (all should PASS)
python run_all.py                 # download data and run both projects
```

**Option B — in your browser, no installation (Google Colab):**
open [colab.research.google.com](https://colab.research.google.com) → *New notebook*, then run:

```python
!git clone https://github.com/<your-username>/climate-flood-research.git
%cd climate-flood-research
!pip install -q -r requirements.txt
!python run_all.py
```

Results appear in `project1_rainfall_trends/results/` and `project2_urban_flood_risk/results/`.

**Offline test:** `python run_all.py --demo` runs everything on *synthetic* data (clearly watermarked "DEMO DATA") to check the code works. Demo outputs go to `results_demo/` folders, which are git-ignored — never report them as findings.

## 🔧 Adapting to another city

Edit `config.yaml`: change `name`, `latitude`, `longitude`, and (for Project 2) the impervious fractions measured with the Earth Engine script. Everything else updates automatically.

## 🧠 Skills demonstrated

Climate data analysis · time-series trend detection · non-parametric statistics · extreme-value theory · hydrological modelling · remote-sensing data (GHSL / Google Earth Engine) · urban flood risk assessment · sustainable drainage (SuDS) & nature-based solutions · scenario & sensitivity analysis · reproducible research in Python · scientific communication

## 🌍 Relevance

Supports **SDG 11** (Sustainable Cities and Communities — target 11.5, reducing disaster losses) and **SDG 13** (Climate Action), and the evidence base needed for climate-adaptive drainage design and land-use planning.

## 📜 License

Code: MIT License (see [`LICENSE`](LICENSE)). Data remain under the terms of their providers (NASA POWER, Copernicus/ECMWF ERA5, European Commission JRC GHSL).

## 📬 Author

*[Atta Albert]* — *[albertsecurx@gmail.com]*
