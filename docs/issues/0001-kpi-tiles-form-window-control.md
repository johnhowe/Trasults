# Form & Crash KPI tiles + Form window control

## Parent

PRD: `docs/prd/0001-dashboard-depth-view.md`

## What to build

Two KPI tiles at the top of the athlete `/dashboard` view: **Form indicator** (mean of the athlete's best 3 routine totals from their last 10 completed routines, per CONTEXT.md → *Form indicator*) and **Crash rate** (share of crashes in the form window, per CONTEXT.md → *Crash rate*). Both computed for the currently-selected athlete within a new **form window** time concept (past N months, default 12), independent of the existing year-range cohort filter (ADR-0001).

A new `?form_months=N` URL parameter drives the window; a small selector control in the dashboard's controls row sets it. The form window does not affect any existing panel.

Introduces three deep modules in service of this slice and everything downstream:

- `routine_classifier` — `is_crash(nelements, discipline)` and `is_compulsory(d, athlete_best_d, nelements, discipline)` predicates. Pure functions. Owns the per-discipline expected-element table `{TRA: 10, DMT: 2, TUM: 8}` and the 30% compulsory threshold.
- `rolling_form` — `best_n_of_last_k(totals, crashes, n=3, k=10)` and `crash_rate_last_k(crashes, k=10)`. Pure functions on parallel chronological arrays. For this slice only the current-value output is wired up; the full series feeds slice #2.
- `form_window` — `parse_months(param, default=12)` and `filter_routines(routines, months, now)`. Pure functions enforcing the ADR-0001 boundary.

A shallow `form_kpi_data(db_path, given_name, surname, discipline, form_months)` helper in `db.py` returns `{form_indicator: float | None, crash_rate: float, n_in_window: int, n_completed_in_window: int}`. Returns `None` for form_indicator when fewer than 3 completed routines exist in the window.

## Acceptance criteria

- [ ] `routine_classifier`, `rolling_form`, `form_window` modules exist with unit tests covering the table cases listed in the PRD's testing-decisions section.
- [ ] `/dashboard` accepts `form_months` query parameter; default 12.
- [ ] Form window selector control renders alongside existing controls and is visually distinct from year_from/year_to.
- [ ] Form indicator KPI tile displays for any athlete with ≥ 3 completed routines in the window; shows a polite empty state otherwise.
- [ ] Crash rate KPI tile displays for any athlete with ≥ 1 routine in the window.
- [ ] No coloured worry thresholds on the crash rate tile (per Q7c).
- [ ] No existing panel's behaviour changes — cohort filter still drives all eight existing panels.
- [ ] Smoke test extends `test_dashboard.py`: `/dashboard?given_name=X&surname=Y&form_months=12` returns 200 with the new KPI tile IDs present.

## Blocked by

None — can start immediately.
