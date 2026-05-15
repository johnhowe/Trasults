"""Form window — past N months from `now` for athlete-scoped recency.

Distinct from the cohort filter (ADR-0001). The cohort filter emits SQL
fragments and bounds the comparison population; this module filters routine
dicts in Python and bounds the recency lens.
"""

import calendar
from datetime import date, datetime


def parse_months(param, default=12):
    """Normalise the ?form_months URL query parameter. Anything missing,
    malformed, zero, or negative falls back to `default`."""
    if param is None:
        return default
    try:
        n = int(param)
    except (TypeError, ValueError):
        return default
    return n if n > 0 else default


def _months_ago(now, months):
    y, m = now.year, now.month - months
    while m <= 0:
        y -= 1
        m += 12
    last = calendar.monthrange(y, m)[1]
    return date(y, m, min(now.day, last))


def _parse_ts(ts):
    if not ts:
        return None
    try:
        return datetime.strptime(ts[:10], '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def filter_routines(routines, months, now=None):
    """Routines whose `frame_last_start_time_g` falls in [now - months, now]."""
    if now is None:
        now = date.today()
    cutoff = _months_ago(now, months)
    out = []
    for r in routines:
        d = _parse_ts(r.get('frame_last_start_time_g'))
        if d is not None and cutoff <= d <= now:
            out.append(r)
    return out
