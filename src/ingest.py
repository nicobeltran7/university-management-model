"""Read the raw IPEDS CSV files and write typed Parquet extracts.

Run with `make ingest`. Reads nothing from the network. Every output file is
reproducible from the public source files listed in docs/data-sources.md.
"""

from __future__ import annotations

import sys

import duckdb

from src import config


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect()


def _quoted(path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def ingest_directory(con: duckdb.DuckDBPyConnection) -> int:
    """Institution directory: one row per institution."""
    src = config.RAW_IPEDS / "hd2025.csv"
    cols = ", ".join(config.HD_COLUMNS)
    out = config.PROCESSED / "institutions.parquet"
    con.execute(
        f"""
        COPY (
            SELECT {cols}
            FROM read_csv_auto({_quoted(src)}, header=true, all_varchar=false,
                               ignore_errors=true, normalize_names=false)
            WHERE UNITID IS NOT NULL
        ) TO {_quoted(out)} (FORMAT PARQUET)
        """
    )
    return con.execute(f"SELECT count(*) FROM read_parquet({_quoted(out)})").fetchone()[0]


def ingest_enrollment(con: duckdb.DuckDBPyConnection) -> int:
    """Derived 12-month enrollment, including full-time equivalent."""
    src = config.RAW_IPEDS / "drvef122025.csv"
    cols = ", ".join(config.ENROLLMENT_COLUMNS)
    out = config.PROCESSED / "enrollment.parquet"
    con.execute(
        f"""
        COPY (
            SELECT {cols}
            FROM read_csv_auto({_quoted(src)}, header=true, ignore_errors=true)
            WHERE UNITID IS NOT NULL
        ) TO {_quoted(out)} (FORMAT PARQUET)
        """
    )
    return con.execute(f"SELECT count(*) FROM read_parquet({_quoted(out)})").fetchone()[0]


def ingest_enrollment_years(con: duckdb.DuckDBPyConnection) -> int:
    """Per-year 12-month enrollment, matched to the finance fiscal years.

    Optional. When none of the DRVEF12 files are present the extract is not
    written, and every per-student figure falls back to the latest snapshot,
    which the application discloses. Years found are loaded; years missing
    are skipped with a note, so a partial download still improves coverage.
    """
    con.execute(
        "CREATE OR REPLACE TEMP TABLE enrollment_years_long "
        "(UNITID BIGINT, fiscal_year INTEGER, fte DOUBLE, headcount DOUBLE)"
    )
    loaded = 0
    for fy, filename in sorted(config.ENROLLMENT_YEAR_FILES.items()):
        src = config.RAW_IPEDS / filename
        if not src.exists():
            print(f"  enrollment_years: skipping FY{fy}, {filename} not found",
                  file=sys.stderr)
            continue
        con.execute(
            f"""
            INSERT INTO enrollment_years_long
            SELECT UNITID, {fy} AS fiscal_year,
                   TRY_CAST(FTE12MN AS DOUBLE) AS fte,
                   TRY_CAST(UNDUP AS DOUBLE)   AS headcount
            FROM read_csv_auto({_quoted(src)}, header=true, ignore_errors=true)
            WHERE UNITID IS NOT NULL
            """
        )
        loaded += 1
    if not loaded:
        print("      enrollment_years: no DRVEF12 files found, skipping",
              file=sys.stderr)
        return 0
    out = config.PROCESSED / "enrollment_years.parquet"
    con.execute(
        f"COPY (SELECT * FROM enrollment_years_long) "
        f"TO {_quoted(out)} (FORMAT PARQUET)"
    )
    return con.execute(
        f"SELECT count(*) FROM read_parquet({_quoted(out)})"
    ).fetchone()[0]


def ingest_finance(con: duckdb.DuckDBPyConnection) -> int:
    """Finance, public institutions under GASB, unpivoted to long form.

    One row per institution, fiscal year, statement section and line item.

    Implemented with UNPIVOT and a mapping table rather than a UNION of one
    SELECT per line item. The earlier version generated roughly forty
    subqueries per year and unioned them in a single statement, which ran out
    of memory once five fiscal years were loaded. This version issues one
    small statement per year and appends, so cost grows linearly and adding
    another decade of data changes nothing but the runtime.
    """
    mapping = []
    for code, label in config.EXPENSE_FUNCTIONS.items():
        mapping.append((code, "expense", "Expense", label))
    mapping.append((config.EXPENSE_TOTAL, "expense_total", "Total",
                    "Total expenses and deductions"))
    for code, (category, label) in config.REVENUE_SOURCES.items():
        mapping.append((code, "revenue", category, label))
    for code, label in config.REVENUE_TOTALS.items():
        mapping.append((code, "revenue_total", "Total", label))

    con.execute(
        "CREATE OR REPLACE TEMP TABLE line_map "
        "(code VARCHAR, section VARCHAR, category VARCHAR, line_item VARCHAR)"
    )
    con.executemany("INSERT INTO line_map VALUES (?, ?, ?, ?)", mapping)

    con.execute(
        "CREATE OR REPLACE TEMP TABLE finance_long "
        "(UNITID BIGINT, fiscal_year INTEGER, section VARCHAR, "
        " category VARCHAR, line_item VARCHAR, amount BIGINT)"
    )

    codes = [row[0] for row in mapping]
    loaded = 0
    for fy, filename in sorted(config.FINANCE_FILES.items()):
        src = config.RAW_IPEDS / filename
        if not src.exists():
            print(f"  skipping FY{fy}: {filename} not found", file=sys.stderr)
            continue

        con.execute(
            f"CREATE OR REPLACE TEMP VIEW raw_year AS "
            f"SELECT * FROM read_csv_auto({_quoted(src)}, header=true, "
            f"ignore_errors=true)"
        )
        present = {row[0] for row in con.execute("DESCRIBE raw_year").fetchall()}
        usable = [c for c in codes if c in present]
        if not usable:
            print(f"  skipping FY{fy}: no expected variables present",
                  file=sys.stderr)
            continue
        absent = [c for c in codes if c not in present]
        if absent:
            print(f"  FY{fy}: {len(absent)} variable(s) not in this release: "
                  f"{', '.join(absent)}", file=sys.stderr)

        columns = ", ".join(f"TRY_CAST({c} AS BIGINT) AS {c}" for c in usable)
        con.execute(
            f"""
            INSERT INTO finance_long
            SELECT u.UNITID, {fy} AS fiscal_year, m.section, m.category,
                   m.line_item, u.amount
            FROM (
                UNPIVOT (SELECT UNITID, {columns} FROM raw_year
                         WHERE UNITID IS NOT NULL)
                ON {", ".join(usable)}
                INTO NAME code VALUE amount
            ) AS u
            JOIN line_map m ON m.code = u.code
            WHERE u.amount IS NOT NULL
            """
        )
        loaded += 1

    if not loaded:
        raise FileNotFoundError("no finance files found in "
                                + str(config.RAW_IPEDS))

    out = config.PROCESSED / "finance.parquet"
    con.execute(
        f"COPY (SELECT * FROM finance_long) TO {_quoted(out)} (FORMAT PARQUET)"
    )
    return con.execute(
        f"SELECT count(*) FROM read_parquet({_quoted(out)})"
    ).fetchone()[0]


def ingest_completions(con: duckdb.DuckDBPyConnection) -> int:
    """Awards conferred by 6-digit CIP code and award level.

    MAJORNUM = 1 keeps first majors only, so a double major is not counted
    twice. CIPCODE '99' is the institution total and is excluded.
    """
    src = config.RAW_IPEDS / "c2025_a.csv"
    out = config.PROCESSED / "completions.parquet"
    con.execute(
        f"""
        COPY (
            SELECT UNITID,
                   CAST(CIPCODE AS VARCHAR)  AS cip_code,
                   TRY_CAST(AWLEVEL AS INT)  AS award_level,
                   TRY_CAST(CTOTALT AS INT)  AS awards
            FROM read_csv_auto({_quoted(src)}, header=true, ignore_errors=true)
            WHERE TRY_CAST(MAJORNUM AS INT) = 1
              AND CAST(CIPCODE AS VARCHAR) NOT IN ('99', '99.0000')
              AND TRY_CAST(CTOTALT AS INT) > 0
        ) TO {_quoted(out)} (FORMAT PARQUET)
        """
    )
    return con.execute(f"SELECT count(*) FROM read_parquet({_quoted(out)})").fetchone()[0]


def ingest_programs(con: duckdb.DuckDBPyConnection) -> int:
    """College Scorecard field-of-study earnings and debt, by program.

    Optional. When the Scorecard download is absent the extract is not written
    and the application hides the module rather than failing.

    Two details matter. The Scorecard marks missing values as "NA" and
    privacy-suppressed values as "PS"; read as text those would turn every
    numeric column into a string, so both are declared as null strings.
    And the Scorecard reports CIP at four digits with no decimal point
    ("1101") while IPEDS reports six with one ("11.0103"), so the join key is
    derived, not assumed.
    """
    src = config.scorecard_field_of_study()
    if src is None:
        print("      programs: Scorecard data not found, skipping",
              file=sys.stderr)
        return 0

    selects = ", ".join(
        f'"{raw}" AS {alias}' for raw, alias in config.SCORECARD_COLUMNS.items()
    )
    nulls = ", ".join(f"'{v}'" for v in config.SCORECARD_NULLS)
    out = config.PROCESSED / "programs.parquet"
    con.execute(
        f"""
        COPY (
            SELECT
                CAST(unitid AS BIGINT)                    AS UNITID,
                lpad(CAST(cip4 AS VARCHAR), 4, '0')       AS cip4,
                trim(rtrim(program, '.'))                 AS program,
                TRY_CAST(credential_level AS INT)         AS credential_level,
                credential                                AS credential,
                TRY_CAST(awards AS INT)                   AS awards,
                TRY_CAST(debt_median AS DOUBLE)           AS debt_median,
                TRY_CAST(earners AS INT)                  AS earners,
                TRY_CAST(earnings_median AS DOUBLE)       AS earnings_median,
                TRY_CAST(earnings_national_median AS DOUBLE)
                                                          AS earnings_national_median,
                TRY_CAST(earnings_national_p25 AS DOUBLE) AS earnings_national_p25,
                TRY_CAST(earnings_national_p75 AS DOUBLE) AS earnings_national_p75
            FROM (
                SELECT {selects}
                FROM read_csv_auto({_quoted(src)}, header=true, all_varchar=true,
                                   nullstr=[{nulls}], ignore_errors=true)
            )
            WHERE unitid IS NOT NULL
        ) TO {_quoted(out)} (FORMAT PARQUET)
        """
    )
    return con.execute(
        f"SELECT count(*) FROM read_parquet({_quoted(out)})"
    ).fetchone()[0]


def main() -> None:
    config.PROCESSED.mkdir(parents=True, exist_ok=True)
    con = _con()
    steps = [
        ("institutions", ingest_directory),
        ("enrollment", ingest_enrollment),
        ("finance", ingest_finance),
        ("enrollment_years", ingest_enrollment_years),
        ("completions", ingest_completions),
        ("programs", ingest_programs),
    ]
    for name, fn in steps:
        rows = fn(con)
        print(f"{name:>14}: {rows:>9,} rows")
    print("\nwrote Parquet extracts to " + str(config.PROCESSED))


if __name__ == "__main__":
    main()
