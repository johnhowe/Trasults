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
# Elite frontiers — top-N frontier is robust to population dilution
# --------------------------------------------------------------------------

def test_difficulty_frontier_ignores_diluting_low_routines(tmp_path):
    path = str(tmp_path / 'tiny.db')
    conn = sqlite3.connect(path)
    conn.execute(f"CREATE TABLE routines ({_MEM_COLS})")
    conn.row_factory = sqlite3.Row
    for _ in range(50):
        _insert(conn, 18.0, event_year='2024')         # _insert default title="Open" → M bucket
    conn.commit()
    before = db.difficulty_frontier(path, top_n=50)
    for _ in range(1000):
        _insert(conn, 1.0, event_year='2024')          # junk low-D dilution
    conn.commit()
    conn.close()
    after = db.difficulty_frontier(path, top_n=50)
    assert before['series']['M']['TRA'] == after['series']['M']['TRA'] == [18.0]
    assert after['counts']['M']['TRA'] == [1050]       # population shift stays visible


def test_difficulty_frontier_partitions_by_gender(tmp_path):
    path = str(tmp_path / 'tiny.db')
    conn = sqlite3.connect(path)
    conn.execute(f"CREATE TABLE routines ({_MEM_COLS})")
    conn.row_factory = sqlite3.Row
    for _ in range(50):
        _insert(conn, 18.0, event_year='2024', competition_title='Mens Senior')
    for _ in range(50):
        _insert(conn, 14.0, event_year='2024', competition_title='Womens Senior')
    conn.commit()
    conn.close()
    fd = db.difficulty_frontier(path, top_n=50)
    # Each gender ranks independently — both buckets are populated.
    assert fd['series']['M']['TRA'] == [18.0]
    assert fd['series']['F']['TRA'] == [14.0]
    assert fd['counts']['M']['TRA'] == [50]
    assert fd['counts']['F']['TRA'] == [50]


def test_tof_frontier_is_tra_only(tmp_path):
    path = str(tmp_path / 'tiny.db')
    conn = sqlite3.connect(path)
    conn.execute(f"CREATE TABLE routines ({_MEM_COLS}, t_sigma REAL)")
    conn.row_factory = sqlite3.Row
    for _ in range(50):
        conn.execute(
            "INSERT INTO routines (frame_state, person_given_name, person_surname, "
            "person_representing, competition_title, frame_nelements, "
            "frame_mark_ttt_g, frame_difficultyt_g, event_year, "
            "competition_discipline, esigma_sigma, stage_kind, t_sigma) "
            "VALUES ('PUBLISHED','A','B','C','Mens Senior','10',50.0,18.0,'2024',"
            "'TRA',15.0,'Final',17.5)")
    conn.commit()
    conn.close()
    tf = db.tof_frontier(path, top_n=50)
    assert tf['series']['M']['TRA'] == [17.5]
    assert 'DMT' not in tf['series']['M']
    assert tf['series']['F']['TRA'] == [None]


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
def test_difficulty_frontier_rose_over_the_decade():
    fd = db.difficulty_frontier(DB_PATH, top_n=50)
    assert fd['years'][0] == 2013 and fd['years'][-1] == 2025
    tra_m = dict(zip(fd['years'], fd['series']['M']['TRA']))
    assert tra_m[2025] > tra_m[2013]
    assert tra_m[2025] > 18.0          # known frontier ~20.4 in 2025
    # Women's series is also populated — gender partitioning keeps it from
    # being silently emptied (ADR-0004).
    tra_f = dict(zip(fd['years'], fd['series']['F']['TRA']))
    assert tra_f[2018] is not None and tra_f[2018] > 14.0


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
# Lookback-window KPI tile smoke test (issue 0001)
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
def test_dashboard_lookback_kpi_tiles_render():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Dylan&surname=Schmidt&lookback_months=12')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'kpi-rolling-peak' in body
    assert 'kpi-crash-rate' in body


# --------------------------------------------------------------------------
# Rolling peak & crashes trend lines (issue 0002)
# --------------------------------------------------------------------------

@real_db
def test_rolling_peak_and_crash_series_returns_aligned_career_series():
    s = db.rolling_peak_and_crash_series(DB_PATH, 'Dylan', 'Schmidt', 'TRA')
    assert set(s) >= {'dates', 'peak', 'crash_rate'}
    n = len(s['dates'])
    assert n >= 10
    assert len(s['peak']) == n
    assert len(s['crash_rate']) == n
    # crash rate is a share in [0, 1]
    assert all(0.0 <= c <= 1.0 for c in s['crash_rate'])
    # peak is either None or a positive routine-score average
    assert all(v is None or v > 0 for v in s['peak'])


@real_db
def test_dashboard_trend_panel_renders():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Dylan&surname=Schmidt')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'panel-trend' in body
    assert 'c-trend' in body
    # JSON payload exposes both series, and they have matching length
    s = db.rolling_peak_and_crash_series(DB_PATH, 'Dylan', 'Schmidt', 'TRA')
    assert '"peak"' in body and '"crash_rate"' in body
    assert len(s['peak']) == len(s['crash_rate']) == len(s['dates']) >= 10


# --------------------------------------------------------------------------
# Radar (issue 0003)
# --------------------------------------------------------------------------

@real_db
def test_radar_data_payload_uses_absolute_bounds_per_discipline():
    import radar_scales
    r = db.radar_data(DB_PATH, 'Dylan', 'Schmidt', 'TRA', lookback_months=36)
    assert r['axes'] == ['D', 'E', 'ToF', 'HD', 'Landing']
    # Axis bounds are *constants* — never re-derived from the athlete (ADR-0002).
    expected = {a: list(b) for a, b in radar_scales.bounds_for('TRA').items()}
    assert r['bounds'] == expected
    assert set(r['field_median']) == {'D', 'E', 'ToF', 'HD', 'Landing'}
    assert r['n_completed'] >= 0
    if r['n_completed']:
        assert set(r['athlete']['pb']) == {'D', 'E', 'ToF', 'HD', 'Landing'}
        assert set(r['athlete']['top5_mean']) == {'D', 'E', 'ToF', 'HD', 'Landing'}


@real_db
def test_radar_data_suppresses_percentile_rings_below_threshold():
    # Tiny window will rarely contain ≥ 10 routines — p75/p50 must drop out
    # but PB / Top-5 still populate when at least one completed routine exists.
    r = db.radar_data(DB_PATH, 'Dylan', 'Schmidt', 'TRA', lookback_months=1,
                      now=__import__('datetime').date(2014, 1, 1))
    if r['n_completed'] < 10:
        assert r['athlete']['p75'] is None
        assert r['athlete']['p50'] is None


@real_db
def test_dashboard_radar_panel_renders():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Dylan&surname=Schmidt')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'panel-radar' in body
    assert 'c-radar' in body
    # Payload markers — the radar's bounds/axes are surfaced to the chart binding.
    assert '"axes"' in body and '"bounds"' in body
    assert '"field_median"' in body


# --------------------------------------------------------------------------
# Trade-off scatters (issue 0004)
# --------------------------------------------------------------------------

@real_db
def test_trade_off_scatter_tra_returns_three_pairs():
    import radar_scales
    s = db.trade_off_scatter(DB_PATH, 'Dylan', 'Schmidt', 'TRA', lookback_months=36)
    assert s['pairs'] == ['DxE', 'DxToF', 'ExToF']
    assert set(s['points']) == {'DxE', 'DxToF', 'ExToF'}
    assert isinstance(s['crashes_in_window'], int) and s['crashes_in_window'] >= 0
    # Visual consistency with the Radar — sport-empirical axis bounds.
    bounds = radar_scales.bounds_for('TRA')
    for pair, x_lo, x_hi, y_lo, y_hi in (
        ('DxE', *bounds['D'], *bounds['E']),
        ('DxToF', *bounds['D'], *bounds['ToF']),
        ('ExToF', *bounds['E'], *bounds['ToF']),
    ):
        for p in s['points'][pair]:
            assert {'x', 'y', 'stage'} <= set(p)
            assert p['stage'] in {'qual', 'final'}
            assert x_lo <= p['x']
            assert y_lo <= p['y']


@real_db
def test_trade_off_scatter_dmt_returns_single_pair():
    s = db.trade_off_scatter(DB_PATH, 'Kayla', 'Nel', 'DMT', lookback_months=120)
    assert s['pairs'] == ['DxE']
    assert set(s['points']) == {'DxE'}
    for p in s['points']['DxE']:
        assert {'x', 'y', 'stage'} <= set(p)
        assert p['stage'] in {'qual', 'final'}


@real_db
def test_trade_off_scatter_excludes_crashes_and_counts_them():
    s = db.trade_off_scatter(DB_PATH, 'Dylan', 'Schmidt', 'TRA', lookback_months=36)
    kpi = db.lookback_kpi_data(DB_PATH, 'Dylan', 'Schmidt', 'TRA', 36)
    # The crash caption mirrors the kpi tile's window-scoped crash count.
    assert s['crashes_in_window'] == kpi['n_in_window'] - kpi['n_completed_in_window']
    # Crashes never enter the cloud — points are bounded by completed routines.
    assert len(s['points']['DxE']) <= kpi['n_completed_in_window']


@real_db
def test_dashboard_scatter_panel_renders_for_tra():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Dylan&surname=Schmidt&discipline=TRA')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'panel-scatter' in body
    assert 'c-scatter-DxE' in body
    assert 'c-scatter-DxToF' in body
    assert 'c-scatter-ExToF' in body
    assert 'crashes this window' in body


@real_db
def test_dashboard_scatter_panel_renders_for_dmt():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Kayla&surname=Nel&discipline=DMT')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'panel-scatter' in body
    assert 'c-scatter-DxE' in body
    # DMT has only one scatter — the TRA-only pairs must not render.
    assert 'c-scatter-DxToF' not in body
    assert 'c-scatter-ExToF' not in body


# --------------------------------------------------------------------------
# Heatmap timeline (issue 0005)
# --------------------------------------------------------------------------

_HM_COLS = (
    "frame_state, person_given_name, person_surname, person_representing, "
    "competition_title, competition_discipline, stage_kind, "
    "frame_nelements, frame_mark_ttt_g, frame_difficultyt_g, esigma_sigma, "
    "event_year, frame_last_start_time_g, timestamp, "
    "esigma_s1, esigma_s2, esigma_s3, esigma_s4, esigma_s5, "
    "esigma_s6, esigma_s7, esigma_s8, esigma_s9, esigma_s10"
)


def _hm_db(tmp_path, rows):
    """Build a tiny SQLite db with the columns heatmap_timeline reads."""
    path = str(tmp_path / 'hm.db')
    conn = sqlite3.connect(path)
    conn.execute(f"CREATE TABLE routines ({_HM_COLS})")
    for r in rows:
        full = dict(frame_state='PUBLISHED', person_given_name='A',
                    person_surname='B', person_representing='C',
                    competition_title='Open', competition_discipline='TRA',
                    stage_kind='Final', frame_nelements='10',
                    frame_mark_ttt_g=50.0, frame_difficultyt_g=15.0,
                    esigma_sigma=17.0, event_year='2024',
                    esigma_s1=0.3, esigma_s2=0.3, esigma_s3=0.3, esigma_s4=0.3,
                    esigma_s5=0.3, esigma_s6=0.3, esigma_s7=0.3, esigma_s8=0.3,
                    esigma_s9=0.3, esigma_s10=0.3)
        full.update(r)
        cols = list(full)
        conn.execute(f"INSERT INTO routines ({','.join(cols)}) VALUES "
                     f"({','.join('?' for _ in cols)})", [full[c] for c in cols])
    conn.commit()
    conn.close()
    return path


def test_heatmap_timeline_tra_shape_and_chronological_order(tmp_path):
    from datetime import date
    rows = [
        # Two TRA voluntaries, one compulsory, inserted out of order to verify sort.
        {'frame_last_start_time_g': '2024-06-01 10:00:00', 'timestamp': 1717236000,
         'frame_difficultyt_g': 16.0},                                      # voluntary
        {'frame_last_start_time_g': '2024-01-15 10:00:00', 'timestamp': 1705312800,
         'frame_difficultyt_g': 2.0},                                       # compulsory (low D)
        {'frame_last_start_time_g': '2024-03-10 10:00:00', 'timestamp': 1710036000,
         'frame_difficultyt_g': 17.5},                                      # voluntary, sets best D
    ]
    path = _hm_db(tmp_path, rows)
    out = db.heatmap_timeline(path, 'A', 'B', 'TRA', lookback_months=120,
                              now=date(2024, 12, 31))
    assert out['skills'] == [f'S{i}' for i in range(1, 11)]
    assert out['n_routines'] == 3 == len(out['columns'])
    dates = [c['date'] for c in out['columns']]
    assert dates == sorted(dates), "columns must be chronological ascending"
    # The D=2.0 routine is < 30% of best D 17.5 -> compulsory.
    comp = [c for c in out['columns'] if c['date'] == '2024-01-15'][0]
    assert comp['is_compulsory'] is True
    vols = [c for c in out['columns'] if c['date'] != '2024-01-15']
    assert all(c['is_compulsory'] is False for c in vols)


def test_heatmap_timeline_excludes_crashes(tmp_path):
    from datetime import date
    rows = [
        {'frame_last_start_time_g': '2024-06-01 10:00:00', 'timestamp': 1717236000,
         'frame_nelements': '10'},                                          # completed
        {'frame_last_start_time_g': '2024-06-02 10:00:00', 'timestamp': 1717322400,
         'frame_nelements': '7'},                                           # crash
        {'frame_last_start_time_g': '2024-06-03 10:00:00', 'timestamp': 1717408800,
         'frame_nelements': '9'},                                           # crash
    ]
    path = _hm_db(tmp_path, rows)
    out = db.heatmap_timeline(path, 'A', 'B', 'TRA', lookback_months=120,
                              now=date(2024, 12, 31))
    assert out['n_routines'] == 1
    assert len(out['columns']) == 1


def test_heatmap_timeline_dmt_omits_compulsory_flag(tmp_path):
    from datetime import date
    rows = [
        {'frame_last_start_time_g': '2024-06-01 10:00:00', 'timestamp': 1717236000,
         'competition_discipline': 'DMT', 'frame_nelements': '2',
         'frame_difficultyt_g': 0.5},   # would be "low D" but DMT has no compulsory
        {'frame_last_start_time_g': '2024-06-02 10:00:00', 'timestamp': 1717322400,
         'competition_discipline': 'DMT', 'frame_nelements': '2',
         'frame_difficultyt_g': 4.0},
    ]
    path = _hm_db(tmp_path, rows)
    out = db.heatmap_timeline(path, 'A', 'B', 'DMT', lookback_months=120,
                              now=date(2024, 12, 31))
    assert out['skills'] == ['S1', 'S2']
    assert out['n_routines'] == 2
    assert all(c['is_compulsory'] is False for c in out['columns'])


@real_db
def test_heatmap_timeline_real_db_matches_kpi_completed_count():
    """The column count equals the lookback-window completed-routine count."""
    out = db.heatmap_timeline(DB_PATH, 'Dylan', 'Schmidt', 'TRA', lookback_months=36)
    kpi = db.lookback_kpi_data(DB_PATH, 'Dylan', 'Schmidt', 'TRA', 36)
    assert out['n_routines'] == kpi['n_completed_in_window']
    assert len(out['columns']) == out['n_routines']
    assert out['skills'] == [f'S{i}' for i in range(1, 11)]


@real_db
def test_dashboard_heatmap_timeline_panel_renders():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Dylan&surname=Schmidt&discipline=TRA')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'panel-heatmap-timeline' in body
    assert 'c-heatmap-timeline' in body
    # chartjs-chart-matrix plugin is loaded alongside Chart.js core.
    assert 'chartjs-chart-matrix' in body
    # TRA shows the compulsory/voluntary strip.
    assert 'class="heatmap-strip"' in body


@real_db
def test_dashboard_heatmap_timeline_no_strip_for_dmt():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Kayla&surname=Nel&discipline=DMT')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'panel-heatmap-timeline' in body
    # DMT/TUM have no compulsory routines — the strip element must not render.
    assert 'class="heatmap-strip"' not in body


# --------------------------------------------------------------------------
# Heatmap class summary (issue 0006)
# --------------------------------------------------------------------------


def test_heatmap_class_summary_tra_four_columns_compulsory_via_classifier(tmp_path):
    """TRA returns Compulsory / Vol Qual / Vol Semi / Vol Final; the
    compulsory bucket is gated by routine_classifier.is_compulsory (low D
    relative to the athlete's career best, nelements==10)."""
    from datetime import date
    common_skills = {f'esigma_s{i}': 0.2 for i in range(1, 11)}
    rows = [
        # Voluntary qualification — high D, contributes to the Vol Qual column.
        {'frame_last_start_time_g': '2024-01-15 10:00:00', 'timestamp': 1705312800,
         'stage_kind': 'Qualification', 'frame_difficultyt_g': 17.0,
         **{f'esigma_s{i}': 0.2 for i in range(1, 11)}},
        # Voluntary final — top D, sets best_d.
        {'frame_last_start_time_g': '2024-02-15 10:00:00', 'timestamp': 1708099200,
         'stage_kind': 'Final', 'frame_difficultyt_g': 18.0,
         **{f'esigma_s{i}': 0.5 for i in range(1, 11)}},
        # Compulsory routine (D=1.0 < 30% of 18.0 best, nelements=10).
        {'frame_last_start_time_g': '2024-03-01 10:00:00', 'timestamp': 1709287200,
         'stage_kind': 'Qualification', 'frame_difficultyt_g': 1.0,
         **{f'esigma_s{i}': 0.1 for i in range(1, 11)}},
    ]
    path = _hm_db(tmp_path, rows)
    out = db.heatmap_class_summary(path, 'A', 'B', 'TRA', lookback_months=120,
                                   now=date(2024, 12, 31))
    assert out['columns'] == ['Compulsory', 'Voluntary Qual',
                              'Voluntary Semi', 'Voluntary Final']
    assert out['rows'] == [f'S{i}' for i in range(1, 11)]
    assert out['counts'] == [1, 1, 0, 1]
    # Mean deduction on S1 for each populated column.
    assert out['cells'][0][0] == pytest.approx(0.1)        # Compulsory
    assert out['cells'][0][1] == pytest.approx(0.2)        # Voluntary Qual
    assert out['cells'][0][3] == pytest.approx(0.5)        # Voluntary Final
    # Voluntary Semi has no routines in the window → every cell is None,
    # distinguishing the empty class from a zero-deduction cell.
    assert all(out['cells'][s][2] is None for s in range(10))
    del common_skills  # silence unused


def test_heatmap_class_summary_dmt_three_columns_no_compulsory(tmp_path):
    """DMT/TUM have no compulsory column — three buckets only."""
    from datetime import date
    rows = [
        {'frame_last_start_time_g': '2024-01-15 10:00:00', 'timestamp': 1705312800,
         'competition_discipline': 'DMT', 'frame_nelements': '2',
         'stage_kind': 'Qualification', 'frame_difficultyt_g': 4.0,
         'esigma_s1': 0.4, 'esigma_s2': 0.4},
        {'frame_last_start_time_g': '2024-02-15 10:00:00', 'timestamp': 1708099200,
         'competition_discipline': 'DMT', 'frame_nelements': '2',
         'stage_kind': 'Semifinal', 'frame_difficultyt_g': 4.0,
         'esigma_s1': 0.5, 'esigma_s2': 0.5},
        {'frame_last_start_time_g': '2024-03-15 10:00:00', 'timestamp': 1710518400,
         'competition_discipline': 'DMT', 'frame_nelements': '2',
         'stage_kind': 'Final', 'frame_difficultyt_g': 4.0,
         'esigma_s1': 0.6, 'esigma_s2': 0.6},
    ]
    path = _hm_db(tmp_path, rows)
    out = db.heatmap_class_summary(path, 'A', 'B', 'DMT', lookback_months=120,
                                   now=date(2024, 12, 31))
    assert out['columns'] == ['Qual', 'Semi', 'Final']
    assert out['rows'] == ['S1', 'S2']
    assert out['counts'] == [1, 1, 1]
    assert out['cells'][0][0] == pytest.approx(0.4)
    assert out['cells'][0][1] == pytest.approx(0.5)
    assert out['cells'][0][2] == pytest.approx(0.6)


def test_heatmap_class_summary_excludes_crashes(tmp_path):
    """Crashes never enter the mean — only completed routines contribute."""
    from datetime import date
    rows = [
        {'frame_last_start_time_g': '2024-01-15 10:00:00', 'timestamp': 1705312800,
         'stage_kind': 'Final', 'frame_nelements': '10', 'frame_difficultyt_g': 17.0,
         **{f'esigma_s{i}': 0.3 for i in range(1, 11)}},
        # Crash — nelements < 10. Would otherwise pollute the Voluntary Final
        # mean with 0.99 deductions.
        {'frame_last_start_time_g': '2024-02-15 10:00:00', 'timestamp': 1708099200,
         'stage_kind': 'Final', 'frame_nelements': '7', 'frame_difficultyt_g': 17.0,
         **{f'esigma_s{i}': 0.99 for i in range(1, 11)}},
    ]
    path = _hm_db(tmp_path, rows)
    out = db.heatmap_class_summary(path, 'A', 'B', 'TRA', lookback_months=120,
                                   now=date(2024, 12, 31))
    assert out['counts'][3] == 1                            # Voluntary Final
    assert out['cells'][0][3] == pytest.approx(0.3)         # crash excluded


@real_db
def test_heatmap_class_summary_real_db_tra_shape():
    out = db.heatmap_class_summary(DB_PATH, 'Dylan', 'Schmidt', 'TRA',
                                   lookback_months=36)
    assert out['rows'] == [f'S{i}' for i in range(1, 11)]
    assert out['columns'] == ['Compulsory', 'Voluntary Qual',
                              'Voluntary Semi', 'Voluntary Final']
    assert len(out['counts']) == 4
    assert all(len(row) == 4 for row in out['cells'])


@real_db
def test_dashboard_heatmap_class_summary_panel_renders_tra():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Dylan&surname=Schmidt&discipline=TRA')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'panel-heatmap-class' in body
    assert 'c-heatmap-class' in body
    # TRA renders four columns — surfaced as hm-col-count chips.
    assert body.count('class="hm-col-count"') == 4
    for col in ('Compulsory', 'Voluntary Qual', 'Voluntary Semi', 'Voluntary Final'):
        assert col in body


@real_db
def test_dashboard_heatmap_class_summary_panel_renders_dmt():
    app = _load_flask_app()
    client = app.test_client()
    resp = client.get('/dashboard?given_name=Kayla&surname=Nel&discipline=DMT')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'panel-heatmap-class' in body
    # DMT renders three columns, never the TRA-specific labels.
    assert body.count('class="hm-col-count"') == 3
    assert 'Compulsory' not in body
    assert 'Voluntary Qual' not in body
    assert 'Voluntary Final' not in body
