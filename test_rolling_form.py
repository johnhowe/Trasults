"""Unit tests for rolling_form."""

import pytest

import rolling_form as rf


def test_best_n_of_last_k_below_threshold_emits_none():
    out = rf.best_n_of_last_k([10.0, 8.0], [False, False], n=3, k=10)
    assert out == [None, None]


def test_best_n_of_last_k_first_eligible_index():
    out = rf.best_n_of_last_k([10.0, 8.0, 12.0], [False, False, False], n=3, k=10)
    assert out[0] is None and out[1] is None
    assert out[2] == pytest.approx(10.0)


def test_best_n_of_last_k_skips_crashes_in_pool():
    # Window draws from completed routines only.
    totals = [10.0, 8.0, 0.0, 12.0]
    crashes = [False, False, True, False]
    out = rf.best_n_of_last_k(totals, crashes, n=3, k=10)
    # at i=2 only 2 completed -> None
    assert out[2] is None
    # at i=3 completed = [10, 8, 12] -> best 3 = mean = 10.0
    assert out[3] == pytest.approx(10.0)


def test_best_n_of_last_k_sliding_window():
    # k=10 over 12 completed routines: window at i=11 is the last 10
    totals = [5.0] * 10 + [100.0, 100.0]
    crashes = [False] * 12
    out = rf.best_n_of_last_k(totals, crashes, n=3, k=10)
    # at i=11 last 10 completed: 8x5 + 2x100 -> best 3 = (100+100+5)/3
    assert out[11] == pytest.approx((100 + 100 + 5) / 3)
    # at i=9 last 10 completed: 10x5 -> best 3 = 5
    assert out[9] == pytest.approx(5.0)


def test_crash_rate_last_k_partial_then_full_window():
    crashes = [False, False, True, False, False]
    out = rf.crash_rate_last_k(crashes, k=10)
    assert out[0] == pytest.approx(0.0)
    assert out[1] == pytest.approx(0.0)
    assert out[2] == pytest.approx(1 / 3)
    assert out[3] == pytest.approx(0.25)
    assert out[4] == pytest.approx(0.2)


def test_crash_rate_last_k_sliding_window_drops_old_crashes():
    crashes = [True] * 5 + [False] * 10
    out = rf.crash_rate_last_k(crashes, k=10)
    # at i=4 all five so far are crashes -> 1.0
    assert out[4] == pytest.approx(1.0)
    # at i=14 the last 10 are all False
    assert out[14] == pytest.approx(0.0)


def test_series_align_at_same_index():
    totals = [10.0, 0.0, 11.0, 12.0]
    crashes = [False, True, False, False]
    forms = rf.best_n_of_last_k(totals, crashes, n=3, k=10)
    rates = rf.crash_rate_last_k(crashes, k=10)
    assert len(forms) == len(rates) == 4
