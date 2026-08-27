# Limitations

Stated plainly, because a tool that names what it cannot do is more useful than
one that implies it can do everything.

## Coverage

- **Public institutions only.** This release reads the GASB 34/35 finance
  schedule (`_f1a`). Private nonprofit and for-profit institutions report on
  different schedules with different line items, and combining them without a
  documented crosswalk would produce comparisons that are wrong.
- **Five fiscal years.** 2020 through 2024. Enough to show a trend through the
  pandemic period and out of it, though still short of a full economic cycle.
  Earlier years are a download away and the ingest handles them without code
  changes.
- **Fiscal 2024 is provisional.** It may be revised by NCES. Charts label the
  fiscal year so the reader knows which release they are seeing.
- **Per-student denominators depend on which enrollment files are loaded.**
  With the per-year DRVEF12 files ingested, each fiscal year divides by its
  own enrollment. Without them, every year divides by the latest snapshot, a
  five-year per-student trend is really a spending trend at fixed enrollment,
  and historical per-student levels are distorted wherever enrollment moved
  materially. The application discloses which case is in force, and hides the
  position-over-time panel in the snapshot case rather than showing a trend
  that is not one.

## What the data cannot answer

- **Operations and maintenance is not a separate function** in the GASB
  schedule. It is allocated across the other functions, so it cannot be
  isolated the way it can in the FASB schedule.
- **Revenue is now complete for the GASB schedule.** All operating,
  nonoperating and capital or other addition lines in Part B are loaded, and
  shares use the reported total rather than a sum of the lines.
- **Most programs have no published earnings figure.** The Scorecard
  suppresses any value drawn from a cohort too small to publish without
  risking identification. Roughly four in five program-and-credential rows
  nationally carry no earnings figure, so the Program returns view shows an
  institution's larger programs, not all of them.
- **Earnings are measured from entry, not from graduation,** five years after
  a student enters the programme, and cover only graduates who received
  federal aid and were working and not enrolled. They are not a placement
  rate and they are not a salary survey.
- **Debt is federal loan debt only.** Private loans, parental borrowing and
  credit are not in the figure.
- **The stress test is arithmetic, not behavioural.** It answers how much
  tuition per student would have to rise to replace lost state funding at
  fixed enrollment. It cannot say whether students would enrol at that price,
  because that requires a demand elasticity IPEDS does not contain.
- **Program mix says nothing about program quality or return.** It reports how
  many awards were conferred in each field. Earnings and debt by field are in
  the Program returns view, from the College Scorecard, where published.
- **No student-level anything.** IPEDS is institution-level aggregate data.
  Nothing here can say anything about an individual student.
- **Reporting is self-reported.** Institutions file their own figures.
  Definitions are standardised, compliance is generally good, and errors exist.

## What the analysis cannot claim

- **Correlation is not causation.** An institution spending more per FTE on
  student services and also retaining more students does not establish that
  the spending caused the retention.
- **Peer groups are approximations.** See the peer set section in
  `methodology.md` for what the rule ignores.
- **Comparisons across sectors are not made** and should not be inferred.

## Next

In rough order of value:

1. Load per-year enrollment so per-student figures use the matching year.
2. Load more fiscal years of Finance to turn direction into trend.
3. Add the FASB schedule with a documented crosswalk, extending coverage to
   private nonprofit institutions.
