# Limitations

Stated plainly, because a tool that names what it cannot do is more useful than
one that implies it can do everything.

## Coverage

- **Public institutions only.** This release reads the GASB 34/35 finance
  schedule (`_f1a`). Private nonprofit and for-profit institutions report on
  different schedules with different line items, and combining them without a
  documented crosswalk would produce comparisons that are wrong.
- **Two fiscal years.** 2023 and 2024. Enough to show direction, not enough to
  establish a trend. More years are a download away and the ingest handles them
  without code changes.
- **Fiscal 2024 is provisional.** It may be revised by NCES. Charts label the
  fiscal year so the reader knows which release they are seeing.

## What the data cannot answer

- **Operations and maintenance is not a separate function** in the GASB
  schedule. It is allocated across the other functions, so it cannot be
  isolated the way it can in the FASB schedule.
- **Revenue is now complete for the GASB schedule.** All operating,
  nonoperating and capital or other addition lines in Part B are loaded, and
  shares use the reported total rather than a sum of the lines.
- **No earnings or debt outcomes yet.** Graduate earnings by field of study
  live in the College Scorecard, not IPEDS. Until that join is built, the
  program mix view shows what an institution produces but not what those
  graduates go on to earn.
- **The stress test is arithmetic, not behavioural.** It answers how much
  tuition per student would have to rise to replace lost state funding at
  fixed enrollment. It cannot say whether students would enrol at that price,
  because that requires a demand elasticity IPEDS does not contain.
- **Program mix says nothing about program quality or return.** It reports how
  many awards were conferred in each field. Earnings and debt by field live in
  the College Scorecard and are not yet joined.
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

1. Join College Scorecard field-of-study earnings and debt to the program mix,
   by CIP code, so program output can be read against program outcome.
2. Load more fiscal years of Finance to turn direction into trend.
3. Add the FASB schedule with a documented crosswalk, extending coverage to
   private nonprofit institutions.
4. Add a scenario model, with every assumption exposed as an input and its
   sensitivity shown.
