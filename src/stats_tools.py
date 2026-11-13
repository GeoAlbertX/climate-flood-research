"""
stats_tools.py
--------------
Statistical methods used in both projects. Each function is written out step by step
so the mathematics in the reports can be traced directly to the code.

Methods
  * descriptive statistics, coefficient of variation (CV)
  * standardized anomaly index (SAI)
  * ordinary least-squares linear trend + t-test
  * Mann-Kendall trend test (with tie correction)
  * Trend-Free Pre-Whitening Mann-Kendall (Yue et al., 2002) for autocorrelated series
  * Sen's slope estimator (with 95 % confidence interval)
  * Pettitt change-point test
  * Welch t-test and Mann-Whitney U test for decade comparison
  * Gumbel (EV1) extreme value analysis: method of moments + Kolmogorov-Smirnov fit test
  * Poisson regression (IRLS) for trends in yearly event counts
"""
import numpy as np
from scipy import stats

EULER_GAMMA = 0.5772156649


# ---------------------------------------------------------------------------
# Descriptive
# ---------------------------------------------------------------------------
def describe(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    mean, sd = x.mean(), x.std(ddof=1)
    return {
        "n": len(x), "mean": mean, "sd": sd, "min": x.min(), "max": x.max(),
        "median": np.median(x), "cv_percent": 100 * sd / mean if mean else np.nan,
        "skewness": stats.skew(x, bias=False),
    }


def standardized_anomaly(x):
    """SAI_i = (x_i - mean) / sd"""
    x = np.asarray(x, float)
    return (x - np.nanmean(x)) / np.nanstd(x, ddof=1)


def lag1_autocorrelation(x):
    x = np.asarray(x, float)
    x = x - x.mean()
    return np.sum(x[1:] * x[:-1]) / np.sum(x * x)


# ---------------------------------------------------------------------------
# Linear regression trend
# ---------------------------------------------------------------------------
def linear_trend(t, x):
    """OLS: x = a + b t. Returns slope b, intercept a, R^2 and the t-test p-value of b."""
    t, x = np.asarray(t, float), np.asarray(x, float)
    ok = ~np.isnan(x)
    res = stats.linregress(t[ok], x[ok])
    return {"slope": res.slope, "intercept": res.intercept, "r2": res.rvalue ** 2,
            "p": res.pvalue, "stderr": res.stderr}


# ---------------------------------------------------------------------------
# Mann-Kendall + Sen's slope
# ---------------------------------------------------------------------------
def mann_kendall(x, alpha=0.05):
    """Non-parametric Mann-Kendall test.

    S      = sum_{k<j} sgn(x_j - x_k)
    Var(S) = [n(n-1)(2n+5) - sum_g t_g(t_g-1)(2t_g+5)] / 18      (t_g = size of tie group g)
    Z      = (S-1)/sqrt(Var S) if S>0 ; 0 if S=0 ; (S+1)/sqrt(Var S) if S<0
    p      = 2 [1 - Phi(|Z|)]
    tau    = S / [n(n-1)/2]
    """
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    n = len(x)
    s = 0.0
    for k in range(n - 1):
        s += np.sign(x[k + 1:] - x[k]).sum()
    _, ties = np.unique(x, return_counts=True)
    var_s = (n * (n - 1) * (2 * n + 5) - np.sum(ties * (ties - 1) * (2 * ties + 5))) / 18.0
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    tau = s / (0.5 * n * (n - 1))
    if p < alpha:
        trend = "significant increase" if z > 0 else "significant decrease"
    else:
        trend = "no significant trend"
    return {"n": n, "S": s, "var_S": var_s, "Z": z, "p": p, "tau": tau, "trend": trend}


def sens_slope(t, x, confidence=0.95):
    """Sen's slope  beta = median[(x_j - x_i)/(t_j - t_i)]  for all i<j, with CI."""
    t, x = np.asarray(t, float), np.asarray(x, float)
    ok = ~np.isnan(x)
    slope, intercept, lo, hi = stats.theilslopes(x[ok], t[ok], alpha=confidence)
    return {"slope": slope, "intercept": intercept, "ci_low": lo, "ci_high": hi}


def mann_kendall_tfpw(t, x, alpha=0.05):
    """Trend-Free Pre-Whitening (Yue et al., 2002).
    1. b = Sen's slope;  2. detrend x'_t = x_t - b t;  3. r1 = lag-1 autocorrelation of x'
    4. y_t = x'_t - r1 x'_{t-1};  5. add trend back  y_t + b t;  6. Mann-Kendall on result."""
    t, x = np.asarray(t, float), np.asarray(x, float)
    ok = ~np.isnan(x)
    t, x = t[ok], x[ok]
    b = sens_slope(t, x)["slope"]
    detr = x - b * t
    r1 = lag1_autocorrelation(detr)
    y = detr[1:] - r1 * detr[:-1] + b * t[1:]
    out = mann_kendall(y, alpha)
    out["r1"] = r1
    return out


def trend_report(years, x, alpha=0.05):
    """Run all trend tests on one annual series and return one flat dictionary."""
    years = np.asarray(years, float)
    x = np.asarray(x, float)
    mk = mann_kendall(x, alpha)
    ss = sens_slope(years, x)
    lr = linear_trend(years, x)
    r1 = lag1_autocorrelation(x[~np.isnan(x)])
    r1_crit = 1.96 / np.sqrt(mk["n"])
    autocorrelated = abs(r1) > r1_crit
    out = {
        "mean": np.nanmean(x), "mk_Z": mk["Z"], "mk_p": mk["p"], "kendall_tau": mk["tau"],
        "mk_trend": mk["trend"], "sen_slope_per_yr": ss["slope"],
        "sen_ci_low": ss["ci_low"], "sen_ci_high": ss["ci_high"],
        "sen_change_over_period": ss["slope"] * (np.nanmax(years) - np.nanmin(years)),
        "ols_slope_per_yr": lr["slope"], "ols_r2": lr["r2"], "ols_p": lr["p"],
        "lag1_r": r1, "autocorrelated": bool(autocorrelated),
    }
    mean = np.nanmean(x)
    out["sen_percent_change"] = 100 * out["sen_change_over_period"] / mean if mean else np.nan
    if autocorrelated:
        tf = mann_kendall_tfpw(years, x, alpha)
        out["tfpw_Z"], out["tfpw_p"], out["tfpw_trend"] = tf["Z"], tf["p"], tf["trend"]
    return out


# ---------------------------------------------------------------------------
# Change point
# ---------------------------------------------------------------------------
def pettitt(x):
    """Pettitt (1979) test for a single abrupt shift in the mean.
    U_t = sum_{i<=t} sum_{j>t} sgn(x_i - x_j);   K = max|U_t|
    p  ~= 2 exp( -6 K^2 / (n^3 + n^2) )"""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    n = len(x)
    sgn = np.sign(x[:, None] - x[None, :])
    U = np.array([sgn[: t + 1, t + 1:].sum() for t in range(n - 1)])
    idx = int(np.argmax(np.abs(U)))
    K = float(np.abs(U[idx]))
    p = min(1.0, 2 * np.exp(-6 * K ** 2 / (n ** 3 + n ** 2)))
    return {"K": K, "last_index_before_change": idx, "p": p,
            "mean_before": x[: idx + 1].mean(), "mean_after": x[idx + 1:].mean()}


# ---------------------------------------------------------------------------
# Two-period comparison
# ---------------------------------------------------------------------------
def compare_periods(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    t = stats.ttest_ind(b, a, equal_var=False)
    u = stats.mannwhitneyu(b, a, alternative="two-sided")
    return {"mean_1": a.mean(), "mean_2": b.mean(),
            "percent_change": 100 * (b.mean() - a.mean()) / a.mean() if a.mean() else np.nan,
            "welch_t": t.statistic, "welch_p": t.pvalue, "mannwhitney_U": u.statistic,
            "mannwhitney_p": u.pvalue}


# ---------------------------------------------------------------------------
# Extreme values (Gumbel / EV1)
# ---------------------------------------------------------------------------
def gumbel_fit(annual_max):
    """Method of moments:  alpha = sqrt(6) s / pi ;  u = mean - 0.5772 alpha"""
    x = np.asarray(annual_max, float)
    x = x[~np.isnan(x)]
    alpha = np.sqrt(6) * x.std(ddof=1) / np.pi
    u = x.mean() - EULER_GAMMA * alpha
    ks = stats.kstest(x, "gumbel_r", args=(u, alpha))
    return {"u": u, "alpha": alpha, "ks_stat": ks.statistic, "ks_p": ks.pvalue}


def gumbel_return_level(u, alpha, T):
    """x_T = u - alpha * ln(-ln(1 - 1/T))"""
    T = np.asarray(T, float)
    return u - alpha * np.log(-np.log(1 - 1 / T))


def gumbel_return_period(u, alpha, x):
    """Inverse: T = 1 / (1 - exp(-exp(-(x-u)/alpha)))"""
    return 1.0 / (1 - np.exp(-np.exp(-(np.asarray(x, float) - u) / alpha)))


def weibull_plotting_positions(x):
    """Empirical return periods: T = (n+1)/m  (m = rank, largest = 1)."""
    x = np.sort(np.asarray(x, float)[~np.isnan(x)])[::-1]
    m = np.arange(1, len(x) + 1)
    return x, (len(x) + 1) / m


# ---------------------------------------------------------------------------
# Poisson regression for counts
# ---------------------------------------------------------------------------
def poisson_trend(years, counts, max_iter=100):
    """log(lambda_t) = b0 + b1 (t - t_mean), fitted by IRLS (maximum likelihood).
    Incidence Rate Ratio IRR = exp(b1) = multiplicative change in expected count per year.
    Dispersion = Pearson chi^2 / (n - 2); values >> 1 mean overdispersion."""
    y = np.asarray(counts, float)
    t = np.asarray(years, float)
    n = len(y)
    if y.sum() == 0:
        return None
    X = np.column_stack([np.ones(n), t - t.mean()])
    beta = np.array([np.log(y.mean()), 0.0])
    for _ in range(max_iter):
        eta = X @ beta
        mu = np.exp(eta)
        z = eta + (y - mu) / mu
        XtW = X.T * mu
        new = np.linalg.solve(XtW @ X, XtW @ z)
        if np.max(np.abs(new - beta)) < 1e-10:
            beta = new
            break
        beta = new
    mu = np.exp(X @ beta)
    cov = np.linalg.inv((X.T * mu) @ X)
    se = np.sqrt(np.diag(cov))
    zval = beta[1] / se[1]
    dispersion = np.sum((y - mu) ** 2 / mu) / (n - 2)
    # quasi-Poisson correction of the p-value when overdispersed
    z_q = zval / np.sqrt(max(dispersion, 1.0))
    return {"b0": beta[0], "b1": beta[1], "se_b1": se[1], "z": zval,
            "p": 2 * (1 - stats.norm.cdf(abs(zval))),
            "p_quasi": 2 * (1 - stats.norm.cdf(abs(z_q))),
            "irr": np.exp(beta[1]), "irr_ci_low": np.exp(beta[1] - 1.96 * se[1]),
            "irr_ci_high": np.exp(beta[1] + 1.96 * se[1]), "dispersion": dispersion,
            "fitted": mu}
