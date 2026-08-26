# Data sources

Every file used by this project is published by the U.S. Department of
Education and is in the public domain. Nothing here is proprietary, and nothing
here comes from the author's employer.

## Where to get the files

All four come from the [IPEDS Data Center](https://nces.ed.gov/ipeds/datacenter/),
under **Complete Data Files**. For each one, download the CSV and its
dictionary. Choose **Final (Revised) Release** where it is offered; a file with
an `_rv` suffix is the revised version and should be preferred.

| Survey component | Year selected | File |
|---|---|---|
| Finance | 2023 | `f2223_f1a_rv.csv` |
| Finance | 2024 | `f2324_f1a.csv` |
| Institutional Characteristics | 2025 | `hd2025.csv` |
| Frequently used / Derived variables | 2025 | `drvef122025.csv` |
| Completions | 2025 | `c2025_a.csv` |

Place them in `Data/Finance Data/`. The paths are declared in `src/config.py`
and nowhere else.

Note the naming convention: `f2324_f1a` holds fiscal year 2024 data collected
in the 2023-24 cycle. Finance is a Spring collection component, so the most
recent year available lags the Fall components by one cycle.

## Which schedule, and why it matters

IPEDS collects institutional finance on three different schedules, because
different institution types report under different accounting standards:

- `_f1a` — public institutions under GASB 34/35
- `_f2` — private nonprofit institutions under FASB
- `_f3` — private for-profit institutions

**This project uses `_f1a` only.** The three schedules are not directly
comparable: the line items differ, the definitions differ, and mixing them
would produce a chart that looks fine and means nothing. Both institutions
named in the endeavor are public, so `_f1a` is the correct schedule for them.
Extending to private institutions is possible but requires a documented
crosswalk, not a union.

## Variable codes used

Taken from the official IPEDS variable dictionary
(`IPEDS202324Tablesdoc.xlsx`, sheet `varTable23`). Labels are verbatim.

### Expenses by function, Part C, current year total

| Code | Label |
|---|---|
| `F1C011` | Instruction |
| `F1C021` | Research |
| `F1C031` | Public service |
| `F1C051` | Academic support |
| `F1C061` | Student services |
| `F1C071` | Institutional support |
| `F1C101` | Scholarships and fellowships |
| `F1C111` | Auxiliary enterprises |
| `F1C121` | Hospital services |
| `F1C131` | Independent operations |
| `F1C141` | Other expenses and deductions |
| `F1C191` | Total expenses and deductions |

Each code ends in `1`, the current-year total. The parallel codes ending in `2`
are salaries and wages only. Using those by mistake would understate every
function, so `tests/test_config.py` asserts the suffix.

### Operating revenue, Part B

| Code | Label |
|---|---|
| `F1B01` | Tuition and fees, net of discounts and allowances |
| `F1B02` | Federal operating grants and contracts |
| `F1B03` | State operating grants and contracts |
| `F1B04` | Local and private operating grants and contracts |

This is not the complete revenue picture. Non-operating revenue, capital
appropriations and investment returns are excluded in this release, so the
revenue view is labelled as partial in the application itself.

## What is committed and what is not

**Not committed:** the raw IPEDS CSV files, roughly 50 MB. Anyone can download
them from the links above, and committing them would make the repository large
without making it more verifiable.

**Committed:** the derived Parquet extracts in `extracts/`, about 1.3 MB
in total. Two reasons. They are what the deployed application reads, and it has
no way to reach the raw files. And they let a reader clone the repository and
inspect exactly the numbers the live application is showing, without
downloading anything.

Anyone can regenerate them from the public sources and confirm they match:

```
python -m src.ingest
```

That command should report 5,985 institutions, 5,806 enrollment records,
56,140 finance rows and 201,886 completions rows.

## Not yet used

Downloaded and available, but not yet joined:

- **College Scorecard** institution and field-of-study files. These carry
  graduate earnings and debt by CIP code, which would let the program mix view
  show what each field actually pays. This is the next planned addition.
- `f2223_f2`, `f2223_f3`, `f2324_f2`, `f2324_f3` — private nonprofit and
  for-profit finance schedules.
- `effy2025` — 12-month unduplicated headcount by level and demographic.
