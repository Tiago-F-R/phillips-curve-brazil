# Phillips Curve in Brazil — Inflation & Unemployment Analysis

Empirical analysis of the inflation-unemployment tradeoff in Brazil 
using official time-series data, developed for the *Economic Data Lab* 
course at FGV EPGE — Escola Brasileira de Economia e Finanças.

---

## Research question

Does Brazil exhibit the inverse inflation-unemployment relationship 
predicted by the Phillips Curve? If so, how strong is the relationship, 
and what factors attenuate it?

---

## Data sources

| Dataset | Source | Period |
|---|---|---|
| IPCA (Consumer Price Index) | Banco Central do Brasil — SGS | 1980–2024 |
| Unemployment rate | IBGE — PNADc | 2012–2024 |

Both series retrieved directly from official Brazilian government sources.

---

## Methodology

- Data loading and preprocessing with **Pandas** (datetime parsing, 
  type conversion, column standardization)
- Coherence and validity testing (range checks, duplicate detection, 
  missing value analysis)
- Exploratory data analysis and time-series visualization with **Matplotlib**
- Joint plot of IPCA and unemployment to visually inspect the 
  Phillips Curve relationship across business cycles

---

## Key finding

An inverse relationship between inflation and unemployment is identifiable 
in the Brazilian data, but the correlation is weak. The relationship is 
significantly attenuated by episodes of simultaneously high inflation and 
high unemployment — most notably during the 2015–2016 recession and the 
post-pandemic period — which introduce substantial noise inconsistent with 
the standard Phillips Curve framework.

---

## Requirements
pandas
matplotlib

Install with:
```bash
pip install pandas matplotlib
```

---

## Data

Place `IPCA.csv` and `PNADC.csv` in the same directory as the notebook.  
Both files can be downloaded from the 
[Banco Central do Brasil — SGS](https://www3.bcb.gov.br/sgspub/).

---

## Author

**Tiago Ferreira Rodrigues**  
B.Sc. Economics — FGV EPGE  
[linkedin.com/in/tiago-f-rodrigues](https://linkedin.com/in/tiago-f-rodrigues)
