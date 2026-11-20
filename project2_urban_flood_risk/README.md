# Project 2 — Concrete, Climate and Floods: Modelling How Urban Growth and Changing Rainfall Drive Flood Risk in Lagos, and Testing Sustainable Drainage Solutions (2005–2024)

Atta Albert · Independent research project · Python, SCS Curve Number hydrology, Google Earth Engine (GHSL), statistics

**Keywords:** urban flooding, impervious surfaces, rainfall–runoff modelling, SCS Curve Number, Poisson regression, attribution, sustainable urban drainage (SuDS), nature-based solutions, urban planning, SDG 11 & 13

---

## Abstract

Urban floods happen when more water reaches the ground surface than the soil can absorb and the drains can carry away. Two things increase that water: **heavier rain** (climate) and **more concrete** (urbanisation), because roofs and roads stop rain from soaking in. This project builds a transparent rainfall–runoff model for a 25 km² urban catchment in Lagos using the **USDA SCS Curve Number** method, driven by 20 years of observed daily rainfall (2005–2024) and a growing impervious (built-up) surface fraction measured from the **Global Human Settlement Layer (GHSL)**. It (1) quantifies the trend in "drainage-overload days" and flood volume using **Mann-Kendall**, **Sen's slope** and **Poisson regression**; (2) **separates** how much of the change is caused by rainfall change versus urban growth, using a counterfactual model run; (3) compares five planning strategies — green roofs, rain gardens and permeable paving, drain upgrades, and an integrated green–grey approach; and (4) tests how sensitive the conclusions are to the model's assumptions. Results are in [`results/RESULTS.md`](results/RESULTS.md).

In simple terms, the model takes each day's rain over part of Lagos and works out how much of it runs off the streets. I used it to ask three things: are floods becoming more frequent, is that because of the rain or because more of the city is paved, and which solutions (green, concrete or both) would reduce flooding the most?

---

## 1. Background

When rain falls on a forest or grassland, most of it soaks into the soil. When it falls on a roof or a road, almost all of it runs off immediately. As cities grow, the share of **impervious surface** rises — and the same storm produces much more runoff, much faster. Lagos has been one of the fastest-growing cities in the world, while many wetlands and natural drainage paths have been built over.

Traditional flood management relies on **"grey" infrastructure** — bigger concrete drains and canals. **Sustainable Drainage Systems (SuDS)**, also called **nature-based solutions** or the "sponge city" approach, instead try to *slow, store and soak up* water where it falls: green roofs, rain gardens, bioswales, permeable paving and detention ponds (Woods Ballard et al., 2015). This project compares both approaches with numbers.

This work connects to **UN Sustainable Development Goal 11** (sustainable cities: target 11.5 on reducing disaster losses) and **SDG 13** (climate action).

## 2. Research questions

| # | Question | Method |
|---|---|---|
| RQ1 | Have modelled flood (drainage-overload) days and volumes increased from 2005 to 2024? | Mann-Kendall, Sen's slope, Poisson regression |
| RQ2 | How much of the change comes from **rainfall change** and how much from **urban growth**? | Counterfactual (fixed land-use) attribution |
| RQ3 | Which planning strategy reduces flooding most? | Scenario analysis of five SuDS/grey options |
| RQ4 | How robust are the findings to uncertain inputs? | One-at-a-time sensitivity analysis |
| RQ5 *(optional)* | Does the model agree with recorded flood events? | Spearman rank correlation |

## 3. Data

| Input | Source | Notes |
|---|---|---|
| Daily rainfall 2005–2024 | NASA POWER / ERA5 (same as Project 1) | `config.yaml → data.source` |
| Impervious (built-up) fraction | **GHSL GHS-BUILT-S R2023A** (European Commission JRC), epochs 2005, 2010, 2015, 2020, 2025 | Measure with [`tools/gee_impervious_ghsl.js`](../tools/gee_impervious_ghsl.js) |
| Soil / land-cover runoff parameters | SCS Curve Number tables (USDA NRCS TR-55, 1986) | CN = 98 impervious; CN = 74 open land, soil group C |
| Recorded flood events *(optional)* | News archives, NEMA/LASEMA reports, Dartmouth Flood Observatory, EM-DAT | Enter in [`data/flood_events.csv`](../data/flood_events.csv) |

**Built-up data:** the impervious fractions in `config.yaml` were measured from GHSL with the Earth Engine script: 54.7 % in 2005, 54.8 % in 2010, 54.9 % in 2015, 55.0 % in 2020 and 55.0 % in 2025 (used for 2024).

## 4. Methodology

```
Daily rainfall ─┐
                ├──►  SCS Curve Number runoff model (with soil-moisture adjustment)
Impervious % ───┘            │
(GHSL, by year)              ▼
                    Daily runoff Q  ──►  compare with drainage capacity  ──►  flood days, excess volume
                             │
         ┌───────────────────┼─────────────────────┬──────────────────────┐
         ▼                   ▼                     ▼                      ▼
   Trend tests      Attribution (climate     SuDS scenarios        Sensitivity
   MK, Sen, Poisson  vs urban growth)        (5 strategies)        analysis
```

### 4.1 The SCS Curve Number method

Developed by the US Soil Conservation Service, this is one of the most widely used methods in the world for estimating how much rain becomes runoff. Each surface gets a **Curve Number (CN)** between 0 and 100: the higher the number, the less water soaks in (concrete ≈ 98; grass on clay soil ≈ 74–80; forest on sandy soil ≈ 30–45).

**Step 1 — Maximum retention** (how much water the ground could hold), in mm:

$$
S = \frac{25400}{CN} - 254
$$

**Step 2 — Initial abstraction** (rain caught before any runoff starts — puddles, leaves, first soaking):

$$
I_a = \lambda S, \qquad \lambda = 0.2
$$

**Step 3 — Runoff depth** for a day with rainfall $P$:

$$
Q = \begin{cases} \dfrac{(P - I_a)^2}{P - I_a + S} & P > I_a \\[3mm] 0 & P \le I_a \end{cases}
$$

For example, take grassland with CN = 80 and 100 mm of rain. Then S = 25400/80 − 254 = 63.5 mm, Iₐ = 0.2 × 63.5 = 12.7 mm and Q = (100 − 12.7)² / (100 − 12.7 + 63.5) = 7,621 / 150.8 = 50.5 mm, so about half the rain runs off. On concrete (CN = 98), the same storm produces about 95 mm of runoff. This example is also one of the checks in `tests/test_stats.py`.

**Step 4 — Mixed urban catchment.** A city is part paved and part open. With impervious fraction $f$, runoff is area-weighted:

$$
Q_{\text{total}} = f \cdot Q(P, CN_{\text{imp}}) + (1-f) \cdot Q(P, CN_{\text{perv}})
$$

**Step 5 — Wet or dry soil (Antecedent Moisture Condition).** Soil that is already soaked from previous days absorbs less. Using the total rain in the previous 5 days, $P_5$:

$$
CN_{I} = \frac{4.2\,CN}{10 - 0.058\,CN} \;\;(P_5 < 35.6\text{ mm, dry}), \qquad
CN_{III} = \frac{23\,CN}{10 + 0.13\,CN} \;\;(P_5 > 53.3\text{ mm, wet})
$$

**Runoff coefficient** — the share of rain that becomes runoff in a year:

$$
C = \frac{\sum Q}{\sum P}
$$

### 4.2 Impervious surface growth

GHSL provides built-up surface area for 2005, 2010, 2015, 2020 (and modelled 2025) on a 100 m grid. For each epoch the catchment fraction is

$$
f = \frac{\text{mean built-up surface per cell (m}^2)}{10{,}000 \text{ m}^2}
$$

Years in between are filled by linear interpolation:

$$
f(t) = f(t_1) + \frac{t - t_1}{t_2 - t_1}\,\big[f(t_2) - f(t_1)\big]
$$

Built-up area does not include every road or paved yard, so it slightly underestimates true imperviousness (see the limitations section).

### 4.3 Flood (drainage-overload) indicator

The drainage network can evacuate a certain depth of runoff per day, $D_{\text{cap}}$ (default 40 mm/day). A **flood day** is any day when runoff exceeds what drains and storage can handle:

$$
E_d = \max\big(0,\; Q_d - S_{\text{store}} - D_{\text{cap}}\big)
$$

$$
\text{Flood days per year} = \#\{d : E_d > 0\}, \qquad
V_{\text{year}} = \sum_d E_d \times A \times 1000 \;\; (\text{m}^3)
$$

where $A$ is the catchment area in km² (1 mm over 1 km² = 1,000 m³ of water).

For drain design at a single outlet, the classic **Rational Method** is also provided in the code:

$$
Q_p = 0.278\; C\, i\, A \quad (\text{m}^3/\text{s}; \; i \text{ in mm/h}, A \text{ in km}^2)
$$

*Example:* C = 0.6, a 50 mm/h storm over 2 km² → Q_p = 0.278 × 0.6 × 50 × 2 ≈ **16.7 m³/s**.

### 4.4 Trend analysis of floods

The Mann-Kendall test and Sen's slope (equations in [Project 1 §5.4–5.5](../project1_rainfall_trends/README.md#54-mann-kendall-trend-test-mann-1945-kendall-1975)) are applied to annual flood days, excess volume, runoff coefficient and maximum daily runoff.

Because flood days are **counts** (0, 1, 2, …), they are also modelled with **Poisson regression**:

$$
N_t \sim \text{Poisson}(\lambda_t), \qquad \ln \lambda_t = \beta_0 + \beta_1 (t - \bar{t})
$$

fitted by maximum likelihood (iteratively re-weighted least squares). The **Incidence Rate Ratio**

$$
\text{IRR} = e^{\beta_1}
$$

is the factor by which expected flood days change each year — e.g. IRR = 1.05 means **+5 % per year**, and $1.05^{19} \approx 2.5\times$ over the study period. Over-dispersion is checked with $\phi = \frac{1}{n-2}\sum \frac{(N_t - \hat\lambda_t)^2}{\hat\lambda_t}$; if $\phi > 1.5$, a quasi-Poisson correction ($z/\sqrt{\phi}$) is applied to the p-value.

### 4.5 Attribution: climate vs urbanisation

The model is run twice over the same 2005–2024 rainfall:

1. **Real world:** impervious fraction grows as measured.
2. **Counterfactual:** impervious fraction **frozen at 2005**.

Comparing the decade means (2015–2024 minus 2005–2014):

$$
\Delta_{\text{total}} = \Delta_{\text{real}}, \qquad
\Delta_{\text{climate}} = \Delta_{\text{counterfactual}}, \qquad
\Delta_{\text{urban}} = \Delta_{\text{total}} - \Delta_{\text{climate}}
$$

$$
\text{Urban share} = 100 \times \frac{\Delta_{\text{urban}}}{\Delta_{\text{total}}}\;\%
$$

The idea is simple: if the city had stopped growing in 2005, how much would flooding still have changed? That part is due to the rain, and the rest is due to building.

### 4.6 SuDS and planning scenarios

Each scenario applies **2024 land use** to all 20 years of rainfall (i.e. "today's city facing two decades of real weather"):

| Scenario | How it is modelled |
|---|---|
| Business as usual | No change |
| Green roofs | 10 % of impervious area disconnected (behaves as pervious) |
| Rain gardens + permeable paving | 15 % disconnected + 5 mm/day extra storage |
| Drain upgrade (grey only) | Drainage capacity × 1.25 |
| Integrated green + grey | 25 % disconnected + 10 mm/day storage + capacity × 1.25 |

Effective impervious fraction: $f_{\text{eff}} = f\,(1 - d)$, where $d$ is the disconnected share. Effectiveness:

$$
\text{Reduction} = 100 \times \left(1 - \frac{V_{\text{scenario}}}{V_{\text{BAU}}}\right)\%
$$

The scenario settings are in `config.yaml`, so other policy options can be tested easily.

### 4.7 Sensitivity analysis

Each uncertain parameter is changed one at a time (drainage capacity ±20 %, pervious CN ±5 %, initial abstraction ratio 0.05 vs 0.30, impervious fraction ±10 %) and the change in average flood days is shown in a **tornado chart**. The widest bar shows which input most needs accurate local measurement.

### 4.8 Optional validation

If real flood events are entered in `data/flood_events.csv`, the yearly event count is compared with modelled flood days using **Spearman's rank correlation**:

$$
\rho = 1 - \frac{6 \sum d_i^2}{n(n^2-1)}
$$

where $d_i$ is the difference in rank of year $i$ between the two series.

## 5. Results

All numbers, tables and figures are in [`results/RESULTS.md`](results/RESULTS.md).

| Figure | What it shows |
|---|---|
| `01_scs_runoff_curves` | How more paving turns the same rain into more runoff (conceptual) |
| `02_impervious_and_runoff_coefficient` | Built-up area over time and the share of rain that runs off |
| `03_flood_days_per_year` | Flood days with and without urban growth, with Poisson trend |
| `04_excess_flood_volume` | Floodwater volume the drains could not carry |
| `05_suds_scenarios` | Flood days and volume reduction for each strategy |
| `06_sensitivity_tornado` | Which assumption changes the answer most |

## 6. Discussion

**Which driver dominates?** In this catchment, rainfall. The GHSL measurements show that central Lagos was already about 55 % built-up in 2005 and has barely changed since (54.7 % to 55.0 %). With so little new building, the model attributes almost all of the change between the two decades to rainfall: the slight rise in flood days, and 99 % of the extra flood volume. The runoff coefficient shows no significant trend (+3.8 %, p = 0.77). That fits Project 1, where the heaviest storms appear to have intensified while annual totals did not.

This does not mean urbanisation is unimportant for Lagos flooding. It means the urban growth of the last twenty years happened somewhere else: on the city's edges in Lekki, Ajah, Ikorodu and around the lagoon, often on wetland. A central catchment is the wrong place to look for its effect, which is the question taken up by the [wetland and reclamation study](https://github.com/GeoAlbertX/lagos-wetland-reclamation). An earlier version of this analysis used assumed built-up values (45 % rising to 60 %) and found a strong urban effect. Replacing them with satellite measurements removed it, which shows how much the conclusions depend on measured rather than assumed land cover.

**Green versus grey.** Upgrading the drains alone reduced flood volume by about a third, similar to rain gardens with permeable paving. The two approaches work differently, though. Bigger drains move the same water downstream faster, which can shift the problem to the lagoon and to low-lying neighbourhoods. Green measures reduce the volume at source and bring other benefits, such as cooling, habitat and water reuse. Only the scenarios that included green infrastructure lowered the runoff coefficient. The integrated scenario performed best by a wide margin, which suggests the two approaches complement each other rather than compete.

**Planning implications.** For Lagos, this points to a mix of policies: limits on impervious cover in new developments, required on-site retention (rain tanks, soakaways, permeable paving), protection of the remaining wetlands and floodplains, enforcement of drainage setbacks, and regular clearing of existing drains.

**Uncertainty.** Drainage capacity is the parameter the results depend on most. A 20 % change moves the average from 0.30 to 0.90 flood days a year. Because the model produces only about nine flood days in 20 years, the exact flood-day percentages should be read with caution. GHSL built-up surface also leaves out many roads and paved yards, so the true impervious share is probably higher than 55 %; raising it by 10 % increases flood days from 0.45 to 0.55 a year.

## 7. Limitations

* **Daily time step:** urban flash floods happen within hours; a daily model captures *volumes* but not peak timing. An hourly model (e.g. EPA SWMM) is the natural next step.
* **Lumped catchment:** the 25 km² area is treated as one unit; real flooding depends on topography, blocked drains and tides (backwater from the Lagos Lagoon).
* **Drainage capacity** is a single assumed value — in reality it varies and is reduced by solid-waste blockage.
* **Built-up ≠ impervious:** GHSL built-up surface underestimates roads and paved yards.
* **SCS-CN** was developed for US agricultural catchments; it is widely used but should be calibrated locally where gauge data exist.
* **No sea-level / tidal component** — coastal surge and lagoon levels also drive flooding in Lagos.

## 8. Conclusions and recommendations

These conclusions use built-up fractions measured from GHSL for a 25 km² catchment around central Lagos (54.7 % in 2005, 55.0 % in 2025).

1. **Central Lagos was already built up by 2005, so urban growth explains little of the recent change there.** With land use almost constant, the runoff coefficient shows no significant trend (+3.8 %, p = 0.77), and rainfall accounts for 99 % of the increase in flood volume between the two decades.
2. **Flood days are rare in this model and their trend is not significant.** With 40 mm/day drainage capacity, the catchment overloads on average 0.45 days per year (about nine days in 20 years). Poisson regression gives +1.2 % per year (IRR = 1.012, 95 % CI 0.90–1.13, p = 0.84).
3. **Integrated green + grey drainage works best.** Applied to the current city over 20 years of real rainfall, combining green infrastructure (25 % of paved area disconnected, 10 mm/day storage) with a 25 % drain upgrade cuts flood volume by **59 %** and flood days by 78 %. A drain upgrade alone gives 34 %, rain gardens with permeable paving 30 %, and green roofs alone 10 %. Only the strategies that include green infrastructure also lower the runoff coefficient, which reduces the water sent downstream to the lagoon.
4. **Drainage capacity is the most important unknown.** Changing it by ±20 % moves average flood days from 0.30 to 0.90 per year, a larger effect than any other parameter. Measuring real drain capacity, including the effect of solid-waste blockage, is the highest priority for improving the model.
5. **The effect of urban growth has to be studied where the growth happened.** Running the same model for a fast-growing peri-urban catchment (for example Lekki–Ajah or Ikorodu) is the natural next step.
6. **Planning recommendations:**
   * Combine green and grey measures instead of relying on bigger drains alone: require on-site retention (rain tanks, soakaways, permeable paving) and upgrade key drains.
   * Keep existing drains clear: lost capacity from blockage has the biggest effect on flooding in this model.
   * Control impervious cover and protect the remaining wetlands and floodplains on the growing edges of the city, where land-use change is still happening.
   * Measure drain capacities and record actual flood events in `data/flood_events.csv` so the model can be validated.

## 9. How to reproduce

```bash
pip install -r requirements.txt
# built-up fractions: measured with tools/gee_impervious_ghsl.js and set in config.yaml
# recorded floods (optional): data/flood_events.csv
python project2_urban_flood_risk/analysis.py
```

## References

* Chow, V. T., Maidment, D. R., & Mays, L. W. (1988). *Applied Hydrology*. McGraw-Hill.
* European Commission, Joint Research Centre (2023). *GHSL Data Package 2023* (GHS-BUILT-S R2023A). Publications Office of the European Union.
* Hawkins, R. H., Ward, T. J., Woodward, D. E., & Van Mullem, J. A. (2009). *Curve Number Hydrology: State of the Practice*. American Society of Civil Engineers.
* Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica*, 13(3), 245–259.
* Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *Journal of the American Statistical Association*, 63(324), 1379–1389.
* United Nations (2015). *Transforming our World: the 2030 Agenda for Sustainable Development* (SDGs 11 and 13).
* USDA Natural Resources Conservation Service (1986). *Urban Hydrology for Small Watersheds*, Technical Release 55 (TR-55).
* Woods Ballard, B., et al. (2015). *The SuDS Manual* (C753). CIRIA, London.
