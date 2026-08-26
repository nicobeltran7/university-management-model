"""Analytic tables built from the Parquet extracts.

All logic lives in SQL against DuckDB rather than in pandas. This mirrors the
principle the project is built on: transformation belongs in the data engine,
not in the presentation layer.
"""

from __future__ import annotations

import functools

import duckdb
import pandas as pd

from src import config


def _quoted(path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


# The columns each extract must contain. Checked at connect time so that a
# stale extract produces a clear instruction rather than a SQL binder error
# several call frames deep.
REQUIRED_COLUMNS = {
    "institutions": {"UNITID", "INSTNM", "STABBR", "SECTOR", "ICLEVEL"},
    "enrollment": {"UNITID", "FTE12MN"},
    "finance": {"UNITID", "fiscal_year", "section", "category", "line_item",
                "amount"},
    "completions": {"UNITID", "cip_code", "award_level", "awards"},
}


@functools.lru_cache(maxsize=1)
def connect() -> duckdb.DuckDBPyConnection:
    """Open a connection with the Parquet extracts registered as views.

    Validates each extract's columns against REQUIRED_COLUMNS. An extract
    written by an older version of the ingest is the most likely cause of a
    confusing failure, so it is caught here with an actionable message.
    """
    con = duckdb.connect()
    for name, required in REQUIRED_COLUMNS.items():
        path = config.PROCESSED / f"{name}.parquet"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is missing.\n\n"
                f"Run the ingest first:  python -m src.ingest"
            )
        con.execute(
            f"CREATE OR REPLACE VIEW {name} AS "
            f"SELECT * FROM read_parquet({_quoted(path)})"
        )
        present = {row[0] for row in con.execute(f"DESCRIBE {name}").fetchall()}
        missing = required - present
        if missing:
            raise RuntimeError(
                f"The '{name}' extract is out of date. It is missing: "
                f"{', '.join(sorted(missing))}.\n\n"
                f"Rebuild it, then restart the app:\n"
                f"    python -m src.ingest\n\n"
                f"Regenerating the Parquet is not enough on its own. The "
                f"database connection is cached for the life of the process, "
                f"so Streamlit has to be stopped and started again."
            )
    return con


def institution_list(state: str | None = None, sector: int | None = None) -> pd.DataFrame:
    """Institutions available for selection, optionally filtered."""
    clauses = ["INSTNM IS NOT NULL"]
    params: list = []
    if state:
        clauses.append("STABBR = ?")
        params.append(state)
    if sector is not None:
        clauses.append("SECTOR = ?")
        params.append(sector)
    sql = f"""
        SELECT UNITID AS unitid, INSTNM AS name, CITY AS city, STABBR AS state,
               SECTOR AS sector, CONTROL AS control, INSTSIZE AS size_category
        FROM institutions
        WHERE {" AND ".join(clauses)}
        ORDER BY INSTNM
    """
    return connect().execute(sql, params).df()


def expenses_by_function(unitid: int) -> pd.DataFrame:
    """Expenses by functional category and fiscal year, with per-FTE and share."""
    unitid = int(unitid)
    sql = """
        WITH e AS (
            SELECT f.fiscal_year, f.line_item, f.amount
            FROM finance f
            WHERE f.UNITID = ? AND f.section = 'expense'
        ),
        t AS (
            SELECT fiscal_year, amount AS total
            FROM finance
            WHERE UNITID = ? AND section = 'expense_total'
        ),
        n AS (SELECT FTE12MN AS fte FROM enrollment WHERE UNITID = ?)
        SELECT e.fiscal_year        AS fiscal_year,
               e.line_item          AS function,
               e.amount             AS amount,
               t.total              AS total_expenses,
               e.amount / NULLIF(t.total, 0)                  AS share_of_total,
               e.amount / NULLIF((SELECT fte FROM n), 0)      AS per_fte
        FROM e
        LEFT JOIN t USING (fiscal_year)
        WHERE e.amount > 0
        ORDER BY e.fiscal_year DESC, e.amount DESC
    """
    return connect().execute(sql, [unitid, unitid, unitid]).df()


def revenue_mix(unitid: int) -> pd.DataFrame:
    """Operating revenue by source and fiscal year."""
    unitid = int(unitid)
    sql = """
        SELECT fiscal_year, line_item AS source, amount
        FROM finance
        WHERE UNITID = ? AND section = 'revenue' AND amount > 0
        ORDER BY fiscal_year DESC, amount DESC
    """
    return connect().execute(sql, [int(unitid)]).df()


def peer_set(unitid: int, size_tolerance: float = 0.5) -> pd.DataFrame:
    """Institutions comparable to the target on sector, level and size.

    The peer definition is deliberately simple and stated in the docs: same
    sector, same institutional level, and full-time-equivalent enrollment
    within a tolerance band of the target. A transparent peer rule the reader
    can check beats a clever one they cannot.
    """
    sql = """
        WITH target AS (
            SELECT i.UNITID, i.SECTOR, i.ICLEVEL, e.FTE12MN AS fte
            FROM institutions i
            LEFT JOIN enrollment e USING (UNITID)
            WHERE i.UNITID = ?
        )
        SELECT i.UNITID AS unitid, i.INSTNM AS name, i.STABBR AS state,
               e.FTE12MN AS fte
        FROM institutions i
        JOIN enrollment e USING (UNITID)
        CROSS JOIN target t
        WHERE i.SECTOR = t.SECTOR
          AND i.ICLEVEL = t.ICLEVEL
          AND i.UNITID <> t.UNITID
          AND e.FTE12MN BETWEEN t.fte * (1 - ?) AND t.fte * (1 + ?)
        ORDER BY abs(e.FTE12MN - (SELECT fte FROM target))
    """
    return connect().execute(
        sql, [int(unitid), float(size_tolerance), float(size_tolerance)]
    ).df()


def peer_comparison(unitid: int, fiscal_year: int) -> pd.DataFrame:
    """Per-FTE spending by function for the target against its peer distribution.

    Functions the target does not report are excluded. Hospital services is the
    reason: only a minority of institutions operate hospitals, so a median
    taken across those that do is enormous and comparing a non-hospital
    institution against it is meaningless.
    """
    peers = peer_set(unitid)
    if peers.empty:
        return pd.DataFrame()
    ids = [int(unitid)] + [int(x) for x in peers["unitid"].tolist()]
    placeholders = ", ".join("?" for _ in ids)
    sql = f"""
        SELECT f.line_item AS function,
               median(f.amount / NULLIF(e.FTE12MN, 0)) AS peer_median_per_fte,
               max(CASE WHEN f.UNITID = ? THEN f.amount / NULLIF(e.FTE12MN, 0) END)
                   AS target_per_fte
        FROM finance f
        JOIN enrollment e USING (UNITID)
        WHERE f.section = 'expense' AND f.fiscal_year = ?
          AND f.UNITID IN ({placeholders})
          AND f.amount > 0 AND e.FTE12MN > 0
        GROUP BY f.line_item
        HAVING max(CASE WHEN f.UNITID = ? THEN f.amount END) IS NOT NULL
        ORDER BY target_per_fte DESC
    """
    return connect().execute(
        sql, [int(unitid), int(fiscal_year), *ids, int(unitid)]
    ).df()


def program_mix(unitid: int, top_n: int = 15) -> pd.DataFrame:
    """Awards conferred by 2-digit CIP family, largest first."""
    sql = """
        SELECT substr(cip_code, 1, 2) AS cip_family,
               sum(awards)            AS awards
        FROM completions
        WHERE UNITID = ?
        GROUP BY 1
        HAVING sum(awards) > 0
        ORDER BY awards DESC
        LIMIT ?
    """
    frame = connect().execute(sql, [unitid, top_n]).df()
    frame["field"] = frame["cip_family"].map(config.CIP_FAMILIES).fillna(
        "CIP " + frame["cip_family"].astype(str)
    )
    return frame


def institution_summary(unitid: int) -> dict:
    """Headline figures for one institution."""
    sql = """
        SELECT i.INSTNM AS name, i.CITY AS city, i.STABBR AS state,
               i.SECTOR AS sector, e.FTE12MN AS fte, e.UNDUP AS headcount
        FROM institutions i
        LEFT JOIN enrollment e USING (UNITID)
        WHERE i.UNITID = ?
    """
    rows = connect().execute(sql, [int(unitid)]).df()
    if rows.empty:
        return {}
    row = rows.iloc[0].to_dict()
    row["sector_label"] = config.SECTOR_LABELS.get(int(row["sector"] or 99), "Unknown")
    return row


def fte(unitid: int) -> float | None:
    """12-month full-time-equivalent enrollment for one institution."""
    row = connect().execute(
        "SELECT FTE12MN FROM enrollment WHERE UNITID = ?", [int(unitid)]
    ).fetchone()
    return float(row[0]) if row and row[0] else None


def opportunity_analysis(unitid: int, fiscal_year: int) -> pd.DataFrame:
    """Every functional gap against the peer median, expressed in dollars.

    This is the prescriptive layer, and it contains no model. For each
    function it states what the institution spends per student, what the
    median comparable institution spends, and the difference, scaled to the
    institution's enrollment.

    It deliberately does not predict what closing a gap would achieve. A gap
    is an observation about how similar institutions allocate differently,
    not evidence that one allocation produces better outcomes.
    """
    comparison = peer_comparison(unitid, fiscal_year)
    if comparison.empty:
        return pd.DataFrame()

    enrolled = fte(unitid)
    frame = comparison.dropna(subset=["target_per_fte", "peer_median_per_fte"]).copy()
    if frame.empty:
        return pd.DataFrame()

    frame["gap_per_fte"] = frame["target_per_fte"] - frame["peer_median_per_fte"]
    frame["gap_total"] = (
        frame["gap_per_fte"] * enrolled if enrolled else None
    )
    frame["position"] = frame["gap_per_fte"].apply(
        lambda g: "Above peer median" if g > 0 else "Below peer median"
    )
    frame["magnitude"] = frame["gap_per_fte"].abs()
    return frame.sort_values("magnitude", ascending=False).reset_index(drop=True)


def peer_count(unitid: int) -> int:
    """Number of institutions in the peer set."""
    return len(peer_set(unitid))


# --------------------------------------------------------------------------
# Revenue
# --------------------------------------------------------------------------

def revenue_detail(unitid: int, fiscal_year: int | None = None) -> pd.DataFrame:
    """Revenue by statement category and source, with share and per-FTE."""
    unitid = int(unitid)
    clause = "AND f.fiscal_year = ?" if fiscal_year else ""
    params: list = [unitid]
    if fiscal_year:
        params.append(int(fiscal_year))
    params += [unitid]
    sql = f"""
        WITH r AS (
            SELECT f.fiscal_year, f.category, f.line_item, f.amount
            FROM finance f
            WHERE f.UNITID = ? AND f.section = 'revenue' AND f.amount > 0 {clause}
        ),
        total AS (
            SELECT fiscal_year, amount AS total_revenue
            FROM finance
            WHERE UNITID = ? AND section = 'revenue_total'
              AND line_item = 'Total all revenues and other additions'
        )
        SELECT r.fiscal_year, r.category, r.line_item AS source, r.amount,
               t.total_revenue,
               r.amount / NULLIF(t.total_revenue, 0) AS share_of_total
        FROM r LEFT JOIN total t USING (fiscal_year)
        ORDER BY r.fiscal_year DESC, r.amount DESC
    """
    return connect().execute(sql, params).df()


def revenue_position(unitid: int, fiscal_year: int) -> dict:
    """Total revenue, total expenses, the difference, and dependence ratios.

    Tuition dependence and state-appropriation share are the two figures a
    public university's finance office watches, because they say how exposed
    the institution is to an enrollment decline or a state budget cut.
    """
    sql = """
        SELECT
          max(CASE WHEN section = 'revenue_total'
                    AND line_item = 'Total all revenues and other additions'
                   THEN amount END)                                AS total_revenue,
          max(CASE WHEN section = 'expense_total' THEN amount END)  AS total_expenses,
          max(CASE WHEN line_item = 'Tuition and fees, net of discounts'
                   THEN amount END)                                AS tuition,
          max(CASE WHEN line_item = 'State appropriations'
                   THEN amount END)                                AS state_appropriations
        FROM finance
        WHERE UNITID = ? AND fiscal_year = ?
    """
    rows = connect().execute(sql, [int(unitid), int(fiscal_year)]).df()
    if rows.empty:
        return {}
    out = rows.iloc[0].to_dict()
    total = out.get("total_revenue")
    out["surplus"] = (
        out["total_revenue"] - out["total_expenses"]
        if out.get("total_revenue") and out.get("total_expenses") else None
    )
    out["tuition_dependence"] = (
        out["tuition"] / total if total and out.get("tuition") else None
    )
    out["state_share"] = (
        out["state_appropriations"] / total
        if total and out.get("state_appropriations") else None
    )
    enrolled = fte(unitid)
    out["fte"] = enrolled
    out["revenue_per_fte"] = total / enrolled if total and enrolled else None
    return out


def peer_revenue_benchmarks(unitid: int, fiscal_year: int) -> dict:
    """Peer median tuition dependence, state share and revenue per FTE."""
    unitid = int(unitid)
    peers = peer_set(unitid)
    if peers.empty:
        return {}
    ids = [int(x) for x in peers["unitid"].tolist()]
    placeholders = ", ".join("?" for _ in ids)
    sql = f"""
        WITH base AS (
            SELECT f.UNITID,
              max(CASE WHEN f.section = 'revenue_total'
                        AND f.line_item = 'Total all revenues and other additions'
                       THEN f.amount END) AS total_revenue,
              max(CASE WHEN f.line_item = 'Tuition and fees, net of discounts'
                       THEN f.amount END) AS tuition,
              max(CASE WHEN f.line_item = 'State appropriations'
                       THEN f.amount END) AS state_appropriations,
              max(e.FTE12MN)              AS fte
            FROM finance f
            JOIN enrollment e USING (UNITID)
            WHERE f.fiscal_year = ? AND f.UNITID IN ({placeholders})
            GROUP BY f.UNITID
        )
        SELECT median(tuition / NULLIF(total_revenue, 0))              AS tuition_dependence,
               median(state_appropriations / NULLIF(total_revenue, 0)) AS state_share,
               median(total_revenue / NULLIF(fte, 0))                  AS revenue_per_fte
        FROM base
        WHERE total_revenue > 0 AND fte > 0
    """
    rows = connect().execute(sql, [int(fiscal_year), *ids]).df()
    return rows.iloc[0].to_dict() if not rows.empty else {}


# --------------------------------------------------------------------------
# Programs
# --------------------------------------------------------------------------

def award_levels_present(unitid: int) -> list[int]:
    """Award levels this institution actually confers."""
    rows = connect().execute(
        "SELECT DISTINCT award_level FROM completions "
        "WHERE UNITID = ? AND award_level IS NOT NULL ORDER BY award_level",
        [int(unitid)],
    ).fetchall()
    return [int(r[0]) for r in rows]


def program_families(unitid: int, levels: list[int] | None = None,
                     top_n: int = 15) -> pd.DataFrame:
    """Awards by 2-digit CIP family, optionally restricted to award levels."""
    params: list = [int(unitid)]
    clause = ""
    if levels:
        clause = "AND award_level IN (" + ", ".join("?" for _ in levels) + ")"
        params += [int(x) for x in levels]
    params.append(int(top_n))
    sql = f"""
        SELECT substr(cip_code, 1, 2) AS cip_family, sum(awards) AS awards
        FROM completions
        WHERE UNITID = ? {clause}
        GROUP BY 1 HAVING sum(awards) > 0
        ORDER BY awards DESC LIMIT ?
    """
    frame = connect().execute(sql, params).df()
    if frame.empty:
        return frame
    frame["field"] = frame["cip_family"].map(config.CIP_FAMILIES).fillna(
        "CIP " + frame["cip_family"].astype(str)
    )
    return frame


def programs_in_family(unitid: int, cip_family: str,
                       levels: list[int] | None = None) -> pd.DataFrame:
    """Individual 6-digit programs inside one CIP family."""
    params: list = [int(unitid), str(cip_family)]
    clause = ""
    if levels:
        clause = "AND award_level IN (" + ", ".join("?" for _ in levels) + ")"
        params += [int(x) for x in levels]
    sql = f"""
        SELECT cip_code, award_level, sum(awards) AS awards
        FROM completions
        WHERE UNITID = ? AND substr(cip_code, 1, 2) = ? {clause}
        GROUP BY 1, 2 HAVING sum(awards) > 0
        ORDER BY awards DESC
    """
    frame = connect().execute(sql, params).df()
    if frame.empty:
        return frame
    frame["level"] = frame["award_level"].map(config.AWARD_LEVELS).fillna("Unknown")
    return frame


def program_mix_gap(unitid: int) -> pd.DataFrame:
    """This institution's share of awards by field against the peer median share.

    Shares rather than counts, so a large institution and a small one are
    comparable. A positive gap means the institution is more concentrated in
    that field than the median comparable institution.
    """
    peers = peer_set(unitid)
    if peers.empty:
        return pd.DataFrame()
    ids = [int(x) for x in peers["unitid"].tolist()]
    placeholders = ", ".join("?" for _ in ids)
    sql = f"""
        WITH by_inst AS (
            SELECT UNITID, substr(cip_code, 1, 2) AS cip_family,
                   sum(awards) AS awards
            FROM completions
            WHERE UNITID IN ({placeholders}) OR UNITID = ?
            GROUP BY 1, 2
        ),
        totals AS (
            SELECT UNITID, sum(awards) AS total FROM by_inst GROUP BY 1
        ),
        shares AS (
            SELECT b.UNITID, b.cip_family, b.awards / NULLIF(t.total, 0) AS share
            FROM by_inst b JOIN totals t USING (UNITID)
        )
        SELECT cip_family,
               max(CASE WHEN UNITID = ? THEN share END) AS target_share,
               median(CASE WHEN UNITID <> ? THEN share END) AS peer_median_share
        FROM shares
        GROUP BY 1
        HAVING max(CASE WHEN UNITID = ? THEN share END) IS NOT NULL
    """
    frame = connect().execute(
        sql, [*ids, int(unitid), int(unitid), int(unitid), int(unitid)]
    ).df()
    if frame.empty:
        return frame
    frame["peer_median_share"] = frame["peer_median_share"].fillna(0)
    frame["gap"] = frame["target_share"] - frame["peer_median_share"]
    frame["field"] = frame["cip_family"].map(config.CIP_FAMILIES).fillna(
        "CIP " + frame["cip_family"].astype(str)
    )
    frame["magnitude"] = frame["gap"].abs()
    return frame.sort_values("magnitude", ascending=False).reset_index(drop=True)


def concentration(unitid: int, levels: list[int] | None = None) -> dict:
    """How concentrated the award output is across fields."""
    frame = program_families(unitid, levels=levels, top_n=1000)
    if frame.empty:
        return {}
    total = float(frame["awards"].sum())
    ordered = frame.sort_values("awards", ascending=False)
    shares = ordered["awards"] / total
    return {
        "total_awards": total,
        "fields": int(len(ordered)),
        "top_field": ordered.iloc[0]["field"],
        "top_share": float(shares.iloc[0]),
        "top3_share": float(shares.head(3).sum()),
        "hhi": float((shares ** 2).sum()),
    }


def headline_findings(unitid: int, fiscal_year: int) -> list[dict]:
    """The three or four things a reader should know first, as structured facts.

    Assembled from figures already computed elsewhere. Nothing here is
    interpreted or scored: each finding is a comparison against an observed
    peer median, phrased by the caller.
    """
    findings: list[dict] = []

    gaps = opportunity_analysis(unitid, fiscal_year)
    if not gaps.empty:
        biggest = gaps.iloc[0]
        findings.append({
            "kind": "spending_gap",
            "function": biggest["function"],
            "target": float(biggest["target_per_fte"]),
            "peer": float(biggest["peer_median_per_fte"]),
            "gap_per_fte": float(biggest["gap_per_fte"]),
            "gap_total": float(biggest["gap_total"]),
        })

    position = revenue_position(unitid, fiscal_year)
    benchmarks = peer_revenue_benchmarks(unitid, fiscal_year)
    if position.get("tuition_dependence") and benchmarks.get("tuition_dependence"):
        findings.append({
            "kind": "tuition_dependence",
            "value": float(position["tuition_dependence"]),
            "peer": float(benchmarks["tuition_dependence"]),
        })
    if position.get("state_share") and benchmarks.get("state_share"):
        findings.append({
            "kind": "state_share",
            "value": float(position["state_share"]),
            "peer": float(benchmarks["state_share"]),
        })

    mix = program_mix_gap(unitid)
    if not mix.empty:
        top = mix.iloc[0]
        findings.append({
            "kind": "program_concentration",
            "field": top["field"],
            "value": float(top["target_share"]),
            "peer": float(top["peer_median_share"]),
        })

    if position.get("surplus") is not None and position.get("total_revenue"):
        findings.append({
            "kind": "surplus",
            "surplus": float(position["surplus"]),
            "margin": float(position["surplus"]) / float(position["total_revenue"]),
        })

    return findings


# --------------------------------------------------------------------------
# Program returns (College Scorecard)
# --------------------------------------------------------------------------

def programs_available() -> bool:
    """Whether the optional Scorecard extract was built."""
    return (config.PROCESSED / "programs.parquet").exists()


@functools.lru_cache(maxsize=1)
def _programs_view() -> bool:
    """Register the optional programs extract, once."""
    if not programs_available():
        return False
    path = config.PROCESSED / "programs.parquet"
    connect().execute(
        f"CREATE OR REPLACE VIEW programs AS "
        f"SELECT * FROM read_parquet({_quoted(path)})"
    )
    return True


def program_returns(unitid: int, min_earners: int = 0) -> pd.DataFrame:
    """Earnings and debt by program, against the national figure for that program.

    Award counts come from the Scorecard's own IPEDSCOUNT1 field rather than
    from a join to the Completions extract. The Scorecard reports CIP at four
    digits and IPEDS at six, so joining them would require collapsing one
    side and would introduce an avoidable source of error for no gain.

    Only rows where the Scorecard published both an earnings and a debt figure
    are returned. Roughly four out of five program-and-credential rows are
    privacy-suppressed because the cohort was too small, so this is a view of
    the larger programs, not of all of them.
    """
    if not _programs_view():
        return pd.DataFrame()
    sql = """
        SELECT program, credential, credential_level, cip4,
               awards, earners, debt_median, earnings_median,
               earnings_national_median, earnings_national_p25,
               earnings_national_p75,
               debt_median / NULLIF(earnings_median, 0) AS debt_to_earnings,
               earnings_median - earnings_national_median AS vs_national,
               (earnings_median - earnings_national_median)
                   / NULLIF(earnings_national_median, 0) AS vs_national_pct
        FROM programs
        WHERE UNITID = ?
          AND earnings_median IS NOT NULL
          AND debt_median IS NOT NULL
          AND coalesce(earners, 0) >= ?
        ORDER BY earnings_median DESC
    """
    return connect().execute(sql, [int(unitid), int(min_earners)]).df()


def program_return_summary(unitid: int) -> dict:
    """Headline figures for the return view."""
    frame = program_returns(unitid)
    if frame.empty:
        return {}
    with_national = frame.dropna(subset=["vs_national"])
    return {
        "programs": int(len(frame)),
        "median_earnings": float(frame["earnings_median"].median()),
        "median_debt": float(frame["debt_median"].median()),
        "median_dte": float(frame["debt_to_earnings"].median()),
        "above_national": int((with_national["vs_national"] > 0).sum()),
        "below_national": int((with_national["vs_national"] < 0).sum()),
        "compared": int(len(with_national)),
        "best": frame.iloc[0].to_dict(),
        "worst_dte": frame.sort_values("debt_to_earnings",
                                      ascending=False).iloc[0].to_dict(),
    }
