# Issue Implementation Progress

- [x] docs/issues/0001-kpi-tiles-form-window-control.md
  Added pure-functional `routine_classifier`, `rolling_form`, `form_window` modules
  with unit tests. Wired a `form_kpi_data` helper in `db.py` and `/dashboard` now
  accepts `?form_months=N` (default 12) with a teal-accented selector, rendering
  Form-indicator and Crash-rate KPI tiles above the existing eight panels.
- [x] docs/issues/0002-form-crash-trend-lines.md
  Added `db.form_and_crash_series` (career chronological form + crash-rate
  arrays) and a wide Depth-section trend panel that renders both on a shared
  x-axis with Chart.js dual y-axes (form navy / crashes red), polite empty
  state under 10 routines. New tests cover the consecutive-crash invariant
  (form plateau / crash climb) and panel smoke render.
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
