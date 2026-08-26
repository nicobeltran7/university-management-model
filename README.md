# University Management Model

A data-driven view of how U.S. public universities allocate money, what they
produce, and how they compare to institutions of similar size and type.

Built on federal open data. Every figure in this application comes from the
U.S. Department of Education. Nothing is estimated, simulated or invented.

## What it does

| View | Question it answers |
|---|---|
| **Overview** | What stands out about this institution when it is set against comparable ones? |
| **Budget allocation** | Where does an institution's money actually go, by function, in total and per full-time-equivalent student? |
| **Peer comparison** | How does that allocation compare to institutions of the same sector, level and size? |
| **Opportunities** | Which functions sit furthest from the peer median, and what is that gap worth in dollars? |
| **Reallocation planner** | If money moved between functions, where would the institution land relative to its peers? |
| **Program mix** | What does the institution actually produce, by field of study? |
| **Program returns** | What do those graduates earn, what did they borrow, and how does that compare to the same programme nationally? |
| **Revenue** | Where does the operating money come from? |

The last two views are the point of the project. Reporting what an institution
spends is description. Naming the gaps in dollars, and letting someone test a
reallocation against them, is what makes the output usable in a decision.

One rule governs both: **the tool shows the position a decision creates, and
never predicts the outcome it produces.** A gap against peers is an
observation about how similar institutions allocate differently. It is not
evidence that one allocation performs better, and the application says so on
the page.

The two institutions pinned as defaults are the University of Cincinnati
(UNITID 201885) and the University of Houston-Downtown (UNITID 225432). Every
other U.S. institution in IPEDS remains selectable.

## Data sources

All public domain, all from the U.S. Department of Education.

| Source | Files | What it provides |
|---|---|---|
| IPEDS Finance (GASB 34/35) | `f2223_f1a_rv`, `f2324_f1a` | Expenses by function and operating revenue, fiscal 2023 and 2024, public institutions |
| IPEDS Institutional Characteristics | `hd2025` | Directory, sector, level, size, location |
| IPEDS Derived Enrollment | `drvef122025` | 12-month full-time-equivalent and unduplicated headcount |
| IPEDS Completions | `c2025_a` | Awards conferred by 6-digit CIP code and award level |
| College Scorecard (optional) | `Most-Recent-Cohorts-Field-of-Study` | Median earnings and federal loan debt by programme and credential |

Raw data is **not** committed to this repository. It is roughly 50 MB of public
federal files that anyone can download from the
[IPEDS Data Center](https://nces.ed.gov/ipeds/datacenter/), and committing it
would make the repository large without making it more trustworthy. See
`docs/data-sources.md` for exactly which files to download and where to put
them, then run `make ingest` to rebuild every derived table.

## Architecture

```
raw CSV  ->  ingest.py   ->  Parquet extracts  ->  transform.py  ->  app.py
             (DuckDB)         (extracts/)          (SQL views)      (Streamlit)
```

Transformation logic lives in SQL against DuckDB, not in the presentation
layer. That is a deliberate choice and the same one made in the author's
professional work: pushing logic into the data engine makes the output faster,
reproducible, and testable independently of the interface.

## Running it

Python 3.11 or later.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Windows** (PowerShell). `make` is not available, so either call the commands
directly or use the included task runner:

```powershell
python -m src.ingest              # or  .\tasks.ps1 ingest
python -m pytest tests -q         # or  .\tasks.ps1 test
streamlit run streamlit_app.py    # or  .\tasks.ps1 run
```

**macOS and Linux:**

```bash
make ingest
make test
make run
```

`python -m src.ingest` reads the files in `Data/` and writes Parquet extracts
to `extracts/`. Expect roughly 5,985 institutions, 5,806 enrollment
records, 56,140 finance rows and 201,886 completions rows.

## Documentation

- [`docs/data-sources.md`](docs/data-sources.md) — every source file, where to get it, and the variable codes used
- [`docs/methodology.md`](docs/methodology.md) — how each metric is calculated and why
- [`docs/limitations.md`](docs/limitations.md) — what this cannot answer, and what it would take
- [`docs/design.md`](docs/design.md) — how the palette was validated and why each chart takes the form it does

## Author

Nicolas Esteban Beltran Rubio. MIT licensed.
