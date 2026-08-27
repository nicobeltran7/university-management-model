# Commit plan

Everything is written, but it should not land in one commit. A finished project
arriving in a single "initial commit" reads as a dump. Ten commits reads as
construction.

Commit these groups in order, ideally across two or three sittings. Run
`make test` before each one.

```bash
git init
git branch -M main
```

**1. Scaffold**
```bash
git add .gitignore LICENSE requirements.txt Makefile
git commit -m "Add project scaffold, licence and dependencies"
```

**2. Configuration and the IPEDS variable map**
```bash
git add src/__init__.py src/config.py
git commit -m "Add IPEDS variable map and project paths

Expense and revenue codes are taken from the official IPEDS variable
dictionary. Every code is declared in one place so it can be checked
against the source."
```

**3. Ingest**
```bash
git add src/ingest.py
git commit -m "Add ingest: raw IPEDS CSV to Parquet extracts

Reads the finance, directory, enrollment and completions files and writes
typed Parquet. Finance is unpivoted to long form so the application groups
rather than selects across hundreds of wide columns."
```

**4. Metric definitions and their tests**
```bash
git add src/metrics.py tests/test_metrics.py
git commit -m "Add metric definitions with tests

Per-FTE, share of total, year-over-year change and program concentration.
Each guards against zero and missing denominators."
```

**5. Variable-map tests**
```bash
git add tests/test_config.py
git commit -m "Add assertions on the IPEDS variable map

Pins the current-year-total suffix. Using the salaries-and-wages code by
mistake would understate every function and still produce a valid chart."
```

**6. Transformation layer**
```bash
git add src/transform.py
git commit -m "Add analytic tables in SQL over DuckDB

Expenses by function, revenue mix, peer set, peer comparison and program
mix. Transformation lives in the data engine, not the presentation layer."
```

**7. Application**
```bash
git add src/app.py streamlit_app.py tasks.ps1
git commit -m "Add Streamlit application and Windows task runner

Four views: budget allocation, peer comparison, program mix and revenue.
University of Cincinnati and University of Houston-Downtown are pinned as
defaults."
```

**7b. Gap analysis and the reallocation planner**
```bash
git add src/transform.py src/app.py tests/test_metrics.py
git commit -m "Add gap analysis against peer median and a reallocation planner

Names every functional gap in dollars per student and in total, and lets a
reallocation be tested against the reported total. Neither predicts an
outcome: the planner reports distance from the peer median, not effect."
```

**7c. Fuller revenue and interactive program detail**
```bash
git add src/config.py src/ingest.py src/transform.py src/app.py docs/
git commit -m "Load the full GASB revenue schedule and add program drill-down

Revenue now carries every Part B line grouped by statement category, with
tuition-dependence and state-share ratios benchmarked against peers and an
arithmetic state-funding stress test. Program mix gains award-level
filtering, six-digit CIP drill-down, concentration measures and a
mix-against-peers comparison."
```

**7d. Interface and design system**
```bash
git add src/theme.py src/app.py src/transform.py .streamlit/config.toml docs/design.md
git commit -m "Add design system, an Overview digest, and plain-language takeaways

Palette validated for colour-vision-deficiency separation and contrast
against the pinned light surface. Chart form chosen per reader task:
emphasis for institution against peers, diverging for above and below a
baseline. Adds an Overview tab that states the five headline findings as
sentences rather than leaving the reader to build them."
```

**7e. Program returns from College Scorecard**
```bash
git add src/config.py src/ingest.py src/transform.py src/app.py extracts docs/
git commit -m "Add program returns from College Scorecard field-of-study data" -m "Median earnings five years after entry against median federal loan debt, by programme and credential, compared to the national figure for the same programme. The source is optional: absent it, the ingest skips it and the view explains what is missing."
```

**8. The derived extracts**
```bash
git add extracts
git commit -m "Add derived Parquet extracts

About 1.3 MB. These are what the deployed application reads, and they are
regenerable from the public source files with python -m src.ingest."
```

**9. Documentation**
```bash
git add README.md docs/
git commit -m "Document data sources, methodology and limitations

Names every source file and variable code, defines every metric, and states
what the data cannot answer."
```

**10. Remove this file once you are done**
```bash
git rm COMMIT_PLAN.md
git commit -m "Remove commit plan"
```

Then create the empty public repository on GitHub named
`university-management-model` and:

```bash
git remote add origin https://github.com/nicobeltran7/university-management-model.git
git push -u origin main
```

## Before the first commit

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.ingest
python -m pytest tests -q
streamlit run streamlit_app.py
```

`make ingest` should report roughly:

```
  institutions:     5,985 rows
    enrollment:     5,806 rows
       finance:    56,140 rows
   completions:   201,886 rows
```

If those numbers differ materially, stop and tell me before committing.
