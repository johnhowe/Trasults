import sqlite3
from datetime import datetime
from statistics import mean, median, stdev, StatisticsError

import form_window
import radar_scales
import rolling_form
import routine_classifier


def build_query(params: dict) -> tuple:
    """Build a parameterized SQL query from a params dict.

    params keys: discipline (tra/dmt/syn/tum), given_name, surname, name,
    representing, stage, dd, mindd, mintof, minhd, minscore, skills,
    since, before, country, year, event, level, female, male
    """
    query = "SELECT * FROM routines WHERE frame_state='PUBLISHED'"
    qparams = []

    disc = (params.get('discipline') or '').lower()
    if disc == 'tra':
        query += " AND competition_discipline = 'TRA'"
    elif disc == 'dmt':
        query += " AND competition_discipline = 'DMT'"
    elif disc == 'syn':
        query += " AND competition_discipline = 'SYN'"
    elif disc == 'tum':
        query += " AND competition_discipline = 'TUM'"

    if params.get('given_name'):
        query += " AND person_given_name LIKE ?"
        qparams.append(f"%{params['given_name']}%")
    if params.get('surname'):
        query += " AND person_surname LIKE ?"
        qparams.append(f"%{params['surname']}%")
    if params.get('name'):
        query += " AND (person_given_name LIKE ? OR person_surname LIKE ?)"
        qparams.append(f"%{params['name']}%")
        qparams.append(f"%{params['name']}%")
    if params.get('representing'):
        query += " AND person_representing LIKE ?"
        qparams.append(f"%{params['representing']}%")
    if params.get('stage'):
        query += " AND stage_kind LIKE ?"
        qparams.append(f"%{params['stage']}%")
    if params.get('dd'):
        query += " AND frame_difficultyt_g = ?"
        qparams.append(float(params['dd']))
    if params.get('mindd'):
        query += " AND frame_difficultyt_g >= ?"
        qparams.append(float(params['mindd']))
    if params.get('mintof'):
        query += " AND t_sigma >= ?"
        qparams.append(float(params['mintof']))
    if params.get('minhd'):
        query += " AND h_sigma >= ?"
        qparams.append(float(params['minhd']))
    if params.get('minscore'):
        query += " AND frame_mark_ttt_g >= ?"
        qparams.append(float(params['minscore']))
    if params.get('skills'):
        query += " AND frame_nelements = ?"
        qparams.append(params['skills'])
    if params.get('since'):
        since_date = datetime.strptime(params['since'], '%Y-%m-%d')
        query += " AND timestamp >= ?"
        qparams.append(int(since_date.timestamp()))
    if params.get('before'):
        before_date = datetime.strptime(params['before'], '%Y-%m-%d')
        query += " AND timestamp <= ?"
        qparams.append(int(before_date.timestamp()))
    if params.get('country'):
        query += " AND event_country LIKE ?"
        qparams.append(f"%{params['country']}%")
    if params.get('year'):
        query += " AND event_year = ?"
        qparams.append(params['year'])
    if params.get('event'):
        query += " AND event_title LIKE ?"
        qparams.append(f"%{params['event']}%")
    if params.get('level'):
        query += " AND competition_title LIKE ?"
        qparams.append(f"%{params['level']}%")

    female_terms = ["fem", "wom", "gir", "ladies", r"\bf\)", "flickor", "女",
                    "Дев", "Женщины", "Юниорки", "tytöt", "dam", "töt", "naiset", "tüdrukud"]
    not_female_terms = [" men", " male", "мужчины", "мужчины и женщины", "&m"]

    if params.get('female'):
        female_conditions = " OR ".join([f"competition_title LIKE ?" for _ in female_terms])
        not_female_conditions = " AND ".join([f"competition_title NOT LIKE ?" for _ in not_female_terms])
        query += f" AND ({female_conditions})"
        qparams.extend([f"%{t}%" for t in female_terms])
        query += f" AND ({not_female_conditions})"
        qparams.extend([f"%{t}%" for t in not_female_terms])

    if params.get('male'):
        male_conditions = " AND ".join([f"competition_title NOT LIKE ?" for _ in female_terms])
        query += f" AND ({male_conditions})"
        qparams.extend([f"%{t}%" for t in female_terms])

    return query, qparams


def query_db(db_path: str, params: dict, order_by: str = 'frame_mark_ttt_g DESC') -> list:
    """Execute a search and return a list of row dicts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query, qparams = build_query(params)
    query += f" ORDER BY {order_by}"
    cursor.execute(query, qparams)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


# --- Score helpers ---

def get_total_score(r) -> float:
    num_skills = int(r['frame_nelements'])
    if num_skills == 0:
        return 0
    return float(r['frame_mark_ttt_g'])


def get_execution(r) -> float:
    e = float(r['esigma_sigma'])
    if e > 1000:
        e = e / 100.0
    elif e > 100:
        e = e / 10.0
    return e


def get_dd(r) -> float:
    return float(r['frame_difficultyt_g'])


def get_tof(r) -> float:
    return float(r['t_sigma'])


def get_hd(r) -> float:
    return float(r['h_sigma'])


def get_num_skills(r) -> int:
    return int(r['frame_nelements'])


def get_timestamp(r) -> float:
    return float(r['timestamp'])


# --- Validation helpers ---

def is_test_routine(r) -> bool:
    return any("test" in str(r.get(f, '')).lower()
               for f in ['person_given_name', 'person_surname', 'competition_title', 'person_representing'])


def is_valid_routine(r) -> bool:
    E_MAX, D_MAX, T_MAX, H_MAX = 30, 25, 25, 20
    TOTAL_MAX = E_MAX + D_MAX + T_MAX + H_MAX
    total = get_total_score(r)
    exe = get_execution(r)
    dd = get_dd(r)
    tof = get_tof(r)
    num_skills = get_num_skills(r)
    return (0 <= exe <= E_MAX and 0 <= dd <= D_MAX and
            0 <= tof <= T_MAX and 0 <= total <= TOTAL_MAX and num_skills > 0)


# --- Display helpers ---

def get_stage_code(r) -> str:
    stage_kind = r['stage_kind']
    if stage_kind[0] == 'Q':
        return f"Q{int(r['routine_number'])}"
    elif stage_kind == 'Semifinal':
        return 'SF'
    elif stage_kind == 'Final2':
        return 'F2'
    elif stage_kind in ('Final', 'Final1'):
        return 'F1'
    elif stage_kind == 'Team Final':
        return 'TF'
    elif stage_kind == 'Team Semifinal':
        return 'TS'
    return stage_kind


def get_deductions(r) -> list:
    """Return list of deduction values in tenths (int) for each executed skill."""
    num_skills = get_num_skills(r)
    disc = r.get('competition_discipline', '').upper()
    if disc == 'TRA':
        cols = ['esigma_s1', 'esigma_s2', 'esigma_s3', 'esigma_s4', 'esigma_s5',
                'esigma_s6', 'esigma_s7', 'esigma_s8', 'esigma_s9', 'esigma_s10']
    elif disc == 'DMT':
        cols = ['esigma_s1', 'esigma_s2']
    elif disc == 'TUM':
        cols = ['esigma_s1', 'esigma_s2', 'esigma_s3', 'esigma_s4',
                'esigma_s5', 'esigma_s6', 'esigma_s7', 'esigma_s8']
    else:
        return []
    return [int(float(r[c]) * 10) for c in cols[:num_skills] if r.get(c) is not None]


def heatmap_rgb(deduction_tenths: int) -> str:
    """Convert a deduction value (0–10 in tenths) to a CSS rgb() colour string.

    Interpolates green → amber → red across two linear segments:
      0  → rgb(144, 238, 144)  light green
      5  → rgb(255, 220,   0)  amber
      10 → rgb(255,  80,  80)  light red
    """
    t = max(0, min(10, int(deduction_tenths)))
    if t <= 5:
        ratio = t / 5.0
        r = int(144 + ratio * (255 - 144))   # 144 → 255
        g = int(238 - ratio * (238 - 220))   # 238 → 220
        b = int(144 * (1 - ratio))            # 144 → 0
    else:
        ratio = (t - 5) / 5.0
        r = 255
        g = int(220 * (1 - ratio * 0.64))    # 220 → 79
        b = int(ratio * 80)                   # 0 → 80
    return f"rgb({r},{g},{b})"


def process_for_display(results: list) -> tuple:
    """Filter, validate, compute bests, and build display-ready dicts.

    Returns (processed_rows, bests) where bests is
    {'total': x, 'dd': x, 'exec': x, 'tof': x, 'hd': x}.
    """
    bests = {'total': 0, 'dd': 0, 'exec': 0, 'tof': 0, 'hd': 0, 'dt': 0}

    valid = []
    for r in results:
        if is_test_routine(r) or not is_valid_routine(r):
            continue
        valid.append(r)
        bests['total'] = max(bests['total'], get_total_score(r))
        bests['dd'] = max(bests['dd'], get_dd(r))
        bests['exec'] = max(bests['exec'], get_execution(r))
        bests['tof'] = max(bests['tof'], get_tof(r))
        bests['hd'] = max(bests['hd'], get_hd(r))
        bests['dt'] = max(bests['dt'], get_dd(r) + get_tof(r))

    processed = []
    for r in valid:
        total = get_total_score(r)
        exe = get_execution(r)
        dd = get_dd(r)
        tof = get_tof(r)
        hd = get_hd(r)
        deductions = get_deductions(r)
        deduction_colors = [heatmap_rgb(d) for d in deductions]
        try:
            date_str = datetime.strptime(r['frame_last_start_time_g'][:19], "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d')
        except Exception:
            date_str = ''
        processed.append({
            'date': date_str,
            'event': r['event_title'],
            'country': r['event_country'],
            'stage': get_stage_code(r),
            'level': r['competition_title'],
            'given_name': r['person_given_name'],
            'surname': r['person_surname'],
            'representing': r['person_representing'],
            'discipline': r['competition_discipline'].lower(),
            'dd': dd,
            'tof': tof,
            'dt': dd + tof,
            'hd': hd,
            'execution': exe,
            'landing': int(10 * float(r['esigma_l'])),
            'penalty': int(10 * float(r['frame_penaltyt'])),
            'total': total,
            'deductions': deductions,
            'deduction_colors': deduction_colors,
            'is_best_total': total == bests['total'],
            'is_best_dd': dd == bests['dd'],
            'is_best_exec': exe == bests['exec'],
            'is_best_tof': tof == bests['tof'],
            'is_best_dt': (dd + tof) == bests['dt'],
            'is_best_hd': hd == bests['hd'],
            'datetime': (r.get('frame_last_start_time_g') or '')[:16],
        })

    return processed, bests


# --- Analytics helpers ---

def compute_stats(rows: list) -> dict:
    """Compute summary statistics for a set of processed rows."""
    def _stats(vals):
        vals = [v for v in vals if v is not None]
        if not vals:
            return {'mean': 0, 'median': 0, 'stdev': 0, 'best': 0, 'count': 0}
        return {
            'mean': mean(vals),
            'median': median(vals),
            'stdev': stdev(vals) if len(vals) > 1 else 0.0,
            'best': max(vals),
            'count': len(vals),
        }
    return {
        'total': _stats([r['total'] for r in rows]),
        'dd': _stats([r['dd'] for r in rows]),
        'exec': _stats([r['execution'] for r in rows]),
        'tof': _stats([r['tof'] for r in rows]),
        'hd': _stats([r['hd'] for r in rows]),
    }


def compute_form(rows: list, n: int = 5) -> dict:
    """Compute recent form vs career average. Rows should be sorted DESC by date."""
    if not rows:
        return {}
    totals = [r['total'] for r in rows]
    recent = totals[:n]
    career_avg = sum(totals) / len(totals)
    recent_avg = sum(recent) / len(recent)
    delta = recent_avg - career_avg
    if delta > 0.5:
        trend = 'up'
    elif delta < -0.5:
        trend = 'down'
    else:
        trend = 'flat'
    return {
        'recent_avg': recent_avg,
        'career_avg': career_avg,
        'delta': delta,
        'trend': trend,
        'n': len(recent),
    }


def compute_deduction_profile(rows: list) -> dict:
    """Compute average deduction per skill position across all rows."""
    if not rows:
        return {}
    max_skills = max((len(r['deductions']) for r in rows), default=0)
    if max_skills == 0:
        return {}
    sums = [0.0] * max_skills
    counts = [0] * max_skills
    for r in rows:
        for i, d in enumerate(r['deductions']):
            sums[i] += d
            counts[i] += 1
    avgs = [round(sums[i] / counts[i], 2) if counts[i] > 0 else 0 for i in range(max_skills)]
    return {
        'avg': avgs,
        'labels': [f'Skill {i + 1}' for i in range(max_skills)],
        'max_skills': max_skills,
    }


def get_leaderboard(db_path: str, discipline: str = 'tra', year: str = '',
                    representing: str = '', top_n: int = 50) -> list:
    """Return top athletes by PB score for a given discipline."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT person_given_name, person_surname, person_representing,
               MAX(frame_mark_ttt_g) as best_total,
               MAX(frame_difficultyt_g) as best_dd,
               COUNT(*) as routine_count
        FROM routines
        WHERE frame_state='PUBLISHED'
          AND frame_nelements > 0
          AND competition_discipline = ?
          AND person_given_name NOT LIKE '%test%'
          AND person_surname NOT LIKE '%test%'
    """
    qparams = [discipline.upper()]
    if year:
        query += " AND event_year = ?"
        qparams.append(year)
    if representing:
        query += " AND person_representing LIKE ?"
        qparams.append(f"%{representing}%")
    query += """
        GROUP BY person_given_name, person_surname, person_representing
        ORDER BY best_total DESC
        LIMIT ?
    """
    qparams.append(top_n)
    cursor.execute(query, qparams)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_competition_report(db_path: str, event_title: str) -> list:
    """Return all published routines for a given event title."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM routines
        WHERE frame_state='PUBLISHED'
          AND event_title LIKE ?
        ORDER BY competition_discipline, competition_title, stage_kind, performance_rank_g
    """, [f"%{event_title}%"])
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# Dashboard aggregation helpers (/dashboard route)
# ============================================================

# Skill positions per discipline (esigma_s1..sN are populated; rest are noise).
DISCIPLINE_SKILLS = {'TRA': 10, 'DMT': 2, 'TUM': 8}

# Judge execution-score columns. All six are populated for every discipline.
JUDGE_COLS = ['e1_sigma', 'e2_sigma', 'e3_sigma', 'e4_sigma', 'e5_sigma', 'e6_sigma']

# SQL twin of get_execution() — some esigma_sigma rows are stored x10 or x100.
E_SCORE_SQL = (
    "(CASE WHEN esigma_sigma > 1000 THEN esigma_sigma / 100.0 "
    "WHEN esigma_sigma > 100 THEN esigma_sigma / 10.0 "
    "ELSE esigma_sigma END)"
)

# Rows that should never enter analytics. event_year/frame_nelements/frame_penaltyt
# have no column affinity, so numeric use must CAST.
_BASE_FILTER = (
    "frame_state = 'PUBLISHED' "
    "AND person_given_name NOT LIKE '%test%' "
    "AND person_surname NOT LIKE '%test%' "
    "AND person_representing NOT LIKE '%test%' "
    "AND competition_title NOT LIKE '%test%' "
    "AND frame_nelements IS NOT NULL "
    "AND CAST(frame_nelements AS INTEGER) > 0 "
    "AND frame_mark_ttt_g >= 0 AND frame_mark_ttt_g < 100"
)


def rescale_execution(value):
    """Python twin of E_SCORE_SQL. Keep the two in lockstep."""
    if value is None:
        return None
    e = float(value)
    if e > 1000:
        return e / 100.0
    if e > 100:
        return e / 10.0
    return e


def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def cohort_filter(discipline=None, year_from=None, year_to=None, stage=None):
    """SQL fragment + params describing a cohort of routines.

    stage: None | 'qual' | 'final'. Returns (sql_fragment, params); the fragment
    is appended after _BASE_FILTER so it always starts with ' AND '.
    """
    sql, params = "", []
    disc = (discipline or '').upper()
    if disc:
        sql += " AND competition_discipline = ?"
        params.append(disc)
    if year_from:
        sql += " AND CAST(event_year AS INTEGER) >= ?"
        params.append(int(year_from))
    if year_to:
        sql += " AND CAST(event_year AS INTEGER) <= ?"
        params.append(int(year_to))
    if stage == 'qual':
        sql += " AND stage_kind LIKE 'Qualif%'"
    elif stage == 'final':
        sql += " AND stage_kind IN ('Final', 'Final1', 'Final2')"
    return sql, params


def _athlete_filter(given_name, surname):
    """Partial, case-insensitive filter for one athlete — matches the LIKE
    behaviour of build_query/the rest of the app. A loose surname can merge
    distinct people; the dashboard shows routine count + representing so a
    merge stays visible (see CONTEXT.md, athlete-identity caveat)."""
    sql, params = "", []
    if given_name:
        sql += " AND person_given_name LIKE ?"
        params.append(f"%{given_name}%")
    if surname:
        sql += " AND person_surname LIKE ?"
        params.append(f"%{surname}%")
    return sql, params


def _agg_stats(conn, expr, where_sql, params):
    """mean / population-stdev / min / max / count of a numeric expression.

    SQLite has no STDEV, so variance comes from the E[x^2] - E[x]^2 moment.
    """
    row = conn.execute(
        f"SELECT COUNT({expr}) n, AVG({expr}) mean, AVG(1.0 * {expr} * {expr}) msq, "
        f"MIN({expr}) mn, MAX({expr}) mx "
        f"FROM routines WHERE {_BASE_FILTER}{where_sql}",
        params).fetchone()
    n = row['n'] or 0
    if not n:
        return {'n': 0, 'mean': 0.0, 'stdev': 0.0, 'min': 0.0, 'max': 0.0}
    mean = row['mean'] or 0.0
    var = max(0.0, (row['msq'] or 0.0) - mean * mean)
    return {'n': n, 'mean': mean, 'stdev': var ** 0.5,
            'min': row['mn'] or 0.0, 'max': row['mx'] or 0.0}


def athlete_disciplines(db_path, given_name, surname):
    """Disciplines this athlete has published routines in, most-routines first."""
    af, ap = _athlete_filter(given_name, surname)
    with _connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT competition_discipline d, COUNT(*) n FROM routines "
            f"WHERE {_BASE_FILTER}{af} GROUP BY 1 ORDER BY 2 DESC", ap).fetchall()
    return [r['d'] for r in rows if r['d'] in DISCIPLINE_SKILLS]


def athlete_summary(db_path, given_name, surname, discipline):
    """Header card: routine count, PB, best D, span of years, representing."""
    af, ap = _athlete_filter(given_name, surname)
    cf, cp = cohort_filter(discipline=discipline)
    with _connect(db_path) as conn:
        row = conn.execute(
            f"SELECT COUNT(*) n, MAX(frame_mark_ttt_g) pb, MAX(frame_difficultyt_g) best_d, "
            f"MIN(CAST(event_year AS INTEGER)) y0, MAX(CAST(event_year AS INTEGER)) y1 "
            f"FROM routines WHERE {_BASE_FILTER}{af}{cf}", ap + cp).fetchone()
        rep = conn.execute(
            f"SELECT person_representing r, COUNT(*) n FROM routines "
            f"WHERE {_BASE_FILTER}{af}{cf} GROUP BY 1 ORDER BY 2 DESC LIMIT 1",
            ap + cp).fetchone()
    return {
        'routine_count': row['n'] or 0,
        'pb': row['pb'] or 0.0,
        'best_d': row['best_d'] or 0.0,
        'year_from': row['y0'],
        'year_to': row['y1'],
        'representing': rep['r'] if rep else '',
    }


def deduction_profile(db_path, given_name, surname, discipline,
                      year_from=None, year_to=None):
    """Metric 1 — average execution deduction per skill position (in tenths),
    athlete vs cohort. Mirrors the ANSI heatmap the CLI prints."""
    disc = (discipline or '').upper()
    n_skills = DISCIPLINE_SKILLS.get(disc, 10)
    cols = [f'esigma_s{i}' for i in range(1, n_skills + 1)]
    avg_expr = ", ".join(f"AVG({c}) * 10.0" for c in cols)

    af, ap = _athlete_filter(given_name, surname)
    cf, cp = cohort_filter(discipline=disc, year_from=year_from, year_to=year_to)

    with _connect(db_path) as conn:
        a = conn.execute(
            f"SELECT COUNT(*) n, {avg_expr} FROM routines "
            f"WHERE {_BASE_FILTER}{cf}{af}", cp + ap).fetchone()
        c = conn.execute(
            f"SELECT COUNT(*) n, {avg_expr} FROM routines "
            f"WHERE {_BASE_FILTER}{cf}", cp).fetchone()

    def _vals(row):
        return [round(row[i + 1] or 0.0, 2) for i in range(n_skills)]

    return {
        'labels': [f'S{i}' for i in range(1, n_skills + 1)],
        'athlete_avg': _vals(a),
        'cohort_avg': _vals(c),
        'athlete_n': a['n'] or 0,
        'cohort_n': c['n'] or 0,
    }


def dscore_progression(db_path, given_name, surname):
    """Metric 2 — D-score (and E, total) over time for each discipline the
    athlete competes in. Returns {disc: [{date, year, dd, e, total}, ...]}."""
    af, ap = _athlete_filter(given_name, surname)
    with _connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT competition_discipline d, frame_last_start_time_g ts, "
            f"event_year yr, frame_difficultyt_g dd, {E_SCORE_SQL} e, "
            f"frame_mark_ttt_g total FROM routines "
            f"WHERE {_BASE_FILTER}{af} AND frame_difficultyt_g > 0 "
            f"ORDER BY timestamp ASC", ap).fetchall()
    series = {}
    for r in rows:
        if r['d'] not in DISCIPLINE_SKILLS:
            continue
        series.setdefault(r['d'], []).append({
            'date': (r['ts'] or '')[:10],
            'year': r['yr'],
            'dd': round(r['dd'], 2),
            'e': round(r['e'] or 0.0, 2),
            'total': round(r['total'] or 0.0, 3),
        })
    return series


def qual_vs_final(db_path, given_name, surname, discipline,
                  year_from=None, year_to=None):
    """Metric 3 — E-score mean & spread, qualification vs final, athlete vs cohort."""
    disc = (discipline or '').upper()
    af, ap = _athlete_filter(given_name, surname)
    out = {}
    with _connect(db_path) as conn:
        for stage in ('qual', 'final'):
            cf, cp = cohort_filter(discipline=disc, year_from=year_from,
                                   year_to=year_to, stage=stage)
            out[stage] = {
                'athlete': _agg_stats(conn, E_SCORE_SQL, cf + af, cp + ap),
                'cohort': _agg_stats(conn, E_SCORE_SQL, cf, cp),
            }
    return out


_COMPONENTS = [
    ('dd', 'frame_difficultyt_g'),
    ('e', E_SCORE_SQL),
    ('tof', 't_sigma'),
    ('hd', 'h_sigma'),
    ('landing', 'esigma_l'),
    ('penalty', 'CAST(frame_penaltyt AS REAL)'),
    ('total', 'frame_mark_ttt_g'),
]


def score_decomposition(db_path, given_name, surname, discipline,
                        year_from=None, year_to=None):
    """Metric 4 — average D / E / ToF / HD / Landing / Pen / total,
    athlete vs cohort."""
    disc = (discipline or '').upper()
    af, ap = _athlete_filter(given_name, surname)
    cf, cp = cohort_filter(discipline=disc, year_from=year_from, year_to=year_to)
    with _connect(db_path) as conn:
        athlete = {k: _agg_stats(conn, expr, cf + af, cp + ap)
                   for k, expr in _COMPONENTS}
        cohort = {k: _agg_stats(conn, expr, cf, cp)
                  for k, expr in _COMPONENTS}
    return {'athlete': athlete, 'cohort': cohort,
            'athlete_n': athlete['total']['n'], 'cohort_n': cohort['total']['n']}


def tof_distribution(db_path, given_name, surname, year_from=None, year_to=None,
                     bin_width=0.2):
    """Metric 5 — Time-of-Flight histogram (TRA only): athlete routines vs the
    whole TRA field, bucketed at bin_width seconds."""
    af, ap = _athlete_filter(given_name, surname)
    cf, cp = cohort_filter(discipline='TRA', year_from=year_from, year_to=year_to)
    tof_ok = " AND t_sigma > 0 AND t_sigma < 25"
    with _connect(db_path) as conn:
        field = conn.execute(
            f"SELECT CAST(t_sigma / ? AS INTEGER) b, COUNT(*) n FROM routines "
            f"WHERE {_BASE_FILTER}{cf}{tof_ok} GROUP BY 1 ORDER BY 1",
            [bin_width] + cp).fetchall()
        athlete = conn.execute(
            f"SELECT t_sigma t FROM routines "
            f"WHERE {_BASE_FILTER}{cf}{af}{tof_ok} ORDER BY t_sigma", cp + ap).fetchall()
        a_stats = _agg_stats(conn, 't_sigma',
                             cf + af + tof_ok, cp + ap)
        f_stats = _agg_stats(conn, 't_sigma', cf + tof_ok, cp)
    return {
        'bin_width': bin_width,
        'field': [{'tof': round(r['b'] * bin_width, 2), 'count': r['n']}
                  for r in field],
        'athlete_values': [round(r['t'], 2) for r in athlete],
        'athlete_stats': a_stats,
        'field_stats': f_stats,
    }


def difficulty_inflation(db_path, top_n=50):
    """Metric 6 — difficulty inflation as the moving *frontier*: the mean D-score
    of the top_n hardest routines each season, per discipline.

    A raw all-routine mean is useless here — the dataset's population shifts
    heavily over time (early years are elite-international only, later years are
    flooded with domestic junior routines), so a mean tracks that shift, not
    difficulty. The top_n frontier is robust to population dilution: adding more
    low-level routines never changes the hardest ones. `counts` carries the total
    eligible routines per year so thin early seasons stay visible."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            f"WITH ranked AS ("
            f"  SELECT CAST(event_year AS INTEGER) yr, competition_discipline d, "
            f"  frame_difficultyt_g dd, "
            f"  ROW_NUMBER() OVER (PARTITION BY CAST(event_year AS INTEGER), "
            f"    competition_discipline ORDER BY frame_difficultyt_g DESC) rn, "
            f"  COUNT(*) OVER (PARTITION BY CAST(event_year AS INTEGER), "
            f"    competition_discipline) total "
            f"  FROM routines "
            f"  WHERE {_BASE_FILTER} AND frame_difficultyt_g > 0 "
            f"  AND frame_difficultyt_g < 25 "
            f"  AND competition_discipline IN ('TRA','DMT','TUM')) "
            f"SELECT yr, d, AVG(dd) mean_d, MIN(total) n FROM ranked "
            f"WHERE rn <= ? GROUP BY yr, d ORDER BY yr", [top_n]).fetchall()
    years = sorted({r['yr'] for r in rows if r['yr']})
    series = {d: {y: None for y in years} for d in ('TRA', 'DMT', 'TUM')}
    counts = {d: {y: 0 for y in years} for d in ('TRA', 'DMT', 'TUM')}
    for r in rows:
        if r['yr'] and r['d'] in series:
            series[r['d']][r['yr']] = round(r['mean_d'], 3)
            counts[r['d']][r['yr']] = r['n']
    return {
        'years': years,
        'top_n': top_n,
        'series': {d: [series[d][y] for y in years] for d in series},
        'counts': {d: [counts[d][y] for y in years] for d in counts},
    }


def head_to_head(db_path, a_given, a_surname, b_given, b_surname, discipline,
                 year_from=None, year_to=None):
    """Metric 7 — two athletes' score-component averages plus the competitions
    they both contested (with each one's best routine score there)."""
    disc = (discipline or '').upper()
    a = score_decomposition(db_path, a_given, a_surname, disc, year_from, year_to)
    b = score_decomposition(db_path, b_given, b_surname, disc, year_from, year_to)
    cf, cp = cohort_filter(discipline=disc, year_from=year_from, year_to=year_to)
    af, ap = _athlete_filter(a_given, a_surname)
    bf, bp = _athlete_filter(b_given, b_surname)
    a_match = af.replace(' AND ', '', 1) if af else '1'
    b_match = bf.replace(' AND ', '', 1) if bf else '1'
    with _connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT event_title et, event_year yr, "
            f"MAX(CASE WHEN {a_match} THEN frame_mark_ttt_g END) a_best, "
            f"MAX(CASE WHEN {b_match} THEN frame_mark_ttt_g END) b_best "
            f"FROM routines WHERE {_BASE_FILTER}{cf} "
            f"AND (({a_match}) OR ({b_match})) "
            f"GROUP BY event_title, event_year "
            f"HAVING a_best IS NOT NULL AND b_best IS NOT NULL "
            f"ORDER BY CAST(event_year AS INTEGER) DESC, event_title",
            ap + bp + cp + ap + bp).fetchall()
    return {
        'a': a, 'b': b,
        'a_name': f"{a_given} {a_surname}".strip(),
        'b_name': f"{b_given} {b_surname}".strip(),
        'shared': [{
            'event': r['et'], 'year': r['yr'],
            'a_best': round(r['a_best'], 3), 'b_best': round(r['b_best'], 3),
        } for r in rows],
    }


def judge_panel_variance(db_path, event_title=None, discipline=None,
                         year_from=None, year_to=None, top_n=20):
    """Metric 8 — disagreement across the six judge execution scores.

    With event_title: per-routine spread for that competition.
    Without: the competitions with the widest mean judge spread.
    """
    spread = (f"(max({','.join(JUDGE_COLS)}) - min({','.join(JUDGE_COLS)}))")
    not_null = " AND " + " AND ".join(f"{c} IS NOT NULL" for c in JUDGE_COLS)
    with _connect(db_path) as conn:
        if event_title:
            rows = conn.execute(
                f"SELECT person_given_name g, person_surname s, competition_title ct, "
                f"stage_kind sk, routine_number rn, {spread} spread, "
                f"{E_SCORE_SQL} e, {','.join(JUDGE_COLS)} FROM routines "
                f"WHERE {_BASE_FILTER}{not_null} AND event_title LIKE ? "
                f"ORDER BY spread DESC LIMIT 500", [f"%{event_title}%"]).fetchall()
            return {
                'mode': 'event',
                'event_title': event_title,
                'routines': [{
                    'athlete': f"{r['g']} {r['s']}",
                    'competition': r['ct'], 'stage': r['sk'],
                    'spread': round(r['spread'], 2),
                    'e': round(r['e'] or 0.0, 2),
                    'judges': [round(r[c], 1) for c in JUDGE_COLS],
                } for r in rows],
            }
        cf, cp = cohort_filter(discipline=discipline, year_from=year_from,
                               year_to=year_to)
        rows = conn.execute(
            f"SELECT event_title et, AVG({spread}) mean_spread, COUNT(*) n "
            f"FROM routines WHERE {_BASE_FILTER}{not_null}{cf} "
            f"GROUP BY 1 HAVING n >= 30 ORDER BY mean_spread DESC LIMIT ?",
            cp + [top_n]).fetchall()
        return {
            'mode': 'overview',
            'competitions': [{
                'event_title': r['et'],
                'mean_spread': round(r['mean_spread'], 3),
                'routine_count': r['n'],
            } for r in rows],
        }


def form_kpi_data(db_path, given_name, surname, discipline, form_months, now=None):
    """KPI tile payload for the Depth view's form window.

    Returns {form_indicator, crash_rate, n_in_window, n_completed_in_window}:
      - form_indicator: mean of the best 3 routine totals among the last 10
        *completed* (non-crash) routines in the window. None when fewer than
        3 completed routines fall inside the window.
      - crash_rate: share of crashes among all routines in the window.
    """
    disc = (discipline or '').upper()
    af, ap = _athlete_filter(given_name, surname)
    cf, cp = cohort_filter(discipline=disc)
    with _connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT frame_last_start_time_g ts, "
            f"CAST(frame_nelements AS INTEGER) ne, "
            f"frame_mark_ttt_g total, competition_discipline disc "
            f"FROM routines WHERE {_BASE_FILTER}{cf}{af} "
            f"ORDER BY timestamp ASC", cp + ap).fetchall()

    routines = [{
        'frame_last_start_time_g': r['ts'],
        'ne': r['ne'],
        'total': float(r['total'] or 0.0),
        'disc': r['disc'],
    } for r in rows]
    windowed = form_window.filter_routines(routines, form_months, now=now)
    crashes = [routine_classifier.is_crash(r['ne'], r['disc']) for r in windowed]
    completed_totals = [r['total'] for r, c in zip(windowed, crashes) if not c]
    n = len(windowed)
    n_completed = len(completed_totals)
    if n_completed < 3:
        form_indicator = None
    else:
        last10 = completed_totals[-10:]
        form_indicator = round(sum(sorted(last10, reverse=True)[:3]) / 3, 3)
    crash_rate = round(sum(crashes) / n, 4) if n else 0.0
    return {
        'form_indicator': form_indicator,
        'crash_rate': crash_rate,
        'n_in_window': n,
        'n_completed_in_window': n_completed,
    }


def radar_data(db_path, given_name, surname, discipline, form_months, now=None):
    """Radar payload for the Depth view (issue 0003).

    Returns ``{axes, bounds, field_median, athlete, n_completed, n_in_window}``
    with every axis value already oriented "larger = better" (inverted-axis
    folding handled by ``radar_scales.invert``). Computed on completed
    routines only — crashes are excluded per CONTEXT.md → *Crash*. ``p75`` /
    ``p50`` are ``None`` when fewer than 10 completed routines fall inside
    the form window; ``pb`` / ``top5_mean`` still populate if their inputs
    exist.
    """
    disc = (discipline or '').upper()
    axes = radar_scales.AXES[disc]
    bounds = radar_scales.bounds_for(disc)

    af, ap = _athlete_filter(given_name, surname)
    cf, cp = cohort_filter(discipline=disc)
    axis_cols = [
        'frame_difficultyt_g', E_SCORE_SQL, 't_sigma', 'h_sigma',
        'esigma_l', 'CAST(frame_penaltyt AS REAL)',
    ]
    select_axes = (
        f"{axis_cols[0]} d, {axis_cols[1]} e, {axis_cols[2]} tof, "
        f"{axis_cols[3]} hd, {axis_cols[4]} landing, {axis_cols[5]} penalty"
    )
    with _connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT frame_last_start_time_g ts, "
            f"CAST(frame_nelements AS INTEGER) ne, "
            f"frame_mark_ttt_g total, competition_discipline cd, "
            f"{select_axes} FROM routines "
            f"WHERE {_BASE_FILTER}{cf}{af} ORDER BY timestamp ASC",
            cp + ap).fetchall()
    routines = [dict(r) for r in rows]
    for r in routines:
        r['frame_last_start_time_g'] = r['ts']
    windowed = form_window.filter_routines(routines, form_months, now=now)
    completed = [r for r in windowed
                 if not routine_classifier.is_crash(r['ne'], r['cd'])]

    _AXIS_KEYS = {'D': 'd', 'E': 'e', 'ToF': 'tof', 'HD': 'hd',
                  'Landing': 'landing', 'Penalty': 'penalty'}

    def _disp(axis, r):
        raw = r[_AXIS_KEYS[axis]]
        return radar_scales.invert(axis, float(raw or 0.0), disc)

    n = len(completed)
    athlete = {'pb': None, 'top5_mean': None, 'p75': None, 'p50': None}
    if n:
        athlete['pb'] = {a: round(max(_disp(a, r) for r in completed), 3)
                         for a in axes}
        top5 = sorted(completed, key=lambda r: r['total'] or 0.0,
                      reverse=True)[:5]
        athlete['top5_mean'] = {
            a: round(sum(_disp(a, r) for r in top5) / len(top5), 3)
            for a in axes}
    if n >= 10:
        sorted_axes = {a: sorted(_disp(a, r) for r in completed) for a in axes}

        def _pct(vals, p):
            idx = min(len(vals) - 1, max(0, int(round(p * (len(vals) - 1)))))
            return round(vals[idx], 3)

        athlete['p75'] = {a: _pct(sorted_axes[a], 0.75) for a in axes}
        athlete['p50'] = {a: _pct(sorted_axes[a], 0.50) for a in axes}

    return {
        'axes': axes,
        'bounds': {a: list(bounds[a]) for a in axes},
        'field_median': radar_scales.field_median(db_path, disc),
        'athlete': athlete,
        'n_completed': n,
        'n_in_window': len(windowed),
    }


def form_and_crash_series(db_path, given_name, surname, discipline):
    """Career-long chronological trend series for the Depth trend panel.

    Returns {'dates', 'form', 'crash_rate'} — three parallel arrays, one
    entry per published routine for this athlete in this discipline, ordered
    by timestamp ASC. `form[i]` is None where fewer than 3 completed routines
    are available in the trailing 10, so a string of crashes plateaus the
    form line instead of collapsing it (user story 11).
    """
    disc = (discipline or '').upper()
    af, ap = _athlete_filter(given_name, surname)
    cf, cp = cohort_filter(discipline=disc)
    with _connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT frame_last_start_time_g ts, "
            f"CAST(frame_nelements AS INTEGER) ne, "
            f"frame_mark_ttt_g total, competition_discipline disc "
            f"FROM routines WHERE {_BASE_FILTER}{cf}{af} "
            f"ORDER BY timestamp ASC", cp + ap).fetchall()
    totals = [float(r['total'] or 0.0) for r in rows]
    crashes = [routine_classifier.is_crash(r['ne'], r['disc']) for r in rows]
    dates = [(r['ts'] or '')[:10] for r in rows]
    forms = rolling_form.best_n_of_last_k(totals, crashes)
    rates = rolling_form.crash_rate_last_k(crashes)
    return {
        'dates': dates,
        'form': [round(v, 3) if v is not None else None for v in forms],
        'crash_rate': [round(v, 4) for v in rates],
    }
