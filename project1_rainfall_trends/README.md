# Project 1 — Is the Rain Changing? A Statistical Analysis of Rainfall Patterns and Extreme-Rainfall Trends in Lagos, Nigeria (2005–2024)

Atta Albert · Independent research project · Python (pandas, NumPy, SciPy, Matplotlib), NASA POWER / ERA5 climate data

**Keywords:** climate variability, rainfall trend, Mann-Kendall, Sen's slope, extreme rainfall, ETCCDI indices, return period, Gumbel distribution, urban flooding

---

## Abstract

Flooding in fast-growing coastal cities such as Lagos is driven first of all by rain — how much falls, how often, and above all how *intensely*. This project examines whether rainfall over Lagos changed between **2005 and 2024** using 20 years (7,305 days) of daily satellite/reanalysis rainfall. Fourteen internationally standardised climate indices (ETCCDI) are calculated for every year, covering total rainfall, number of rainy days, rainfall intensity, wettest days, dry spells and seasonality. Each index is tested for a long-term trend with the non-parametric **Mann-Kendall test**, the size of the change is estimated with **Sen's slope**, sudden shifts are searched for with the **Pettitt change-point test**, and the two decades (2005–2014 vs 2015–2024) are compared with **Welch's t-test** and the **Mann-Whitney U test**. Finally, the size of rare storms (2- to 100-year return periods) is estimated with the **Gumbel extreme-value distribution** to see whether "1-in-10-year" storms have become more common. The full results are in [`results/RESULTS.md`](results/RESULTS.md), which the analysis script writes directly from the data.

Put simply, I measured 14 different aspects of Lagos rainfall for each of 20 years (how much fell, how heavy it was, how many stormy days there were, and so on) and tested which of them have genuinely changed and which differences could just be chance.

---

## 1. Background and problem statement

Climate change is expected to make heavy rainfall more intense in many tropical regions, because a warmer atmosphere holds more water vapour — roughly **7 % more per 1 °C of warming** (the Clausius–Clapeyron relationship; IPCC, 2021). Lagos is a low-lying coastal megacity with a bimodal rainy season (a long season peaking around June and a shorter one around September–October), rapid urban expansion and drainage channels that are often blocked. Severe floods — such as the widely reported July 2011 event — disrupt transport, damage homes and spread waterborne disease.

City planners usually design drains using **historical** rainfall statistics. If the rain has changed, those designs may already be out of date. Yet most people's sense that "the rain is heavier now" is based on memory, not measurement. This project replaces impressions with evidence.

## 2. Research questions and hypotheses

| # | Research question | Null hypothesis (H₀) | Alternative (H₁) |
|---|---|---|---|
| RQ1 | Has total annual rainfall changed since 2005? | No monotonic trend in annual rainfall | Significant increasing or decreasing trend |
| RQ2 | Has rainfall become more **intense** (more rain per wet day, more extreme days)? | No trend in SDII, Rx1day, Rx5day, R20mm, R50mm, R95p | Significant increase |
| RQ3 | Has the **timing/seasonality** of rainfall shifted? | No trend in monthly totals or PCI | Trend in one or more months |
| RQ4 | Was there an **abrupt shift** in rainfall, and do the two decades differ? | No change point; equal decade means | Significant change point / difference |
| RQ5 | Have **extreme storms** become more frequent? | Return levels unchanged between decades | Return period of a fixed storm has fallen |

All tests use a significance level of **α = 0.05** (5 %).

## 3. Study area

| Item | Value |
|---|---|
| Location | Lagos Metropolitan Area, south-west Nigeria |
| Analysis point | 6.5244° N, 3.3792° E (central Lagos) |
| Climate | Tropical savanna / monsoon (Köppen Aw–Am), bimodal rainy season |
| Why Lagos | One of Africa's largest and fastest-growing cities; low elevation; recurrent flooding |

The study point and period are set in [`config.yaml`](../config.yaml), so the whole project can be repeated for **any city in the world** by changing two numbers.

## 4. Data

| Dataset | Variable | Resolution | Access |
|---|---|---|---|
| **NASA POWER** (default) | `PRECTOTCORR` — bias-corrected total precipitation (mm/day) | Daily, 0.5° × 0.625° | Free API, no key |
| Open-Meteo / ERA5 (alternative) | `precipitation_sum` (mm/day) | Daily, ~0.25° | Free API, no key |
| Rain gauge (optional) | NiMet station data, CSV `date, precip_mm` | Daily, point | On request from NiMet |

**Quality control** (in `src/data_loader.py`):
1. Fill values (−999) and negative numbers are set to *missing*.
2. Every calendar day 2005-01-01 → 2024-12-31 is checked; missing days are made explicit.
3. Any year with more than 10 % missing days is excluded from the trend analysis.

One limitation applies throughout: gridded satellite/reanalysis data represent an area average tens of kilometres wide, so they usually show smaller extremes than a single rain gauge would. Trends from these products are generally more reliable than their absolute extreme values. Rerunning the analysis with ERA5 instead of NASA POWER (by changing `source:` in the config) is a simple robustness check.

## 5. Methodology

The workflow, step by step:

```
Daily rainfall (7,305 days)
   │  quality control
   ▼
14 annual climate indices  ──►  descriptive statistics, anomalies, CV, PCI
   │
   ├──► Trend: Mann-Kendall (+ pre-whitening) · Sen's slope · linear regression
   ├──► Seasonal trend: Mann-Kendall for each calendar month
   ├──► Change point: Pettitt test · decade comparison (Welch t, Mann-Whitney U)
   └──► Extremes: Gumbel fit · return levels · K-S goodness-of-fit
```

### 5.1 Rainfall indices (what is measured each year)

A **wet day** is a day with at least 1 mm of rain (the WMO/ETCCDI convention). Let $P_d$ be the rain on day $d$ of a year.

| Index | Formula | Meaning |
|---|---|---|
| ANNUAL | $\sum_d P_d$ | Total rain in the year |
| PRCPTOT | $\sum_{d:\,P_d \ge 1} P_d$ | Rain on wet days |
| WETDAYS | $\#\{d : P_d \ge 1\}$ | Number of wet days |
| SDII | $\text{PRCPTOT} / \text{WETDAYS}$ | Average rain per wet day (**intensity**) |
| Rx1day | $\max_d P_d$ | Wettest single day |
| Rx5day | $\max_d \sum_{k=0}^{4} P_{d-k}$ | Wettest 5-day period |
| R10mm, R20mm, R50mm | $\#\{d : P_d \ge 10, 20, 50\}$ | Heavy, very heavy and extreme days |
| R95p | $\sum_{d:\,P_d > P_{95}} P_d$ | Rain falling on the most extreme 5 % of wet days |
| R95pTOT | $100 \cdot \text{R95p} / \text{PRCPTOT}$ | % of the year's rain from extreme days |
| CDD / CWD | longest run of $P_d < 1$ / $P_d \ge 1$ | Longest dry / wet spell |

$P_{95}$ is the 95th percentile of all wet-day amounts in 2005–2024.

**Precipitation Concentration Index** (Oliver, 1980) measures how unevenly rain is spread through the year, using the 12 monthly totals $p_1 \dots p_{12}$:

$$
\text{PCI} = 100 \times \frac{\sum_{i=1}^{12} p_i^2}{\left(\sum_{i=1}^{12} p_i\right)^2}
$$

| PCI | Interpretation |
|---|---|
| ≤ 10 | Uniform — rain spread evenly over the year |
| 11–15 | Moderately seasonal |
| 16–20 | Seasonal |
| > 20 | Strongly irregular — most rain in a few months |

As a check, if every month had equal rain, PCI = 100/12 ≈ 8.3; if all the rain fell in one month, PCI = 100.

### 5.2 Descriptive statistics and anomalies

Mean $\bar{x} = \frac{1}{n}\sum x_i$, standard deviation $s = \sqrt{\frac{1}{n-1}\sum (x_i-\bar{x})^2}$ and the **coefficient of variation**

$$
\text{CV} = \frac{s}{\bar{x}} \times 100\%
$$

(CV < 20 % = low year-to-year variability, 20–30 % = moderate, > 30 % = high).

The **Standardized Anomaly Index** shows how unusual each year was:

$$
\text{SAI}_i = \frac{x_i - \bar{x}}{s}
$$

An SAI of +1.5 means the year was 1.5 standard deviations wetter than normal. Years beyond ±1 are treated as notably wet or dry.

### 5.3 Linear regression trend

The simplest trend model is a straight line $x_t = a + b\,t$, where the slope $b$ is the change per year:

$$
b = \frac{\sum (t_i - \bar{t})(x_i - \bar{x})}{\sum (t_i - \bar{t})^2}, \qquad a = \bar{x} - b\,\bar{t}
$$

The slope is tested with $t = b / SE(b)$ on $n-2$ degrees of freedom, and $R^2$ tells how much of the variation the line explains.

Regression alone isn't enough here. Rainfall is skewed and has outliers (one huge storm can tilt the line), and regression assumes normally distributed residuals. The main tests below are therefore non-parametric: they work with ranks and signs rather than raw values, so outliers have little influence. Regression is kept as a familiar point of comparison.

### 5.4 Mann-Kendall trend test (Mann, 1945; Kendall, 1975)

Compare every pair of years. If the later year is bigger, score +1; smaller, −1; equal, 0:

$$
S = \sum_{k=1}^{n-1} \sum_{j=k+1}^{n} \operatorname{sgn}(x_j - x_k), \qquad
\operatorname{sgn}(\theta) = \begin{cases} +1 & \theta > 0 \\ 0 & \theta = 0 \\ -1 & \theta < 0 \end{cases}
$$

If there is no trend, $S$ is close to 0. Its variance (correcting for tied values, where $t_g$ is the size of tie group $g$) is

$$
\operatorname{Var}(S) = \frac{n(n-1)(2n+5) - \sum_{g} t_g(t_g-1)(2t_g+5)}{18}
$$

and the standardised test statistic is

$$
Z = \begin{cases} \dfrac{S-1}{\sqrt{\operatorname{Var}(S)}} & S > 0 \\[2mm] 0 & S = 0 \\[1mm] \dfrac{S+1}{\sqrt{\operatorname{Var}(S)}} & S < 0 \end{cases}
\qquad
p = 2\left[1 - \Phi(|Z|)\right]
$$

If $|Z| > 1.96$ ($p < 0.05$) the trend is significant; the sign of $Z$ gives its direction. Kendall's $\tau = S / [n(n-1)/2]$ ranges from −1 to +1 like a correlation.

A small worked example: take rainfall in four years of 1, 3, 2 and 4 (hundreds of mm). The pairs score (1→3) +1, (1→2) +1, (1→4) +1, (3→2) −1, (3→4) +1, (2→4) +1, so S = 4. Then Var(S) = 4·3·13/18 = 8.67, Z = (4−1)/√8.67 = 1.02 and p = 0.31, which is not significant (four years is far too short a record). The same example is used as a check in `tests/test_stats.py`.

**Autocorrelation check.** Mann-Kendall assumes years are independent. If one wet year tends to follow another (lag-1 autocorrelation $r_1$ outside $\pm 1.96/\sqrt{n}$), false trends can appear. In that case the code also runs the **Trend-Free Pre-Whitening** version (Yue et al., 2002): remove the trend, remove the autocorrelation $y_t = x'_t - r_1 x'_{t-1}$, put the trend back, and test again.

### 5.5 Sen's slope estimator (Sen, 1968)

Mann-Kendall says *whether* there is a trend; Sen's slope says *how big* it is. Calculate the slope between every pair of years and take the **median**:

$$
\beta = \operatorname{median}\left( \frac{x_j - x_i}{t_j - t_i} \right), \qquad \text{for all } i < j
$$

With 20 years there are 190 pairwise slopes. Because it uses the median, one extreme year cannot distort it. The total change over the period and the percentage change are

$$
\Delta = \beta \,(t_{\text{end}} - t_{\text{start}}), \qquad \%\Delta = 100 \cdot \frac{\Delta}{\bar{x}}
$$

A 95 % confidence interval for $\beta$ is also reported.

### 5.6 Seasonal analysis

Mann-Kendall and Sen's slope are repeated for each calendar month (all Januaries, all Februaries…). This reveals whether, for example, June is getting wetter while August is getting drier — a shift in the rainy season that the annual total would hide.

### 5.7 Change-point detection — Pettitt test (Pettitt, 1979)

Did the rainfall "jump" in a particular year instead of changing gradually? For every possible split point $t$:

$$
U_t = \sum_{i=1}^{t} \sum_{j=t+1}^{n} \operatorname{sgn}(x_i - x_j), \qquad K = \max_t |U_t|
$$

The year where $|U_t|$ peaks is the most likely change point, with approximate significance

$$
p \approx 2 \exp\!\left( \frac{-6K^2}{n^3 + n^2} \right)
$$

### 5.8 Comparing the two decades

The years are split into 2005–2014 and 2015–2024 and compared with:

* **Welch's t-test** (compares means, does not assume equal variances):
  $t = \dfrac{\bar{x}_2 - \bar{x}_1}{\sqrt{s_1^2/n_1 + s_2^2/n_2}}$
* **Mann-Whitney U test** (non-parametric — compares the rank order of the two groups):
  $U = n_1 n_2 + \frac{n_1(n_1+1)}{2} - R_1$, where $R_1$ is the sum of ranks of group 1.

### 5.9 Extreme value analysis — Gumbel distribution

To design a drain, engineers ask: *"How much rain falls in the worst day of a typical 10-, 25- or 100-year period?"* The annual maximum daily rainfall (Rx1day) is fitted to the **Gumbel (Extreme Value Type I)** distribution:

$$
F(x) = \exp\!\left[ -\exp\!\left( -\frac{x-u}{\alpha} \right) \right]
$$

Parameters by the method of moments:

$$
\alpha = \frac{\sqrt{6}\, s}{\pi}, \qquad u = \bar{x} - 0.5772\,\alpha
$$

The **return level** $x_T$ — the rainfall exceeded on average once every $T$ years ($P(\text{exceed}) = 1/T$ in any year):

$$
x_T = u - \alpha \ln\!\left[ -\ln\!\left(1 - \frac{1}{T}\right) \right]
$$

and in reverse, the return period of a given rainfall $x$:

$$
T(x) = \frac{1}{1 - \exp\!\left[-\exp\!\left(-\frac{x-u}{\alpha}\right)\right]}
$$

Observed maxima are plotted using **Weibull plotting positions** $T = (n+1)/m$ (rank $m = 1$ for the largest). Fit quality is checked with the **Kolmogorov-Smirnov test** ($p > 0.05$ → the Gumbel fit is acceptable).

**Key test of change:** the Gumbel model is fitted separately to each decade. The first-decade 10-year storm $x_{10}^{(1)}$ is then inserted into the second-decade model to find its *new* return period $T^{(2)}(x_{10}^{(1)})$. If it is now, say, a 1-in-5-year event, that storm has become **twice as frequent** — which directly affects drainage design.

Note that "1-in-100-year" does not mean once a century. The chance of at least one such storm in any 30-year period is $1-(1-1/100)^{30} \approx 26\%$.

## 6. Results

All numbers, tables and figures are in [`results/RESULTS.md`](results/RESULTS.md), with the CSV tables in `results/tables/`. The figures are:

| Figure | What it shows | What to look for |
|---|---|---|
| `01_annual_rainfall_trend` | Annual totals with Sen and regression lines | Slope direction; are both lines similar? |
| `02_rainfall_anomaly` | Wet (blue) and dry (orange) years | Clusters of wet/dry years; extreme years beyond ±1 |
| `03_monthly_climatology_by_decade` | Average monthly rain, decade 1 vs 2 | Has the rainy-season peak moved or grown? |
| `04_monthly_heatmap` | Every month of every year | Unusually wet months (dark cells) |
| `05_extreme_rainfall_indices` | Rx1day, Rx5day, R50mm, SDII trends | Is intensity rising even if totals are not? |
| `06_return_levels_gumbel` | Return-level curves by decade | Is the red (recent) curve above the grey one? |
| `07_decade_boxplots` | Spread of values in each decade | Shift in median and in the upper whisker |

## 7. Discussion

**Totals versus intensity.** The clearest pattern in the results is that the amount of rain hasn't changed much, but the way it falls may have. Between the two decades, annual rainfall fell slightly (−3.5 %) and there were fewer wet days (−7 %). At the same time, the wettest day of the year rose by about 25 %, rain from extreme days by 24 %, and days with 50 mm or more went from 0.6 to 1.4 per year. Fewer but heavier rain days is the pattern expected in a warming climate, since warmer air holds more moisture. For flooding, the intensity matters more than the annual total.

**Statistical versus practical significance.** None of these changes passes the 5 % significance test, which is not surprising with only 20 years of data: a real change of 15–25 % can easily fail to be detected over a period this short. For that reason I report the Sen's slope and its confidence interval alongside each p-value, and describe the changes as indications rather than confirmed trends.

**Natural variability.** West African rainfall is strongly controlled by the West African Monsoon, Atlantic sea-surface temperatures and ENSO, all of which vary over several years. A 20-year window can be dominated by these cycles, so part of the difference between the two decades may be natural variability rather than long-term climate change.

**Link to flooding.** The indices that matter most for urban flooding are Rx1day, R50mm and the return levels, because drains are designed around short, intense storms. The rise in the 10-year design storm, from about 87 mm to 119 mm per day, is directly relevant to drainage design and feeds into the flood model in [Project 2](../project2_urban_flood_risk/README.md).

## 8. Limitations

* **Short record:** 20 years is short for climate trends (WMO recommends 30-year normals); results describe *recent change*, not long-term climate change.
* **Gridded data:** area-averaged products underestimate point extremes; validation with NiMet rain-gauge data is recommended.
* **Single point:** Lagos is large; rainfall differs between, e.g., the Island and the mainland.
* **Multiple testing:** 14 indices + 12 months are tested; at α = 0.05 about one "significant" result could appear by chance. A Bonferroni or false-discovery-rate correction can be applied as an extension.
* **Stationary Gumbel per decade:** 10 values per decade make decade-specific return levels uncertain. A non-stationary GEV model with time-varying location is a natural next step.

## 9. Conclusions and recommendations

These conclusions are based on NASA POWER daily rainfall for central Lagos, 2005–2024. All 7,305 days were available, with no missing data.

1. **No statistically significant trend.** None of the 14 rainfall indices and none of the 12 calendar months shows a significant Mann-Kendall trend at the 5 % level. Mean annual rainfall is 1,588 mm with moderate year-to-year variability (CV = 17.2 %), and the Pettitt test finds no significant change point (p = 0.88). With only 20 years of data, this means changes cannot be *confirmed*, not that they are absent.
2. **Totals flat, extremes pointing upward.** The direction of change differs between totals and extremes. Annual rainfall fell slightly between the two decades (−3.5 %) and there were fewer wet days (−7.1 %). Meanwhile the wettest day of the year rose by 24.6 %, rain from extreme days (> P95) by 24.3 %, and days with ≥ 50 mm went from 0.6 to 1.4 per year. This "fewer but heavier rain days" pattern is what climate science expects under warming, but none of these differences is statistically significant (all p > 0.09), so they should be treated as *indications* that need a longer record.
3. **The 10-year storm has become more frequent in the model.** The Gumbel fit is acceptable (K-S p = 0.48). The 1-in-10-year daily rainfall was 87 mm in 2005–2014; in the 2015–2024 fit, the same storm behaves like a **1-in-3.7-year** event, and the 10-year design storm rises from 87 to 119 mm. Each decade has only 10 annual maxima, so these decade-specific return levels are uncertain.
4. **Recommendations:**
   * Review Lagos drainage design rainfall (IDF curves) with recent data rather than older records, and consider a climate-change uplift factor for extremes.
   * Strengthen rain-gauge monitoring (NiMet) and validate these satellite/reanalysis results against gauges, which capture point extremes better.
   * Extend the record (e.g. ERA5 back to 1980) and apply a non-stationary GEV model to confirm or reject the apparent rise in extremes. *Update, November 2026:* done for 1981–2024 with three datasets (ERA5, NASA POWER, CHIRPS). They disagree: none shows a consistent trend in total rainfall or in the wettest day, and the gauge-based CHIRPS record does not support the rise in extremes suggested by the 2005–2024 data. See [LONG_RECORD_CHECK.md](LONG_RECORD_CHECK.md).

## 10. How to reproduce

```bash
pip install -r requirements.txt
python project1_rainfall_trends/analysis.py
```

## References

* Gumbel, E. J. (1958). *Statistics of Extremes*. Columbia University Press.
* Hersbach, H., et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*, 146, 1999–2049.
* IPCC (2021). *Climate Change 2021: The Physical Science Basis*. Contribution of Working Group I to the Sixth Assessment Report. Cambridge University Press.
* Kendall, M. G. (1975). *Rank Correlation Methods* (4th ed.). Charles Griffin, London.
* Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica*, 13(3), 245–259.
* NASA Langley Research Center. *Prediction Of Worldwide Energy Resources (POWER) Project*. https://power.larc.nasa.gov
* Oliver, J. E. (1980). Monthly precipitation distribution: a comparative index. *The Professional Geographer*, 32(3), 300–309.
* Pettitt, A. N. (1979). A non-parametric approach to the change-point problem. *Journal of the Royal Statistical Society, Series C*, 28(2), 126–135.
* Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *Journal of the American Statistical Association*, 63(324), 1379–1389.
* Yue, S., Pilon, P., Phinney, B., & Cavadias, G. (2002). The influence of autocorrelation on the ability to detect trend in hydrological series. *Hydrological Processes*, 16(9), 1807–1829.
* Zhang, X., et al. (2011). Indices for monitoring changes in extremes based on daily temperature and precipitation data. *WIREs Climate Change*, 2(6), 851–870.
