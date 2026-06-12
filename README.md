# The Phillips Curve in Brazil 🇧🇷

**An automated empirical analysis of the inflation–unemployment tradeoff**, using
official time series pulled directly from the Central Bank of Brazil's API.

Developed at FGV EPGE — Escola Brasileira de Economia e Finanças.

---

## Research question

Does Brazil exhibit the inverse inflation–unemployment relationship predicted by
the Phillips Curve? How strong is it — and how **stable** is it across
business-cycle regimes?

## Highlights

- **Fully automated data pipeline** — both series are fetched at runtime from the
  [BCB SGS API](https://dadosabertos.bcb.gov.br/) (no manual downloads, no
  encoding fixes), with local caching for reproducibility and offline execution.
- **Programmatic data validation** — range, duplicate, and missing-value checks
  that fail fast before any analysis runs.
- **Regime-aware analysis** — observations classified into five macroeconomic
  episodes (commodity boom tail, 2015–16 recession, slow recovery, pandemic,
  post-pandemic), revealing the instability a pooled scatter hides.
- **Serious inference** — OLS with HAC (Newey–West) standard errors,
  contemporaneous *and* lagged specifications (NKPC-motivated), plus a 24-month
  rolling correlation as a structural-stability diagnostic.

## Data

| Series | SGS code | Frequency | Coverage |
|---|---|---|---|
| IPCA — monthly variation (%) | 433 | Monthly | 1980– |
| Unemployment — PNAD Contínua (%) | 24369 | Monthly (moving quarter) | 2012– |

Monthly IPCA variations are compounded into 12-month (YoY) inflation. The
effective sample starts in 2013 (12 months of IPCA history + PNADc availability).

## Key findings

A negative inflation–unemployment correlation exists in the pooled sample, but it
is **weak and regime-dependent**. The 2015–16 recession and the post-pandemic
period place Brazil in the high-inflation / high-unemployment quadrant —
consistent with supply shocks and de-anchored expectations rather than movements
along a stable Phillips Curve. The rolling correlation makes these
"anti-Phillips" episodes explicit. Estimates are presented as descriptive
correlations, not causal slopes; the notebook discusses what a structural
estimate would additionally require (expectations, imported-inflation controls,
identification).

## Quickstart

```bash
pip install -r requirements.txt

# Notebook — full analysis with narrative
jupyter notebook phillips_curve_brazil.ipynb

# Interactive dashboard (Streamlit + Altair)
streamlit run app.py
```

The first execution downloads the data from the BCB API and caches it under
`data/`. Subsequent runs work offline.

## Interactive dashboard

`app.py` is a Streamlit companion to the notebook, sharing the same automated
data pipeline (cached for 12 h via `st.cache_data`). It provides:

- **Time series** — interactive dual-series chart with per-month tooltips
- **Phillips curve** — regime-colored Altair scatter with pooled OLS fit;
  hover any point to identify the exact month behind it
- **Rolling correlation** — adjustable window (12–48 months) highlighting
  Phillips-consistent vs. "anti-Phillips" episodes
- **Regression panel** — HAC-robust OLS across lag specifications (0/3/6/12
  months), with sample window and regime filters applied live

## Requirements

```
pandas
numpy
requests
matplotlib
seaborn
statsmodels
scipy
```

## Possible extensions

- Services core inflation (SGS 10844) instead of headline IPCA
- Expectations-augmented specification using BCB Focus survey data
- Unemployment gap (HP-filter NAIRU proxy) instead of the unemployment level

## Author

**Tiago Ferreira Rodrigues**  
B.Sc. Economics · FGV EPGE  
[linkedin.com/in/tiago-f-rodrigues](https://linkedin.com/in/tiago-f-rodrigues) · [github.com/Tiago-F-R](https://github.com/Tiago-F-R)

