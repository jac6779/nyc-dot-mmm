"""Build an Excel data dictionary for dot_mmm_panel.csv.  Usage: python build_data_dictionary.py panel.csv out.xlsx"""
import sys
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

panel_path, out_path = sys.argv[1:3]
p = pd.read_csv(panel_path, parse_dates=["week_start"])
F = "Arial"
HDR_FILL = PatternFill("solid", start_color="1F3864")
HDR_FONT = Font(name=F, bold=True, color="FFFFFF", size=10)
BODY = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
WRAP = Alignment(wrap_text=True, vertical="top")

SPEND_SRC = "Local Law 83 City Agency Advertising Spend (NYC Open Data, file dated 2026-10-17), City Agency = DOT"
CRASH_SRC = "NYPD Motor Vehicle Collisions - Crashes (NYC Open Data, dataset h9gi-nx95)"
DERIVED = "Derived (calendar / index)"


def rng(col, money=False):
    s = p[col]
    if pd.api.types.is_datetime64_any_dtype(s):
        return f"{s.min():%Y-%m-%d} to {s.max():%Y-%m-%d}"
    fmt = "{:,.0f}" if money else "{:,.0f}"
    return f"{fmt.format(s.min())} to {fmt.format(s.max())}"


safety_note = ("Safety campaigns = DOT campaign names containing: Vision Zero, Speed Camera, Truck Safety, DWI, "
               "Work Zone, E-Bike Safety.")
spread_note = ("Each buy's net spend is spread evenly across its run start-end dates (inclusive), then summed by "
               "Monday-start week.")

rows = [
    ("week_start", "date", "YYYY-MM-DD (Monday)", "First day (Monday) of the week. Unique row key; one row per week.", DERIVED,
     "Weeks start Mon 2022-06-27 and end Mon 2025-06-30. Spend window is 2022-07-01 to 2025-06-30, so the first and last weeks have truncated spend (see Notes)."),
    ("spend_safety_tv", "float", "USD / week", "DOT safety-campaign spend on TV.", SPEND_SRC,
     f"Media Type (Standardized) = TV. {safety_note} {spread_note}"),
    ("spend_safety_radio", "float", "USD / week", "DOT safety-campaign spend on radio.", SPEND_SRC,
     f"Media Type = Radio. {safety_note} {spread_note}"),
    ("spend_safety_print", "float", "USD / week", "DOT safety-campaign spend on print.", SPEND_SRC,
     f"Media Type = Print. {safety_note} {spread_note}"),
    ("spend_safety_digital", "float", "USD / week", "DOT safety-campaign spend on digital (display, publications, programmatic, search).", SPEND_SRC,
     f"Media Type in Digital, Digital Publications, Programmatic, Search. {safety_note} {spread_note}"),
    ("spend_safety_social", "float", "USD / week", "DOT safety-campaign spend on social media.", SPEND_SRC,
     f"Media Type = Social Media. {safety_note} {spread_note} Active in few weeks; consider merging."),
    ("spend_safety_ooh", "float", "USD / week", "DOT safety-campaign spend on out-of-home (incl. digital out-of-home).", SPEND_SRC,
     f"Media Type in Out of Home, Digital Out of Home. {safety_note} {spread_note} Active in few weeks; consider merging."),
    ("spend_safety_other", "float", "USD / week", "DOT safety-campaign spend on media types classed 'Other' (incl. sports sponsorships).", SPEND_SRC,
     f"Media Type in Other, Sports (and any unmapped type). {safety_note} {spread_note} Largest safety channel but not a single medium."),
    ("spend_safety_total", "float", "USD / week", "Total DOT safety-campaign spend across all channels.", "Derived",
     "Sum of the seven spend_safety_* channel columns."),
    ("spend_nonsafety_total", "float", "USD / week", "DOT spend on non-safety campaigns (Summer Streets, BQE closures, Open Streets, recruitment, RFPs, etc.).", SPEND_SRC,
     f"All DOT campaigns not matched by the safety keyword list, all channels combined. {spread_note} Suggested use: control variable."),
    ("spend_total", "float", "USD / week", "Total DOT advertising spend (safety + non-safety).", "Derived",
     "spend_safety_total + spend_nonsafety_total."),
    ("crashes", "int", "count / week", "Police-reported motor vehicle crashes in NYC (citywide, all boroughs).", CRASH_SRC,
     "Count of crash records by CRASH DATE, summed to Monday-start weeks. Likely outcome (Y) for the MMM."),
    ("injured", "int", "persons / week", "Persons injured in NYC motor vehicle crashes.", CRASH_SRC,
     "Sum of NUMBER OF PERSONS INJURED by week."),
    ("killed", "int", "persons / week", "Persons killed in NYC motor vehicle crashes.", CRASH_SRC,
     "Sum of NUMBER OF PERSONS KILLED by week. Sparse (low counts); better as a secondary outcome."),
    ("days_observed", "int", "days (1-7)", "Number of distinct calendar days with crash records in the week.", "Derived",
     "Data-quality check on the crash join. 7 in every week of this panel."),
    ("partial_week", "int (0/1)", "flag", "1 if days_observed < 7, else 0.", "Derived",
     "Flags incomplete CRASH data only. It does NOT flag the truncated-spend weeks at the start and end of the panel."),
    ("iso_week", "int", "1-53", "ISO-8601 week number of week_start.", DERIVED,
     "Use for seasonality. Note 2024-12-30 has iso_week 1 but month 12."),
    ("month", "int", "1-12", "Calendar month of week_start (the Monday).", DERIVED,
     "Weeks straddling a month boundary take the Monday's month."),
    ("t", "int", "weeks", "Zero-based time index.", DERIVED,
     "0 for the first row, increments by 1 each week. Use for trend."),
]

wb = Workbook()
ws = wb.active
ws.title = "Data Dictionary"
hdr = ["Column", "Type", "Unit / Format", "Description", "Source", "How it was derived / notes",
       "Observed range", "Non-null rows", "Zero-valued rows"]
ws.append(hdr)
for name, typ, unit, desc, src, note in rows:
    col = p[name]
    zeros = int((col == 0).sum()) if name.startswith(("spend_", "crashes", "injured", "killed", "partial_week")) else "n/a"
    ws.append([name, typ, unit, desc, src, note, rng(name), int(col.notna().sum()), zeros])

for c in ws[1]:
    c.font, c.fill, c.alignment, c.border = HDR_FONT, HDR_FILL, Alignment(wrap_text=True, vertical="center"), BORDER
for r in ws.iter_rows(min_row=2):
    for c in r:
        c.font, c.alignment, c.border = BODY, WRAP, BORDER
    r[0].font = BOLD
for i, w in enumerate([22, 11, 18, 46, 44, 70, 26, 13, 15], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "B2"
ws.auto_filter.ref = ws.dimensions
ws.row_dimensions[1].height = 30

# ---- Channel mapping
cm = wb.create_sheet("Channel Mapping")
cm.append(["Source media type (Media Type - Standardized)", "Panel channel", "Panel column"])
mapping = [("TV", "tv", "spend_safety_tv"), ("Radio", "radio", "spend_safety_radio"), ("Print", "print", "spend_safety_print"),
           ("Digital", "digital", "spend_safety_digital"), ("Digital Publications", "digital", "spend_safety_digital"),
           ("Programmatic", "digital", "spend_safety_digital"), ("Search", "digital", "spend_safety_digital"),
           ("digital (lowercase typo in source)", "digital", "spend_safety_digital"),
           ("Social Media", "social", "spend_safety_social"), ("Out of Home", "ooh", "spend_safety_ooh"),
           ("Digital Out of Home", "ooh", "spend_safety_ooh"), ("Other", "other", "spend_safety_other"),
           ("Sports", "other", "spend_safety_other"), ("Any unmapped type", "other", "spend_safety_other")]
for m in mapping:
    cm.append(list(m))
cm.append([])
cm.append(["Safety-campaign keywords (case-insensitive match on Ad Campaign Name)"])
for k in ["Vision Zero", "Speed Camera", "Truck Safety", "DWI", "Work Zone", "E-Bike Safety"]:
    cm.append([k])
for c in cm[1]:
    c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BORDER
for r in cm.iter_rows(min_row=2):
    for c in r:
        c.font = BODY
for r in cm.iter_rows(min_row=17, max_row=17):
    r[0].font = BOLD
for i, w in enumerate([62, 18, 26], 1):
    cm.column_dimensions[get_column_letter(i)].width = w

# ---- Sources & Assumptions
sa = wb.create_sheet("Sources & Assumptions")
sa.append(["Item", "Detail"])
items = [
    ("Panel coverage", f"{len(p)} weekly rows, {p.week_start.min():%Y-%m-%d} to {p.week_start.max():%Y-%m-%d}. Spend window 2022-07-01 to 2025-06-30 (FY2023-FY2025)."),
    ("Spend source", "NYC Local Law 83 City Agency Advertising Spend, NYC Open Data. File dated 2026-10-17, with accompanying data dictionary. Filtered to City Agency = DOT (1,460 rows, $13.45M)."),
    ("Outcome source", "NYPD Motor Vehicle Collisions - Crashes, NYC Open Data, dataset id h9gi-nx95 (https://data.cityofnewyork.us/d/h9gi-nx95). Aggregated to Monday-start weeks. Record the date you downloaded it."),
    ("Spend allocation", "Spend is spread evenly across each buy's run dates. The source has no actual delivery data, so weekly shape within a buy is an assumption."),
    ("Date fixes", "11 DOT rows with end date earlier than start date were treated as swapped. Rows with a start date but no end date were treated as single-day buys. 7 'E-Bike Trade In' rows with two insertion dates (e.g. '2/21, 2/28') were split equally across the two dates (year inferred from fiscal year)."),
    ("Excluded spend", "About $101k of Summer Streets spend dated July-August 2025 falls outside the window and is excluded. Panel total spend is $13.35M versus $13.45M in the source."),
    ("Reconciliation", "Panel spend + excluded spend equals the DOT source total to within $0.03."),
    ("Truncated edge weeks", "The week of 2022-06-27 contains only 3 days of spend (window starts 7/1) and the week of 2025-06-30 only 1 day, while crashes cover all 7 days. Drop both rows before modelling (156 weeks remain)."),
    ("Known confounders", "Congestion pricing began January 2025 and crashes trend down over the period; heavy spend falls in spring/summer and December flights overlap the Christmas-week crash dip. Include trend, seasonality, holiday and policy controls."),
    ("Channel overlap", "Safety channels are highly correlated (e.g. radio vs other r=0.91, radio vs digital r=0.85); social and out-of-home are active in few weeks. Separate channel coefficients may not be identifiable."),
    ("Not in this dataset", "Impressions, reach, clicks, geography, or any outcome directly tied to ad exposure. Weather, traffic volume and holidays must be added separately."),
    ("Build scripts", "build_spend_panel.py (spend panel), join_crashes.py (adds crash outcomes and calendar features), build_data_dictionary.py (this file)."),
]
for it in items:
    sa.append(list(it))
for c in sa[1]:
    c.font, c.fill, c.border = HDR_FONT, HDR_FILL, BORDER
for r in sa.iter_rows(min_row=2):
    r[0].font, r[1].font = BOLD, BODY
    for c in r:
        c.alignment, c.border = WRAP, BORDER
sa.column_dimensions["A"].width = 24
sa.column_dimensions["B"].width = 120

wb.save(out_path)
print("saved", out_path)
