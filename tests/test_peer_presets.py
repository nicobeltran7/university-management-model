"""The statutory peer group. A named group is only useful if it is exactly the
list the state publishes, so these tests assert membership rather than shape.
"""

import pytest

from src import config, transform

GROUP = "THECB Master's Universities (Texas)"
UHD = 225432
UC = 201885


@pytest.fixture(autouse=True)
def reset_group():
    yield
    transform.set_peer_group(None)


def test_group_is_declared():
    assert GROUP in config.PEER_PRESETS
    assert len(config.PEER_PRESETS[GROUP]) == 10
    assert UHD in config.PEER_PRESETS[GROUP]


def test_unknown_group_is_refused():
    with pytest.raises(ValueError):
        transform.set_peer_group("Not a real group")


def test_default_is_the_derived_rule():
    assert transform.peer_group() is None
    assert not transform.peer_group_applies(UHD)


def test_group_applies_only_to_its_members():
    transform.set_peer_group(GROUP)
    assert transform.peer_group_applies(UHD)
    assert not transform.peer_group_applies(UC)


def test_peer_set_returns_the_group_without_the_target():
    transform.set_peer_group(GROUP)
    peers = transform.peer_set(UHD)
    ids = set(int(x) for x in peers["unitid"])
    assert UHD not in ids
    assert ids == set(config.PEER_PRESETS[GROUP]) - {UHD}
    assert transform.peer_count(UHD) == 9


def test_non_member_falls_back_to_the_derived_rule():
    transform.set_peer_group(GROUP)
    peers = transform.peer_set(UC)
    ids = set(int(x) for x in peers["unitid"])
    assert ids != set(config.PEER_PRESETS[GROUP]) - {UC}
    assert len(peers) > 0


def test_peer_comparison_uses_the_group():
    transform.set_peer_group(GROUP)
    frame = transform.peer_comparison(UHD, 2024)
    assert not frame.empty


def test_basis_is_reported_honestly():
    transform.set_peer_group(GROUP)
    assert transform.peer_group_basis(UHD) == GROUP
    assert "Derived" in transform.peer_group_basis(UC)


# ---------------------------------------------------------------------------
# Explicit peer selection
# ---------------------------------------------------------------------------

TAMU_SAN_ANTONIO = 459949
UNT_DALLAS = 484905


@pytest.fixture(autouse=True)
def reset_chosen():
    yield
    transform.set_peer_institutions(None)


def test_chosen_institutions_become_the_peer_set():
    transform.set_peer_institutions([TAMU_SAN_ANTONIO, UNT_DALLAS])
    peers = transform.peer_set(UHD)
    assert set(int(x) for x in peers["unitid"]) == {TAMU_SAN_ANTONIO, UNT_DALLAS}
    assert transform.peer_count(UHD) == 2


def test_choosing_institutions_clears_a_named_group():
    transform.set_peer_group(GROUP)
    transform.set_peer_institutions([UNT_DALLAS])
    assert transform.peer_group() is None
    assert not transform.peer_group_applies(UHD)


def test_choosing_a_named_group_clears_chosen_institutions():
    transform.set_peer_institutions([UNT_DALLAS])
    transform.set_peer_group(GROUP)
    assert transform.peer_institutions() is None
    assert transform.peer_count(UHD) == 9


def test_the_target_cannot_be_its_own_peer():
    transform.set_peer_institutions([UHD, UNT_DALLAS])
    peers = transform.peer_set(UHD)
    assert set(int(x) for x in peers["unitid"]) == {UNT_DALLAS}


def test_empty_selection_falls_back_to_the_derived_rule():
    transform.set_peer_institutions([])
    assert transform.peer_institutions() is None
    assert "Derived" in transform.peer_group_basis(UHD)


def test_basis_names_the_chosen_count():
    transform.set_peer_institutions([TAMU_SAN_ANTONIO, UNT_DALLAS])
    assert transform.peer_group_basis(UHD) == "Selected institutions (2)"


# ---------------------------------------------------------------------------
# The institution picker must not offer choices that produce nothing
# ---------------------------------------------------------------------------

def test_finance_only_is_a_strict_subset():
    everything = transform.institution_list()
    filed = transform.institution_list(finance_only=True)
    assert 0 < len(filed) < len(everything)
    assert set(filed["unitid"]).issubset(set(everything["unitid"]))


def test_every_offered_institution_has_finance_data():
    filed = transform.institution_list(finance_only=True)
    sample = [int(u) for u in filed["unitid"].head(25)]
    for unitid in sample:
        assert not transform.expenses_by_function(unitid).empty


def test_both_endeavor_sites_survive_the_filter():
    filed = set(int(u) for u in transform.institution_list(finance_only=True)["unitid"])
    for unitid in config.FOCUS_UNITIDS:
        assert unitid in filed


def test_sectors_present_is_labelled_and_counted():
    frame = transform.sectors_present(finance_only=True)
    assert not frame.empty
    assert {"sector", "institutions", "label"}.issubset(frame.columns)
    public_four_year = frame[frame["sector"] == 1]
    assert not public_four_year.empty
    assert public_four_year.iloc[0]["label"] == "Public, 4-year or above"


# ---------------------------------------------------------------------------
# "Current data" means current, and an administrative unit is not a school
# ---------------------------------------------------------------------------

def test_every_offered_institution_filed_in_the_latest_year():
    latest = transform.latest_fiscal_year()
    offered = [int(u) for u in transform.institution_list(finance_only=True)["unitid"]]
    assert offered
    con = transform.connect()
    placeholders = ", ".join("?" for _ in offered)
    missing = con.execute(
        f"""SELECT count(*) FROM (SELECT unnest([{placeholders}]) AS u)
            WHERE u NOT IN (SELECT UNITID FROM finance
                            WHERE fiscal_year = ? AND section = 'expense')""",
        offered + [latest],
    ).fetchone()[0]
    assert missing == 0


def test_administrative_units_are_not_offered():
    offered = transform.institution_list(finance_only=True)
    assert (offered["sector"] != 0).all()
    assert 0 not in set(transform.sectors_present(finance_only=True)["sector"])


def test_sector_counts_match_what_selecting_them_yields():
    for row in transform.sectors_present(finance_only=True).itertuples():
        listed = transform.institution_list(
            sector=int(row.sector), finance_only=True
        )
        assert len(listed) == int(row.institutions)


def test_latest_fiscal_year_is_the_maximum_loaded():
    con = transform.connect()
    expected = con.execute("SELECT max(fiscal_year) FROM finance").fetchone()[0]
    assert transform.latest_fiscal_year() == int(expected)


# ---------------------------------------------------------------------------
# Header medians
# ---------------------------------------------------------------------------

def test_headline_medians_cover_the_four_header_figures():
    year = transform.latest_fiscal_year()
    medians = transform.headline_medians(UHD, year)
    assert {"fte", "headcount", "expenses", "revenue"} <= set(medians)
    for key in ("fte", "headcount", "expenses", "revenue"):
        assert medians[key] is None or medians[key] > 0


def test_headline_medians_follow_the_peer_basis():
    year = transform.latest_fiscal_year()
    transform.set_peer_group(GROUP)
    statutory = transform.headline_medians(UHD, year)
    transform.set_peer_group(None)
    derived = transform.headline_medians(UHD, year)
    assert statutory and derived
    assert statutory != derived


def test_headline_medians_include_enrollment_intensity():
    year = transform.latest_fiscal_year()
    medians = transform.headline_medians(UHD, year)
    assert "intensity" in medians
    assert medians["intensity"] is None or 0 < medians["intensity"] <= 1.5


def test_revenue_benchmarks_cover_gifts_and_auxiliary():
    year = transform.latest_fiscal_year()
    marks = transform.peer_revenue_benchmarks(UHD, year)
    assert {"gifts_per_fte", "auxiliary_share"} <= set(marks)
    pos = transform.revenue_position(UHD, year)
    assert "gifts_per_fte" in pos and "auxiliary_share" in pos
