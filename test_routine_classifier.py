"""Unit tests for routine_classifier — pure predicates, no DB."""

import routine_classifier as rc


def test_is_crash_tra_boundary():
    assert rc.is_crash(0, 'TRA') is True
    assert rc.is_crash(9, 'TRA') is True
    assert rc.is_crash(10, 'TRA') is False
    assert rc.is_crash(11, 'TRA') is False


def test_is_crash_dmt_boundary():
    assert rc.is_crash(0, 'DMT') is True
    assert rc.is_crash(1, 'DMT') is True
    assert rc.is_crash(2, 'DMT') is False


def test_is_crash_tum_boundary():
    assert rc.is_crash(0, 'TUM') is True
    assert rc.is_crash(7, 'TUM') is True
    assert rc.is_crash(8, 'TUM') is False


def test_is_crash_lowercase_discipline_accepted():
    assert rc.is_crash(9, 'tra') is True
    assert rc.is_crash(10, 'tra') is False


def test_is_crash_unknown_discipline_returns_false():
    assert rc.is_crash(0, 'SYN') is False
    assert rc.is_crash(0, '') is False


def test_is_compulsory_tra_classifies_low_d_full_routine():
    # PB D = 18.0, threshold = 5.4 — a D=5 routine is compulsory.
    assert rc.is_compulsory(5.0, 18.0, 10, 'TRA') is True
    assert rc.is_compulsory(5.4, 18.0, 10, 'TRA') is False
    assert rc.is_compulsory(6.0, 18.0, 10, 'TRA') is False


def test_is_compulsory_classifies_low_d_junior_correctly():
    # Junior with PB D=4, threshold = 1.2. A D=1.0 compulsory routine.
    assert rc.is_compulsory(1.0, 4.0, 10, 'TRA') is True
    assert rc.is_compulsory(1.2, 4.0, 10, 'TRA') is False


def test_is_compulsory_crash_is_never_compulsory():
    # nelements < 10 -> not compulsory even if D is low.
    assert rc.is_compulsory(2.0, 18.0, 9, 'TRA') is False
    assert rc.is_compulsory(2.0, 18.0, 0, 'TRA') is False


def test_is_compulsory_dmt_tum_always_false():
    assert rc.is_compulsory(0.5, 8.0, 2, 'DMT') is False
    assert rc.is_compulsory(0.5, 8.0, 8, 'TUM') is False


def test_is_compulsory_zero_best_d_returns_false():
    assert rc.is_compulsory(0.0, 0.0, 10, 'TRA') is False


def test_classify_three_outcomes():
    assert rc.classify(8, 0.0, 18.0, 'TRA') == 'crash'
    assert rc.classify(10, 2.0, 18.0, 'TRA') == 'compulsory'
    assert rc.classify(10, 15.0, 18.0, 'TRA') == 'voluntary'
    assert rc.classify(2, 2.0, 2.5, 'DMT') == 'voluntary'
    assert rc.classify(1, 2.0, 2.5, 'DMT') == 'crash'
