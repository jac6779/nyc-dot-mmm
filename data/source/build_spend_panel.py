"""Build a weekly NYC DOT ad-spend panel (by channel) from the Local Law 83 file.

Assumptions (all flagged in the output summary):
  * Spend is spread evenly across each buy's run dates (inclusive), then summed by
    Monday-start week.
  * Window = FY2023-FY2025 (2022-07-01 .. 2025-06-30). Later rows (FY2025 Summer
    Streets spillover into Jul/Aug 2025) fall outside complete reporting and are dropped.
  * 11 rows with end < start are treated as swapped dates.
  * Rows with a start but no end are treated as single-day buys.
  * "E-Bike Trade In" rows with two start dates ("2/21, 2/28") split spend equally
    across those dates (year inferred from fiscal year).
"""
import re
import sys
import numpy as np
import pandas as pd

SRC, OUT = sys.argv[1], sys.argv[2]
WIN_START, WIN_END = pd.Timestamp("2022-07-01"), pd.Timestamp("2025-06-30")

CHANNEL = {
    "TV": "tv", "Radio": "radio", "Print": "print",
    "Digital": "digital", "Digital Publications": "digital", "Programmatic": "digital",
    "Search": "digital", "digital": "digital",
    "Social Media": "social",
    "Out of Home": "ooh", "Digital Out of Home": "ooh",
    "Other": "other", "Sports": "other",
}
SAFETY_PAT = re.compile(r"vision zero|speed camera|truck safety|dwi|work zone|e-bike safety", re.I)

d = pd.read_csv(SRC)
d.columns = [c.strip() for c in d.columns]
d = d[d["City Agency"] == "DOT"].copy()
d["spend"] = pd.to_numeric(d["Net Spend Amount"].astype(str).str.replace(r"[$,()]", "", regex=True))
total_src = d["spend"].sum()
d["channel"] = d["Media Type (Standardized)"].map(CHANNEL).fillna("other")
d["safety"] = d["Ad Campaign Name"].str.contains(SAFETY_PAT)

d = d.rename(columns={"Fiscal Year": "fy", "Run Start Date": "s_raw", "Run End Date": "e_raw"})
rows, dropped_nodate = [], 0.0
for r in d.itertuples():
    s_raw, e_raw = str(r.s_raw), str(r.e_raw)
    starts = []
    m = re.fullmatch(r"\s*(\d{1,2})/(\d{1,2})\s*,\s*(\d{1,2})/(\d{1,2})\s*", s_raw)
    if m:  # two month/day insertion dates, no year
        fy = int(r.fy.split()[-1])
        for mo, dy in ((m[1], m[2]), (m[3], m[4])):
            yr = fy if int(mo) <= 6 else fy - 1
            starts.append(pd.Timestamp(year=yr, month=int(mo), day=int(dy)))
        ends = starts[:]
    else:
        s = pd.to_datetime(s_raw, errors="coerce")
        e = pd.to_datetime(e_raw, errors="coerce")
        if pd.isna(s):
            dropped_nodate += r.spend
            continue
        if pd.isna(e):
            e = s
        if e < s:
            s, e = e, s
        starts, ends = [s], [e]
    share = r.spend / len(starts)
    for s, e in zip(starts, ends):
        rows.append((s, e, share, r.channel, r.safety))

b = pd.DataFrame(rows, columns=["s", "e", "spend", "channel", "safety"])
b["days"] = (b["e"] - b["s"]).dt.days + 1

daily = []
for r in b.itertuples():
    idx = pd.date_range(r.s, r.e)
    daily.append(pd.DataFrame({"date": idx, "spend": r.spend / r.days,
                               "channel": r.channel, "safety": r.safety}))
daily = pd.concat(daily)
dropped_outside = daily.loc[(daily.date < WIN_START) | (daily.date > WIN_END), "spend"].sum()
daily = daily[(daily.date >= WIN_START) & (daily.date <= WIN_END)]
daily["week_start"] = daily["date"] - pd.to_timedelta(daily["date"].dt.weekday, unit="D")

weeks = pd.date_range(WIN_START - pd.Timedelta(days=WIN_START.weekday()),
                      WIN_END - pd.Timedelta(days=WIN_END.weekday()), freq="7D")
saf = (daily[daily.safety].pivot_table(index="week_start", columns="channel", values="spend", aggfunc="sum")
       .reindex(weeks).fillna(0.0))
saf = saf.reindex(columns=["tv", "radio", "print", "digital", "social", "ooh", "other"], fill_value=0.0)
saf.columns = [f"spend_safety_{c}" for c in saf.columns]
nons = daily[~daily.safety].groupby("week_start").spend.sum().reindex(weeks).fillna(0.0)

panel = saf.copy()
panel["spend_safety_total"] = saf.sum(axis=1)
panel["spend_nonsafety_total"] = nons
panel["spend_total"] = panel["spend_safety_total"] + panel["spend_nonsafety_total"]
panel.index.name = "week_start"
panel = panel.round(2)
panel.to_csv(OUT)

print(f"source DOT total            : {total_src:,.0f}")
print(f"panel total                 : {panel.spend_total.sum():,.0f}")
print(f"dropped (no usable start)   : {dropped_nodate:,.0f}")
print(f"dropped (outside window)    : {dropped_outside:,.0f}")
print(f"reconciles (diff)           : {total_src - panel.spend_total.sum() - dropped_nodate - dropped_outside:,.2f}")
print("weeks:", len(panel), panel.index.min().date(), "->", panel.index.max().date())
print("weeks with safety spend:", int((panel.spend_safety_total > 0).sum()),
      "| any DOT spend:", int((panel.spend_total > 0).sum()))
print("\nspend by column:\n", panel.sum().round(0).to_string())
print("\nweeks with spend, by safety channel:\n", (saf > 0).sum().to_string())
