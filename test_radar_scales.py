"""Unit tests for radar_scales — bounds shape per discipline and the
field-median cache that backs the radar reference ring (issue 0003).

`field_median` is cached for the lifetime of the process so the Flask app
doesn't re-query the whole discipline on every request.
"""

import sqlite3

import radar_scales


# --------------------------------------------------------------------------
# bounds_for: discipline-specific axis shape (ADR-0002)
# --------------------------------------------------------------------------

def test_bounds_for_tra_has_five_axes():
    b = radar_scales.bounds_for('TRA')
    assert set(b) == {'D', 'E', 'ToF', 'HD', 'Landing'}


def test_bounds_for_dmt_has_four_axes_with_penalty_separate_from_landing():
    b = radar_scales.bounds_for('DMT')
    assert set(b) == {'D', 'E', 'Landing', 'Penalty'}


def test_bounds_for_tum_has_four_axes_with_penalty_separate_from_landing():
    b = radar_scales.bounds_for('TUM')
    assert set(b) == {'D', 'E', 'Landing', 'Penalty'}


def test_bounds_for_lowercase_discipline_accepted():
    assert radar_scales.bounds_for('tra') == radar_scales.bounds_for('TRA')


def test_bounds_for_returns_zero_centred_positive_ceiling():
    for disc in ('TRA', 'DMT', 'TUM'):
        for axis, (lo, hi) in radar_scales.bounds_for(disc).items():
            assert lo == 0.0, f"{disc}/{axis} lo {lo} must be 0"
            assert hi > 0.0, f"{disc}/{axis} hi {hi} must be positive"


# --------------------------------------------------------------------------
# field_median: in-process cache
# --------------------------------------------------------------------------

def _build_tiny_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE routines ("
        "frame_state TEXT, person_given_name TEXT, person_surname TEXT, "
        "competition_title TEXT, person_representing TEXT, "
        "competition_discipline TEXT, frame_nelements TEXT, "
        "frame_difficultyt_g REAL, esigma_sigma REAL, "
        "t_sigma REAL, h_sigma REAL, esigma_l REAL, frame_penaltyt REAL, "
        "frame_mark_ttt_g REAL)")
    rows = [
        ('PUBLISHED', 'A', 'B', 'Open', 'C', 'TRA', '10',
         10.0, 15.0, 14.0, 7.0, 0.3, 0.0, 50.0),
        ('PUBLISHED', 'A', 'B', 'Open', 'C', 'TRA', '10',
         12.0, 16.0, 14.5, 8.0, 0.4, 0.0, 52.0),
        ('PUBLISHED', 'A', 'B', 'Open', 'C', 'TRA', '10',
         14.0, 17.0, 15.0, 9.0, 0.5, 0.0, 54.0),
    ]
    conn.executemany(
        "INSERT INTO routines VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def test_field_median_cached_within_process(tmp_path, monkeypatch):
    """A second call with the same (db_path, discipline) returns the same
    object without re-opening the database."""
    db_path = str(tmp_path / 'tiny.db')
    _build_tiny_db(db_path)
    radar_scales._FIELD_MEDIAN_CACHE.clear()

    opens = []
    orig_connect = sqlite3.connect

    def counting_connect(*args, **kwargs):
        opens.append(args)
        return orig_connect(*args, **kwargs)

    monkeypatch.setattr(radar_scales.sqlite3, 'connect', counting_connect)

    a = radar_scales.field_median(db_path, 'TRA')
    b = radar_scales.field_median(db_path, 'TRA')
    assert a is b
    assert len(opens) == 1


def test_field_median_cache_keyed_by_discipline(tmp_path):
    db_path = str(tmp_path / 'tiny.db')
    _build_tiny_db(db_path)
    radar_scales._FIELD_MEDIAN_CACHE.clear()

    tra = radar_scales.field_median(db_path, 'TRA')
    # Different discipline must miss the TRA cache entry — distinct dicts.
    assert tra is not radar_scales._FIELD_MEDIAN_CACHE.get((db_path, 'DMT'))


def test_field_median_returns_axes_for_discipline(tmp_path):
    db_path = str(tmp_path / 'tiny.db')
    _build_tiny_db(db_path)
    radar_scales._FIELD_MEDIAN_CACHE.clear()
    fm = radar_scales.field_median(db_path, 'TRA')
    assert set(fm) == {'D', 'E', 'ToF', 'HD', 'Landing'}
    for axis, v in fm.items():
        lo, hi = radar_scales.bounds_for('TRA')[axis]
        assert lo <= v <= hi, f"{axis} median {v} outside bounds {lo}..{hi}"


# --------------------------------------------------------------------------
# Inversion: "lower is better" axes are folded so larger = better
# --------------------------------------------------------------------------

def test_invert_passes_natural_axes_through():
    assert radar_scales.invert('D', 12.0, 'TRA') == 12.0
    assert radar_scales.invert('E', 16.5, 'TRA') == 16.5
    assert radar_scales.invert('ToF', 18.2, 'TRA') == 18.2


def test_invert_folds_landing_so_zero_deduction_is_ceiling():
    ceiling = radar_scales.bounds_for('TRA')['Landing'][1]
    # A perfect landing (0 deduction) maps to the outer edge.
    assert radar_scales.invert('Landing', 0.0, 'TRA') == ceiling
    # Worst-case (ceiling deduction) maps to centre.
    assert radar_scales.invert('Landing', ceiling, 'TRA') == 0.0


def test_invert_clamps_outliers_to_axis_range():
    ceiling = radar_scales.bounds_for('DMT')['Penalty'][1]
    # Raw deduction beyond the calibrated ceiling clamps to centre, not negative.
    assert radar_scales.invert('Penalty', ceiling + 5.0, 'DMT') == 0.0
