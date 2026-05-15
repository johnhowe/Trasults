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
- [ ] docs/issues/0003-radar-chart.md
- [ ] docs/issues/0004-trade-off-scatters.md
- [ ] docs/issues/0005-heatmap-timeline.md
- [ ] docs/issues/0006-heatmap-class-summary.md
