"""Join weekly NYC crash outcomes onto the DOT weekly spend panel.

Usage:  python join_crashes.py dot_weekly_spend.csv crashes.csv dot_mmm_panel.csv

`crashes.csv` can be either:
  (a) the small daily aggregate from the SoQL query in README_crashes.txt
      (columns: day, crashes, injured, killed), or
  (b) the full NYPD "Motor Vehicle Collisions - Crashes" export (one row per crash;
      CRASH DATE, NUMBER OF PERSONS INJURED, NUMBER OF PERSONS KILLED, ...).
Weeks are Monday-start, matching the spend panel.
"""
import sys
import numpy as np
import pandas as pd

spend_path, crash_path, out_path = sys.argv[1:4]

spend = pd.read_csv(spend_path, parse_dates=["week_start"])

c = pd.read_csv(crash_path)
c.columns = [x.strip().lower().replace(" ", "_") for x in c.columns]

if "crash_date" in c.columns:  # raw export -> daily
    c["day"] = pd.to_datetime(c["crash_date"]).dt.normalize()
    for col in ("number_of_persons_injured", "number_of_persons_killed"):
        c[col] = pd.to_numeric(c[col], errors="coerce").fillna(0)
    daily = c.groupby("day").agg(crashes=("day", "size"),
                                 injured=("number_of_persons_injured", "sum"),
                                 killed=("number_of_persons_killed", "sum")).reset_index()
elif {"day", "crashes"} <= set(c.columns):
    daily = c[["day", "crashes", "injured", "killed"]].copy()
    daily["day"] = pd.to_datetime(daily["day"]).dt.normalize()
else:
    sys.exit(f"Unrecognised crash file columns: {list(c.columns)}")

daily["week_start"] = daily["day"] - pd.to_timedelta(daily["day"].dt.weekday, unit="D")
wk = daily.groupby("week_start").agg(crashes=("crashes", "sum"), injured=("injured", "sum"),
                                     killed=("killed", "sum"), days_observed=("day", "nunique")).reset_index()

panel = spend.merge(wk, on="week_start", how="left")
n_missing = int(panel["crashes"].isna().sum())
# first/last week are partial relative to the FY window; flag any week with <7 observed days
panel["partial_week"] = (panel["days_observed"].fillna(0) < 7).astype(int)

iso = panel["week_start"].dt.isocalendar()
panel["iso_week"] = iso["week"].astype(int)
panel["month"] = panel["week_start"].dt.month
panel["t"] = np.arange(len(panel))

panel.to_csv(out_path, index=False)
print(f"rows: {len(panel)} | weeks missing crash data: {n_missing} | partial weeks: {int(panel.partial_week.sum())}")
print(panel[["crashes", "injured", "killed", "spend_safety_total"]].describe().round(1).to_string())
print("corr(safety spend, crashes):", round(panel["spend_safety_total"].corr(panel["crashes"]), 3))
