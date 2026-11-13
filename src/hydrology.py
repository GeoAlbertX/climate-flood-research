"""
hydrology.py
------------
Urban rainfall-runoff model based on the USDA SCS Curve Number method (NRCS TR-55),
used to turn daily rainfall into daily runoff for a city catchment whose impervious
(paved/built) area grows over time.

Core equations (all depths in mm)
  S   = 25400 / CN - 254                  potential maximum retention
  Ia  = lambda * S                        initial abstraction (lambda = 0.2)
  Q   = (P - Ia)^2 / (P - Ia + S)  if P > Ia, else 0

Area-weighted runoff for a mixed catchment
  Q_total = f_imp * Q(P, CN_imp) + (1 - f_imp) * Q(P, CN_perv)

Antecedent Moisture Condition (AMC) adjustment of the pervious CN using the
previous 5 days of rain (P5):
  AMC I  (dry, P5 < 35.6 mm):  CN_I   = 4.2 CN / (10 - 0.058 CN)
  AMC III(wet, P5 > 53.3 mm):  CN_III = 23 CN / (10 + 0.13 CN)

Flood-exceedance ("drainage overload") proxy
  E_d = max(0, Q_d - storage - capacity)      excess runoff depth on day d
  V_d = E_d * A * 1000                        excess volume in m^3 (A in km^2)
"""
import numpy as np
import pandas as pd


def retention_S(cn):
    return 25400.0 / np.asarray(cn, float) - 254.0


def scs_runoff(P, cn, lam=0.2):
    P = np.asarray(P, float)
    S = retention_S(cn)
    Ia = lam * S
    return np.where(P > Ia, (P - Ia) ** 2 / (P - Ia + S), 0.0)


def cn_amc_dry(cn):
    return 4.2 * cn / (10 - 0.058 * cn)


def cn_amc_wet(cn):
    return 23 * cn / (10 + 0.13 * cn)


def impervious_series(years, table):
    """Linear interpolation of the impervious fraction between the years given in config."""
    ky = np.array(sorted(int(k) for k in table))
    kv = np.array([table[k] if k in table else table[str(k)] for k in ky], float)
    return pd.Series(np.interp(years, ky, kv), index=years)


def simulate_runoff(daily, f_imp_by_year, ucfg, disconnected=0.0, extra_storage_mm=0.0,
                    capacity_multiplier=1.0):
    """Daily runoff and drainage-exceedance for a catchment.

    daily          : daily rainfall Series (mm)
    f_imp_by_year  : Series indexed by year with impervious fraction
    disconnected   : fraction of impervious area redirected to green infrastructure
    """
    P = daily.fillna(0.0)
    years = P.index.year
    f_imp = f_imp_by_year.reindex(years).values * (1 - disconnected)
    cn_p = np.full(len(P), float(ucfg["pervious_curve_number"]))
    if ucfg.get("use_antecedent_moisture", True):
        p5 = P.shift(1).rolling(5, min_periods=1).sum().fillna(0).values
        cn0 = ucfg["pervious_curve_number"]
        cn_p = np.where(p5 < 35.6, cn_amc_dry(cn0), np.where(p5 > 53.3, cn_amc_wet(cn0), cn0))
    lam = ucfg.get("initial_abstraction_ratio", 0.2)
    q_imp = scs_runoff(P.values, ucfg["impervious_curve_number"], lam)
    q_per = scs_runoff(P.values, cn_p, lam)
    Q = f_imp * q_imp + (1 - f_imp) * q_per
    cap = ucfg["drainage_capacity_mm_per_day"] * capacity_multiplier
    excess = np.maximum(0.0, Q - extra_storage_mm - cap)
    A = ucfg["catchment_area_km2"]
    return pd.DataFrame({"P_mm": P.values, "f_imp": f_imp, "Q_mm": Q,
                         "excess_mm": excess, "excess_m3": excess * A * 1000.0},
                        index=P.index)


def annual_flood_metrics(sim):
    g = sim.groupby(sim.index.year)
    out = pd.DataFrame({
        "rain_mm": g["P_mm"].sum(),
        "runoff_mm": g["Q_mm"].sum(),
        "flood_days": g["excess_mm"].apply(lambda s: int((s > 0).sum())),
        "excess_volume_m3": g["excess_m3"].sum(),
        "max_daily_runoff_mm": g["Q_mm"].max(),
        "impervious_frac": g["f_imp"].mean(),
    })
    out["runoff_coeff"] = out["runoff_mm"] / out["rain_mm"]
    out.index.name = "year"
    return out


def rational_peak_flow(C, i_mm_per_hr, area_km2):
    """Rational method Q_p = 0.278 C i A   (m^3/s; i in mm/h, A in km^2)."""
    return 0.278 * C * i_mm_per_hr * area_km2
