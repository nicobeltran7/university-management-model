"""A one-page institutional brief, as a self-contained HTML document.

Built entirely from figures the application already computes, phrased the same
way: position against an observed peer median, never a verdict. The file is
plain HTML with inline styles and a print stylesheet, so it opens anywhere,
attaches to an email, and prints to a clean PDF from any browser.
"""

from __future__ import annotations

import html

from src import theme, transform


def _esc(value) -> str:
    return html.escape(str(value))


def _money(value) -> str:
    return theme.exact_money(value)


def _short(value) -> str:
    return theme.compact_money(value)


def _pct(value, places: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{places}%}"


def one_page_brief(unitid: int) -> str:
    """Render the brief for one institution as an HTML string."""
    summary = transform.institution_summary(unitid)
    expenses = transform.expenses_by_function(unitid)
    year = int(expenses["fiscal_year"].max()) if not expenses.empty else None
    basis = transform.peer_group_basis(unitid)
    peers = transform.peer_count(unitid)

    name = _esc(summary.get("name", "Unknown institution"))
    place = f"{_esc(summary.get('city', ''))}, {_esc(summary.get('state', ''))}"
    sector = _esc(summary.get("sector_label", ""))
    fte = summary.get("fte")
    headcount = summary.get("headcount")
    intensity = (fte / headcount) if fte and headcount else None

    rows: list[str] = []
    if year is not None:
        gaps = transform.opportunity_analysis(unitid, year)
        for _, row in gaps.head(5).iterrows():
            direction = "above" if row["gap_per_fte"] > 0 else "below"
            total = (_short(abs(row["gap_total"]))
                     if row["gap_total"] is not None else "n/a")
            rows.append(
                f"<tr><td>{_esc(row['function'])}</td>"
                f"<td class='num'>{_money(row['target_per_fte'])}</td>"
                f"<td class='num'>{_money(row['peer_median_per_fte'])}</td>"
                f"<td class='num'>{_money(abs(row['gap_per_fte']))} {direction}"
                f"</td><td class='num'>{total}</td></tr>"
            )
        position = transform.revenue_position(unitid, year)
        benchmarks = transform.peer_revenue_benchmarks(unitid, year)
    else:
        position, benchmarks = {}, {}

    def bench(label: str, key: str, kind: str) -> str:
        value, peer = position.get(key), benchmarks.get(key)
        fmt = (lambda v: _pct(v)) if kind == "pct" else (lambda v: _money(v))
        shown = fmt(value) if value is not None else "not reported"
        against = f"peer median {fmt(peer)}" if peer is not None else "no peer figure"
        return (f"<tr><td>{label}</td><td class='num'>{shown}</td>"
                f"<td class='num'>{against}</td></tr>")

    concentration = transform.concentration(unitid) or {}

    fy_label = f"FY{year}" if year is not None else "no current filing"
    year_note = (
        "Per-student figures divide each fiscal year by that year's "
        "enrollment." if transform.enrollment_years_available() else
        "Per-student figures divide by the latest enrollment collection, the "
        "single snapshot loaded."
    )

    stats = "".join(
        f"<div class='stat'><div class='label'>{label}</div>"
        f"<div class='value'>{value}</div></div>"
        for label, value in (
            ("Students (FTE)", f"{fte:,.0f}" if fte else "n/a"),
            ("Headcount", f"{headcount:,.0f}" if headcount else "n/a"),
            ("Enrollment intensity", _pct(intensity, 0)),
            (f"Total expenses, {fy_label}",
             _short(position.get("total_expenses"))),
            (f"Total revenue, {fy_label}",
             _short(position.get("total_revenue"))),
        )
    )

    gaps_table = (
        "<table><thead><tr><th>Function</th><th class='num'>This institution "
        "($/student)</th><th class='num'>Peer median ($/student)</th>"
        "<th class='num'>Distance</th><th class='num'>Total</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        if rows else "<p>No peer comparison available.</p>"
    )

    concentration_line = ""
    if concentration:
        concentration_line = (
            f"<p>Largest field of study: <b>{_esc(concentration['top_field'])}"
            f"</b> at {_pct(concentration['top_share'])} of all awards; the "
            f"three largest fields together are "
            f"{_pct(concentration['top3_share'])} across "
            f"{concentration['fields']} fields.</p>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{name}: institutional brief</title>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; color: #12151a;
         max-width: 720px; margin: 2rem auto; padding: 0 1rem;
         line-height: 1.5; font-size: 15px; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 0.1rem; }}
  .sub {{ color: #5c6270; margin-bottom: 1.2rem; }}
  h2 {{ font-size: 1.05rem; border-bottom: 1px solid #d8d7d1;
        padding-bottom: 3px; margin-top: 1.6rem; }}
  .stats {{ display: flex; gap: 10px; flex-wrap: wrap; }}
  .stat {{ border: 1px solid #d8d7d1; border-radius: 8px;
           padding: 8px 12px; min-width: 118px; }}
  .stat .label {{ font-size: 0.72rem; color: #5c6270;
                  font-family: Arial, sans-serif; }}
  .stat .value {{ font-size: 1.15rem; font-weight: 700; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.88rem; }}
  th, td {{ text-align: left; padding: 5px 8px;
            border-bottom: 1px solid #e4e3dd; }}
  th {{ font-family: Arial, sans-serif; font-size: 0.72rem; color: #5c6270; }}
  .num {{ text-align: right; }}
  .note {{ font-size: 0.8rem; color: #5c6270; margin-top: 1.6rem;
           border-top: 1px solid #d8d7d1; padding-top: 0.6rem; }}
  @media print {{ body {{ margin: 0.4in auto; }} }}
</style>
</head>
<body>
<h1>{name}</h1>
<div class="sub">{place} &middot; {sector} &middot; IPEDS UNITID {int(unitid)}</div>

<div class="stats">{stats}</div>

<h2>Spending position against the peer median, {fy_label}</h2>
<p>Peer basis: {_esc(basis)} ({peers} institutions; the institution is never
part of its own benchmark). The five largest per-student distances:</p>
{gaps_table}

<h2>Revenue exposure, {fy_label}</h2>
<table><tbody>
{bench("Tuition share of revenue", "tuition_dependence", "pct")}
{bench("State appropriations share", "state_share", "pct")}
{bench("Gifts per student", "gifts_per_fte", "money")}
{bench("Auxiliary share of revenue", "auxiliary_share", "pct")}
</tbody></table>

<h2>Award output</h2>
{concentration_line}

<div class="note">
<b>How to read this page.</b> Every figure is read from federal filings:
IPEDS Finance (GASB 34/35), the IPEDS directory, derived enrollment and
completions, and the College Scorecard where cited. Every comparison is
against an observed peer median. A distance from the median is an
observation about how similar institutions allocate differently, not a
recommendation, and nothing on this page is estimated, simulated or
projected. {year_note} Generated by the University Management Model,
an open-source tool; source and methodology at
github.com/nicobeltran7/university-management-model.
</div>
</body>
</html>
"""
