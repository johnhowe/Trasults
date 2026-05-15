# Dashboard Depth View

## Problem Statement

The existing `/dashboard` route gives a basic athlete overview — eight per-metric panels averaged over the cohort filter. As a coach or analyst, I can see *that* an athlete scores X, but not *where they're lacking*, not *how their form is trending*, not *how often they crash*, and not *what their performance shape looks like* across components. The numbers are aggregated and the visuals are mostly bar charts and tables. I want a deeper view that reveals patterns: which skill positions consistently lose points, whether execution holds up at higher difficulty, whether the athlete is in form or in a slump, and whether they're crashing too often.

The existing dashboard also conflates two different time concepts in one year-range filter. The "comparison field" question (who is this athlete being measured against?) and the "recent form" question (how are they looking right now?) should not share a single control.

A further constraint: **crashes are common in trampoline**, and routines cut short produce very low scores. If raw means and distributions include crashed routines, the depth view will be dominated by noise from incomplete performances rather than revealing what the athlete is actually capable of when they hit a routine. But crash *frequency* is itself a coaching signal — if it's climbing, that's a worry.

## Solution

A new "Depth" section is added to the top of the `/dashboard` athlete page. The section centres on a **Radar** chart that collapses an athlete's performance shape into one visual, surrounded by a **Form indicator** (best-3-of-last-10 routine totals), a **Crash rate** indicator, paired **form-and-crash trend lines** showing how those two move over the athlete's career, **Trade-off scatters** revealing the D/E/ToF relationships routine-by-routine, and two **skill heatmaps** showing exactly which skill positions are losing points and how that pattern varies across routine class.

A **Crash** is canonically defined as a routine where `nelements < expected_for_discipline` (TRA=10, DMT=2, TUM=8). All performance metrics are computed on **completed routines only**; reliability metrics use all routines. This split is fundamental and applies everywhere.

A new **Form window** control (past N months) sits alongside the existing **Cohort filter** (year_from/year_to) as a second, independent time concept. The cohort filter bounds the comparison field for cross-athlete panels; the form window bounds the athlete-scoped recency lens for the new Depth view.

The existing eight panels remain in place below the Depth section, untrimmed. Coaches who use the old panels still have them; the new view sits on top.

## User Stories

1. As a coach, I want a Radar showing my athlete's performance shape across D, E, ToF, HD, and Landing (TRA — or D, E, Landing, Penalty for DMT/TUM), so that I can read their strengths and weaknesses at a single glance instead of reading numbers off a table.
2. As a coach, I want the Radar's axes to run from zero at the centre to a sport-empirical ceiling at the outer edge, so that a developing junior's shape correctly reads as small and an elite's correctly reads as large — and so that two athletes' radars are directly comparable.
3. As a coach of a developing athlete, I want a grey "field median" reference ring on the Radar, so that an athlete far below the elite ceiling is still legibly positioned against typical performance instead of being a tiny invisible blob in the centre.
4. As a coach, I want the Radar to overlay four rings — PB, Top-5-mean-by-total, p75, and p50 — so that I can see the gap between the athlete's ceiling, their best-day shape, their good days, and their typical days at the same time.
5. As a coach, I want the Radar's percentile rings (p75, p50) to be suppressed when there are fewer than 10 routines in the form window, so that I don't read a percentile based on three data points.
6. As a coach, I want the Radar to be computed on **completed routines only** so that a string of recent crashes doesn't make the athlete's shape collapse — their underlying ability is still there.
7. As a coach, I want a **Form indicator** showing the mean of my athlete's best 3 routine totals from their last 10 completed routines, so that I have a single number summarising current form that's robust to one bad routine.
8. As a coach, I want the same form indicator plotted as a **trend line** across the athlete's full career, so that I can see whether they're at a peak, in a slump, or on a plateau.
9. As a coach, I want a **Crash rate** indicator showing the share of crashes in the form window, so that I can see the reliability side of current form at the same glance as performance.
10. As a coach, I want a **rolling crashes-per-10-routines line** paired visually with the form trend line, so that I can scan both at once — form going up is good, crashes going up is bad.
11. As a coach with crashes-as-routine, I want a string of crashes to show up as a *stalled* form trend (because they're excluded from the best-of-3 pool) rather than a *collapsed* one, so that the form indicator reflects underlying capability and the crash line carries the reliability signal separately.
12. As a coach with a TRA athlete, I want **three trade-off scatters** — D×E, D×ToF, and E×ToF — so that I can read the difficulty/execution trade-off, the air-time potential, and the in-flight cleanness as three separate relationships.
13. As a coach with a DMT or TUM athlete, I want a single D×E trade-off scatter, so that I see the only ToF-less relationship that applies to my discipline.
14. As a coach, I want scatter points coloured by stage (qual vs final), so that I can see whether my athlete's execution holds up under final pressure or drops.
15. As a coach, I want crashes excluded from the scatter clouds but counted in a caption ("crashes this window: N"), so that the cloud shape tells me about completed performance without crash-low-scores dragging it down.
16. As a coach, I want a **Skill × Routine timeline heatmap** showing the deduction at each skill position for every completed routine in chronological order, so that I can see exactly where my athlete is losing points and whether the pattern is moving over time.
17. As a coach with a TRA athlete, I want a colour strip above the timeline heatmap marking each routine as **compulsory** (D < 30% of athlete's career-best D) or **voluntary**, so that I can tell at a glance which class each column belongs to.
18. As a coach with a DMT or TUM athlete, I want no compulsory/voluntary strip on the timeline heatmap, because those disciplines don't have compulsory routines.
19. As a coach, I want a **Skill × Routine-class summary heatmap** showing mean deduction by skill position grouped by routine class — for TRA: Compulsory / Voluntary Qual / Voluntary Semi / Voluntary Final; for DMT/TUM: Qual / Semi / Final — so that I can read "where my athlete is lacking under pressure, for each kind of routine".
20. As a coach, I want a **Form window** control (past N months, default 12) that updates the Radar, KPIs, scatters, and timeline heatmap, so that I can ask "how is my athlete looking right now?" independently of the cohort filter.
21. As a coach, I want the **Cohort filter** (year_from / year_to) to continue driving the existing eight panels untouched, so that I don't lose any of the analysis I already rely on.
22. As a coach, I want the Form window and the Cohort filter to be visually distinct in the UI and labelled differently, so that I never confuse the comparison-field question with the recency-lens question.
23. As a coach, I want crash-rate displayed without coloured "worry" thresholds, so that I form my own judgement from the visual rather than being nudged by a red tag.
24. As a coach, I want all new panels to share the existing dashboard's visual style (Montserrat font, red/navy/teal palette, Chart.js), so that the Depth section feels like one product with the existing dashboard.
25. As a coach, I want the existing eight panels to remain available below the Depth section, so that I keep the deduction profile, D-progression, qual-vs-final table, score decomposition, ToF distribution, difficulty inflation, head-to-head, and judge-panel variance views I already use.
26. As a coach evaluating a TRA compulsory specialist, I want compulsory routines to count toward the Radar and scatters when their D is genuinely low, because the per-athlete 30% threshold correctly classifies them rather than dropping them as outliers.
27. As a coach, I want the Form indicator's "best 3" pool to exclude crashes, so that recent reliability problems don't depress my reading of current technical capability.
28. As a coach, I want the Radar's outer edge to be a *fixed* sport-empirical ceiling (calibrated once from dataset 99th-percentile), not a moving athlete-personal max, so that the Radar shape means the same thing as my athlete improves over a season.
29. As a coach with two athletes to compare, I want their Radars to share the same axis scale so I can visually compare them — even though this is currently a single-athlete view, the scale choice keeps the option open for a future "compare two athletes" mode.
30. As an analyst looking at the data, I want the same crash predicate to apply consistently across every new visual (Radar, scatters, heatmap timeline, form trend), so that "completed routines only" is a single load-bearing concept and not redefined per panel.

## Implementation Decisions

### Deep modules (extracted from per-panel helpers)

- **`routine_classifier`** — pure-functional module owning the canonical predicates:
  - `is_crash(nelements: int, discipline: str) -> bool` — implements `nelements < expected_for_discipline` with the per-discipline table `{TRA: 10, DMT: 2, TUM: 8}`.
  - `is_compulsory(d_score: float, athlete_best_d: float, nelements: int, discipline: str) -> bool` — TRA-only; returns `nelements == 10 AND d_score < 0.3 * athlete_best_d`; always `False` for DMT/TUM.
  - `classify(nelements, d_score, athlete_best_d, discipline) -> Literal['crash','compulsory','voluntary']` — convenience.
  - No DB access; all inputs are scalars.

- **`rolling_form`** — pure-functional module computing both the form indicator series and the crash rate series from a chronological routine list:
  - `best_n_of_last_k(totals: list[float], crashes: list[bool], n: int = 3, k: int = 10) -> list[float]` — at each index `i`, return the mean of the best `n` values among the last `k` non-crashed totals ending at `i`. Returns `None` (or omits) entries where `< n` completed routines are available in the window.
  - `crash_rate_last_k(crashes: list[bool], k: int = 10) -> list[float]` — at each index `i`, the share of crashes among the last `k` routines ending at `i`.
  - Both functions take parallel arrays indexed by chronological routine order; the caller is responsible for ordering and crash-flagging.

- **`form_window`** — module enforcing the ADR-0001 boundary between cohort filter and form window:
  - `parse_months(param: str | None, default: int = 12) -> int` — normalises the URL query parameter.
  - `filter_routines(routines: list[dict], months: int, now: date | None = None) -> list[dict]` — returns the subset whose `frame_last_start_time_g` is within the past N months from `now`.
  - Module exists to enforce that this filtering is never reused by code that should be using the cohort filter, and vice versa.

- **`radar_scales`** — module owning the sport-empirical axis bounds per discipline (ADR-0002):
  - `bounds_for(discipline: str) -> dict[axis, tuple[float, float]]` — returns calibrated `(min, max)` per axis. Values calibrated once from the dataset's 99th-percentile per (discipline, component) and committed as a constant table; recalibration is a deliberate maintenance event, not a per-request computation.
  - `field_median(db_path: str, discipline: str) -> dict[axis, float]` — returns the field-median reference ring values. Cached in-process for the lifetime of the Flask app; if pre-aggregation becomes desirable later, this is the single cache surface to swap.
  - Inverts "lower is better" axes (Landing, Penalty, HD on TRA) at the boundary so the rest of the codebase can treat all axes as "larger area = better performance".

### Shallow query helpers (appended to `db.py`)

Each function follows the existing pattern: `helper(db_path, given_name, surname, discipline, **filter_args) -> dict` returning a JSON-serialisable payload for the template. Each delegates classification, rolling math, and scale lookups to the deep modules above.

- `radar_data` — returns `{axes, athlete: {pb, top5_mean, p75, p50}, field_median, bounds, n_completed}` for the current form window.
- `form_series` — returns the rolling best-3-of-10 series across the athlete's full career, plus a single "current" value for the KPI tile (form window scoped).
- `crash_series` — returns the rolling crashes-per-10 series across the full career, plus a single "current" value for the KPI tile (form window scoped). Always paired with `form_series`.
- `trade_off_scatter` — returns `{pairs: ['DxE', 'DxToF', 'ExToF'], points: [...], crashes_in_window: int}` for TRA; just `DxE` for DMT/TUM. Each point carries `(x, y, stage)`.
- `heatmap_timeline` — returns `{skills, columns: [{date, d, is_compulsory, deductions: [...]}], n_routines}` ordered chronologically.
- `heatmap_class_summary` — returns `{rows: skill_positions, columns: class_labels, cells: [[mean_deduction, ...], ...]}`. Class labels are discipline-specific per the CONTEXT.md spec.

### Flask route changes

- `/dashboard` keeps its existing query parameters (`given_name`, `surname`, `discipline`, `year_from`, `year_to`, `cmp_given`, `cmp_surname`).
- New query parameter: `form_months` (default 12). Distinct from `year_from`/`year_to` per ADR-0001.
- Existing cohort filter continues to drive the existing eight panels.
- Form window drives the new Depth panels.

### Template changes

- `dashboard.html`: new "Depth" section is inserted between the athlete-header card and the existing `.panel-grid`. Inside it:
  - A KPI row (Form indicator number, Crash rate number, form window selector).
  - The Radar panel (wide).
  - The paired form/crash trend lines (wide, two-line chart).
  - The trade-off scatters (TRA: small-multiples row of three; DMT/TUM: single).
  - Heatmap A (wide, horizontally scrollable when `n_routines > 200`).
  - Heatmap B (compact).
- Existing eight panels are untouched.

### CSS changes

- New tokens for: form-window control styling, KPI tile, heatmap colour ramp (red/heat scale), compulsory-strip two-tone (compulsory=pale, voluntary=dark).
- The radar's four rings use weight/style discipline: PB dotted outermost, Top-5 mean solid filled (headline), p75 thin solid, p50 thin dashed. Field-median reference ring grey dotted.

### JavaScript / chart bindings

- IIFE per new chart inside `dashboard.html`, matching the existing pattern.
- Chart.js core handles radar, line, scatter natively.
- **Heatmap requires `chartjs-chart-matrix` plugin** loaded from CDN. This is a deliberate new dependency for v1 (acceptable: small, single-purpose, widely used). If the plugin proves unsuitable during implementation, an SVG-based heatmap is the fallback.
- The Radar uses Chart.js's radar type with manually-injected scale max from `radar_scales.bounds_for(...)`.
- The form/crash trend pair is one Chart.js line chart with two y-axes (form on the left, crash rate on the right) to keep them visually paired.

### Architectural rules enforced

- The crash predicate is defined in *exactly one place* (`routine_classifier.is_crash`) and used by every consumer. Inline `nelements < N` literals outside the module are a code-smell to be flagged in review.
- The form window and the cohort filter never share a code path. ADR-0001 is enforced by the module boundary: `form_window` filters routines; `cohort_filter` (existing) emits SQL. They have different return types on purpose.
- Radar axis bounds are constants in `radar_scales`, not derived per-request from the data. ADR-0002.
- The compulsory threshold (30% × athlete best D) appears only in `routine_classifier.is_compulsory`. Threshold change is a single-point edit.

## Testing Decisions

Tests assert **external behaviour** of each deep module — given inputs, the function returns the expected output. They do not assert internal implementation (no patches, no spies, no asserting on intermediate state). Prior art lives in `test_dashboard.py` at the repo root, which uses `pytest` and table-driven cases against the live SQLite DB for the existing helpers.

### Modules to unit-test

- **`routine_classifier`** — table-driven tests for `is_crash` and `is_compulsory` covering every discipline, plus edge cases (`nelements = 0`, `nelements = expected − 1`, `nelements = expected`, athlete with zero best D, compulsory routine with low D, voluntary routine with low D, DMT/TUM rejection of compulsory). Pure functions, no DB needed.
- **`rolling_form`** — table-driven tests for `best_n_of_last_k` and `crash_rate_last_k` covering: synthetic sequences with known answers; the boundary `n_completed < n` where the function declines to emit; alignment of the two series at the same index; a long sequence with intermittent crashes verifying the rolling window slides correctly.
- **`form_window`** — small set of tests covering `parse_months` (valid integer, missing, malformed) and `filter_routines` (routine just inside the window, just outside, with `now` injected for determinism).
- **`radar_scales`** — tests for `bounds_for` returning the documented per-discipline shape with the correct axis set (TRA has 5 axes including ToF/HD; DMT/TUM have 4 with Penalty). `field_median` is tested for cache behaviour: identical successive calls return the same dict without re-querying (mock the DB connection).

### Modules NOT separately tested (rationale)

- The shallow per-panel query helpers (`radar_data`, `form_series`, etc.) are tested via the existing `test_dashboard.py` smoke-test pattern — invoke against the live DB, assert structure and reasonable ranges, not exact values. Most of their logic lives in the deep modules that already have unit tests.
- The Flask route gets one extension to `test_dashboard.py`: hit `/dashboard?given_name=X&surname=Y&form_months=12`, assert HTTP 200 and that the response contains the expected new panel IDs (`#c-radar`, `#c-form-trend`, `#c-crash-trend`, `#c-scatter-*`, `#c-heatmap-timeline`, `#c-heatmap-class`).
- Chart.js bindings are not unit-tested (no browser in the environment); existing dashboard's precedent is to validate JSON payload shape server-side and verify charts manually in a browser.

## Out of Scope

- **SYN discipline** — excluded by the existing dashboard's scope and unchanged here.
- **Cross-athlete comparison on the Radar** — the Radar's absolute scale (ADR-0002) is designed to support future side-by-side comparison, but the v1 view shows one athlete at a time. The existing head-to-head panel stays for cross-athlete work.
- **Configurable form indicator window** — the 3-of-10 ratio and the form-window default of 12 months are fixed for v1. Adjustability is deferred until there's evidence the defaults are wrong.
- **Per-stage / per-routine-class crash rate breakdown** — the dashboard surfaces overall crash rate in the form window plus the rolling line. A breakdown by qual/final/compulsory was considered (Q7) and explicitly deferred.
- **Coloured worry thresholds on crash rate** — explicitly rejected; the visual is the signal.
- **Heatmap C (athlete-vs-field delta)** — considered as a way to show "where the athlete is lacking *relative to peers*" but deprioritised; the user prefers the absolute deduction view.
- **Pre-aggregation / indexes / materialised views for performance** — speed is not critical per the existing dashboard's stated stance; live per-request SQL continues.
- **Trimming or restructuring the existing eight panels** — Q8 resolved to a single long page with the Depth section appended on top. The existing panels are not touched.
- **Athlete-identity disambiguation** — name-based matching with the existing `_athlete_filter` (partial `LIKE`) is unchanged. A loose surname can still merge distinct people; routine count + representing on the header card remains the visible cue.
- **DMT/TUM D-band calibration** — not required because the compulsory/voluntary split is TRA-only. DMT/TUM heatmap B columns are stage-only.

## Further Notes

- The two ADRs `docs/adr/0001-form-window-separate-from-cohort-filter.md` and `docs/adr/0002-radar-uses-sport-empirical-absolute-scale.md` should be read before implementation. They explain the two architectural decisions a future maintainer is most likely to "fix" by mistake.
- `CONTEXT.md` carries the canonical glossary used throughout this PRD: Crash, Radar, Form indicator, Crash rate, Cohort filter, Form window, Compulsory vs voluntary, Trade-off scatters, Skill heatmaps. The PRD's terminology must stay in lockstep with that glossary.
- The sport-empirical axis bounds in `radar_scales` need a one-shot calibration step before the radar is meaningful — a small script that queries the 99th-percentile per (discipline, component) and emits the constant table. That script's output is committed; the script itself can live in `tools/` or be inlined as a `__main__` block on `radar_scales`.
- The `chartjs-chart-matrix` CDN dependency is the only new third-party JS this PRD introduces. If the project prefers to avoid it, an SVG-rendered heatmap (server-side rendered grid of coloured `<div>`s) is a viable fallback at the cost of interactivity.
- Crash predicate at the SQL boundary: when filtering at SQL time for performance, the predicate is `CAST(frame_nelements AS INTEGER) >= ?` with the expected element count from `routine_classifier`. The Python-side `is_crash` and any SQL fragment that filters by `nelements` must stay in lockstep (same pattern as the existing `rescale_execution` / `E_SCORE_SQL` twins).
