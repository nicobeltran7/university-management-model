"""University Management Model — a data-driven view of institutional finance.

Streamlit application. Run with:  streamlit run streamlit_app.py

Every figure shown comes from the U.S. Department of Education's IPEDS
collection. Nothing is estimated, simulated or invented. Where the application
compares an institution to others, the comparison is against observed values,
never against a modelled expectation.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src import config, theme, transform

st.set_page_config(
    page_title="University Management Model",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------
# Small presentation helpers
# --------------------------------------------------------------------------

def takeaway(text: str) -> None:
    """The one sentence a reader should leave a chart with."""
    st.markdown(f'<div class="takeaway">{text}</div>', unsafe_allow_html=True)


def eyebrow(text: str) -> None:
    st.markdown(f'<div class="eyebrow">{text}</div>', unsafe_allow_html=True)


def pct(value: float | None, places: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{places}%}"


money = theme.exact_money
short = theme.compact_money


@st.cache_resource
def _ready() -> bool:
    transform.connect()
    return True


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

@st.cache_data
def _all_institutions() -> pd.DataFrame:
    frame = transform.institution_list()
    frame["display"] = frame["name"] + "  ·  " + frame["state"].fillna("")
    return frame


def sidebar_selection() -> int:
    st.sidebar.markdown("## University Management Model")
    st.sidebar.caption(
        "Federal open data on how U.S. public universities allocate money, "
        "what they produce, and how they compare to institutions like them."
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Choose an institution")

    named = list(config.FOCUS_UNITIDS.values())
    frame = _all_institutions()
    options = named + [
        row for row in frame["display"].tolist()
        if not any(row.startswith(n) for n in named)
    ]

    choice = st.sidebar.selectbox(
        "Search by name", options, index=0,
        help="Start typing to search all 5,985 institutions in the IPEDS "
             "directory. The two at the top are the sites described in the "
             "proposed endeavor.",
    )

    for unitid, name in config.FOCUS_UNITIDS.items():
        if choice == name:
            return unitid
    return int(frame.loc[frame["display"] == choice, "unitid"].iloc[0])


def sidebar_reference() -> None:
    st.sidebar.markdown("---")
    with st.sidebar.expander("What the terms mean"):
        st.markdown(
            "**FTE** — full-time equivalent. Part-time students counted as "
            "fractions of a full-time one, so institutions with different "
            "enrollment patterns are comparable.\n\n"
            "**Per FTE** — a total divided by FTE enrollment. A large "
            "university spends more on teaching than a small one by "
            "definition; per-student figures make the comparison mean "
            "something.\n\n"
            "**Institutional support** — the IPEDS term for administration. "
            "Executive management, legal, fiscal operations, public "
            "relations.\n\n"
            "**Academic support** — libraries, museums, academic "
            "computing, curriculum development. Support *for* teaching "
            "rather than teaching itself.\n\n"
            "**GASB 34/35** — the accounting standard public institutions "
            "report under. Private institutions use a different one, which "
            "is why they are not included here.\n\n"
            "**CIP code** — Classification of Instructional Programs, the "
            "federal taxonomy of fields of study.\n\n"
            "**Peer group** — institutions of the same sector and level "
            "whose FTE enrollment is within 50 percent of this one's."
        )
    st.sidebar.caption(
        "Source: IPEDS, U.S. Department of Education. Public domain. "
        "No estimated or simulated figures appear anywhere in this "
        "application."
    )


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

def render_header(unitid: int) -> tuple[dict, int | None]:
    summary = transform.institution_summary(unitid)
    if not summary:
        st.error("No directory record for that institution.")
        st.stop()

    eyebrow("Institutional profile")
    st.markdown(f"# {summary['name']}")
    st.markdown(
        f'<div class="subtitle">{summary["city"]}, {summary["state"]}'
        f'  ·  {summary["sector_label"]}  ·  IPEDS UNITID {unitid}</div>',
        unsafe_allow_html=True,
    )

    expenses = transform.expenses_by_function(unitid)
    year = int(expenses["fiscal_year"].max()) if not expenses.empty else None

    columns = st.columns(4)
    columns[0].metric("Students (FTE)", f"{summary.get('fte') or 0:,.0f}")
    columns[1].metric("Headcount", f"{summary.get('headcount') or 0:,.0f}")
    if year:
        total = expenses.loc[expenses["fiscal_year"] == year,
                             "total_expenses"].iloc[0]
        columns[2].metric(f"Expenses, FY{year}", short(total))
        position = transform.revenue_position(unitid, year)
        columns[3].metric(f"Revenue, FY{year}",
                          short(position.get("total_revenue")))
    else:
        columns[2].metric("Expenses", "not reported")
        columns[3].metric("Revenue", "not reported")
    return summary, year


# --------------------------------------------------------------------------
# Overview
# --------------------------------------------------------------------------

def render_overview(unitid: int, summary: dict, year: int | None) -> None:
    st.subheader("What this institution looks like")
    st.caption(
        "The five things that stand out when this institution is set against "
        "comparable ones. Every figure below is read from federal filings; "
        "every comparison is against an observed peer median."
    )

    if year is None:
        st.info(
            "This institution does not report on the GASB schedule used here, "
            "so no comparison is available. Only public institutions are "
            "covered in this release."
        )
        return

    findings = transform.headline_findings(unitid, year)
    if not findings:
        st.info("No peer group available for this institution.")
        return

    peers = transform.peer_count(unitid)
    enrolled = summary.get("fte") or 0
    st.markdown(
        f"FY{year}, measured against **{peers}** institutions of the same "
        f"sector and level with enrollment within 50 percent of this one's."
    )

    for finding in findings:
        kind = finding["kind"]

        if kind == "spending_gap":
            direction = "more" if finding["gap_per_fte"] > 0 else "less"
            takeaway(
                f"<b>Its largest spending difference is "
                f"{finding['function'].lower()}.</b> It spends "
                f"{money(finding['target'])} per student where the median "
                f"comparable institution spends "
                f"{money(finding['peer'])}. That is "
                f"{money(abs(finding['gap_per_fte']))} {direction} per "
                f"student, or {short(abs(finding['gap_total']))} across "
                f"{enrolled:,.0f} students."
            )

        elif kind == "tuition_dependence":
            gap = (finding["value"] - finding["peer"]) * 100
            word = "more" if gap > 0 else "less"
            takeaway(
                f"<b>It is {word} dependent on tuition than its peers.</b> "
                f"Tuition is {pct(finding['value'])} of total revenue, "
                f"against a peer median of {pct(finding['peer'])}, a "
                f"difference of {abs(gap):.1f} percentage points. Tuition "
                f"dependence is exposure to an enrollment decline."
            )

        elif kind == "state_share":
            gap = (finding["value"] - finding["peer"]) * 100
            word = "more" if gap > 0 else "less"
            takeaway(
                f"<b>It receives {word} state support than its peers.</b> "
                f"State appropriations are {pct(finding['value'])} of total "
                f"revenue, against a peer median of {pct(finding['peer'])}."
            )

        elif kind == "program_concentration":
            ratio = (finding["value"] / finding["peer"]) if finding["peer"] else None
            multiple = f" roughly {ratio:.1f} times the peer share," if ratio else ""
            takeaway(
                f"<b>Its output is concentrated in "
                f"{finding['field'].lower()}.</b> That field is "
                f"{pct(finding['value'])} of all awards conferred,{multiple} "
                f"against a peer median of {pct(finding['peer'])}. "
                f"Concentration is efficient while demand holds and a risk "
                f"when it does not."
            )

        elif kind == "surplus":
            word = "surplus" if finding["surplus"] >= 0 else "deficit"
            takeaway(
                f"<b>It ran a {word} of "
                f"{short(abs(finding['surplus']))} in FY{year},</b> "
                f"{pct(abs(finding['margin']))} of total revenue."
            )

    st.markdown("---")
    st.markdown(
        "**Where to go next.** *Opportunities* puts every spending gap in "
        "dollars. *Reallocation planner* lets you test moving money between "
        "functions. *Program mix* breaks the award output down to individual "
        "programs. *Revenue* has a state-funding stress test."
    )


# --------------------------------------------------------------------------
# Budget allocation
# --------------------------------------------------------------------------

def render_budget(unitid: int) -> None:
    st.subheader("Where the money goes")
    st.caption(
        "Expenses by functional category, IPEDS Finance, public institutions "
        "reporting under GASB 34/35. Shares use the reported total rather "
        "than a sum of the lines."
    )

    frame = transform.expenses_by_function(unitid)
    if frame.empty:
        st.info(
            "This institution does not report on the GASB schedule used here. "
            "Only public institutions are covered in this release."
        )
        return

    years = sorted(frame["fiscal_year"].unique(), reverse=True)
    year = int(st.selectbox("Fiscal year", years,
                            format_func=lambda y: f"FY{y}"))
    current = frame[frame["fiscal_year"] == year].copy()

    largest = current.iloc[0]
    takeaway(
        f"The single largest call on the budget is "
        f"<b>{largest['function'].lower()}</b> at "
        f"{short(largest['amount'])}, "
        f"{pct(largest['share_of_total'])} of total expenses and "
        f"{money(largest['per_fte'])} per student."
    )

    left, right = st.columns([3, 2])
    with left:
        # Magnitude, low to high. Single series, so no legend and one hue.
        chart = px.bar(
            current.sort_values("amount"), x="amount", y="function",
            orientation="h",
            labels={"amount": f"FY{year} expenses ($)", "function": ""},
            color_discrete_sequence=[theme.SUBJECT],
        )
        chart.update_traces(
            marker_line_width=0,
            hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
        )
        chart.update_layout(**theme.plotly_layout(430, legend=False))
        st.plotly_chart(chart, use_container_width=True)

    with right:
        display = current[["function", "amount", "share_of_total",
                           "per_fte"]].copy()
        display["share_of_total"] = (display["share_of_total"] * 100).round(1)
        display["per_fte"] = display["per_fte"].round(0)
        st.dataframe(
            display.rename(columns={
                "function": "Function", "amount": "Expenses ($)",
                "share_of_total": "Share (%)", "per_fte": "Per student ($)",
            }),
            hide_index=True, use_container_width=True, height=430,
        )

    if len(years) > 1:
        st.markdown(f"**Trend, FY{min(years)} to FY{max(years)}**")
        st.caption(
            "Expenses per student by function and fiscal year. Nine functions "
            "across five years is a grid, so it is shown as one: a grouped "
            "bar chart at that size forces the reader to count bars, and "
            "assigning nine or ten colours to an ordered series would misuse "
            "colour to encode time."
        )
        grid = frame.pivot_table(index="function", columns="fiscal_year",
                                 values="per_fte", aggfunc="sum")
        grid = grid.reindex(
            grid.mean(axis=1).sort_values(ascending=False).index
        )
        heat = px.imshow(
            grid.values,
            x=[f"FY{int(c)}" for c in grid.columns],
            y=list(grid.index),
            color_continuous_scale=theme.SEQUENTIAL,
            aspect="auto",
            labels=dict(color="$ per student"),
        )
        heat.update_traces(
            hovertemplate="%{y}<br>%{x}<br>$%{z:,.0f} per student<extra></extra>"
        )
        layout = theme.plotly_layout(430, legend=False)
        layout["coloraxis_colorbar"] = dict(title="$ / student", thickness=12)
        heat.update_layout(**layout)
        st.plotly_chart(heat, use_container_width=True)

        first, last = int(min(years)), int(max(years))
        change = grid[[last]].join(grid[[first]], lsuffix="_last")
        change.columns = ["last", "first"]
        change["pct"] = (change["last"] - change["first"]) / change["first"]
        movers = change.dropna().sort_values("pct", ascending=False)
        if not movers.empty:
            top = movers.iloc[0]
            takeaway(
                f"Over five years the function that grew fastest per student "
                f"is <b>{movers.index[0].lower()}</b>, from "
                f"{money(top['first'])} in FY{first} to "
                f"{money(top['last'])} in FY{last}, a change of "
                f"{top['pct']:+.0%}."
            )
            st.dataframe(
                movers.reset_index().rename(columns={
                    "function": "Function",
                    "first": f"FY{first} ($/student)",
                    "last": f"FY{last} ($/student)",
                    "pct": "Change",
                }).round({f"FY{first} ($/student)": 0,
                          f"FY{last} ($/student)": 0}).assign(
                    Change=lambda d: (d["Change"] * 100).round(1)
                ).rename(columns={"Change": "Change (%)"}),
                hide_index=True, use_container_width=True,
            )


# --------------------------------------------------------------------------
# Peer comparison
# --------------------------------------------------------------------------

def render_peers(unitid: int) -> None:
    st.subheader("Against comparable institutions")
    st.caption(
        "Peers are institutions in the same IPEDS sector and level whose "
        "full-time-equivalent enrollment falls within 50 percent of this "
        "one's. The rule is deliberately simple so that it can be checked."
    )

    peers = transform.peer_set(unitid)
    if peers.empty:
        st.info("No peers matched on sector, level and size.")
        return

    frame = transform.expenses_by_function(unitid)
    if frame.empty:
        return
    year = int(frame["fiscal_year"].max())
    comparison = transform.peer_comparison(unitid, year)
    if comparison.empty:
        st.info("Peer comparison unavailable for this fiscal year.")
        return

    st.metric("Institutions in the peer group", f"{len(peers):,}")

    melted = comparison.melt(
        id_vars="function",
        value_vars=["target_per_fte", "peer_median_per_fte"],
        var_name="series", value_name="per_fte",
    )
    melted["series"] = melted["series"].map({
        "target_per_fte": "This institution",
        "peer_median_per_fte": "Peer median",
    })
    # Emphasis, not categorical: the institution is the subject, the peer
    # median is context. Accent hue plus de-emphasis grey.
    chart = px.bar(
        melted, x="function", y="per_fte", color="series", barmode="group",
        labels={"per_fte": f"FY{year} expenses per student ($)", "function": ""},
        color_discrete_map={"This institution": theme.SUBJECT,
                            "Peer median": theme.CONTEXT},
        category_orders={"series": ["This institution", "Peer median"]},
    )
    chart.update_traces(marker_line_width=0,
                        hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>")
    chart.update_layout(**theme.plotly_layout(430))
    st.plotly_chart(chart, use_container_width=True)

    with st.expander(f"The {len(peers)} institutions in this peer group"):
        st.dataframe(
            peers.rename(columns={"unitid": "UNITID", "name": "Institution",
                                  "state": "State", "fte": "Students (FTE)"}),
            hide_index=True, use_container_width=True, height=330,
        )


# --------------------------------------------------------------------------
# Opportunities
# --------------------------------------------------------------------------

def render_opportunities(unitid: int) -> None:
    st.subheader("Where the gaps are")
    st.caption(
        "Every functional category where per-student spending differs from "
        "the median comparable institution, per student and in total dollars."
    )

    frame = transform.expenses_by_function(unitid)
    if frame.empty:
        st.info("No finance data on the GASB schedule for this institution.")
        return
    year = int(frame["fiscal_year"].max())
    gaps = transform.opportunity_analysis(unitid, year)
    if gaps.empty:
        st.info("No peer comparison available for this institution.")
        return

    enrolled = transform.fte(unitid)
    peers = transform.peer_count(unitid)
    above = gaps[gaps["gap_per_fte"] > 0]["gap_total"].sum()
    below = gaps[gaps["gap_per_fte"] < 0]["gap_total"].sum()

    columns = st.columns(3)
    columns[0].metric("Peer group", f"{peers:,} institutions")
    columns[1].metric("Above peer median", short(above),
                      help="Spending in excess of the median comparable "
                           "institution, summed across functions.")
    columns[2].metric("Below peer median", short(abs(below)),
                      help="Spending short of the median comparable "
                           "institution, summed across functions.")

    # Above/below a baseline: diverging, two hues with a neutral midpoint.
    chart = px.bar(
        gaps.sort_values("gap_per_fte"), x="gap_per_fte", y="function",
        orientation="h", color="position",
        labels={"gap_per_fte": f"FY{year} gap against peer median, per student ($)",
                "function": ""},
        color_discrete_map={"Above peer median": theme.ABOVE,
                            "Below peer median": theme.BELOW},
        category_orders={"position": ["Below peer median", "Above peer median"]},
    )
    chart.update_traces(marker_line_width=0,
                        hovertemplate="%{y}<br>$%{x:,.0f} per student<extra></extra>")
    chart.update_layout(**theme.plotly_layout(430))
    chart.add_vline(x=0, line_width=1, line_color=theme.NEUTRAL)
    st.plotly_chart(chart, use_container_width=True)

    st.markdown("**Read in order of size**")
    for _, row in gaps.head(5).iterrows():
        direction = "more" if row["gap_per_fte"] > 0 else "less"
        st.markdown(
            f"- **{row['function']}**: {money(row['target_per_fte'])} per "
            f"student against a peer median of "
            f"{money(row['peer_median_per_fte'])}. That is "
            f"{money(abs(row['gap_per_fte']))} {direction} per student, or "
            f"**{money(abs(row['gap_total']))}** across the institution."
        )

    display = gaps[["function", "target_per_fte", "peer_median_per_fte",
                    "gap_per_fte", "gap_total", "position"]].round(0)
    st.dataframe(
        display.rename(columns={
            "function": "Function",
            "target_per_fte": "This institution ($/student)",
            "peer_median_per_fte": "Peer median ($/student)",
            "gap_per_fte": "Gap ($/student)", "gap_total": "Gap, total ($)",
            "position": "Position",
        }),
        hide_index=True, use_container_width=True,
    )

    st.info(
        "**A gap is an observation, not a recommendation.** It says that "
        "institutions of similar sector, level and size allocate money "
        "differently. It does not establish that one allocation produces "
        "better outcomes. Research intensity, hospital operations, state "
        "funding regime and campus age all drive legitimate differences that "
        "this comparison does not control for."
    )


# --------------------------------------------------------------------------
# Reallocation planner
# --------------------------------------------------------------------------

def render_planner(unitid: int) -> None:
    st.subheader("Reallocation planner")
    st.caption(
        "Move dollars between functions and see where the institution lands "
        "relative to its peer group. The total is held to the reported figure."
    )

    frame = transform.expenses_by_function(unitid)
    if frame.empty:
        st.info("No finance data on the GASB schedule for this institution.")
        return
    year = int(frame["fiscal_year"].max())
    current = frame[frame["fiscal_year"] == year].copy()
    gaps = transform.opportunity_analysis(unitid, year)
    if gaps.empty:
        st.info("No peer comparison available, so there is nothing to plan "
                "against.")
        return

    enrolled = transform.fte(unitid)
    reported_total = float(current["total_expenses"].iloc[0])
    medians = dict(zip(gaps["function"], gaps["peer_median_per_fte"]))

    st.warning(
        "**This is arithmetic, not a forecast.** It shows the position a "
        "reallocation would create. It does not predict what that "
        "reallocation would achieve, because nothing in the source data "
        "supports such a prediction."
    )

    functions = current.sort_values("amount", ascending=False)
    planned: dict[str, float] = {}

    st.markdown(f"**Set FY{year} allocations**, in millions of dollars")
    columns = st.columns(3)
    for index, (_, row) in enumerate(functions.iterrows()):
        name = row["function"]
        actual_m = float(row["amount"]) / 1_000_000
        ceiling = max(actual_m * 2.0, actual_m + 25.0)
        with columns[index % 3]:
            planned[name] = st.slider(
                name, min_value=0.0, max_value=round(ceiling, 1),
                value=round(actual_m, 1), step=0.1,
                key=f"plan_{unitid}_{year}_{name}",
            ) * 1_000_000

    planned_total = sum(planned.values())
    difference = planned_total - reported_total

    columns = st.columns(3)
    columns[0].metric(f"Reported total, FY{year}", short(reported_total))
    columns[1].metric("Planned total", short(planned_total))
    columns[2].metric(
        "Out of balance by", short(abs(difference)),
        delta=f"{difference / reported_total:+.2%}" if reported_total else None,
        delta_color="off",
    )

    if abs(difference) > reported_total * 0.001:
        st.error(
            f"The plan is out of balance by {money(abs(difference))}. Adjust "
            "the sliders until the difference is close to zero, so the plan "
            "is a reallocation rather than a change in total spending."
        )
    else:
        st.success("The plan balances against the reported total.")

    rows = []
    for _, row in functions.iterrows():
        name = row["function"]
        actual = float(row["amount"])
        new = planned[name]
        median = medians.get(name)
        actual_pf = actual / enrolled if enrolled else None
        new_pf = new / enrolled if enrolled else None
        movement = "no peer median"
        if median is not None and actual_pf is not None and new_pf is not None:
            before, after = abs(actual_pf - median), abs(new_pf - median)
            if abs(after - before) < 1:
                movement = "unchanged"
            else:
                movement = ("toward peer median" if after < before
                            else "away from peer median")
        rows.append({
            "Function": name,
            "Current ($)": actual,
            "Planned ($)": new,
            "Change ($)": new - actual,
            "Current ($/student)": actual_pf,
            "Planned ($/student)": new_pf,
            "Peer median ($/student)": median,
            "Effect": movement,
        })

    st.dataframe(pd.DataFrame(rows).round(0), hide_index=True,
                 use_container_width=True)
    st.caption(
        '"Effect" reports only whether the planned figure sits closer to or '
        "further from the peer median than the current figure. It is a "
        "statement about distance, not about quality."
    )


# --------------------------------------------------------------------------
# Program mix
# --------------------------------------------------------------------------

def render_programs(unitid: int) -> None:
    st.subheader("What the institution produces")
    st.caption(
        "Awards conferred, IPEDS Completions survey, first majors only so a "
        "double major is counted once. The file carries detail levels only, "
        "with no aggregate rows, so summing across levels does not double "
        "count."
    )

    available = transform.award_levels_present(unitid)
    if not available:
        st.info("No completions reported for this institution.")
        return

    labels = {config.AWARD_LEVELS.get(lv, f"Level {lv}"): lv for lv in available}
    degree_labels = [n for n, lv in labels.items() if lv in config.DEGREE_LEVELS]
    chosen = st.multiselect(
        "Award levels", list(labels), default=degree_labels or list(labels),
        help="Defaults to degrees only. Add certificates to include shorter "
             "credentials, which changes the picture at many institutions.",
    )
    levels = [labels[name] for name in chosen] or available

    stats = transform.concentration(unitid, levels=levels)
    if stats:
        columns = st.columns(4)
        columns[0].metric("Awards conferred", f"{stats['total_awards']:,.0f}")
        columns[1].metric("Fields of study", f"{stats['fields']}")
        columns[2].metric("Largest field", pct(stats["top_share"]),
                          help=stats["top_field"])
        columns[3].metric("Top three fields", pct(stats["top3_share"]),
                          help="Share of all awards conferred by the three "
                               "largest fields. A high value means output is "
                               "concentrated, which is a risk if demand for "
                               "those fields falls.")
        takeaway(
            f"Its largest field is <b>{stats['top_field'].lower()}</b> at "
            f"{pct(stats['top_share'])} of awards, and the three largest "
            f"fields together account for {pct(stats['top3_share'])} across "
            f"{stats['fields']} fields in total."
        )

    frame = transform.program_families(unitid, levels=levels)
    if frame.empty:
        st.info("No awards at the selected levels.")
        return

    chart = px.bar(
        frame.sort_values("awards"), x="awards", y="field", orientation="h",
        labels={"awards": "Awards conferred", "field": ""},
        color_discrete_sequence=[theme.SUBJECT],
    )
    chart.update_traces(marker_line_width=0,
                        hovertemplate="%{y}<br>%{x:,.0f} awards<extra></extra>")
    chart.update_layout(**theme.plotly_layout(460, legend=False))
    st.plotly_chart(chart, use_container_width=True)

    st.markdown("**Drill into a field**")
    field = st.selectbox("Field of study", frame["field"].tolist())
    family = frame.loc[frame["field"] == field, "cip_family"].iloc[0]
    detail = transform.programs_in_family(unitid, family, levels=levels)
    if detail.empty:
        st.info("No programs at the selected levels in this field.")
    else:
        st.dataframe(
            detail[["cip_code", "level", "awards"]].rename(columns={
                "cip_code": "CIP code", "level": "Award level",
                "awards": "Awards conferred",
            }),
            hide_index=True, use_container_width=True, height=320,
        )
        st.caption(
            f"{len(detail)} program and award-level combinations in "
            f"{field.lower()}. CIP codes are the federal Classification of "
            "Instructional Programs, 2020 edition."
        )

    st.markdown("**Program mix against comparable institutions**")
    st.caption(
        "Share of all awards by field, this institution against the peer "
        "median share. Shares rather than counts, so institutions of "
        "different sizes are comparable. All award levels are included here."
    )
    mix = transform.program_mix_gap(unitid)
    if mix.empty:
        st.info("No peer group available for a mix comparison.")
        return

    top = mix.head(12).copy()
    top["direction"] = top["gap"].apply(
        lambda g: "More concentrated than peers" if g > 0
        else "Less concentrated than peers"
    )
    chart = px.bar(
        top.sort_values("gap"), x="gap", y="field", orientation="h",
        color="direction",
        labels={"gap": "Difference in share of awards", "field": ""},
        color_discrete_map={"More concentrated than peers": theme.ABOVE,
                            "Less concentrated than peers": theme.BELOW},
        category_orders={"direction": ["Less concentrated than peers",
                                       "More concentrated than peers"]},
    )
    chart.update_traces(marker_line_width=0,
                        hovertemplate="%{y}<br>%{x:+.1%} vs peers<extra></extra>")
    layout = theme.plotly_layout(460)
    layout["xaxis"]["tickformat"] = ".1%"
    chart.update_layout(**layout)
    chart.add_vline(x=0, line_width=1, line_color=theme.NEUTRAL)
    st.plotly_chart(chart, use_container_width=True)

    st.info(
        "Graduate earnings and median debt by CIP code are published in the "
        "College Scorecard field-of-study file. Joining that to this view is "
        "the next planned release, and it is what turns program mix into "
        "program return."
    )


# --------------------------------------------------------------------------
# Revenue
# --------------------------------------------------------------------------

def render_revenue(unitid: int) -> None:
    st.subheader("Where the money comes from")
    st.caption(
        "Revenue by statement category and source, IPEDS Finance, public "
        "institutions under GASB 34/35. Shares use the reported total, not a "
        "sum of the lines."
    )

    detail = transform.revenue_detail(unitid)
    if detail.empty:
        st.info("No revenue reported on the GASB schedule for this institution.")
        return

    years = sorted(detail["fiscal_year"].unique(), reverse=True)
    year = int(st.selectbox("Fiscal year", years,
                            format_func=lambda y: f"FY{y}",
                            key=f"rev_year_{unitid}"))
    current = detail[detail["fiscal_year"] == year]
    position = transform.revenue_position(unitid, year)
    benchmarks = transform.peer_revenue_benchmarks(unitid, year)

    columns = st.columns(4)
    columns[0].metric("Total revenue", short(position.get("total_revenue")))
    columns[1].metric("Total expenses", short(position.get("total_expenses")))
    surplus = position.get("surplus")
    margin = None
    if surplus is not None and position.get("total_revenue"):
        margin = f"{surplus / position['total_revenue']:+.1%} of revenue"
    columns[2].metric("Surplus or deficit", short(surplus), delta=margin)
    columns[3].metric("Revenue per student",
                      money(position.get("revenue_per_fte")))

    st.markdown("**Exposure**")
    st.caption(
        "The two ratios a public institution's finance office watches. "
        "Tuition dependence is exposure to an enrollment decline. State "
        "share is exposure to a state budget decision."
    )
    left, right = st.columns(2)
    for column, key, label in (
        (left, "tuition_dependence", "Tuition as a share of revenue"),
        (right, "state_share", "State appropriations as a share of revenue"),
    ):
        value, peer = position.get(key), benchmarks.get(key)
        if value is None:
            column.metric(label, "not reported")
            continue
        delta = None
        if peer is not None:
            delta = f"{(value - peer) * 100:+.1f} pts vs peer median"
        column.metric(label, pct(value), delta=delta, delta_color="off")
        if peer is not None:
            column.caption(f"Peer median: {pct(peer)}")

    st.markdown("**Composition**")
    composition = px.treemap(
        current, path=["category", "source"], values="amount",
        color="category", color_discrete_sequence=theme.CATEGORICAL,
    )
    composition.update_traces(
        marker_line_width=1, marker_line_color=theme.SURFACE,
        hovertemplate="%{label}<br>$%{value:,.0f}<extra></extra>",
    )
    composition.update_layout(**theme.plotly_layout(470, legend=False))
    st.plotly_chart(composition, use_container_width=True)

    display = current[["category", "source", "amount", "share_of_total"]].copy()
    display["share_of_total"] = (display["share_of_total"] * 100).round(1)
    st.dataframe(
        display.rename(columns={
            "category": "Category", "source": "Source",
            "amount": "Amount ($)", "share_of_total": "Share of total (%)",
        }),
        hide_index=True, use_container_width=True,
    )

    st.markdown("**State funding stress test**")
    st.caption(
        "If state appropriations were reduced, how much would tuition have to "
        "rise per student to hold total revenue constant? This is an "
        "arithmetic identity at fixed enrollment, not a forecast. It does not "
        "model whether students would enrol at the higher price."
    )
    appropriations = position.get("state_appropriations")
    enrolled = position.get("fte")
    tuition = position.get("tuition")
    if not appropriations or not enrolled or not tuition:
        st.info("This institution does not report state appropriations, so "
                "the stress test does not apply.")
    else:
        cut = st.slider("Reduction in state appropriations", 0, 50, 10, step=1,
                        format="%d%%", key=f"stress_{unitid}_{year}")
        lost = appropriations * cut / 100
        per_student = lost / enrolled
        tuition_per_student = tuition / enrolled
        increase = per_student / tuition_per_student if tuition_per_student else None

        columns = st.columns(3)
        columns[0].metric("Revenue lost", short(lost))
        columns[1].metric("Per student", money(per_student))
        columns[2].metric("Tuition increase to offset",
                          pct(increase) if increase is not None else "n/a")
        if cut:
            takeaway(
                f"A {cut}% reduction in state appropriations removes "
                f"<b>{money(lost)}</b>. Across {enrolled:,.0f} students that "
                f"is {money(per_student)} each, a "
                f"<b>{pct(increase)}</b> increase on current net tuition of "
                f"{money(tuition_per_student)} per student."
            )

    if len(years) > 1:
        recent = sorted(years, reverse=True)[:2]
        later, earlier = int(recent[0]), int(recent[1])
        st.markdown(f"**Change, FY{earlier} to FY{later}**")
        pivot = detail[detail["fiscal_year"].isin([earlier, later])].pivot_table(
            index=["category", "source"], columns="fiscal_year",
            values="amount", aggfunc="sum",
        ).reset_index()
        # Every column is renamed to a string. Leaving integer year columns in
        # place produces a frame with mixed-type column names, which Arrow
        # cannot round-trip and Streamlit warns about.
        pivot.columns = [
            c if isinstance(c, str) else f"FY{int(c)} ($)" for c in pivot.columns
        ]
        first_col, last_col = f"FY{earlier} ($)", f"FY{later} ($)"
        if first_col in pivot.columns and last_col in pivot.columns:
            pivot["Change ($)"] = pivot[last_col] - pivot[first_col]
            pivot["Change (%)"] = (
                (pivot[last_col] - pivot[first_col]) / pivot[first_col] * 100
            ).round(1)
            st.dataframe(
                pivot.rename(columns={"category": "Category",
                                      "source": "Source"})
                     .sort_values("Change ($)", ascending=False).round(0),
                hide_index=True, use_container_width=True,
            )

    st.info(
        "Revenue here is every line reported under GASB Part B, grouped as "
        "operating, nonoperating, and capital or other additions. State "
        "appropriations are nonoperating in this schedule even though they "
        "fund core operations at a public university, which is why the "
        "category split is shown rather than a single total."
    )


# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------

def render_footer() -> None:
    st.markdown(
        '<div class="pagefoot">'
        "<b>University Management Model.</b> Built by Nicolas Beltran. "
        "MIT licensed, source and methodology on GitHub.<br>"
        "Data: Integrated Postsecondary Education Data System (IPEDS), "
        "National Center for Education Statistics, U.S. Department of "
        "Education. Public domain.<br>"
        "Finance and revenue: fiscal years 2023 and 2024, GASB 34/35 "
        "schedule. Directory, enrollment and completions: 2025 collection. "
        "FY2024 is a provisional release and may be revised.<br>"
        "No figure in this application is estimated, simulated or projected. "
        "Every comparison is against an observed value."
        "</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    st.markdown(theme.CSS, unsafe_allow_html=True)
    _ready()

    unitid = sidebar_selection()
    sidebar_reference()

    summary, year = render_header(unitid)
    st.markdown("")

    tabs = st.tabs([
        "Overview", "Budget allocation", "Peer comparison", "Opportunities",
        "Reallocation planner", "Program mix", "Revenue",
    ])
    with tabs[0]:
        render_overview(unitid, summary, year)
    with tabs[1]:
        render_budget(unitid)
    with tabs[2]:
        render_peers(unitid)
    with tabs[3]:
        render_opportunities(unitid)
    with tabs[4]:
        render_planner(unitid)
    with tabs[5]:
        render_programs(unitid)
    with tabs[6]:
        render_revenue(unitid)

    render_footer()


if __name__ == "__main__":
    main()
