"""Unit tests for lookback_window."""

from datetime import date

import lookback_window as lw


def test_parse_months_valid_integer():
    assert lw.parse_months('6') == 6
    assert lw.parse_months('24', default=12) == 24


def test_parse_months_missing_or_blank_returns_default():
    assert lw.parse_months(None) == 12
    assert lw.parse_months('') == 12
    assert lw.parse_months(None, default=6) == 6


def test_parse_months_malformed_returns_default():
    assert lw.parse_months('abc') == 12
    assert lw.parse_months('1.5') == 12
    assert lw.parse_months('12 months') == 12


def test_parse_months_nonpositive_returns_default():
    assert lw.parse_months('0') == 12
    assert lw.parse_months('-3') == 12


def test_filter_routines_inside_and_outside_window():
    routines = [
        {'frame_last_start_time_g': '2024-05-01 10:00:00'},  # 1.5 months ago
        {'frame_last_start_time_g': '2024-06-10 10:00:00'},  # 5 days ago
        {'frame_last_start_time_g': '2023-06-01 10:00:00'},  # ~12 months ago
    ]
    out = lw.filter_routines(routines, months=6, now=date(2024, 6, 15))
    dates = [r['frame_last_start_time_g'] for r in out]
    assert '2024-05-01 10:00:00' in dates
    assert '2024-06-10 10:00:00' in dates
    assert '2023-06-01 10:00:00' not in dates


def test_filter_routines_boundary_just_inside_and_just_outside():
    routines = [
        {'frame_last_start_time_g': '2023-12-15 12:00:00'},  # exactly 6mo
        {'frame_last_start_time_g': '2023-12-14 12:00:00'},  # 1 day older
    ]
    out = lw.filter_routines(routines, months=6, now=date(2024, 6, 15))
    kept = {r['frame_last_start_time_g'] for r in out}
    assert '2023-12-15 12:00:00' in kept
    assert '2023-12-14 12:00:00' not in kept


def test_filter_routines_skips_unparseable_timestamps():
    routines = [
        {'frame_last_start_time_g': ''},
        {'frame_last_start_time_g': None},
        {'frame_last_start_time_g': 'not-a-date'},
        {'frame_last_start_time_g': '2024-05-01 10:00:00'},
    ]
    out = lw.filter_routines(routines, months=6, now=date(2024, 6, 15))
    assert len(out) == 1
    assert out[0]['frame_last_start_time_g'] == '2024-05-01 10:00:00'


def test_filter_routines_excludes_future_dates():
    routines = [{'frame_last_start_time_g': '2024-07-01 12:00:00'}]
    out = lw.filter_routines(routines, months=6, now=date(2024, 6, 15))
    assert out == []
