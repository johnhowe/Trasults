# Heatmap A — Skill × Routine timeline

## Parent

PRD: `docs/prd/0001-dashboard-depth-view.md`

## What to build

The **Skill heatmaps → Heatmap A (timeline)** view from CONTEXT.md. Rows = skill positions (TRA 1–10, DMT 1–2, TUM 1–8). Columns = **every completed routine** in the lookback window, ordered chronologically (oldest left → newest right). Cell colour = execution deduction at that skill position (red-heat ramp; deeper red = larger deduction).

TRA gets a two-tone **compulsory / voluntary strip** above the columns — pale for compulsory (per `routine_classifier.is_compulsory`), dark for voluntary. The strip explains why some columns have suspiciously clean skill-1 cells without rearranging the chronology. DMT and TUM omit the strip entirely (no compulsory in those disciplines).

Horizontal scroll within the panel when n_routines > 200. Crashed routines are excluded from the columns entirely (consistent with "completed routines only" — they have incomplete skill data anyway).

Introduces the `chartjs-chart-matrix` CDN dependency (matrix-heatmap support is not in Chart.js core). The plugin is loaded alongside the existing Chart.js CDN script tag.

A shallow `heatmap_timeline(db_path, given_name, surname, discipline, lookback_months)` helper returns `{skills: [...], columns: [{date, d, is_compulsory, deductions: [...]}], n_routines}`. The `is_compulsory` flag is `False` for DMT/TUM.

## Acceptance criteria

- [ ] `chartjs-chart-matrix` plugin loads via CDN alongside Chart.js core.
- [ ] Heatmap renders for any athlete with ≥ 1 completed routine in the lookback window.
- [ ] TRA athletes see a compulsory/voluntary strip; DMT and TUM athletes do not.
- [ ] Columns are ordered strictly by routine timestamp ascending.
- [ ] Cells use a red-heat colour ramp; legend shows the deduction range.
- [ ] Horizontal scroll engages when n > 200, without reflowing the rest of the page.
- [ ] Crashes are not rendered as columns.
- [ ] Smoke test verifies the panel ID renders and the column count matches `n_routines`.

## Blocked by

- #1 (requires both `is_crash` and `is_compulsory` from `routine_classifier`).
