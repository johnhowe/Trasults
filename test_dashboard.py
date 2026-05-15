"""Tests for the /dashboard data layer (db.py aggregation helpers).

Pure-logic tests run in-memory. Integration tests run against the real
trasults.db and are skipped if it is absent.
"""

import importlib.util
import os
import sqlite3
import statistics
import sys

import pytest

import db

DB_PATH = os.path.join(os.path.dirname(__file__), 'trasults.db')
real_db = pytest.mark.skipif(not os.path.exists(DB_PATH),
                             reason="trasults.db not present")


# --------------------------------------------------------------------------
# In-memory helpers
# --------------------------------------------------------------------------

_MEM_COLS = (
    "frame_state, person_given_name, person_surname, person_representing, "
    "competition_title, frame_nelements, frame_mark_ttt_g, frame_difficultyt_g, "
    "event_year, competition_discipline, esigma_sigma, stage_kind"
)


def _mem_conn():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute(f"CREATE TABLE routines ({_MEM_COLS})")
    return conn


def _insert(conn, dd, **over):
    row = dict(frame_state='PUBLISHED', person_given_name='A', person_surname='B',
               person_representing='C', competition_title='Open', frame_nelements='10',
               frame_mark_ttt_g=50.0, frame_difficultyt_g=dd, event_year='2024',
               competition_discipline='TRA', esigma_sigma=15.0, stage_kind='Final')
    row.update(over)
    cols = list(row)
    conn.execute(f"INSERT INTO routines ({','.join(cols)}) VALUES "
                 f"({','.join('?' for _ in cols)})", [row[c] for c in cols])


# --------------------------------------------------------------------------
# Score-component arithmetic: E-score rescaling
# --------------------------------------------------------------------------

def test_rescale_execution_branches():
    assert db.rescale_execution(None) is None
    assert db.rescale_execution(0.0) == 0.0
    assert db.rescale_execution(8.5) == 8.5
    assert db.rescale_execution(100.0) == 100.0          # not > 100, untouched
    assert db.rescale_execution(150.0) == 15.0           # > 100  -> / 10
    assert db.rescale_execution(1000.0) == 100.0         # > 100  -> / 10
    assert db.rescale_execution(1500.0) == 15.0          # > 1000 -> / 100
    assert db.rescale_execution(1001.0) == pytest.approx(10.01)


def test_e_score_sql_matches_python_twin():
    """E_SCORE_SQL and rescale_execution must agree on every branch boundary."""
    conn = sqlite3.connect(':memory:')
    conn.execute("CREATE TABLE t (esigma_sigma REAL)")
    vals = [0.0, 8.5, 17.3, 99.9, 100.0, 100.1, 150.0, 999.0, 1000.0, 1000.1, 1500.0]
    conn.executemany("INSERT INTO t VALUES (?)", [(v,) for v in vals])
    for raw, sql_val in conn.execute(f"SELECT esigma_sigma, {db.E_SCORE_SQL} FROM t"):
        assert sql_val == pytest.approx(db.rescale_execution(raw))
    conn.close()


# --------------------------------------------------------------------------
# Cohort / athlete filter construction
# --------------------------------------------------------------------------

def test_cohort_filter_discipline_and_years():
    sql, params = db.cohort_filter(discipline='tra', year_from=2020, year_to=2024)
    assert 'competition_discipline = ?' in sql
    assert 'CAST(event_year AS INTEGER) >= ?' in sql
    assert 'CAST(event_year AS INTEGER) <= ?' in sql
    assert params == ['TRA', 2020, 2024]


def test_cohort_filter_stage_qual_final_disjoint():
    qsql, _ = db.cohort_filter(stage='qual')
    fsql, _ = db.cohort_filter(stage='final')
    assert "stage_kind LIKE 'Qualif%'" in qsql
    assert "stage_kind IN ('Final', 'Final1', 'Final2')" in fsql
    assert 'Qualif' not in fsql and 'Final' not in qsql


def test_cohort_filter_empty():
    assert db.cohort_filter() == ("", [])


def test_athlete_filter_partial_like_match():
    sql, params = db._athlete_filter('Dylan', 'Schmidt')
    assert sql == " AND person_given_name LIKE ? AND person_surname LIKE ?"
    assert params == ['%Dylan%', '%Schmidt%']
    assert db._athlete_filter('', '') == ("", [])


# --------------------------------------------------------------------------
# _agg_stats: moment-based mean / population stdev
# --------------------------------------------------------------------------

def test_agg_stats_matches_statistics_module():
    vals = [10.0, 12.0, 14.0, 11.0, 13.0, 9.0]
    conn = _mem_conn()
    for v in vals:
        _insert(conn, v)
    s = db._agg_stats(conn, 'frame_difficultyt_g', '', [])
    assert s['n'] == len(vals)
    assert s['mean'] == pytest.approx(statistics.fmean(vals))
    assert s['stdev'] == pytest.approx(statistics.pstdev(vals), rel=1e-9)
    assert s['min'] == min(vals) and s['max'] == max(vals)
    conn.close()


def test_agg_stats_empty_is_zeroed():
    conn = _mem_conn()
    assert db._agg_stats(conn, 'frame_difficultyt_g', '', []) == {
        'n': 0, 'mean': 0.0, 'stdev': 0.0, 'min': 0.0, 'max': 0.0}
    conn.close()


def test_base_filter_excludes_test_unpublished_and_zero_skill_rows():
    conn = _mem_conn()
    _insert(conn, 15.0, person_given_name='Test')      # test routine
    _insert(conn, 15.0, frame_nelements='0')           # zero skills
    _insert(conn, 15.0, frame_state='EDITING')         # not published
    _insert(conn, 15.0, frame_mark_ttt_g=250.0)        # garbage total
    _insert(conn, 15.0)                                # the only valid row
    s = db._agg_stats(conn, 'frame_difficultyt_g', '', [])
    assert s['n'] == 1
    conn.close()


# --------------------------------------------------------------------------
# Metric 6 — difficulty inflation frontier is robust to population dilution
# --------------------------------------------------------------------------

def test_difficulty_inflation_ignores_diluting_low_routines(tmp_path):
    path = str(tmp_path / 'tiny.db')
    conn = sqlite3.connect(path)
    conn.execute(f"CREATE TABLE routines ({_MEM_COLS})")
    conn.row_factory = sqlite3.Row
    for _ in range(50):
        _insert(conn, 18.0, event_year='2024')
    conn.commit()
    before = db.difficulty_inflation(path, top_n=50)
    for _ in range(1000):
        _insert(conn, 1.0, event_year='2024')          # junk low-D dilution
    conn.commit()
    conn.close()
    after = db.difficulty_inflation(path, top_n=50)
    assert before['series']['TRA'] == after['series']['TRA'] == [18.0]
    assert after['counts']['TRA'] == [1050]            # population shift stays visible


# --------------------------------------------------------------------------
# Integration tests against the real database
# --------------------------------------------------------------------------

@real_db
def test_athlete_disciplines_are_known():
    discs = db.athlete_disciplines(DB_PATH, 'Dylan', 'Schmidt')
    assert 'TRA' in discs
    assert all(d in db.DISCIPLINE_SKILLS for d in discs)


@real_db
def test_deduction_profile_hand_check_against_direct_sql():
    g, s, disc = 'Dylan', 'Schmidt', 'TRA'
    prof = db.deduction_profile(DB_PATH, g, s, disc)
    assert prof['labels'] == [f'S{i}' for i in range(1, 11)]
    assert len(prof['athlete_avg']) == 10
    assert prof['athlete_n'] > 0 and prof['cohort_n'] > prof['athlete_n']

    conn = db._connect(DB_PATH)
    af, ap = db._athlete_filter(g, s)
    cf, cp = db.cohort_filter(discipline=disc)
    direct = conn.execute(
        f"SELECT AVG(esigma_s1) * 10.0 FROM routines "
        f"WHERE {db._BASE_FILTER}{cf}{af}", cp + ap).fetchone()[0]
    conn.close()
    assert prof['athlete_avg'][0] == pytest.approx(round(direct, 2), abs=0.011)


@real_db
def test_deduction_profile_skill_count_per_discipline():
    assert len(db.deduction_profile(DB_PATH, '', '', 'TRA')['labels']) == 10
    assert len(db.deduction_profile(DB_PATH, '', '', 'DMT')['labels']) == 2
    assert len(db.deduction_profile(DB_PATH, '', '', 'TUM')['labels']) == 8


@real_db
def test_qual_vs_final_split_is_bounded_by_total():
    g, s, disc = 'Dylan', 'Schmidt', 'TRA'
    qf = db.qual_vs_final(DB_PATH, g, s, disc)
    assert set(qf) == {'qual', 'final'}
    summ = db.athlete_summary(DB_PATH, g, s, disc)
    split = qf['qual']['athlete']['n'] + qf['final']['athlete']['n']
    assert 0 < split <= summ['routine_count']


@real_db
def test_score_decomposition_shape_and_counts():
    sd = db.score_decomposition(DB_PATH, 'Dylan', 'Schmidt', 'TRA')
    for side in ('athlete', 'cohort'):
        for key in ('dd', 'e', 'tof', 'hd', 'landing', 'penalty', 'total'):
            assert 'mean' in sd[side][key]
    assert 0 < sd['athlete_n'] < sd['cohort_n']
    # an Olympic-level trampolinist outscores the whole-field mean
    assert sd['athlete']['total']['mean'] > sd['cohort']['total']['mean']


@real_db
def test_difficulty_inflation_frontier_rose_over_the_decade():
    inf = db.difficulty_inflation(DB_PATH, top_n=50)
    assert inf['years'][0] == 2013 and inf['years'][-1] == 2025
    tra = dict(zip(inf['years'], inf['series']['TRA']))
    assert tra[2025] > tra[2013]
    assert tra[2025] > 18.0          # known frontier ~20.4 in 2025


@real_db
def test_tof_distribution_tra_only_shape():
    tof = db.tof_distribution(DB_PATH, 'Dylan', 'Schmidt')
    assert tof['bin_width'] > 0
    assert len(tof['athlete_values']) == tof['athlete_stats']['n']
    assert all(0 < v < 25 for v in tof['athlete_values'])
    assert tof['field_stats']['n'] > tof['athlete_stats']['n']


@real_db
def test_head_to_head_structure_and_shared_events():
    h = db.head_to_head(DB_PATH, 'Dylan', 'Schmidt', 'Brodie', 'Summers', 'TRA')
    assert h['a_name'] == 'Dylan Schmidt' and h['b_name'] == 'Brodie Summers'
    assert 'athlete' in h['a'] and 'athlete' in h['b']
    for entry in h['shared']:
        assert entry['a_best'] > 0 and entry['b_best'] > 0


@real_db
def test_judge_panel_variance_overview_sorted_descending():
    pv = db.judge_panel_variance(DB_PATH)
    assert pv['mode'] == 'overview'
    spreads = [c['mean_spread'] for c in pv['competitions']]
    assert spreads and spreads == sorted(spreads, reverse=True)
    assert all(c['routine_count'] >= 30 for c in pv['competitions'])


@real_db
def test_judge_panel_variance_event_mode():
    pv = db.judge_panel_variance(DB_PATH, event_title='World Age Group')
    assert pv['mode'] == 'event'
    for r in pv['routines']:
        assert len(r['judges']) == 6
        assert r['spread'] == pytest.approx(max(r['judges']) - min(r['judges']), abs=0.05)


# --------------------------------------------------------------------------
# Form-window KPI tile smoke test (issue 0001)
# --------------------------------------------------------------------------

def _load_flask_app():
    """Load flask/flask_app.py via importlib to avoid the project's flask/
    directory shadowing the real Flask package on sys.path. Registers the
    module in sys.modules so Flask can resolve its template/static folder
    via __name__ -> __file__."""
    name = 'trasults_flask_app'
    if name in sys.modules:
        return sys.modules[name].app
    path = os.path.join(os.path.dirname(__file__), 'flask', 'flask_app.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.app


@real_db
def test_dashboard_form_kpi_tiles_render():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Dylan&surname=Schmidt&form_months=12')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'kpi-form-indicator' in body
    assert 'kpi-crash-rate' in body


# --------------------------------------------------------------------------
# Form & crashes trend lines (issue 0002)
# --------------------------------------------------------------------------

@real_db
def test_form_and_crash_series_returns_aligned_career_series():
    s = db.form_and_crash_series(DB_PATH, 'Dylan', 'Schmidt', 'TRA')
    assert set(s) >= {'dates', 'form', 'crash_rate'}
    n = len(s['dates'])
    assert n >= 10
    assert len(s['form']) == n
    assert len(s['crash_rate']) == n
    # crash rate is a share in [0, 1]
    assert all(0.0 <= c <= 1.0 for c in s['crash_rate'])
    # form is either None or a positive routine-score average
    assert all(v is None or v > 0 for v in s['form'])


@real_db
def test_dashboard_form_trend_panel_renders():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Dylan&surname=Schmidt')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'panel-form-trend' in body
    assert 'c-form-trend' in body
    # JSON payload exposes both series, and they have matching length
    s = db.form_and_crash_series(DB_PATH, 'Dylan', 'Schmidt', 'TRA')
    assert '"form"' in body and '"crash_rate"' in body
    assert len(s['form']) == len(s['crash_rate']) == len(s['dates']) >= 10
