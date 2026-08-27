"""Tests for the shareable-link slugs, year-matched enrollment, the position
trend, and the one-page brief."""

import pytest

from src import brief, config, transform

UHD = 225432


@pytest.fixture(autouse=True)
def reset_peer_state():
    transform.set_peer_institutions(None)
    transform.set_peer_group(None)
    yield
    transform.set_peer_institutions(None)
    transform.set_peer_group(None)


def test_peer_preset_slugs_round_trip():
    # A slug in a shared URL must resolve to a real preset, and back.
    for slug, name in config.PEER_PRESET_SLUGS.items():
        assert name in config.PEER_PRESETS
        assert config.PEER_PRESET_TO_SLUG[name] == slug


def test_enrollment_year_files_cover_the_finance_years():
    # Every finance fiscal year needs a matching enrollment file to divide by.
    assert set(config.ENROLLMENT_YEAR_FILES) == set(config.FINANCE_FILES)


def test_fte_for_year_always_returns_a_denominator():
    year = transform.latest_fiscal_year()
    value = transform.fte_for_year(UHD, year)
    assert value is not None and value > 0
    if not transform.enrollment_years_available():
        # Without the per-year extract, the snapshot serves every year.
        assert value == transform.fte(UHD)


def test_position_trend_reports_a_gap_per_function_and_year():
    frame = transform.position_trend(UHD)
    assert not frame.empty
    assert {"fiscal_year", "function", "gap_per_fte",
            "target_per_fte", "peer_median_per_fte"} <= set(frame.columns)
    # The gap must be the stated arithmetic, not something scored.
    row = frame.iloc[0]
    assert row["gap_per_fte"] == pytest.approx(
        row["target_per_fte"] - row["peer_median_per_fte"]
    )


def test_brief_is_a_self_contained_page():
    page = brief.one_page_brief(UHD)
    assert page.lstrip().startswith("<!doctype html>")
    assert "University of Houston-Downtown" in page
    assert "peer median" in page
    # The hard line: observations, never recommendations.
    assert "not a\nrecommendation" in page or "not a recommendation" in page
    # House style: no em dashes anywhere a reader sees.
    assert "—" not in page


def test_brief_names_the_peer_basis_in_force():
    transform.set_peer_group("THECB Master's Universities (Texas)")
    page = brief.one_page_brief(UHD)
    assert "THECB Master" in page
