"""Tests on the variable map.

The IPEDS variable codes are the one place where a silent typo would produce
a chart that is wrong but looks fine. These assertions pin them.
"""

from src import config


def test_expense_functions_are_current_year_totals():
    # Every expense code in the map must end in '1', the current-year total
    # suffix in the IPEDS Part C schedule. A code ending in '2' is salaries
    # and wages only, which would understate the function.
    for code in config.EXPENSE_FUNCTIONS:
        assert code.startswith("F1C")
        assert code.endswith("1"), f"{code} is not a current-year total"


def test_expense_total_is_not_in_the_function_map():
    # Including the total alongside the functions would double count.
    assert config.EXPENSE_TOTAL not in config.EXPENSE_FUNCTIONS


def test_instruction_is_present():
    assert config.EXPENSE_FUNCTIONS["F1C011"] == "Instruction"


def test_focus_institutions_are_the_two_named_in_the_endeavor():
    assert set(config.FOCUS_UNITIDS) == {201885, 225432}


def test_finance_files_are_gasb_public_files():
    for filename in config.FINANCE_FILES.values():
        assert "_f1a" in filename.lower()
