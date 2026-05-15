# Heatmap B — Skill × Routine-class summary

## Parent

PRD: `docs/prd/0001-dashboard-depth-view.md`

## What to build

The **Skill heatmaps → Heatmap B (class summary)** view from CONTEXT.md. Rows = skill positions. Columns = routine class:

- TRA: **Compulsory**, **Voluntary Qual**, **Voluntary Semi**, **Voluntary Final** (4 columns).
- DMT / TUM: **Qual**, **Semi**, **Final** (3 columns — no compulsory split in those disciplines).

Cell = mean deduction at that (skill position, routine class) across the form window's completed routines. This is the "where the athlete is lacking, for each kind of routine" view that pairs with the timeline heatmap.

Reuses the `chartjs-chart-matrix` plugin loaded by slice #5 and the same red-heat colour ramp for visual consistency. Empty cells (a class with no routines in the window) render as a neutral grey, not pure white, so the absence is distinguishable from "deduction = 0".

A shallow `heatmap_class_summary(db_path, given_name, surname, discipline, form_months)` helper returns `{rows: [...], columns: [...], cells: [[mean_deduction | None, ...], ...], counts: [...]}`. `counts` carries the n per column so a tiny-sample class can be visually de-emphasised.

## Acceptance criteria

- [ ] Heatmap renders 4 columns for TRA, 3 for DMT/TUM.
- [ ] Compulsory column on TRA correctly uses `routine_classifier.is_compulsory` (per-athlete 30% threshold).
- [ ] Empty cells distinguishable from zero-deduction cells.
- [ ] Column n-counts visible to the user (caption, tooltip, or subscript) so low-sample columns aren't over-interpreted.
- [ ] Uses the same red-heat ramp as Heatmap A.
- [ ] Smoke test verifies the panel ID renders with the correct column count per discipline.

## Blocked by

- #5 (shares the `chartjs-chart-matrix` CDN load and the deduction-cell rendering style).
