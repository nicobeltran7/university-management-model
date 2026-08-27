"""Paths, constants, and the IPEDS variable map.

Every IPEDS variable code used anywhere in this project is declared here and
nowhere else. The labels are taken verbatim from the official IPEDS variable
dictionary (IPEDS202324Tablesdoc.xlsx, sheet varTable23) so that a reader can
check each one against the source.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_IPEDS = ROOT / "Data" / "Finance Data"
RAW_SCORECARD = ROOT / "Data" / "Scorecard"


def scorecard_field_of_study() -> "Path | None":
    """Locate the College Scorecard field-of-study file.

    The download unzips into a dated folder, so the path is discovered rather
    than hard-coded. Returns None when the data has not been downloaded, which
    the application treats as a missing optional module rather than an error.
    """
    if not RAW_SCORECARD.exists():
        return None
    matches = sorted(RAW_SCORECARD.glob("**/Most-Recent-Cohorts-Field-of-Study.csv"))
    return matches[0] if matches else None
# Derived Parquet extracts. Deliberately NOT under data/ or Data/: on a
# case-insensitive filesystem the raw-data ignore rule would swallow them
# and no negation can rescue a file inside an excluded directory.
EXTRACTS = ROOT / "extracts"
PROCESSED = EXTRACTS  # retained name, used throughout

# The two institutions named in the proposed endeavor.
FOCUS_UNITIDS = {
    201885: "University of Cincinnati-Main Campus",
    225432: "University of Houston-Downtown",
}

# Statutory peer group. The Texas Higher Education Coordinating Board assigns
# every public university to a peer group for accountability reporting, and
# UHD sits in the Master's Universities group. Using the state's own grouping
# matters: the comparison set is not the author's choice, so the result cannot
# be dismissed as a peer list picked to flatter or to indict.
#
# Source: THECB, "Data Management & Research Institutional Peer Groups,
# Public Universities FY 2026".
# https://reportcenter.highered.texas.gov/reports/data/university-peer-group-categories/
#
# Two reconciliations between the THECB list and IPEDS, both deliberate:
#  - THECB lists Sul Ross Rio Grande College as a separate member. It has no
#    IPEDS UNITID of its own and is reported under Sul Ross State University,
#    so the eleven THECB entries map to ten IPEDS institutions.
#  - The institution THECB lists as University of Houston-Victoria became
#    Texas A&M University-Victoria in August 2025, when the legislature moved
#    it to the Texas A&M System. Same institution, same UNITID, new name.
THECB_MASTERS_UNIVERSITIES = {
    222831: "Angelo State University",
    226833: "Midwestern State University",
    228501: "Sul Ross State University",
    483036: "Texas A&M University-Central Texas",
    459949: "Texas A&M University-San Antonio",
    224545: "Texas A&M University-Texarkana",
    225502: "Texas A&M University-Victoria",
    229018: "The University of Texas Permian Basin",
    225432: "University of Houston-Downtown",
    484905: "University of North Texas at Dallas",
}

# Named peer groups a reader can select instead of the derived rule.
PEER_PRESETS = {
    "THECB Master's Universities (Texas)": THECB_MASTERS_UNIVERSITIES,
}

# URL slugs for the peer bases, so a view can be linked to. The slug appears
# in the address bar (?peers=thecb-masters-tx) and must stay stable once
# published, because a changed slug silently breaks every link already sent.
PEER_PRESET_SLUGS = {
    "thecb-masters-tx": "THECB Master's Universities (Texas)",
}
PEER_PRESET_TO_SLUG = {name: slug for slug, name in PEER_PRESET_SLUGS.items()}

# IPEDS Finance, public institutions reporting under GASB 34/35.
# Part C: expenses and other deductions, current year total.
EXPENSE_FUNCTIONS = {
    "F1C011": "Instruction",
    "F1C021": "Research",
    "F1C031": "Public service",
    "F1C051": "Academic support",
    "F1C061": "Student services",
    "F1C071": "Institutional support",
    "F1C101": "Scholarships and fellowships",
    "F1C111": "Auxiliary enterprises",
    "F1C121": "Hospital services",
    "F1C131": "Independent operations",
    "F1C141": "Other expenses and deductions",
}
EXPENSE_TOTAL = "F1C191"  # Total expenses and deductions, current year total

# Part B: revenues and other additions. Labels verbatim from the IPEDS
# variable dictionary. Grouped by the statement category the source belongs to,
# because operating and nonoperating revenue behave very differently: state
# appropriations are nonoperating but are the backbone of a public university.
REVENUE_SOURCES = {
    # Operating
    "F1B01": ("Operating", "Tuition and fees, net of discounts"),
    "F1B02": ("Operating", "Federal operating grants and contracts"),
    "F1B03": ("Operating", "State operating grants and contracts"),
    "F1B04": ("Operating", "Local and private operating grants and contracts"),
    "F1B05": ("Operating", "Sales and services of auxiliary enterprises"),
    "F1B06": ("Operating", "Sales and services of hospitals"),
    "F1B26": ("Operating", "Sales and services of educational activities"),
    "F1B07": ("Operating", "Independent operations"),
    "F1B08": ("Operating", "Other operating sources"),
    # Nonoperating
    "F1B10": ("Nonoperating", "Federal appropriations"),
    "F1B11": ("Nonoperating", "State appropriations"),
    "F1B12": ("Nonoperating", "Local appropriations and education district taxes"),
    "F1B13": ("Nonoperating", "Federal nonoperating grants"),
    "F1B14": ("Nonoperating", "State nonoperating grants"),
    "F1B15": ("Nonoperating", "Local nonoperating grants"),
    "F1B16": ("Nonoperating", "Gifts and contributions"),
    "F1B17": ("Nonoperating", "Investment income"),
    "F1B18": ("Nonoperating", "Other nonoperating revenues"),
    # Capital and other additions
    "F1B20": ("Other additions", "Capital appropriations"),
    "F1B21": ("Other additions", "Capital grants and gifts"),
    "F1B22": ("Other additions", "Additions to permanent endowments"),
    "F1B23": ("Other additions", "Other revenues and additions"),
}

# Reported totals. Taken as filed rather than summed, so shares reflect what
# the institution actually reported.
REVENUE_TOTALS = {
    "F1B09": "Total operating revenues",
    "F1B19": "Total nonoperating revenues",
    "F1B24": "Total other revenues and additions",
    "F1B25": "Total all revenues and other additions",
}

# The single line item used for tuition dependence.
TUITION_CODE = "F1B01"
STATE_APPROPRIATION_CODE = "F1B11"
TOTAL_REVENUE_CODE = "F1B25"

# Award levels present in the Completions file. The aggregate codes (12, 13,
# 14, 15) are totals and do not appear in the detail file, so summing across
# these levels does not double count.
AWARD_LEVELS = {
    1: "Certificate, under 1 year",
    2: "Certificate, 1 to 2 years",
    3: "Associate's degree",
    4: "Certificate, 2 to 4 years",
    5: "Bachelor's degree",
    6: "Postbaccalaureate certificate",
    7: "Master's degree",
    8: "Post-master's certificate",
    17: "Doctorate, research or scholarship",
    18: "Doctorate, professional practice",
    19: "Doctorate, other",
    20: "Certificate, under 12 weeks",
    21: "Certificate, 12 weeks to 1 year",
}

# Award levels that represent a degree rather than a certificate.
DEGREE_LEVELS = [3, 5, 7, 17, 18, 19]

# Directory (HD) columns retained.
HD_COLUMNS = [
    "UNITID", "INSTNM", "CITY", "STABBR", "SECTOR", "ICLEVEL", "CONTROL",
    "HLOFFER", "LOCALE", "C21BASIC", "CARNEGIESIZE", "INSTSIZE", "LANDGRNT",
]

# Derived 12-month enrollment (DRVEF12) columns retained.
ENROLLMENT_COLUMNS = ["UNITID", "FTE12MN", "UNDUP", "UNDUPUG"]

# Sector codes, from the IPEDS value sets.
SECTOR_LABELS = {
    0: "Administrative unit",
    1: "Public, 4-year or above",
    2: "Private nonprofit, 4-year or above",
    3: "Private for-profit, 4-year or above",
    4: "Public, 2-year",
    5: "Private nonprofit, 2-year",
    6: "Private for-profit, 2-year",
    7: "Public, less-than-2-year",
    8: "Private nonprofit, less-than-2-year",
    9: "Private for-profit, less-than-2-year",
    99: "Sector unknown",
}

# Finance files present in the raw folder, mapped to the fiscal year reported.
# Fiscal year reported, mapped to the file that carries it. The filename
# encodes the collection year, which is one behind the fiscal year: the
# 2023-24 collection carries fiscal 2024. An "_rv" suffix is the revised
# release and is preferred over the provisional one.
FINANCE_FILES = {
    2020: "f1920_f1a_rv.csv",  # revised
    2021: "f2021_f1a_rv.csv",  # revised
    2022: "f2122_f1a_rv.csv",  # revised
    2023: "f2223_f1a_rv.csv",  # revised
    2024: "f2324_f1a.csv",     # provisional, may be revised by NCES
}

# Derived 12-month enrollment, one file per fiscal year, matching the finance
# years above. DRVEF12 for a collection year covers the twelve months ending
# June of that year, so the 2024 file is the denominator for fiscal 2024.
# Optional: when these files are absent the extract is not written and every
# per-student figure divides by the latest snapshot instead, which the
# interface discloses. Download from the IPEDS data center alongside the
# finance files (DRVEF122020.zip through DRVEF122024.zip).
ENROLLMENT_YEAR_FILES = {
    2020: "drvef122020.csv",
    2021: "drvef122021.csv",
    2022: "drvef122022.csv",
    2023: "drvef122023.csv",
    2024: "drvef122024.csv",
}


# CIP 2-digit series labels, NCES CIP 2020 taxonomy. Only the series that
# appear in the Completions file are named; anything unmapped falls back to
# the raw code rather than being guessed at.
CIP_FAMILIES = {
    "01": "Agriculture",
    "03": "Natural resources and conservation",
    "04": "Architecture",
    "05": "Area, ethnic and gender studies",
    "09": "Communication and journalism",
    "10": "Communications technologies",
    "11": "Computer and information sciences",
    "12": "Personal and culinary services",
    "13": "Education",
    "14": "Engineering",
    "15": "Engineering technologies",
    "16": "Foreign languages and linguistics",
    "19": "Family and consumer sciences",
    "22": "Legal professions and studies",
    "23": "English language and literature",
    "24": "Liberal arts and humanities",
    "25": "Library science",
    "26": "Biological and biomedical sciences",
    "27": "Mathematics and statistics",
    "29": "Military technologies",
    "30": "Multi and interdisciplinary studies",
    "31": "Parks, recreation and fitness",
    "38": "Philosophy and religious studies",
    "39": "Theology and religious vocations",
    "40": "Physical sciences",
    "41": "Science technologies",
    "42": "Psychology",
    "43": "Homeland security and law enforcement",
    "44": "Public administration and social service",
    "45": "Social sciences",
    "46": "Construction trades",
    "47": "Mechanic and repair technologies",
    "48": "Precision production",
    "49": "Transportation and materials moving",
    "50": "Visual and performing arts",
    "51": "Health professions",
    "52": "Business, management and marketing",
    "54": "History",
    "60": "Residency and internship programs",
}


# College Scorecard field-of-study columns retained. Labels are the official
# ones from the data dictionary.
SCORECARD_COLUMNS = {
    "UNITID": "unitid",
    "CIPCODE": "cip4",                      # 4-digit CIP, no decimal point
    "CIPDESC": "program",
    "CREDLEV": "credential_level",
    "CREDDESC": "credential",
    "IPEDSCOUNT1": "awards",
    "DEBT_ALL_STGP_EVAL_MDN": "debt_median",
    "EARN_COUNT_WNE_5YR": "earners",
    "EARN_MDN_5YR": "earnings_median",
    "EARN_MDN_4YR_NAT": "earnings_national_median",
    "EARN_P25_4YR_NAT": "earnings_national_p25",
    "EARN_P75_4YR_NAT": "earnings_national_p75",
}

# Values the Scorecard uses for missing data. "PS" is privacy-suppressed: the
# cohort was too small to publish. Both must be read as null, not as text,
# or every numeric column silently becomes a string.
SCORECARD_NULLS = ["NA", "PS", "PrivacySuppressed", ""]

# Scorecard credential levels.
CREDENTIAL_LEVELS = {
    1: "Undergraduate certificate",
    2: "Associate's degree",
    3: "Bachelor's degree",
    4: "Post-baccalaureate certificate",
    5: "Master's degree",
    6: "Doctoral degree",
    7: "First professional degree",
    8: "Graduate certificate",
}

# IPEDS award level to Scorecard credential level. Used only to describe the
# correspondence in the interface; the join itself is on CIP code and
# credential level as the Scorecard reports them.
AWARD_TO_CREDENTIAL = {
    2: 1, 3: 2, 5: 3, 6: 4, 7: 5, 8: 8, 17: 6, 18: 7, 19: 6, 20: 1, 21: 1,
}
