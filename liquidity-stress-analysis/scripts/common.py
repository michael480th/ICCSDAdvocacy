"""
Shared configuration and loaders for the Iowa School District Liquidity Stress
Benchmarking analysis.

This analysis is intentionally kept SEPARATE from the rest of the repository.
It only READS from the repo's shared raw / cleansed data (../../data, ../../CAR,
../../FinalCashReserveLevies, ../../UAB). It writes only inside
liquidity-stress-analysis/output. Nothing here is wired into the public
GitHub Pages site.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = SCRIPTS_DIR.parent                      # liquidity-stress-analysis/
REPO_ROOT = ANALYSIS_DIR.parent                        # repo root
DATA_DIR = REPO_ROOT / "data"                          # shared cleansed data
CAR_CSV = DATA_DIR / "car-fund-balances.csv"
AUDITED_CSV = DATA_DIR / "iowa-district-financials.csv"
NOTES_CSV = DATA_DIR / "iowa-district-notes.csv"
GF_CASH_CSV = DATA_DIR / "gf-operating-cash.csv"
ICCSD_CASH_SUPP_CSV = DATA_DIR / "iccsd-cash-supplemental.csv"
DOM_DIR = DATA_DIR / "dom"
SBRC_DIR = REPO_ROOT / "FinalCashReserveLevies"
UAB_XLSX = REPO_ROOT / "UAB" / "Unspent Authorized Budget Report.xlsx"

OUTPUT_DIR = ANALYSIS_DIR / "output"
INPUTS_DIR = ANALYSIS_DIR / "inputs"        # curated analysis inputs (e.g. board disclosures)
CHARTS_DIR = OUTPUT_DIR / "charts"
TABLES_DIR = OUTPUT_DIR / "tables"
for _d in (OUTPUT_DIR, CHARTS_DIR, TABLES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

MASTER_CSV = OUTPUT_DIR / "district_year_master.csv"
FOCUS_CSV = OUTPUT_DIR / "focus_peer_detail.csv"
DICT_CSV = OUTPUT_DIR / "data_dictionary.csv"

# ---------------------------------------------------------------------------
# District identity
# ---------------------------------------------------------------------------
# CAR district_code (int, == state 4-digit Dist code without leading zeros) ->
# canonical display name used in this analysis.
FOCUS15 = {
    261: "Ankeny CSD",
    882: "Burlington CSD",
    1053: "Cedar Rapids CSD",
    1337: "College Community CSD (Prairie)",
    1611: "Davenport CSD",
    1737: "Des Moines Independent CSD",
    1863: "Dubuque CSD",
    3141: "Iowa City CSD",
    3231: "Johnston CSD",
    3715: "Linn-Mar CSD",
    4581: "Muscatine CSD",
    5250: "Pleasant Valley CSD",
    6795: "Waterloo CSD",
    6822: "Waukee CSD",
    6957: "West Des Moines CSD",
}

# The 9 districts of interest called out by name in the workplan.
NAMED_FOCUS = {3141, 1053, 1737, 1611, 6039, 3715, 261, 6822, 6957}
# (6039 = Sioux City CSD -- in the statewide screen but NOT in the audited 15.)

# Map the audited-financials / DOM district name -> CAR district_code.
AUDITED_NAME_TO_CODE = {
    "Ankeny CSD": 261,
    "Burlington CSD": 882,
    "Cedar Rapids CSD": 1053,
    "College CSD (Prairie)": 1337,
    "Davenport CSD": 1611,
    "Des Moines Independent CSD": 1737,
    "Dubuque CSD": 1863,
    "Iowa City CSD": 3141,
    "Johnston CSD": 3231,
    "Linn-Mar CSD": 3715,
    "Muscatine CSD": 4581,
    "Pleasant Valley CSD": 5250,
    "Waterloo CSD": 6795,
    "Waukee CSD": 6822,
    "West Des Moines CSD": 6957,
}

# ---------------------------------------------------------------------------
# Funds (CAR `fund` values) and how we classify them.
# ---------------------------------------------------------------------------
# Governmental funds we sum into "total governmental fund balance".
# Enterprise and Nutrition are treated as proprietary and EXCLUDED.
GOVERNMENTAL_FUNDS = [
    "General", "Management", "PPEL", "PERL", "Debt Service",
    "Sales Tax", "Other Capital Projects", "Activity",
    "Emergency_Disaster", "Entrepreneurial_Reorganization",
]

FY_MIN, FY_MAX = 2017, 2024          # CAR coverage
PEER_FY_MIN, PEER_FY_MAX = 2020, 2025  # audited coverage

# Most-recent fiscal year with broad statewide component coverage.
COMMON_RECENT_FY = 2024
