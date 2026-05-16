# Radar chart with sport-empirical absolute scale

## Parent

PRD: `docs/prd/0001-dashboard-depth-view.md`

## What to build

The **Radar** panel from CONTEXT.md → *Radar*. Headline visual of the Depth section. One axis per score component:

- TRA: D, E, ToF, HD, Landing (5 axes)
- DMT / TUM: D, E, Landing, Penalty (4 axes)

"Lower is better" axes (Landing, Penalty, HD on TRA) inverted at the data boundary so larger area always means stronger performance. All axes share an absolute scale: centre = 0, outer edge = sport-empirical ceiling, calibrated once from the dataset's 99th percentile per (discipline, component) (ADR-0002).

A static **field-median reference ring** is drawn in grey, so a developing athlete's small shape is still legibly positioned.

Four athlete rings overlay:

- **PB** (axis-wise personal max) — outermost dotted
- **Top-5 mean** (axes averaged over the athlete's 5 best routines by total score) — solid filled, headline ring
- **p75** — thin solid
- **p50** — thin dashed

p75 and p50 are suppressed when fewer than 10 completed routines exist in the lookback window.

Introduces the `radar_scales` deep module: `bounds_for(discipline)` returns the calibrated per-axis (min, max), `field_median(db_path, discipline)` returns the reference-ring values (cached in-process). A calibration script as `__main__` of the module queries the 99th-percentile per (discipline, component) and emits the committed constants table; the script is run once and its output checked in.

A shallow `radar_data(db_path, given_name, surname, discipline, lookback_months)` helper returns `{axes, bounds, field_median, athlete: {pb, top5_mean, p75, p50}, n_completed}` with all axis values already oriented so "larger = better."

## Acceptance criteria

- [ ] `radar_scales.bounds_for(discipline)` returns the documented axis shape (5 for TRA, 4 for DMT/TUM with Penalty separate from Landing).
- [ ] `radar_scales.field_median(db_path, discipline)` is cached — a second call within the same process does not re-query.
- [ ] Calibration script runs against the live DB, emits the constants table, and the table is committed.
- [ ] Radar panel renders five overlaid rings: field-median grey reference + PB dotted + Top-5 filled + p75 thin solid + p50 thin dashed.
- [ ] When n_completed < 10 in lookback window, p75 and p50 rings are suppressed; PB and Top-5 still render if their inputs exist.
- [ ] Radar axes never re-derive from the athlete's own data — bounds are constants per ADR-0002.
- [ ] All radar inputs are computed on completed routines only (crashes excluded per CONTEXT.md → *Crash*).
- [ ] Unit tests cover `radar_scales`: bounds shape per discipline, cache behaviour for `field_median`.
- [ ] Smoke test verifies the radar panel ID renders with the expected payload structure.

## Blocked by

- #1 (requires `routine_classifier.is_crash` and `lookback_window` from slice 1).
