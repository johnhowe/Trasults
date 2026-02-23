import sqlite3
from datetime import datetime
from statistics import mean, median, stdev, StatisticsError


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
    bests = {'total': 0, 'dd': 0, 'exec': 0, 'tof': 0, 'hd': 0}

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
            'is_best_hd': hd == bests['hd'],
            'datetime': r.get('frame_last_start_time_g', '')[:16],
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
