"""Presentation layer: palette, typography and small formatting helpers.

The palette is separated from the application so it can be validated
independently and reused. Every colour here was checked against the light
surface (#fcfcfb) for lightness band, chroma floor, colour-vision-deficiency
separation and contrast before use. See docs/design.md.
"""

from __future__ import annotations

# Categorical hues, assigned in fixed order and never cycled.
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]

# Emphasis pair: the subject in the accent hue, context in de-emphasis grey.
# Used where one series is the point and the other is background, such as an
# institution against its peer median.
SUBJECT = "#2a78d6"
CONTEXT = "#b9b8b2"

# Diverging pair for above/below a baseline, with a neutral midpoint.
ABOVE = "#eb6834"
BELOW = "#2a78d6"
NEUTRAL = "#8e8e93"

# One hue at two steps, for a before-and-after comparison of the same measure.
TIME_RECENT = "#2a78d6"
TIME_PRIOR = "#a8c8ee"

# Sequential ramp, one hue, light to dark. For magnitude across a grid, where
# the categorical checks do not apply but lightness monotonicity does.
SEQUENTIAL = ["#eef4fb", "#cfe0f5", "#a8c8ee", "#6fa4e2", "#2a78d6", "#1c5aa3"]

INK = "#12151a"
INK_MUTED = "#5c6270"
SURFACE = "#fcfcfb"
GRID = "#e4e3dd"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"], .stMarkdown, .stMetric {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}

/* Page title and section headings carry the serif; body text stays sans. */
h1 { font-family: 'Source Serif 4', Georgia, serif !important;
     font-weight: 600 !important; letter-spacing: -0.015em;
     font-size: 2.35rem !important; line-height: 1.15; margin-bottom: 0.15rem; }
h2 { font-family: 'Source Serif 4', Georgia, serif !important;
     font-weight: 600 !important; font-size: 1.5rem !important;
     letter-spacing: -0.01em; margin-top: 0.4rem; }
h3 { font-weight: 600 !important; font-size: 1.05rem !important; }

.block-container { padding-top: 2.4rem; max-width: 1400px; }

/* Metric cards. The default renders as floating text with no boundary, which
   reads as debug output rather than as a figure worth attention. */
div[data-testid="stMetric"] {
  background: #ffffff;
  border: 1px solid #e4e3dd;
  border-radius: 10px;
  padding: 14px 16px 12px 16px;
}
div[data-testid="stMetricLabel"] p {
  font-size: 0.78rem !important; font-weight: 500 !important;
  color: #5c6270 !important; letter-spacing: 0.01em;
}
div[data-testid="stMetricValue"] {
  font-size: 1.65rem !important; font-weight: 600 !important;
  letter-spacing: -0.02em; color: #12151a;
}
div[data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

/* Header stat tiles. The left border carries position against the peer
   median: warm above, cool below, grey when no comparison exists. The hue
   says above or below and nothing more. */
.stat-tile {
  background: #ffffff;
  border: 1px solid #e4e3dd;
  border-left-width: 4px;
  border-radius: 10px;
  padding: 14px 16px 12px 16px;
  height: 100%;
}
.stat-tile .label {
  font-size: 0.78rem; font-weight: 500; color: #5c6270;
  letter-spacing: 0.01em; margin-bottom: 2px;
}
.stat-tile .value {
  font-size: 1.65rem; font-weight: 600; letter-spacing: -0.02em;
  color: #12151a; line-height: 1.2;
}
.stat-tile .versus {
  font-size: 0.74rem; font-weight: 500; margin-top: 3px;
}

/* Tabs: give them weight so they read as navigation. */
button[data-baseweb="tab"] {
  font-size: 0.95rem !important; font-weight: 500 !important;
  padding-left: 14px !important; padding-right: 14px !important;
}
div[data-baseweb="tab-border"] { background-color: #e4e3dd; }

/* Captions do real work in this app, so they need to be readable. */
div[data-testid="stCaptionContainer"] p {
  font-size: 0.84rem !important; color: #5c6270 !important; line-height: 1.5;
}

/* The takeaway line under a chart: the sentence a reader should leave with. */
.takeaway {
  border-left: 3px solid #2a78d6;
  background: #f4f7fc;
  padding: 11px 15px;
  border-radius: 0 8px 8px 0;
  font-size: 0.93rem;
  line-height: 1.55;
  color: #12151a;
  margin: 2px 0 18px 0;
}

.eyebrow {
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.09em;
  text-transform: uppercase; color: #2a78d6; margin-bottom: 2px;
  /* Without an explicit line-height the container computes a height smaller
     than the glyphs and clips them at the bottom. */
  line-height: 1.6; padding-bottom: 2px; overflow: visible;
}
/* Streamlit can clip custom HTML blocks to their computed height. */
div[data-testid="stMarkdownContainer"] { overflow: visible; }

.subtitle { color: #5c6270; font-size: 0.95rem; margin-bottom: 0.2rem; }

.pagefoot {
  border-top: 1px solid #e4e3dd; margin-top: 2.6rem; padding-top: 1rem;
  color: #5c6270; font-size: 0.8rem; line-height: 1.7;
}

section[data-testid="stSidebar"] { background: #f4f4f1; }
section[data-testid="stSidebar"] h2 { font-size: 1.15rem !important; }
</style>
"""


def compact_money(value: float | None) -> str:
    """Headline dollar figures, shortened. Tables keep the exact number.

    A hero figure exists to be read at a glance. "$1.61B" is read instantly;
    "$1,609,356,036" has to be counted.
    """
    if value is None:
        return "not reported"
    magnitude = abs(value)
    if magnitude >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"
    if magnitude >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    if magnitude >= 1_000:
        return f"${value / 1_000:,.0f}K"
    return f"${value:,.0f}"


def exact_money(value: float | None) -> str:
    """Full precision, for tables and for any figure a reader may check."""
    if value is None:
        return "not reported"
    return f"${value:,.0f}"


def plotly_layout(height: int = 420, legend: bool = True) -> dict:
    """Shared layout: recessive grid and axes, ink-coloured text, no chartjunk."""
    return dict(
        height=height,
        # A legend drawn above the plot needs headroom in the top margin, or
        # it overlaps the first bar. 8px was enough only for legendless charts.
        margin=dict(l=0, r=10, t=44 if legend else 8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=INK),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    title_text="") if legend else dict(),
        showlegend=legend,
        hoverlabel=dict(font_size=12, font_family="Inter, sans-serif"),
    )
