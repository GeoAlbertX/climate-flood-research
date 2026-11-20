"""
PROJECT 2 — Urban Growth, Rainfall Change and Flood Risk: Testing Sustainable
Drainage (SuDS) Strategies (2005–2024)

Run from the repository root:
    python project2_urban_flood_risk/analysis.py            # real data
    python project2_urban_flood_risk/analysis.py --demo     # offline test with fake data

Outputs (in project2_urban_flood_risk/results/): figures, tables and RESULTS.md
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from src import hydrology as hy  # noqa: E402
from src import stats_tools as st  # noqa: E402
from src.data_loader import load_config, load_rainfall  # noqa: E402
from src.plotting import BLUE, GREEN, GREY, ORANGE, PURPLE, RED, finish, plt  # noqa: E402


def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def run(demo=False, cfg=None):
    cfg = cfg or load_config()
    alpha = cfg["statistics"]["significance_level"]
    u = cfg["urban"]
    out = HERE / ("results_demo" if demo else "results")
    (out / "figures").mkdir(parents=True, exist_ok=True)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    F = out / "figures"

    print("PROJECT 2 — urban flood risk")
    daily = load_rainfall(cfg, demo=demo)
    src = daily.attrs["source"]
    y0, y1 = cfg["period"]["start_year"], cfg["period"]["end_year"]
    yrs = np.arange(y0, y1 + 1)

    f_imp = hy.impervious_series(yrs, u["impervious_fraction_by_year"])
    f_fixed = pd.Series(f_imp.iloc[0], index=yrs)          # land cover frozen at start year
    f_final = pd.Series(f_imp.iloc[-1], index=yrs)         # today's city

    # ---------------- 1. simulations --------------------------------------
    combined = hy.annual_flood_metrics(hy.simulate_runoff(daily, f_imp, u))
    climate_only = hy.annual_flood_metrics(hy.simulate_runoff(daily, f_fixed, u))
    combined.round(4).to_csv(out / "tables" / "annual_flood_metrics_combined.csv")
    climate_only.round(4).to_csv(out / "tables" / "annual_flood_metrics_climate_only.csv")

    # ---------------- 2. trend statistics ---------------------------------
    t = yrs.astype(float)
    rows = []
    for name, df in [("Climate + urban growth", combined), ("Climate only (land use fixed)", climate_only)]:
        for col in ["flood_days", "excess_volume_m3", "runoff_coeff", "max_daily_runoff_mm"]:
            r = st.trend_report(t, df[col].values, alpha)
            r.update({"scenario": name, "variable": col})
            rows.append(r)
    trends = pd.DataFrame(rows).set_index(["scenario", "variable"])
    trends.round(5).to_csv(out / "tables" / "trend_tests.csv")

    pois = st.poisson_trend(t, combined["flood_days"].values)
    pois_c = st.poisson_trend(t, climate_only["flood_days"].values)

    # ---------------- 3. attribution: climate vs urbanisation -------------
    mid = (y0 + y1) // 2
    early = combined.index <= mid
    late = ~early
    def dmean(df, col):
        return df.loc[late, col].mean() - df.loc[early, col].mean()
    attr = {}
    for col in ["flood_days", "excess_volume_m3", "runoff_mm"]:
        total = dmean(combined, col)
        clim = dmean(climate_only, col)
        # a share is only meaningful when the total change is not close to zero
        # (less than 1 % of the variable's mean would give nonsense like 2,000 %)
        meaningful = abs(total) >= 0.01 * abs(combined[col].mean())
        attr[col] = {"total_change": total, "climate_part": clim, "urban_part": total - clim,
                     "urban_share_percent": 100 * (total - clim) / total if meaningful else np.nan}
    attr_df = pd.DataFrame(attr).T
    attr_df.round(3).to_csv(out / "tables" / "attribution_climate_vs_urban.csv")

    # ---------------- 4. SuDS scenarios on today's city -------------------
    srows = []
    for sc in cfg["suds_scenarios"]:
        sim = hy.simulate_runoff(daily, f_final, u, sc["disconnected_impervious"],
                                 sc["extra_storage_mm"], sc["capacity_multiplier"])
        a = hy.annual_flood_metrics(sim)
        srows.append({"scenario": sc["name"], "flood_days_per_yr": a["flood_days"].mean(),
                      "excess_m3_per_yr": a["excess_volume_m3"].mean(),
                      "runoff_coeff": a["runoff_coeff"].mean()})
    suds = pd.DataFrame(srows).set_index("scenario")
    base = suds.iloc[0]
    suds["flood_days_reduction_%"] = 100 * (1 - suds["flood_days_per_yr"] / base["flood_days_per_yr"]) if base["flood_days_per_yr"] else 0
    suds["volume_reduction_%"] = 100 * (1 - suds["excess_m3_per_yr"] / base["excess_m3_per_yr"]) if base["excess_m3_per_yr"] else 0
    suds.round(3).to_csv(out / "tables" / "suds_scenarios.csv")

    # ---------------- 5. one-at-a-time sensitivity analysis ---------------
    def mean_flood_days(ucfg, fser):
        return hy.annual_flood_metrics(hy.simulate_runoff(daily, fser, ucfg))["flood_days"].mean()
    ref = mean_flood_days(u, f_final)
    sens = []
    for label, key, lo, hi in [
        ("Drainage capacity ±20 %", "drainage_capacity_mm_per_day", 0.8, 1.2),
        ("Pervious CN ±5 %", "pervious_curve_number", 0.95, 1.05),
        ("Initial abstraction ratio 0.05 vs 0.30", "initial_abstraction_ratio", None, None),
    ]:
        if key == "initial_abstraction_ratio":
            vlo = mean_flood_days({**u, key: 0.05}, f_final)
            vhi = mean_flood_days({**u, key: 0.30}, f_final)
        else:
            vlo = mean_flood_days({**u, key: u[key] * lo}, f_final)
            vhi = mean_flood_days({**u, key: min(u[key] * hi, 99) if "curve" in key else u[key] * hi}, f_final)
        sens.append({"parameter": label, "low": vlo, "high": vhi})
    vlo = mean_flood_days(u, (f_final * 0.9).clip(0, 1))
    vhi = mean_flood_days(u, (f_final * 1.1).clip(0, 1))
    sens.append({"parameter": "Impervious fraction ±10 %", "low": vlo, "high": vhi})
    sens = pd.DataFrame(sens).set_index("parameter")
    sens["range"] = (sens["high"] - sens["low"]).abs()
    sens = sens.sort_values("range")
    sens.round(3).to_csv(out / "tables" / "sensitivity.csv")

    # ---------------- 6. optional validation with real flood records ------
    val_text = ""
    ev_path = ROOT / "data" / "flood_events.csv"
    if ev_path.exists() and not demo:
        ev = pd.read_csv(ev_path)
        if len(ev):
            ev["year"] = pd.to_datetime(ev["date"]).dt.year
            obs = ev.groupby("year").size().reindex(yrs, fill_value=0)
            rho, p = stats.spearmanr(obs.values, combined["flood_days"].values)
            pd.DataFrame({"observed_events": obs, "model_flood_days": combined["flood_days"]}).to_csv(
                out / "tables" / "validation_observed_vs_model.csv")
            val_text = (f"Recorded flood events ({len(ev)} entries in `data/flood_events.csv`) vs modelled "
                        f"flood days per year: Spearman ρ = {rho:.2f}, p = {fmt_p(p)}. "
                        + ("The model reproduces the year-to-year pattern of real floods."
                           if p < alpha and rho > 0 else
                           "The agreement is weak — see the limitations section of the report."))

    # ======================= FIGURES =======================================
    # Fig 1: SCS curves (conceptual)
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    P = np.linspace(0, 200, 300)
    for f, c in [(0.2, GREEN), (0.45, BLUE), (0.6, ORANGE), (0.8, RED)]:
        Q = f * hy.scs_runoff(P, u["impervious_curve_number"]) + (1 - f) * hy.scs_runoff(P, u["pervious_curve_number"])
        ax.plot(P, Q, color=c, lw=2, label=f"{int(f * 100)} % paved")
    ax.plot(P, P, color=GREY, ls=":", label="All rain becomes runoff")
    ax.set(title="Same rain, more concrete → more runoff (SCS Curve Number)",
           xlabel="Daily rainfall P (mm)", ylabel="Runoff Q (mm)")
    ax.legend(fontsize=8)
    finish(fig, F / "01_scs_runoff_curves.png", "SCS-CN equations (conceptual)", False)

    # Fig 2: impervious + runoff coefficient
    fig, ax1 = plt.subplots(figsize=(9, 4))
    ax1.plot(yrs, 100 * f_imp.values, color=GREY, lw=2, label="Impervious area (%) — input")
    ax1.set_ylabel("Impervious area (%)")
    ax2 = ax1.twinx()
    ax2.plot(yrs, combined["runoff_coeff"], "o-", color=BLUE, label="Runoff coefficient Q/P")
    ax2.set_ylabel("Runoff coefficient")
    ax2.grid(False)
    ax1.set(title="Urban growth and the share of rain that becomes runoff", xlabel="Year")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    finish(fig, F / "02_impervious_and_runoff_coefficient.png", src, demo)

    # Fig 3: flood days climate-only vs combined
    fig, ax = plt.subplots(figsize=(9, 4.2))
    w = 0.4
    ax.bar(yrs - w / 2, climate_only["flood_days"], w, color=GREY, label="Climate only (2005 land use)")
    ax.bar(yrs + w / 2, combined["flood_days"], w, color=RED, alpha=0.8, label="Climate + urban growth")
    if pois:
        ax.plot(yrs, pois["fitted"], color="black", lw=1.5, ls="--",
                label=f"Poisson trend: ×{pois['irr']:.3f} per year")
    ax.set(title="Drainage-overload (flood) days per year", xlabel="Year", ylabel="Days")
    ax.legend(fontsize=8)
    finish(fig, F / "03_flood_days_per_year.png", src, demo)

    # Fig 4: excess volume
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.fill_between(yrs, climate_only["excess_volume_m3"] / 1e6, color=GREY, alpha=0.5, label="Climate only")
    ax.plot(yrs, combined["excess_volume_m3"] / 1e6, "o-", color=RED, label="Climate + urban growth")
    ax.set(title="Floodwater the drains could not carry", xlabel="Year", ylabel="Excess volume (million m³)")
    ax.legend(fontsize=8)
    finish(fig, F / "04_excess_flood_volume.png", src, demo)

    # Fig 5: SuDS
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    cols = [GREY, GREEN, GREEN, PURPLE, BLUE][: len(suds)]
    axs[0].barh(suds.index, suds["flood_days_per_yr"], color=cols)
    axs[0].set(title="Average flood days per year", xlabel="Days")
    axs[0].invert_yaxis()
    axs[1].barh(suds.index, suds["volume_reduction_%"], color=cols)
    axs[1].set(title="Reduction in flood volume vs business as usual", xlabel="%")
    axs[1].invert_yaxis()
    axs[1].set_yticklabels([])
    finish(fig, F / "05_suds_scenarios.png", src, demo)

    # Fig 6: sensitivity tornado
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for i, (name, r) in enumerate(sens.iterrows()):
        lo, hi = sorted([r["low"], r["high"]])
        ax.barh(i, hi - lo, left=lo, color=ORANGE, alpha=0.8)
    ax.axvline(ref, color="black", lw=1, label=f"Reference = {ref:.1f} days/yr")
    ax.set_yticks(range(len(sens)), sens.index)
    ax.set(title="Which assumption matters most? (sensitivity)", xlabel="Average flood days per year")
    ax.legend(fontsize=8)
    finish(fig, F / "06_sensitivity_tornado.png", src, demo)

    # ======================= RESULTS.md ====================================
    tc = trends.loc["Climate + urban growth"]
    to = trends.loc["Climate only (land use fixed)"]
    L = []
    if demo:
        L += ["> **SYNTHETIC DEMO DATA — these numbers are NOT real and must not be reported.**", ""]
    L += [
        f"# Project 2 Results — {cfg['study_area']['name']}, {y0}–{y1}",
        "",
        f"*Produced by `analysis.py`. Rainfall: {src}. Catchment {u['catchment_area_km2']} km², drainage capacity "
        f"{u['drainage_capacity_mm_per_day']} mm/day, CN pervious {u['pervious_curve_number']} / impervious "
        f"{u['impervious_curve_number']}. Impervious fraction {100 * f_imp.iloc[0]:.0f} % → {100 * f_imp.iloc[-1]:.0f} % "
        "(GHSL built-up surface, set in `config.yaml`).*",
        "",
        "## 1. Flood-trend statistics",
        "",
        "| Variable | Scenario | Mean | Sen's slope /yr | % change over period | MK p | Result |",
        "|---|---|---|---|---|---|---|",
    ]
    names = {"flood_days": "Flood days/yr", "excess_volume_m3": "Excess volume (m³/yr)",
             "runoff_coeff": "Runoff coefficient", "max_daily_runoff_mm": "Max daily runoff (mm)"}
    for var, nm in names.items():
        for scn, tbl in [("Climate + urban", tc), ("Climate only", to)]:
            r = tbl.loc[var]
            L.append(f"| {nm} | {scn} | {r['mean']:.3g} | {r['sen_slope_per_yr'] + 0.0:+.3g} | "
                     f"{r['sen_percent_change'] + 0.0:+.1f} % | {fmt_p(r['mk_p'])} | {r['mk_trend']} |")
    if pois:
        L += ["",
              f"**Poisson regression of flood days (climate + urban):** IRR = {pois['irr']:.3f} "
              f"(95 % CI {pois['irr_ci_low']:.3f}–{pois['irr_ci_high']:.3f}), p = {fmt_p(pois['p'])}, "
              f"dispersion = {pois['dispersion']:.2f}"
              + (f" (overdispersed → quasi-Poisson p = {fmt_p(pois['p_quasi'])})" if pois["dispersion"] > 1.5 else "")
              + f". This means the expected number of flood days changes by "
              f"**{100 * (pois['irr'] - 1):+.1f} % per year**, i.e. ×{pois['irr'] ** (y1 - y0):.2f} over {y1 - y0} years."]
    if pois_c:
        L.append(f"With land use frozen at {y0}, the same model gives IRR = {pois_c['irr']:.3f} (p = {fmt_p(pois_c['p'])}).")
    L += ["", "## 2. Attribution — how much is climate, how much is urban growth?", "",
          f"Change in the average of {mid + 1}–{y1} compared with {y0}–{mid}:", "",
          "| Quantity | Total change | Due to rainfall change | Due to urban growth | Urban share |",
          "|---|---|---|---|---|"]
    for k, r in attr_df.iterrows():
        share = ("n/a (total change close to zero)" if pd.isna(r["urban_share_percent"])
                 else f"{r['urban_share_percent']:.0f} %")
        L.append(f"| {k} | {r['total_change']:+.3g} | {r['climate_part']:+.3g} | {r['urban_part']:+.3g} | {share} |")
    L += ["", "*Method: run the model twice — once with real land-use growth, once with land use frozen at "
          f"{y0}. The difference between the two runs is the effect of urbanisation.*", "",
          "## 3. Sustainable drainage (SuDS) scenarios", "",
          f"Each scenario applies {y1} land use to all {len(yrs)} years of observed rainfall.", "",
          "| Scenario | Flood days/yr | Excess m³/yr | Runoff coeff. | Flood-day reduction | Volume reduction |",
          "|---|---|---|---|---|---|"]
    for k, r in suds.iterrows():
        L.append(f"| {k} | {r['flood_days_per_yr']:.2f} | {r['excess_m3_per_yr']:,.0f} | {r['runoff_coeff']:.3f} | "
                 f"{r['flood_days_reduction_%']:.0f} % | {r['volume_reduction_%']:.0f} % |")
    best = suds["volume_reduction_%"].idxmax()
    L += ["", f"**Best performing strategy:** {best} ({suds.loc[best, 'volume_reduction_%']:.0f} % less floodwater).", "",
          "## 4. Sensitivity analysis", "",
          "| Parameter varied | Flood days/yr (low) | Flood days/yr (high) |", "|---|---|---|"]
    for k, r in sens.iloc[::-1].iterrows():
        L.append(f"| {k} | {r['low']:.2f} | {r['high']:.2f} |")
    L += ["", f"The result is most sensitive to **{sens.index[-1].split(' ±')[0].lower()}** — this is the "
          "parameter most worth measuring carefully.", ""]
    if val_text:
        L += ["## 5. Validation against recorded floods", "", val_text, ""]
    L += ["## Figures", ""]
    for f in sorted(F.glob("*.png")):
        L += [f"![{f.stem}](figures/{f.name})", ""]
    (out / "RESULTS.md").write_text("\n".join(L), encoding="utf-8")
    print(f"  Done -> {out.relative_to(ROOT)}/RESULTS.md")
    return {"combined": combined, "climate_only": climate_only, "suds": suds}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="use synthetic data (offline test only)")
    run(demo=ap.parse_args().demo)
