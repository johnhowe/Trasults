# Paired form & crash trend lines

## Parent

PRD: `docs/prd/0001-dashboard-depth-view.md`

## What to build

A wide panel in the Depth section showing two paired trend lines across the athlete's full career: the **Form indicator** rolling series (mean of best 3 of last 10 completed routine totals) and the **Crashes-per-10-routines** rolling series. Same x-axis (chronological), two y-axes (form on the left in navy, crash rate on the right in red), so a coach scans both at once — form going up is good, crashes going up is bad.

Both series are emitted by `rolling_form` (extended from slice #1 to return the full chronological series, not just the current value). Form indicator entries are omitted at indices where fewer than 3 completed routines are available in the trailing 10; the line resumes when enough completed data accumulates.

A shallow `form_and_crash_series(db_path, given_name, surname, discipline)` helper in `db.py` returns `{dates: [...], form: [...], crash_rate: [...]}` over the athlete's entire history (not form-window-scoped — the trend line is the *career view* of what the KPI summarises in the window).

## Acceptance criteria

- [ ] `rolling_form.best_n_of_last_k` and `rolling_form.crash_rate_last_k` return parallel chronological series with aligned indices.
- [ ] Trend panel renders for any athlete with ≥ 10 routines; shows a polite empty state below that threshold.
- [ ] Both lines share x-axis and use a Chart.js dual y-axis configuration.
- [ ] Form line and crash line use the dashboard's existing red/navy palette consistently with the rest of the page.
- [ ] A string of consecutive crashes produces a *stalled* form line (gap or flat segment) and a *climbing* crash line, not a collapsed form line (per user story 11).
- [ ] Smoke test verifies the panel ID renders and the JSON payload contains both series with matching length.

## Blocked by

- #1 (requires `routine_classifier` and `rolling_form` from slice 1).
