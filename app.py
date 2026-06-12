"""
Phillips Curve in Brazil — Interactive Dashboard
================================================
Companion app to `phillips_curve_brazil.ipynb`.

Data is pulled at runtime from the Central Bank of Brazil (SGS API),
cached locally for offline use, and explored interactively with Altair.

Run with:
    streamlit run app.py

Author: Tiago Ferreira Rodrigues — FGV EPGE
"""

from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
import streamlit as st
from scipy import stats

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Phillips Curve · Brazil",
    page_icon="📉",
    layout="wide",
)

CACHE_DIR = Path("data")
CACHE_DIR.mkdir(exist_ok=True)

SGS_SERIES = {
    "ipca_monthly": 433,     # IPCA — monthly % variation
    "unemployment": 24369,   # PNADc unemployment rate (%)
}
START_DATE = "01/01/2012"

REGIME_ORDER = [
    "2013–2014 · Commodity boom tail",
    "2015–2016 · Recession",
    "2017–2019 · Slow recovery",
    "2020–2021 · Pandemic",
    "2022– · Post-pandemic",
]


# ──────────────────────────────────────────────────────────────────────
# Data layer (mirrors the notebook pipeline)
# ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def fetch_sgs(series_code: int, name: str, start: str = START_DATE) -> pd.Series:
    """Fetch an SGS series with local CSV caching and offline fallback."""
    cache_file = CACHE_DIR / f"sgs_{series_code}.csv"
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados"
        f"?formato=json&dataInicial={start}"
    )
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        raw = pd.DataFrame(resp.json())
        raw.to_csv(cache_file, index=False)
    except (requests.RequestException, ValueError):
        if not cache_file.exists():
            raise RuntimeError(
                f"SGS {series_code}: API unavailable and no local cache found."
            )
        raw = pd.read_csv(cache_file)

    return (
        raw.assign(
            date=pd.to_datetime(raw["data"], format="%d/%m/%Y"),
            value=pd.to_numeric(raw["valor"], errors="coerce"),
        )
        .set_index("date")["value"]
        .rename(name)
        .sort_index()
    )


def assign_regime(d: pd.Timestamp) -> str:
    if d.year <= 2014:
        return REGIME_ORDER[0]
    if d.year <= 2016:
        return REGIME_ORDER[1]
    if d.year <= 2019:
        return REGIME_ORDER[2]
    if d.year <= 2021:
        return REGIME_ORDER[3]
    return REGIME_ORDER[4]


@st.cache_data(ttl=60 * 60 * 12, show_spinner=False)
def build_panel() -> pd.DataFrame:
    """Fetch both series, compute YoY inflation, merge, validate."""
    ipca_m = fetch_sgs(SGS_SERIES["ipca_monthly"], "ipca_monthly")
    unemp = fetch_sgs(SGS_SERIES["unemployment"], "unemployment")

    inflation_yoy = (
        ((1 + ipca_m / 100).rolling(12).apply(np.prod, raw=True) - 1) * 100
    ).rename("inflation_yoy")

    df = pd.concat([inflation_yoy, unemp], axis=1).dropna()

    # Fail fast on incoherent data
    assert df["unemployment"].between(0, 100).all()
    assert not df.index.duplicated().any()
    assert df.index.is_monotonic_increasing

    df["regime"] = [assign_regime(d) for d in df.index]
    return df.reset_index().rename(columns={"date": "date"})


def run_ols(d: pd.DataFrame, lag: int) -> dict:
    """OLS of inflation on (lagged) unemployment with HAC standard errors."""
    tmp = d.assign(u_lag=d["unemployment"].shift(lag)).dropna()
    m = sm.OLS(
        tmp["inflation_yoy"], sm.add_constant(tmp["u_lag"])
    ).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
    return {
        "beta": m.params["u_lag"],
        "se": m.bse["u_lag"],
        "p": m.pvalues["u_lag"],
        "r2": m.rsquared,
        "n": int(m.nobs),
        "alpha": m.params["const"],
    }


# ──────────────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────────────
try:
    panel = build_panel()
except RuntimeError as err:
    st.error(f"Could not load data: {err}")
    st.stop()

# ──────────────────────────────────────────────────────────────────────
# Sidebar controls
# ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📉 Phillips Curve · Brazil")
    st.caption(
        "Inflation–unemployment tradeoff with live data from the "
        "[BCB SGS API](https://dadosabertos.bcb.gov.br/)."
    )

    years = panel["date"].dt.year
    yr_min, yr_max = int(years.min()), int(years.max())
    yr_range = st.slider("Sample window", yr_min, yr_max, (yr_min, yr_max))

    regimes_sel = st.multiselect(
        "Regimes",
        options=REGIME_ORDER,
        default=REGIME_ORDER,
    )

    roll_window = st.slider("Rolling-correlation window (months)", 12, 48, 24, step=6)
    lag_sel = st.select_slider("Unemployment lag (months)", options=[0, 3, 6, 12], value=0)

    st.divider()
    st.caption(
        "**Series** · IPCA 12-month accumulated (SGS 433, compounded) · "
        "PNADc unemployment rate (SGS 24369). "
        "Estimates are descriptive correlations, **not** causal slopes."
    )

mask = (
    years.between(*yr_range)
    & panel["regime"].isin(regimes_sel)
)
df = panel.loc[mask].copy()

if len(df) < 24:
    st.warning("Fewer than 24 observations in the selected window — widen the filters.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────
# Header metrics
# ──────────────────────────────────────────────────────────────────────
st.title("The Phillips Curve in Brazil")
st.markdown(
    "Does Brazil exhibit the inverse inflation–unemployment relationship "
    "predicted by the Phillips Curve — and how stable is it across regimes?"
)

r, p = stats.pearsonr(df["unemployment"], df["inflation_yoy"])
ols = run_ols(df.set_index("date"), lag_sel)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Observations", f"{len(df)}")
c2.metric("Pearson ρ", f"{r:.3f}", help="Contemporaneous correlation in the selected sample.")
c3.metric(
    f"OLS slope β (lag {lag_sel}m)",
    f"{ols['beta']:.3f}",
    help="HAC (Newey–West, 12 lags) standard errors.",
)
c4.metric("HAC p-value", f"{ols['p']:.4f}")

# ──────────────────────────────────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────────────────────────────────
tab_ts, tab_pc, tab_roll, tab_reg = st.tabs(
    ["📈 Time series", "🎯 Phillips curve", "🌊 Rolling correlation", "📊 Regression"]
)

REGIME_SCALE = alt.Scale(domain=REGIME_ORDER, scheme="viridis")

# --- Tab 1: time series -----------------------------------------------
with tab_ts:
    long = df.melt(
        id_vars=["date", "regime"],
        value_vars=["inflation_yoy", "unemployment"],
        var_name="series",
        value_name="value",
    )
    long["series"] = long["series"].map(
        {"inflation_yoy": "Inflation (IPCA 12m, %)", "unemployment": "Unemployment (PNADc, %)"}
    )

    ts_chart = (
        alt.Chart(long)
        .mark_line(strokeWidth=2.2)
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("value:Q", title="%"),
            color=alt.Color(
                "series:N",
                title=None,
                scale=alt.Scale(range=["#1f4e79", "#c0504d"]),
            ),
            tooltip=[
                alt.Tooltip("date:T", format="%b %Y", title="Month"),
                alt.Tooltip("series:N", title="Series"),
                alt.Tooltip("value:Q", format=".2f", title="Value (%)"),
            ],
        )
        .properties(height=420)
        .interactive()
    )
    st.altair_chart(ts_chart, width="stretch")
    st.caption(
        "2015–16 pushes *both* series up — the first visual hint that a single "
        "stable Phillips relationship does not hold across the full sample."
    )

# --- Tab 2: Phillips scatter ------------------------------------------
with tab_pc:
    scatter = (
        alt.Chart(df)
        .mark_circle(size=80, opacity=0.85)
        .encode(
            x=alt.X(
                "unemployment:Q",
                title="Unemployment rate (%)",
                scale=alt.Scale(zero=False),
            ),
            y=alt.Y("inflation_yoy:Q", title="Inflation — IPCA 12m (%)"),
            color=alt.Color("regime:N", title="Regime", scale=REGIME_SCALE),
            tooltip=[
                alt.Tooltip("date:T", format="%b %Y", title="Month"),
                alt.Tooltip("unemployment:Q", format=".2f", title="Unemployment (%)"),
                alt.Tooltip("inflation_yoy:Q", format=".2f", title="Inflation (%)"),
                alt.Tooltip("regime:N", title="Regime"),
            ],
        )
    )
    trend = (
        alt.Chart(df)
        .transform_regression("unemployment", "inflation_yoy")
        .mark_line(color="black", strokeDash=[6, 4], strokeWidth=1.8)
        .encode(x="unemployment:Q", y="inflation_yoy:Q")
    )
    st.altair_chart(
        (scatter + trend).properties(height=480).interactive(),
        width="stretch",
    )
    st.caption(
        "Pooled OLS fit (dashed). Points from 2015–16 and the post-pandemic period "
        "sit in the high-inflation/high-unemployment quadrant — a configuration the "
        "textbook Phillips Curve rules out, attributable to supply shocks and "
        "expectation de-anchoring."
    )

# --- Tab 3: rolling correlation ---------------------------------------
with tab_roll:
    roll = (
        df.set_index("date")["inflation_yoy"]
        .rolling(roll_window)
        .corr(df.set_index("date")["unemployment"])
        .dropna()
        .rename("rho")
        .reset_index()
    )
    roll["sign"] = np.where(roll["rho"] > 0, "ρ > 0 · anti-Phillips", "ρ < 0 · Phillips-consistent")

    base = alt.Chart(roll).encode(
        x=alt.X("date:T", title=None),
        tooltip=[
            alt.Tooltip("date:T", format="%b %Y", title="Window end"),
            alt.Tooltip("rho:Q", format=".3f", title="Pearson ρ"),
        ],
    )
    area = base.mark_area(opacity=0.25).encode(
        y=alt.Y("rho:Q", title=f"Pearson ρ ({roll_window}m window)"),
        color=alt.Color(
            "sign:N",
            title=None,
            scale=alt.Scale(
                domain=["ρ < 0 · Phillips-consistent", "ρ > 0 · anti-Phillips"],
                range=["#1f4e79", "#c0504d"],
            ),
        ),
    )
    line = base.mark_line(color="#1f4e79", strokeWidth=2).encode(y="rho:Q")
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="black").encode(y="y:Q")

    st.altair_chart((area + line + zero).properties(height=420), width="stretch")
    st.caption(
        "Sustained excursions above zero flag periods where inflation and unemployment "
        "rose *together* — supply-driven episodes incompatible with a demand-side "
        "Phillips mechanism."
    )

# --- Tab 4: regression -------------------------------------------------
with tab_reg:
    st.markdown(
        rf"""
**Specification** (HAC / Newey–West SEs, 12 lags):

$$\pi_t = \alpha + \beta\, u_{{t-{lag_sel}}} + \varepsilon_t$$
"""
    )

    rows = []
    for lag in [0, 3, 6, 12]:
        res = run_ols(df.set_index("date"), lag)
        rows.append(
            {
                "Lag (months)": lag,
                "β (slope)": round(res["beta"], 3),
                "HAC s.e.": round(res["se"], 3),
                "p-value": round(res["p"], 4),
                "R²": round(res["r2"], 3),
                "N": res["n"],
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    st.info(
        "**Reading the lag structure.** In New Keynesian Phillips Curve (NKPC) "
        "formulations, staggered (Calvo) pricing means inflation responds to slack "
        "with a delay — if the mechanism operates, lagged unemployment should "
        "correlate more strongly with current inflation than the contemporaneous rate."
    )
    st.warning(
        "**These are descriptive estimates, not causal slopes.** A structural "
        "Phillips Curve would require inflation expectations (BCB Focus survey), "
        "imported-inflation controls (exchange rate, commodities), and an "
        "identification strategy for the endogeneity of unemployment."
    )

st.divider()
st.caption(
    "Built by **Tiago Ferreira Rodrigues** · FGV EPGE · "
    "Companion to [`phillips_curve_brazil.ipynb`](https://github.com) · "
    "Data: Banco Central do Brasil (SGS) & IBGE (PNADc)."
)
