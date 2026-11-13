"""
PROJECT 1 — Changing Rainfall Patterns and Extreme-Rainfall Trends (2005–2024)

Run from the repository root:
    python project1_rainfall_trends/analysis.py            # real data
    python project1_rainfall_trends/analysis.py --demo     # offline test with fake data

Outputs (in project1_rainfall_trends/results/):
    figures/*.png, tables/*.csv and RESULTS.md (auto-written summary of findings)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from src import climate_indices as ci  # noqa: E402
from src import stats_tools as st  # noqa: E402
from src.data_loader import load_config, load_rainfall  # noqa: E402
from src.plotting import BLUE, GREY, ORANGE, RED, finish, plt  # noqa: E402

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def run(demo=False, cfg=None):
    cfg = cfg or load_config()
    alpha = cfg["statistics"]["significance_level"]
    out = HERE / ("results_demo" if demo else "results")
    (out / "figures").mkdir(parents=True, exist_ok=True)
    (out / "tables").mkdir(parents=True, exist_ok=True)

    print("PROJECT 1 — rainfall trends")
    daily = load_rainfall(cfg, demo=demo)
    src = daily.attrs["source"]
    wet = cfg["data"]["wet_day_threshold_mm"]

    # ---------------- 1. indices ------------------------------------------
    p95 = ci.wet_day_percentile(daily, 0.95, wet)
    idx = ci.annual_indices(daily, wet, cfg["data"]["max_missing_fraction"], p95)
    idx.round(3).to_csv(out / "tables" / "annual_indices.csv")
    valid = idx.dropna(subset=["ANNUAL"])
    years = valid.index.values.astype(float)
    mon = ci.monthly_table(daily)
    mon.round(1).to_csv(out / "tables" / "monthly_rainfall_matrix.csv")

    # ---------------- 2. descriptive + anomalies ---------------------------
    desc = st.describe(valid["ANNUAL"])
    valid = valid.assign(SAI=st.standardized_anomaly(valid["ANNUAL"]))

    # ---------------- 3. trend tests on every index ------------------------
    trend_rows = []
    for col in ci.INDEX_INFO:
        r = st.trend_report(years, valid[col].values, alpha)
        r["index"] = col
        r["description"], r["unit"] = ci.INDEX_INFO[col]
        trend_rows.append(r)
    trends = pd.DataFrame(trend_rows).set_index("index")
    trends.round(4).to_csv(out / "tables" / "trend_tests.csv")

    # ---------------- 4. monthly (seasonal) trends -------------------------
    mrows = []
    for m in range(1, 13):
        col = mon[m].dropna()
        mk = st.mann_kendall(col.values, alpha)
        ss = st.sens_slope(col.index.values, col.values)
        mrows.append({"month": MONTHS[m - 1], "mean_mm": col.mean(),
                      "sen_slope_mm_per_yr": ss["slope"], "mk_Z": mk["Z"], "mk_p": mk["p"],
                      "trend": mk["trend"]})
    mtrend = pd.DataFrame(mrows).set_index("month")
    mtrend.round(4).to_csv(out / "tables" / "monthly_trends.csv")

    # ---------------- 5. change point + decade comparison ------------------
    pt = st.pettitt(valid["ANNUAL"].values)
    cp_year = int(valid.index[pt["last_index_before_change"]])
    mid = int(np.floor((years.min() + years.max()) / 2))
    first, second = valid[valid.index <= mid], valid[valid.index > mid]
    comp_rows = []
    for col in ["ANNUAL", "WETDAYS", "SDII", "Rx1day", "Rx5day", "R20mm", "R50mm", "R95p"]:
        c = st.compare_periods(first[col], second[col])
        c["index"] = col
        comp_rows.append(c)
    comp = pd.DataFrame(comp_rows).set_index("index")
    comp.round(4).to_csv(out / "tables" / "decade_comparison.csv")

    # ---------------- 6. extreme value analysis ----------------------------
    gb = st.gumbel_fit(valid["Rx1day"].values)
    T = np.array(cfg["statistics"]["return_periods_years"], float)
    rl = st.gumbel_return_level(gb["u"], gb["alpha"], T)
    # how has the 10-year storm changed between the two decades?
    gb1, gb2 = st.gumbel_fit(first["Rx1day"].values), st.gumbel_fit(second["Rx1day"].values)
    rl1 = st.gumbel_return_level(gb1["u"], gb1["alpha"], T)
    rl2 = st.gumbel_return_level(gb2["u"], gb2["alpha"], T)
    ret = pd.DataFrame({"return_period_yr": T, "rx1day_all_years_mm": rl,
                        f"rx1day_{int(first.index.min())}_{int(first.index.max())}_mm": rl1,
                        f"rx1day_{int(second.index.min())}_{int(second.index.max())}_mm": rl2})
    ret.round(2).to_csv(out / "tables" / "return_levels.csv", index=False)
    old10 = st.gumbel_return_level(gb1["u"], gb1["alpha"], 10.0)
    new_T_of_old10 = float(st.gumbel_return_period(gb2["u"], gb2["alpha"], old10))

    # ======================= FIGURES =======================================
    F = out / "figures"
    yrs = valid.index.values

    # Fig 1: annual totals with trends
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(yrs, valid["ANNUAL"], color=BLUE, alpha=0.75, label="Annual rainfall")
    ss = st.sens_slope(years, valid["ANNUAL"].values)
    lr = st.linear_trend(years, valid["ANNUAL"].values)
    ax.plot(yrs, ss["intercept"] + ss["slope"] * years, color=RED, lw=2,
            label=f"Sen's slope: {ss['slope']:+.1f} mm/yr")
    ax.plot(yrs, lr["intercept"] + lr["slope"] * years, color=ORANGE, lw=1.5, ls="--",
            label=f"Linear fit: {lr['slope']:+.1f} mm/yr (R²={lr['r2']:.2f})")
    ax.axhline(desc["mean"], color=GREY, lw=1, ls=":", label=f"Mean = {desc['mean']:.0f} mm")
    ax.set(title="Annual rainfall and trend", xlabel="Year", ylabel="Rainfall (mm)")
    ax.legend(loc="upper left", fontsize=8)
    finish(fig, F / "01_annual_rainfall_trend.png", src, demo)

    # Fig 2: standardized anomaly
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.bar(yrs, valid["SAI"], color=np.where(valid["SAI"] >= 0, BLUE, ORANGE))
    for y_ in (1, -1):
        ax.axhline(y_, color=GREY, lw=0.8, ls="--")
    ax.set(title="Standardized rainfall anomaly (wet years blue, dry years orange)",
           xlabel="Year", ylabel="Anomaly (standard deviations)")
    finish(fig, F / "02_rainfall_anomaly.png", src, demo)

    # Fig 3: monthly climatology by decade
    fig, ax = plt.subplots(figsize=(9, 4))
    w = 0.4
    x = np.arange(12)
    m1 = mon.loc[mon.index <= mid].mean()
    m2 = mon.loc[mon.index > mid].mean()
    ax.bar(x - w / 2, m1.values, w, color=GREY, label=f"{int(first.index.min())}–{mid}")
    ax.bar(x + w / 2, m2.values, w, color=BLUE, label=f"{mid + 1}–{int(second.index.max())}")
    ax.set_xticks(x, MONTHS)
    ax.set(title="Average monthly rainfall: first vs second decade", ylabel="Rainfall (mm)")
    ax.legend()
    finish(fig, F / "03_monthly_climatology_by_decade.png", src, demo)

    # Fig 4: heatmap
    fig, ax = plt.subplots(figsize=(9, 5.2))
    im = ax.imshow(mon.values, aspect="auto", cmap="Blues")
    ax.set_xticks(range(12), MONTHS)
    ax.set_yticks(range(len(mon.index)), mon.index)
    ax.set(title="Monthly rainfall (mm) — every month, every year")
    fig.colorbar(im, ax=ax, label="mm")
    finish(fig, F / "04_monthly_heatmap.png", src, demo)

    # Fig 5: extremes panel
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.5))
    for ax, col, color in zip(axs.flat, ["Rx1day", "Rx5day", "R50mm", "SDII"], [RED, ORANGE, BLUE, "#7c3aed"]):
        v = valid[col].values.astype(float)
        s2 = st.sens_slope(years, v)
        mk = st.mann_kendall(v, alpha)
        ax.plot(yrs, v, "o-", color=color, ms=4)
        ax.plot(yrs, s2["intercept"] + s2["slope"] * years, color="black", lw=1.2, ls="--")
        name, unit = ci.INDEX_INFO[col]
        ax.set_title(f"{name}\nSen {s2['slope']:+.2f} {unit}/yr, MK p={fmt_p(mk['p'])}", fontsize=9.5)
        ax.set_ylabel(unit)
    finish(fig, F / "05_extreme_rainfall_indices.png", src, demo)

    # Fig 6: return levels
    fig, ax = plt.subplots(figsize=(8, 4.5))
    xe, Te = st.weibull_plotting_positions(valid["Rx1day"].values)
    Ts = np.logspace(np.log10(1.05), 2, 100)
    ax.semilogx(Ts, st.gumbel_return_level(gb["u"], gb["alpha"], Ts), color=BLUE, label="Gumbel fit (all years)")
    ax.semilogx(Ts, st.gumbel_return_level(gb1["u"], gb1["alpha"], Ts), color=GREY, ls="--", label="Gumbel, first decade")
    ax.semilogx(Ts, st.gumbel_return_level(gb2["u"], gb2["alpha"], Ts), color=RED, ls="--", label="Gumbel, second decade")
    ax.scatter(Te, xe, color="black", s=18, zorder=3, label="Observed annual maxima")
    ax.set(title="How big is the 'once-in-T-years' rainstorm?", xlabel="Return period T (years)",
           ylabel="1-day rainfall (mm)")
    ax.legend(fontsize=8)
    finish(fig, F / "06_return_levels_gumbel.png", src, demo)

    # Fig 7: decade box plots
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.8))
    for ax, col in zip(axs, ["ANNUAL", "Rx1day", "R20mm"]):
        bp = ax.boxplot([first[col].dropna(), second[col].dropna()], patch_artist=True,
                        tick_labels=[f"≤{mid}", f">{mid}"])
        for patch, c in zip(bp["boxes"], [GREY, BLUE]):
            patch.set_facecolor(c)
            patch.set_alpha(0.6)
        ax.set_title(ci.INDEX_INFO[col][0], fontsize=9.5)
        ax.set_ylabel(ci.INDEX_INFO[col][1])
    finish(fig, F / "07_decade_boxplots.png", src, demo)

    # ======================= RESULTS.md ====================================
    sig = trends[trends["mk_p"] < alpha]
    lines = []
    if demo:
        lines += ["> ⚠️ **SYNTHETIC DEMO DATA — these numbers are NOT real and must not be reported.**", ""]
    lines += [
        f"# Project 1 Results — {cfg['study_area']['name']}, {int(years.min())}–{int(years.max())}",
        "",
        f"*Auto-generated by `analysis.py`. Data source: {src}. Years analysed: {len(valid)}. "
        f"Wet-day threshold: {wet} mm. 95th-percentile wet-day rainfall: {p95:.1f} mm.*",
        "",
        "## 1. Headline numbers",
        "",
        "| Statistic | Value |",
        "|---|---|",
        f"| Mean annual rainfall | {desc['mean']:.0f} mm |",
        f"| Standard deviation | {desc['sd']:.0f} mm |",
        f"| Coefficient of variation | {desc['cv_percent']:.1f} % |",
        f"| Wettest year | {int(valid['ANNUAL'].idxmax())} ({valid['ANNUAL'].max():.0f} mm) |",
        f"| Driest year | {int(valid['ANNUAL'].idxmin())} ({valid['ANNUAL'].min():.0f} mm) |",
        f"| Wettest single day | {valid['Rx1day'].max():.1f} mm in {int(valid['Rx1day'].idxmax())} |",
        f"| Mean PCI | {valid['PCI'].mean():.1f} |",
        "",
        "## 2. Trend tests (Mann-Kendall + Sen's slope + linear regression)",
        "",
        "| Index | Mean | Sen's slope /yr | Change over period | MK Z | MK p | Result |",
        "|---|---|---|---|---|---|---|",
    ]
    for k, r in trends.iterrows():
        res = r["mk_trend"]
        if r["autocorrelated"]:
            res += f" (TFPW p={fmt_p(r['tfpw_p'])})"
        lines.append(f"| {r['description']} ({r['unit']}) | {r['mean']:.1f} | {r['sen_slope_per_yr']:+.3f} | "
                     f"{r['sen_percent_change']:+.1f} % | {r['mk_Z']:+.2f} | {fmt_p(r['mk_p'])} | {res} |")
    lines += ["", "**Interpretation (plain English):** "]
    if len(sig):
        parts = [f"{r['description'].lower()} ({'up' if r['mk_Z'] > 0 else 'down'} {abs(r['sen_percent_change']):.0f} % over the period)"
                 for _, r in sig.iterrows()]
        lines.append("Statistically significant changes (5 % level) were found in: " + "; ".join(parts) + ".")
    else:
        lines.append("No index shows a statistically significant trend at the 5 % level. With only "
                     f"{len(valid)} years of data, modest trends may exist but cannot be confirmed — "
                     "report the direction and size of the Sen's slope, but describe it as 'not significant'.")
    lines += [
        "",
        "## 3. Seasonal (monthly) trends",
        "",
        "| Month | Mean (mm) | Sen's slope (mm/yr) | MK p | Result |",
        "|---|---|---|---|---|",
    ]
    for mname, r in mtrend.iterrows():
        lines.append(f"| {mname} | {r['mean_mm']:.0f} | {r['sen_slope_mm_per_yr']:+.2f} | {fmt_p(r['mk_p'])} | {r['trend']} |")
    lines += [
        "",
        "## 4. Change point and decade comparison",
        "",
        f"Pettitt test on annual rainfall: K = {pt['K']:.0f}, p = {fmt_p(pt['p'])}. Most probable shift after "
        f"**{cp_year}** (mean {pt['mean_before']:.0f} mm before vs {pt['mean_after']:.0f} mm after) — "
        + ("**statistically significant**." if pt["p"] < alpha else "not statistically significant."),
        "",
        f"| Index | {int(first.index.min())}–{mid} mean | {mid + 1}–{int(second.index.max())} mean | % change | Welch p | Mann-Whitney p |",
        "|---|---|---|---|---|---|",
    ]
    for k, r in comp.iterrows():
        lines.append(f"| {ci.INDEX_INFO[k][0]} | {r['mean_1']:.1f} | {r['mean_2']:.1f} | {r['percent_change']:+.1f} % | "
                     f"{fmt_p(r['welch_p'])} | {fmt_p(r['mannwhitney_p'])} |")
    lines += [
        "",
        "## 5. Extreme rainfall return levels (Gumbel)",
        "",
        f"Gumbel parameters (all years): location u = {gb['u']:.1f} mm, scale α = {gb['alpha']:.1f} mm. "
        f"Kolmogorov-Smirnov goodness-of-fit p = {fmt_p(gb['ks_p'])} "
        + ("(Gumbel fits acceptably)." if gb["ks_p"] > 0.05 else "(Gumbel fit is questionable — consider GEV)."),
        "",
        "| Return period (years) | 1-day rainfall, all years (mm) | first decade (mm) | second decade (mm) |",
        "|---|---|---|---|",
    ]
    for i, t_ in enumerate(T):
        lines.append(f"| {int(t_)} | {rl[i]:.1f} | {rl1[i]:.1f} | {rl2[i]:.1f} |")
    lines += [
        "",
        f"**Key finding:** the storm that was a *1-in-10-year* event in the first decade ({old10:.0f} mm/day) "
        f"behaves like a **1-in-{new_T_of_old10:.1f}-year** event in the second decade "
        + ("— it has become more frequent." if new_T_of_old10 < 10 else "— it has become rarer."),
        "",
        "## 6. Figures",
        "",
    ]
    for f in sorted(F.glob("*.png")):
        lines.append(f"![{f.stem}](figures/{f.name})")
        lines.append("")
    (out / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  Done → {out.relative_to(HERE.parent)}/RESULTS.md")
    return {"indices": idx, "trends": trends, "daily": daily}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="use synthetic data (offline test only)")
    run(demo=ap.parse_args().demo)
