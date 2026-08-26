"""Metric definitions.

Every ratio the application shows is defined once, here, as a plain function
over plain numbers. Two reasons: the definitions are testable in isolation,
and a reader can check the arithmetic without reading any SQL.
"""

from __future__ import annotations

from typing import Optional

Number = Optional[float]


def _safe_div(numerator: Number, denominator: Number) -> Number:
    """Divide, returning None rather than raising on a zero or missing input."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return numerator / denominator


def per_fte(amount: Number, fte_enrollment: Number) -> Number:
    """Dollars per full-time-equivalent student.

    The standard way to compare spending across institutions of different
    sizes. A total is meaningless on its own: a large university spends more
    on instruction than a small one by definition.
    """
    return _safe_div(amount, fte_enrollment)


def share_of_total(amount: Number, total: Number) -> Number:
    """One line item as a fraction of the total. Returns a fraction, not a percent."""
    return _safe_div(amount, total)


def instruction_ratio(instruction: Number, institutional_support: Number) -> Number:
    """Instruction spending relative to institutional support.

    Institutional support is the IPEDS term for administration: executive
    management, legal, fiscal operations, public relations. The ratio is a
    rough read on how much of an institution's spending reaches teaching
    versus running the institution. Higher favours instruction.

    This is a comparison, not a judgement. Institutions with hospitals,
    heavy research portfolios, or large auxiliary operations allocate
    differently for legitimate reasons.
    """
    return _safe_div(instruction, institutional_support)


def year_over_year_change(current: Number, prior: Number) -> Number:
    """Fractional change from prior to current. Returns a fraction, not a percent."""
    if current is None or prior is None or prior == 0:
        return None
    return (current - prior) / prior


def program_concentration(top_program_awards: Number, total_awards: Number) -> Number:
    """Share of all awards conferred by the single largest program.

    A high value means the institution's output is concentrated in one field,
    which is a risk if demand for that field falls.
    """
    return _safe_div(top_program_awards, total_awards)
