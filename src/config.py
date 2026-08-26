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
