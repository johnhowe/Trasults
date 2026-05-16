# Issue Implementation Progress

- [x] docs/issues/0001-kpi-tiles-lookback-window-control.md
  Added pure-functional `routine_classifier`, `rolling_peak`, `lookback_window`
  modules with unit tests. Wired a `lookback_kpi_data` helper in `db.py` and
  `/dashboard` now accepts `?lookback_months=N` (default 12) with a
  teal-accented selector, rendering Rolling-peak and Crash-rate KPI tiles
  above the existing eight panels.
- [x] docs/issues/0002-rolling-peak-and-crash-trend-lines.md
  Added `db.rolling_peak_and_crash_series` (career chronological peak +
  crash-rate arrays) and a wide Depth-section trend panel that renders both on
  a shared x-axis with Chart.js dual y-axes (peak navy / crashes red), polite
  empty state under 10 routines. New tests cover the consecutive-crash
  invariant (peak plateau / crash climb) and panel smoke render.
- [x] docs/issues/0003-radar-chart.md
  Added `radar_scales` module with calibrated 99th-percentile BOUNDS per
  (discipline, axis), `bounds_for()`, an inversion helper that folds
  "lower is better" axes, and a cached `field_median()` driving the grey
  reference ring. `db.radar_data` returns axes/bounds/field_median plus
  PB / Top-5 mean / p75 / p50 athlete rings (percentile rings suppressed
  below n_completed=10). Dashboard radar panel renders five rings via
  Chart.js with per-axis normalisation to a shared radial scale.
- [x] docs/issues/0004-trade-off-scatters.md
  Added `db.trade_off_scatter` helper returning three pairs for TRA
  (D×E / D×ToF / E×ToF) and a single D×E for DMT/TUM, with crashed
  routines excluded from the cloud and surfaced as a "crashes this
  window" caption. New `panel-scatter` section renders Chart.js scatter
  small-multiples, coloured navy=qual / red=final, with axes locked to
  the radar's sport-empirical bounds for cross-panel visual consistency.
- [x] docs/issues/0005-heatmap-timeline.md
  Added `db.heatmap_timeline` returning skill rows × chronological completed
  routine columns (crashes excluded, TRA columns flagged compulsory via
  `routine_classifier.is_compulsory`, DMT/TUM always voluntary). Wired a
  new `panel-heatmap-timeline` section rendering via the
  `chartjs-chart-matrix` CDN plugin: red-heat cells, TRA-only
  compulsory/voluntary strip, horizontal scroll engaged via `.heatmap-scroll`
  past 200 columns.
- [x] docs/issues/0006-heatmap-class-summary.md
  Added `db.heatmap_class_summary` returning skill rows × class columns
  (TRA: Compulsory / Voluntary Qual / Semi / Final; DMT/TUM: Qual / Semi /
  Final) with mean deductions, `None` for empty classes, and per-column
  counts. New `panel-heatmap-class` section renders via the existing
  `chartjs-chart-matrix` plugin using a shared `heatColor()` ramp;
  neutral grey for `None` cells, n-count chips beneath the canvas
  (amber-highlighted when n<3) so low-sample columns aren't over-read.
- [x] docs/issues/0007-routine-gender-module.md
  Extracted the multilingual female lexicon from `build_query` into a new
  `routine_gender` module exposing three surfaces over one constant:
  `gender_case_sql()` (literal SQL CASE for PARTITION BY), `gender_filter_sql()`
  (parameterised predicate for the CLI/web --female/--male filter), and
  `infer()` (Python-side, total — returns `'M'` or `'F'` for every input
  including `None`). Dropped the dead `\bf\)` regex entry that LIKE never
  honoured. Table-driven tests cover English, Portuguese, Spanish, French,
  German, Russian, Japanese, Finnish, Danish, Swedish, Estonian and Chinese
  titles.
- [x] docs/issues/0010-frontier-chart-point-clicks.md
  Wired an `onClick` handler on each of the four `c-frontier-*` canvases
  via a single `frontierClickHandler(metric, gender, years, disciplines)`
  factory closed over the canvas's metric/gender at chart-init time (so
  the wiring stays correct if Chart.js reorders datasets). D-frontier
  canvases pick discipline from the clicked dataset's slot (TRA / DMT /
  TUM); ToF-frontier canvases hard-code `['TRA']` so the `tof × non-TRA`
  404 from #0009 cannot be reached by a click. Uses
  `chart.getElementsAtEventForMode(..., 'nearest', { intersect: true }, true)`
  so null/empty data points are a natural no-op. No on-page caption /
  cursor / tooltip change — deliberate, per issue. New test asserts the
  handler markers and the ToF discipline-pin are present in the rendered
  overview page.
- [x] docs/issues/0009-frontier-routines-drill-down-page.md
  Added `db.frontier_routines(metric, year, discipline, gender, top_n=50)`
  reusing `routine_gender.gender_case_sql()` and `_BASE_FILTER` with the
  same `>0 AND <25` validity bound as the frontier line helpers; returns
  `None` for structurally invalid partitions (bad enum or `tof × non-TRA`)
  so the route maps cleanly to 404, and a 6-column row payload otherwise.
  New `/frontier` Flask route renders a bookmarkable
  `metric=…&year=…&discipline=…&gender=…` drill-down table with athlete
  cells linking to `/athlete` and event cells to `/competition`; empty
  partitions render an empty-state message instead of 404. Tests cover the
  payload contract, all 404 cases, low-n parity with `tof_frontier` counts,
  and the live `(d, 2018, TRA, M)` smoke (mean ≈ frontier point).
- [x] docs/issues/0008-elite-frontiers-overview-section.md
  Renamed `db.difficulty_inflation` → `difficulty_frontier` and added a
  parallel `tof_frontier` (TRA-only) — both partition the elite top-N by
  `(year, discipline, gender)` via `routine_gender.gender_case_sql()` (no
  re-inlining of the lexicon). Payload now nests gender-first
  (`series['M']['TRA']`, etc.) so the dashboard pivots cleanly. The overview
  template's `#c-inflation` panel is replaced by an **Elite frontiers** 2×2
  grid (rows = D / ToF, columns = M / F → canvases `#c-frontier-d-m`,
  `#c-frontier-d-f`, `#c-frontier-tof-m`, `#c-frontier-tof-f`) with
  `Judge-panel variance` unchanged below.
