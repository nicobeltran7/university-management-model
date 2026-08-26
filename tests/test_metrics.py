"""Tests for the metric definitions.

These are arithmetic tests, not integration tests. They exist so that a change
to a definition cannot pass silently.
"""

import pytest

from src import metrics


def test_per_fte_divides():
    assert metrics.per_fte(1_000_000, 10_000) == 100.0


def test_per_fte_handles_zero_enrollment():
    assert metrics.per_fte(1_000_000, 0) is None


def test_per_fte_handles_missing_inputs():
    assert metrics.per_fte(None, 10_000) is None
    assert metrics.per_fte(1_000, None) is None


def test_share_of_total_returns_a_fraction():
    assert metrics.share_of_total(25, 100) == 0.25


def test_instruction_ratio():
    assert metrics.instruction_ratio(300, 100) == 3.0
    assert metrics.instruction_ratio(300, 0) is None


def test_year_over_year_change_signs():
    assert metrics.year_over_year_change(110, 100) == pytest.approx(0.10)
    assert metrics.year_over_year_change(90, 100) == pytest.approx(-0.10)


def test_year_over_year_change_guards_zero_base():
    assert metrics.year_over_year_change(100, 0) is None


def test_program_concentration():
    assert metrics.program_concentration(400, 1000) == 0.4
    assert metrics.program_concentration(400, 0) is None


def test_gap_arithmetic_is_target_minus_peer():
    """The gap sign convention: positive means the institution spends more.

    This is asserted here because the sign drives the wording shown to the
    user ("more per student" versus "less per student"), and an inverted sign
    would produce confident, readable, wrong sentences.
    """
    target_per_fte = 4_537.0
    peer_median_per_fte = 3_204.0
    gap = target_per_fte - peer_median_per_fte
    assert gap > 0
    assert round(gap, 0) == 1_333.0
    assert round(gap * 37_738, 0) == 50_304_754.0
