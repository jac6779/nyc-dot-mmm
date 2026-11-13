# NYC DOT Road-Safety Advertising — Bayesian Marketing Mix Modeling

An end-to-end, independently assembled **Bayesian Marketing Mix Modeling (MMM)** portfolio project using **Google Meridian** to examine whether New York City Department of Transportation (NYC DOT) road-safety advertising expenditures are associated with changes in weekly motor vehicle crashes.

The goal is to estimate channel-level contributions, quantify uncertainty, and understand the limits of drawing conclusions from observational advertising data—not to forecast crashes or assume that modeled associations are causal effects.

---

## Project Overview

Using public NYC advertising expenditure and crash records, I constructed a weekly dataset covering approximately three fiscal years, explored advertising and crash patterns, engineered temporal controls, and fit a Bayesian MMM with five advertising channels.

The analysis addresses three questions:

- Which advertising channels are associated with changes in weekly crash frequency?
- How much uncertainty surrounds the estimated contributions of those channels?
- Are the results sufficiently reliable to inform advertising spending decisions?

**Main conclusion:** The model fits weekly crashes moderately well, but much of that fit may come from the trend, seasonality, holiday, and policy controls rather than advertising. I did not fit a controls-only baseline, so I cannot separate the two. The combined advertising contribution is uncertain, and the results are inconclusive.

---

## Research Problem and Outcome

NYC DOT invests in road-safety advertising intended to influence behavior and improve traffic safety. I wanted to investigate whether publicly reported advertising spending was associated with changes in citywide motor vehicle crash frequency.

I chose **weekly crashes** as the primary outcome because collisions can occur without injuries or fatalities, making crash counts a broader measure of collision frequency. Injuries and fatalities were retained during analysis as additional road-safety outcomes.

This is an **observational association study**, not a causal evaluation of NYC DOT advertising. Higher crash rates may themselves prompt additional advertising, and other changes in travel activity or public policy can affect crash numbers.

---

## Data Sources

| Source | Use |
|---|---|
| [Local Law 83 — City Agency Advertising Spend](https://data.cityofnewyork.us/City-Government/Local-Law-83-City-Agency-Advertising-Spend/n56u-3hzv/about_data) | NYC agency advertising expenditures, campaign information, media types, and scheduled run dates |
| [NYPD Motor Vehicle Collisions — Crashes](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95/about_data) | Daily citywide crash records and associated injury and fatality counts |

I downloaded the original advertising data as a CSV and used Python scripts to construct the weekly modeling panel.

### Dataset Construction

1. **Filter advertising records:** Retain NYC DOT expenditures and identify road-safety campaigns using terms including *Vision Zero*, *Speed Camera*, *Truck Safety*, *DWI*, *Work Zone*, and *E-Bike Safety*.
2. **Standardize channels:** Group original media types into TV, Radio, Print, Digital, Social, Out-of-Home (OOH), and Other.
3. **Allocate spending over time:** Address run-date irregularities and distribute each advertising buy's reported expenditure evenly across its scheduled dates; aggregate the resulting allocations into Monday-start weeks.
4. **Aggregate crash outcomes:** Sum daily crashes, injuries, and fatalities into matching Monday-start weeks.
5. **Join and validate:** Combine the weekly series by `week_start`, review observed crash days, and add calendar and time-index fields.
6. **Exclude incomplete spending weeks:** Remove the first and last weeks because the selected expenditure window does not cover all seven days of those weeks.

The original combined panel contained **158 weeks** (June 27, 2022–June 30, 2025). After excluding the two edge weeks with incomplete spending coverage, the analysis uses **156 complete Monday-start weeks**, from **July 4, 2022, through June 23, 2025**.

I selected fiscal years **2023–2025** to work with approximately three years of history and multiple annual seasonal cycles.

**Key data assumption:** The source reports expenditure for scheduled advertising runs, not observed daily delivery. Allocating each buy uniformly across its run dates produces **estimated weekly spending**, not measured weekly impressions, reach, or frequency.

---

## Notebook Workflow

The four notebooks document the analysis from data preparation through model interpretation.

| Notebook | Purpose |
|---|---|
| `01_nyc_dot_mmm_preprocessing.ipynb` | Data validation, date fields, holiday and congestion-pricing indicators, removal of incomplete spending weeks, channel consolidation, and cleaned-data export |
| `02_nyc_dot_mmm_data_analysis.ipynb` | Spending sparsity, crash trends, seasonality, channel correlations, distributions, and relationships with crash outcomes |
| `03_nyc_dot_mmm_feature_engineering.ipynb` | Cyclical seasonal features, scaled time trend, modeling inputs, and final integrity checks |
| `04_nyc_dot_mmm_modeling_meridian.ipynb` | Meridian model specification, Bayesian sampling, convergence checks, predictive evaluation, and channel contribution estimates |

### 1. Preprocessing

I validated the combined dataset, created a holiday-week indicator and a post-congestion-pricing indicator, excluded incomplete expenditure weeks, and consolidated sparse advertising categories into **five channels**: TV, Radio, Print, Digital/Social, and OOH/Other.

### 2. Exploratory Data Analysis

The EDA highlighted several patterns relevant to the modeling approach:

- **Intermittent spending:** Each channel had many zero-spend weeks, sometimes followed by substantial campaign spending and long gaps without activity.
- **Crash trends and seasonality:** Crashes and injuries generally declined across the study period, with lower counts in winter and increased activity during warmer months.
- **Spending concentration:** OOH/Other accounted for the largest spending share (**35.3%**), followed by TV (**23.8%**) and Radio (**22.6%**). OOH/Other combines multiple underlying media types.
- **Channel overlap:** Radio spending was strongly correlated with Digital/Social and OOH/Other spending (approximately **r = 0.90**), making it more difficult to isolate individual channel contributions.
- **Spending distributions:** Active-week spending was generally right-skewed for TV, Radio, Print, and OOH/Other; Digital/Social showed multiple peaks.
- **Simple outcome correlations:** TV and Print had the strongest positive observed correlations with crashes and injuries. These exploratory correlations do **not** establish advertising effectiveness.

These findings supported including seasonal controls and interpreting channel attribution cautiously.

### 3. Feature Engineering

I added annual sine and cosine features to represent seasonality as a continuous cycle, preserving the relationship between the end and beginning of each calendar year. I also scaled the sequential time index to a **0–1** range using `MinMaxScaler`, preserving its temporal ordering while reducing its numerical magnitude.

The final feature engineering notebook reported **156 observations and 15 columns**, with no missing values, duplicate weeks, negative spending values, or weekly gaps.

### 4. Bayesian MMM with Google Meridian

I used **Google Meridian** with weekly crashes as a **non-revenue KPI** and five advertising spending channels. The model includes five controls:

- Scaled time trend (`t_scaled`)
- Post-congestion-pricing indicator (`post_congestion`)
- Holiday-week indicator (`is_holiday_week`)
- Annual seasonality sine (`season_sin`)
- Annual seasonality cosine (`season_cos`)

I used a zero-centered **Normal(0, 1)** media coefficient prior so that positive and negative associations were both possible; I did not assume that road-safety advertising necessarily reduces crashes.

Meridian models **adstock** (potential delayed or carryover advertising associations) and **saturation** (diminishing responses as spending increases). I used a seeded **random 10% holdout** to distribute test observations across the study period rather than concentrating them in the post-congestion-pricing months.

The posterior sampling configuration used **four MCMC chains**, with **500 adaptation**, **500 burn-in**, and **1,000 retained samples per chain**. R-hat diagnostics near 1 suggested satisfactory convergence. The random holdout provides an assessment of within-period predictive fit, not a rigorous forecast of future weeks.

---

## Predictive Performance

| Metric | Training | Holdout test |
|---|---:|---:|
| **R²** | **0.741** | **0.856** |
| **MAPE** | **3.74%** | **2.74%** |

The model explained a moderate-to-large share of the variation in weekly crashes, and the expected-versus-actual plot followed much of the observed trend and seasonality. Because the controls themselves capture trend and seasonality, this fit does not show how much of it is due to advertising.

**Important:** Predictive fit does **not** demonstrate that individual advertising contributions are correctly identified. The random test weeks may also be easier to predict than a genuinely future period because nearby observations can share temporal patterns. Test R² is higher than training R², which likely reflects the small holdout (roughly 16 randomly chosen weeks) rather than better generalization, so I do not read it as a meaningful result.

---

## Estimated Advertising Channel Contributions

The following estimates are **modeled contributions to total crashes over the study period**, not observed crashes attributable to an advertisement or established causal effects. A **positive** contribution corresponds to an association with *more* crashes in the model; a **negative** contribution corresponds to an association with *fewer* crashes.

| Channel | Mean estimated contribution | 95% credible interval |
|---|---:|---:|
| TV | +6,778 | +690 to +14,202 |
| Radio | −1,949 | −12,127 to +6,103 |
| Print | −9,366 | −18,596 to +2,077 |
| Digital/Social | +1,549 | −4,373 to +5,925 |
| OOH/Other | +2,275 | −5,701 to +7,178 |
| **All channels** | **−713** | **−4,521 to +3,076** |

### Results Interpretation

- **TV:** The estimated contribution is positive, and its 95% credible interval is entirely above zero. This supports a positive *modeled association*, but it does not mean TV advertising caused additional crashes. One possible explanation, which I did not test, is that NYC DOT increased TV spending in response to elevated crash rates (**reverse causality**).
- **Print:** The largest negative mean estimate, but its credible interval includes positive values. The direction of its association remains uncertain.
- **Radio, Digital/Social, and OOH/Other:** Credible intervals cross zero, leaving substantial uncertainty about the direction and magnitude of individual contributions.
- **Combined advertising:** The mean net contribution is slightly negative, but its credible interval spans both negative and positive values. The model therefore does **not** establish an overall increase or reduction in crashes associated with advertising.

Expected and no-advertising-baseline crash estimates were relatively close in the model-fit visualization. This is consistent with a small estimated **net** contribution, potentially reflecting offsetting channel estimates rather than an absence of individual associations.

### Prior Sensitivity

In separate sensitivity checks, I compared media coefficient prior standard deviations of **0.5, 1, and 2**. Channel contribution estimates changed in magnitude, but the broad directional conclusions remained similar. This reduced my concern that the original prior standard deviation alone was driving the findings; it does not resolve the underlying identification or causal-inference limitations. These checks were run interactively and are not included in the notebooks; results are summarized qualitatively.

---

## Limitations and Practical Implications

The main limitations of this analysis are:

- **Spend is not exposure:** The data do not contain impressions, reach, frequency, or measured campaign delivery. Weekly spending is allocated from campaign run dates rather than observed daily activity.
- **Reverse causality:** Advertising may be increased in response to crash rates, potentially creating positive spending–crash associations even if advertising itself is beneficial.
- **Channel correlation and sparsity:** Overlapping campaigns and long periods with zero spend make separating individual channel contributions difficult.
- **Unmeasured factors:** Traffic volume, weather, driving patterns, and other policies could explain variation not captured by the current controls. A binary congestion-pricing indicator cannot represent the policy's full effects.
- **Observational attribution:** Convergence and predictive accuracy do not establish causal effects or justify interpreting modeled contributions as definitive advertising effectiveness.
- **No controls-only baseline:** I cannot say how much predictive value the media inputs add beyond trend, seasonality, and holiday and policy controls.

**Decision:** I would **not recommend budget reallocations** based on these results. I would prioritize additional investigation into the timing of TV advertising relative to elevated crash rates, while treating the overall conclusions as inconclusive.

---

## Additional Research Opportunities

This project is a completed observational MMM exercise. Potential extensions—not prerequisites for completion—include:

1. Adding impressions, reach, and frequency to improve the measurement of advertising exposure.
2. Studying campaign launch decisions and whether increased crash rates trigger additional spending.
3. Exploring uncertainty in adstock and saturation parameters.
4. Incorporating detailed traffic volume and congestion-pricing measures, as well as other relevant external controls.
5. Comparing predictive performance with a **controls-only** baseline to assess the incremental value of media inputs.
6. Using stronger causal identification before making advertising budget decisions.

---

## Key Skills Demonstrated

- Public-data acquisition, cleaning, aggregation, and reconciliation
- Time-series exploratory analysis and temporal feature engineering
- Marketing mix modeling using Google Meridian
- Bayesian priors, posterior interpretation, credible intervals, and MCMC convergence diagnostics
- Specifying adstock and saturation in Meridian
- Holdout evaluation and predictive metrics
- Prior sensitivity checks and critical interpretation of observational results
- Communicating findings and practical limitations to decision-makers

---

## Related Projects

- [Citi Bike Availability Prediction](https://github.com/jac6779/citi-bike-prediction)
- [NYC 311 Complaint Resolution Prediction](https://github.com/jac6779/nyc-311-ml-api)
- [Brooklyn Home Price Prediction](https://github.com/jac6779/brooklyn-home-sales-llm)
- [Household Grocery Shopping Customer Segmentation](https://github.com/jac6779/dh-segmentation)

---

## Author

**Justin Cox**

GitHub: https://github.com/jac6779  
LinkedIn: https://www.linkedin.com/in/justincox1
