# Design

Colour is the part of a chart that is usually chosen by taste and is actually
computable. So it was computed.

## The palette was validated, not eyeballed

Every colour in `src/theme.py` was checked against the light surface
(`#fcfcfb`) on five measures: lightness band, chroma floor, colour-vision-
deficiency separation between adjacent pairs, a normal-vision separation floor,
and contrast against the surface.

The categorical set `#2a78d6 · #eb6834 · #1baf7a · #eda100 · #e87ba4` passes
all five. Worst adjacent CVD separation is ΔE 9.1 under protanopia between the
amber and the green, above the ΔE 8 target. The three lower-chroma hues carry a
contrast warning against the surface, which obligates visible labels or a table
view; every chart that uses them has both.

## The form is chosen before the colour

Each chart's type follows from what the reader has to do with it, and the colour
job follows from the form. This is why the charts do not all look the same:

| View | Reader's job | Form | Colour job |
|---|---|---|---|
| Budget allocation | Compare magnitude | Horizontal bar, single series | One hue, no legend |
| Year over year | Before and after, same measure | Grouped bar | One hue at two steps |
| Peer comparison | This institution against context | Grouped bar, **emphasis** | Accent hue plus de-emphasis grey |
| Opportunities | Above or below a baseline | Diverging bar, zero line | Two hues, neutral midpoint |
| Program mix vs peers | Above or below a baseline | Diverging bar, zero line | Two hues, neutral midpoint |
| Revenue composition | Part to whole, many parts | Treemap | Categorical by statement category |

The peer comparison is the one worth explaining. It is not a categorical chart.
The institution is the subject and the peer median is background, so it uses
emphasis: the accent hue for the institution, grey for the peers. Giving the
peer median its own bright hue would make two things compete that are not equal
in importance.

## Light mode only, on purpose

The app pins a light theme in `.streamlit/config.toml`. Dark mode is not a
colour inversion: the palette would need re-stepping and re-validating against
a dark surface. Rather than ship a dark mode whose contrast has not been
checked, the app does not offer one.

## Numbers are formatted for the job

Headline figures are shortened (`$1.61B`) because a hero number exists to be
read at a glance. Tables keep full precision (`$1,609,356,036`) because a
figure a reader may want to check has to be exactly there. Both live in
`theme.compact_money` and `theme.exact_money` so the rule is applied once.

## The takeaway line

Under the charts that carry a finding there is a single sentence stating what
the chart shows, in words, with the numbers in it. A chart that requires the
reader to construct the sentence themselves has not finished its job. The
Overview tab is built entirely from these.

## Typography

Source Serif 4 for headings, Inter for everything else. Serif headings give the
page a document quality rather than a dashboard quality, which suits a tool
whose output is meant to be read and cited. Metric cards get a border and a
white surface, because Streamlit's default renders a headline figure as
floating text that reads more like debug output than like a number worth
attention.
