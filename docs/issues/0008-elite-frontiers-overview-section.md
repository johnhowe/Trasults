# "Elite frontiers" 2×2 overview section

## What to build

A new **Elite frontiers** section at the top of the `/dashboard` overview state (no athlete selected) — a 2×2 grid of frontier charts that tells the sport's evolution story over time (CONTEXT.md → *Frontier*; ADR-0004).

- **Top row — D-frontier**: two side-by-side line charts (Men | Women). Each chart has three lines (TRA, DMT, TUM). Y = mean of the top-50 D-scores per year **within that (discipline, gender) partition**.
- **Bottom row — ToF-frontier**: two side-by-side line charts (Men | Women). Each chart has one line (TRA only — ToF is meaningless for DMT/TUM). Y = mean of the top-50 ToFs per year within that (TRA, gender) partition.

The single-pass-per-gender ranking is the load-bearing implementation decision (ADR-0004): a `ROW_NUMBER() OVER (PARTITION BY year, discipline, gender ORDER BY metric DESC)` then `AVG()` over the top-50 per partition. Global ranking followed by a gender split would produce a near-empty women's frontier in this dataset.

The existing `difficulty_inflation` function and the existing single-chart "Year-over-year difficulty inflation" panel are replaced:

- `difficulty_inflation(db_path, top_n=50)` → `difficulty_frontier(db_path, top_n=50)`. Returns `{years, top_n, series: {'M': {TRA: [...], DMT: [...], TUM: [...]}, 'F': {TRA: [...], DMT: [...], TUM: [...]}}, counts: {...}}` — gender-first nesting matches the chart layout.
- New `tof_frontier(db_path, top_n=50)`. Returns `{years, top_n, series: {'M': {TRA: [...]}, 'F': {TRA: [...]}}, counts: {...}}`. Only TRA is populated.
- The overview template's `panel-grid` is restructured: the section heading "Elite frontiers" wraps the 2×2 grid; *Judge-panel variance* sits below as its own section (unchanged content).

Both helpers consume `routine_gender.gender_case_sql()` for the `PARTITION BY gender` step — single source of truth for the lexicon (#0007).

Filtering reuses the existing `_BASE_FILTER` plus the metric's validity bound (`frame_difficultyt_g > 0 AND < 25` for D; `t_sigma > 0 AND < 25` for ToF). Test events are already excluded via `_BASE_FILTER`'s `NOT LIKE '%test%'` clauses; no additional sanitisation.

Empty `(year, discipline, gender)` buckets render as `None` placeholders in the series, identical to today's `difficulty_inflation` handling.

## Acceptance criteria

- [ ] `difficulty_frontier` returns gender-partitioned top-N means; ranking is within each (year, discipline, gender) bucket, not global.
- [ ] `tof_frontier` returns the parallel ToF payload, TRA-only, gender-partitioned.
- [ ] Both helpers use `routine_gender.gender_case_sql()` for partitioning — the lexicon is not duplicated inline.
- [ ] Smoke test against the live DB: 2013 TRA women's D-frontier returns a non-empty series with mean ≈ 12.4 (calibrating that the partition is actually keeping women's routines, not silently emptying); 2018 TRA men's mean ≈ 18.0.
- [ ] The overview page renders the 2×2 grid under an "Elite frontiers" section heading.
- [ ] Top row charts each show three lines (TRA/DMT/TUM) using the existing red/navy/teal palette.
- [ ] Bottom row charts each show one line (TRA only).
- [ ] `Judge-panel variance` panel still renders below the new section, unchanged.
- [ ] Smoke test verifies the new panel IDs render (`#c-frontier-d-m`, `#c-frontier-d-f`, `#c-frontier-tof-m`, `#c-frontier-tof-f`) and the existing `#c-inflation` ID is no longer present.
- [ ] `progress.md` updated to reflect the rename `difficulty_inflation → difficulty_frontier` and the new `tof_frontier`.

## Blocked by

- #0007 (requires `routine_gender.gender_case_sql` to partition by gender consistently with the CLI search filter).
