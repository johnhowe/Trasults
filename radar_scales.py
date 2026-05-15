"""Sport-empirical absolute axis bounds for the Depth-view radar (ADR-0002).

Every dial has axis bounds calibrated *once* from the dataset's 99th
percentile per (discipline, component). The radar's centre is 0 and the outer
edge is the calibrated ceiling, regardless of which athlete is being viewed.
"Lower is better" axes (HD on TRA, Landing, Penalty) are folded at the
boundary so the whole dial reads "larger area = stronger performance".

A static field-median reference ring sits inside the dial so a developing
athlete's small shape is still legibly positioned (see CONTEXT.md → Radar).
"""

import sqlite3
from statistics import median


# Axis order per discipline — read by callers and the template.
AXES = {
    'TRA': ['D', 'E', 'ToF', 'HD', 'Landing'],
    'DMT': ['D', 'E', 'Landing', 'Penalty'],
    'TUM': ['D', 'E', 'Landing', 'Penalty'],
}

# Axes where the raw column is a deduction — must be inverted so larger=better.
INVERTED_AXES = frozenset({'HD', 'Landing', 'Penalty'})

# SQL expression per axis for the raw value (pre-inversion). The E-score branch
# is the twin of db.E_SCORE_SQL / db.rescale_execution and must stay aligned.
_AXIS_SQL = {
    'D': 'CAST(frame_difficultyt_g AS REAL)',
    'E': '(CASE WHEN esigma_sigma > 1000 THEN esigma_sigma / 100.0 '
         'WHEN esigma_sigma > 100 THEN esigma_sigma / 10.0 '
         'ELSE esigma_sigma END)',
    'ToF': 'CAST(t_sigma AS REAL)',
    'HD': 'CAST(h_sigma AS REAL)',
    'Landing': 'CAST(esigma_l AS REAL)',
    'Penalty': 'CAST(frame_penaltyt AS REAL)',
}

# Calibrated 99th-percentile ceilings per (discipline, axis). Emitted by the
# __main__ calibration block below; recalibration is a deliberate event, not a
# per-request computation (ADR-0002). Inverted-axis ceilings are stored in raw
# units; inversion happens in `invert()`.
BOUNDS = {
    'TRA': {
        'D': (0.0, 16.2),
        'E': (0.0, 18.5),
        'ToF': (0.0, 17.4),
        'HD': (0.0, 10.0),
        'Landing': (0.0, 2.0),
    },
    'DMT': {
        'D': (0.0, 8.8),
        'E': (0.0, 29.0),
        'Landing': (0.0, 2.0),
        'Penalty': (0.0, 1.2),
    },
    'TUM': {
        'D': (0.0, 9.2),
        'E': (0.0, 28.3),
        'Landing': (0.0, 3.0),
        'Penalty': (0.0, 0.6),
    },
}


def bounds_for(discipline):
    """Per-axis (lo, hi) for the discipline, in the canonical axis order."""
    disc = (discipline or '').upper()
    return {a: BOUNDS[disc][a] for a in AXES[disc]}


def invert(axis, raw_value, discipline):
    """Map a raw axis value to the displayed value (larger = better).

    Natural axes (D, E, ToF) pass through clamped to ``≥ 0``. Inverted axes
    fold via ``ceiling − raw``, clamped to the bounds so out-of-range
    deductions don't spill past the dial.
    """
    v = float(raw_value)
    if axis not in INVERTED_AXES:
        return max(0.0, v)
    ceiling = BOUNDS[(discipline or '').upper()][axis][1]
    return max(0.0, min(ceiling, ceiling - v))


_FIELD_MEDIAN_CACHE = {}


def field_median(db_path, discipline):
    """Median of each axis across the discipline's completed routines.

    Drives the grey field-median reference ring. Cached on
    ``(db_path, discipline)`` for the lifetime of the process; recompute means
    clearing ``_FIELD_MEDIAN_CACHE`` or restarting the app.
    """
    disc = (discipline or '').upper()
    key = (db_path, disc)
    if key in _FIELD_MEDIAN_CACHE:
        return _FIELD_MEDIAN_CACHE[key]

    from routine_classifier import EXPECTED_ELEMENTS
    expected = EXPECTED_ELEMENTS[disc]

    conn = sqlite3.connect(db_path)
    out = {}
    try:
        for axis in AXES[disc]:
            expr = _AXIS_SQL[axis]
            rows = conn.execute(
                f"SELECT {expr} v FROM routines "
                f"WHERE frame_state = 'PUBLISHED' "
                f"AND person_given_name NOT LIKE '%test%' "
                f"AND person_surname NOT LIKE '%test%' "
                f"AND CAST(frame_nelements AS INTEGER) >= ? "
                f"AND competition_discipline = ? "
                f"AND {expr} IS NOT NULL",
                [expected, disc]).fetchall()
            vals = [float(r[0]) for r in rows if r[0] is not None]
            raw_med = median(vals) if vals else 0.0
            out[axis] = round(invert(axis, raw_med, disc), 3)
    finally:
        conn.close()

    _FIELD_MEDIAN_CACHE[key] = out
    return out


def _calibrate(db_path):
    """One-off recalibration: emits a ``BOUNDS = {...}`` literal to stdout.
    Run as ``python radar_scales.py path/to/trasults.db`` and paste the
    output back into the ``BOUNDS`` constant above."""
    from routine_classifier import EXPECTED_ELEMENTS

    conn = sqlite3.connect(db_path)
    print('BOUNDS = {')
    for disc in ('TRA', 'DMT', 'TUM'):
        print(f"    {disc!r}: {{")
        expected = EXPECTED_ELEMENTS[disc]
        for axis in AXES[disc]:
            expr = _AXIS_SQL[axis]
            rows = conn.execute(
                f"SELECT {expr} FROM routines "
                f"WHERE frame_state = 'PUBLISHED' "
                f"AND person_given_name NOT LIKE '%test%' "
                f"AND person_surname NOT LIKE '%test%' "
                f"AND CAST(frame_nelements AS INTEGER) >= ? "
                f"AND competition_discipline = ? "
                f"AND {expr} IS NOT NULL "
                f"ORDER BY {expr}",
                [expected, disc]).fetchall()
            vals = [float(r[0]) for r in rows if r[0] is not None]
            ceiling = round(vals[int(0.99 * (len(vals) - 1))], 1) if vals else 0.0
            print(f"        {axis!r}: (0.0, {ceiling}),")
        print('    },')
    print('}')
    conn.close()


if __name__ == '__main__':
    import sys
    _calibrate(sys.argv[1] if len(sys.argv) > 1 else 'trasults.db')
