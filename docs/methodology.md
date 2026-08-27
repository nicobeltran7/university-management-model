# Methodology

## Principles

1. **No invented numbers.** Every figure displayed is read from a federal
   source file. Where the application derives a value, the derivation is
   defined in `src/metrics.py` as a single function and tested in
   `tests/test_metrics.py`.
2. **Transformation in the data engine.** All aggregation happens in SQL
   against DuckDB. The Streamlit layer selects and draws; it does not compute.
3. **Simple rules over clever ones.** A peer definition a reader can verify is
   worth more than one that is statistically elegant and opaque.
4. **Missing is missing.** A null is displayed as "not reported", never as
   zero. Dividing by a zero or missing denominator returns null rather than
   raising or silently producing a large number.

## Metric definitions

### Expenses per full-time-equivalent student

```
expenses_per_fte = functional_expense_total / FTE12MN
```

`FTE12MN` is the IPEDS derived 12-month full-time-equivalent enrollment. Totals
alone are not comparable across institutions: a large university spends more on
instruction than a small one by definition. Per-FTE puts institutions of
different sizes on the same axis.

### Share of total expenses

```
share = functional_expense / F1C191
```

`F1C191` is the reported total, not a sum of the functional lines. Using the
reported total means the shares reflect what the institution actually filed,
including any functions not carried in this release.

### Year-over-year change

```
change = (current - prior) / prior
```

Returns a fraction. Null if either year is missing or the prior year is zero.

Five fiscal years are currently loaded, 2020 through 2024. Note that 2024 is
a provisional release and may be revised. The application labels the year on
every chart so a reader always knows which release they are looking at.

### Peer set

Three bases are available, and the one in force is always stated on screen.

**Derived (the default).** An institution is a peer if it has:

- the same IPEDS `SECTOR`, and
- the same IPEDS `ICLEVEL`, and
- 12-month FTE enrollment within plus or minus 50 percent of the target's.

Peers are ordered by absolute enrollment distance from the target. The
tolerance is a parameter, not a constant, and is exposed in
`transform.peer_set`.

This rule is deliberately crude. It does not account for research intensity,
urbanicity, whether the institution operates a hospital, or state funding
regime, all of which legitimately drive spending differences. It is a starting
comparison, not a verdict, and the application says so on the page.

**Statutory.** A peer group defined by a state agency rather than by this
tool. The one implemented is the Texas Higher Education Coordinating Board's
Master's Universities group (*Institutional Peer Groups, Public Universities
FY 2026*), which applies to its ten member institutions and to nothing else:
selecting it for a non-member falls back to the derived rule, with a notice.
The value of a statutory group is precisely that the author did not choose
it. The membership list, and two documented reconciliations between the THECB
list and the IPEDS directory, live in `src/config.py`.

**Chosen.** The reader selects up to eight institutions by name and every
comparison runs against exactly those. Below three selections the application
warns that a median across so few institutions is not a distribution and
should be read as individual comparisons.

In every mode, functions the target institution does not report are excluded
from the comparison, and the header tiles colour position against the peer
median of whichever basis is in force.

### Enrollment intensity

FTE divided by unduplicated 12-month headcount. Near 100% means a mostly
full-time student body; lower means more part-time students. It is reported in
the header, with position against the peer median, because it is the single
strongest reason per-student spending comparisons need care: two institutions
with the same headcount can differ by a third or more in the full-time
equivalents that per-FTE figures divide by. This is the first step of planned
enrollment-composition coverage; student demographics by race, gender and age
live in the IPEDS EFFY survey, which is not yet ingested.

### Revenue exposure ratios

```
tuition_dependence = F1B01 / F1B25
state_share        = F1B11 / F1B25
```

`F1B25` is total all revenues and other additions, taken as reported rather
than summed. These two ratios are what a public institution's finance office
watches: tuition dependence is exposure to an enrollment decline, state share
is exposure to a state budget decision. Both are compared against the peer
median.

Note that state appropriations sit in the *nonoperating* section of the GASB
schedule even though they fund core operations at a public university. That is
why revenue is shown split by statement category rather than as a single total.

### The state funding stress test

```
revenue_lost         = state_appropriations * cut
per_student          = revenue_lost / FTE12MN
tuition_increase_pct = per_student / (tuition / FTE12MN)
```

This is an arithmetic identity at fixed enrollment, not a forecast. It answers
"how much would net tuition per student have to rise to replace this money",
and nothing more. It does not model whether students would still enrol at the
higher price, because estimating that requires a demand elasticity that IPEDS
does not contain.

### Program mix

Awards conferred, aggregated to the 2-digit CIP family. Two filters matter:

- `MAJORNUM = 1` keeps first majors only, so a student with a double major is
  counted once rather than twice.
- `CIPCODE` values of `99` are excluded. That code is the institution-wide
  total in the IPEDS Completions file, and including it would double the count.

### Program mix against peers

Share of awards by CIP family, this institution against the peer median share.

```
gap = target_share - peer_median_share
```

Shares rather than counts, so a large institution and a small one are
comparable. A positive gap means the institution is more concentrated in that
field than the median comparable institution. All award levels are included in
this comparison, because restricting it would change the denominator for the
target and the peers inconsistently.

### Concentration

```
top_share  = largest field awards / total awards
top3_share = three largest fields / total awards
hhi        = sum of squared field shares
```

The Herfindahl index is reported because it captures concentration across the
whole distribution rather than just the top of it. A high value means output is
concentrated, which is a risk if demand for those fields falls. It is not a
judgement: a specialist institution is concentrated by design.

### Instruction to institutional support ratio

```
ratio = F1C011 / F1C071
```

Institutional support is the IPEDS term for administration: executive
management, legal, fiscal operations, public relations. The ratio is a rough
read on how much spending reaches teaching relative to running the institution.

It is a comparison, not a judgement. Institutions with hospitals, heavy
research portfolios or large auxiliary operations allocate differently for
sound reasons, and a low ratio is not evidence of waste.

### Gap against the peer median

```
gap_per_fte  = target_per_fte - peer_median_per_fte
gap_total    = gap_per_fte * FTE12MN
```

A positive gap means the institution spends more per student than the median
comparable institution. The sign convention drives the wording shown to the
user, so `tests/test_metrics.py` asserts it.

Functions the target does not report are excluded from the comparison. Hospital
services is the reason: only a minority of institutions operate a hospital, so
a median taken across those that do is very large, and comparing an
institution without one against it is meaningless.

### The reallocation planner

The planner does exactly three things:

1. Takes the reported total expenses for the selected fiscal year as a fixed
   constraint.
2. Lets the user set a planned figure for each function, and reports whether
   the plan balances against that total.
3. States, for each function, whether the planned figure sits closer to or
   further from the peer median than the current figure.

That third output is a statement about distance, nothing more. The planner
contains no behavioural model, no elasticity, no yield curve and no predicted
outcome, because nothing in IPEDS supports estimating one. A planner that
claimed "moving three million dollars from institutional support to instruction
raises retention by two points" would be inventing the relationship.

This is the central design constraint of the whole project: **show the position
a decision creates, never predict the outcome it produces.**

## What is not modelled

This release contains no forecast, no projection and no scenario model. An
earlier prototype of this project included a tuition-discount scenario built on
an assumed enrollment-yield curve. That curve was an assumption presented as a
model, so it has been removed rather than carried forward. If a scenario model
returns, its assumptions will be exposed as inputs on the page and its
sensitivity to each one will be shown.
