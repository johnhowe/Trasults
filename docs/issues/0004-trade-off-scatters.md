# Trade-off scatters

## Parent

PRD: `docs/prd/0001-dashboard-depth-view.md`

## What to build

The **Trade-off scatters** panel from CONTEXT.md → *Trade-off scatters*. Small-multiples view of pairwise component relationships, one dot per completed routine in the lookback window, coloured by stage (qual = navy, final = red).

- TRA: three scatters side-by-side — **D×E**, **D×ToF**, **E×ToF**.
- DMT / TUM: single **D×E** scatter.

No regression lines, no quadrant guides — the cloud carries the story. Crashes are excluded from the cloud and surfaced as a "crashes this window: N" caption beside the panel title.

E×ToF is intentionally included even though ToF feeds into E mechanically — ToF is the *potential* for high E (more air = more time to display form) but doesn't guarantee it; E×ToF separates "athletic ceiling" from "in-flight cleanness".

A shallow `trade_off_scatter(db_path, given_name, surname, discipline, lookback_months)` helper returns `{pairs: ['DxE', 'DxToF', 'ExToF'] | ['DxE'], points: {[pair]: [{x, y, stage}, ...]}, crashes_in_window: int}`.

## Acceptance criteria

- [ ] TRA athletes get three small-multiple scatters; DMT/TUM athletes get one.
- [ ] Points coloured by stage using the dashboard's existing red/navy palette.
- [ ] Crashed routines do not appear as dots; their count appears in a caption.
- [ ] Each scatter uses sport-empirical axis bounds where possible (e.g. D-axis matches radar D bounds, E-axis matches radar E bounds, ToF-axis matches radar ToF bounds) — visual consistency with the Radar.
- [ ] No regression line or quadrant guide overlays (per Q5b).
- [ ] Smoke test verifies the scatter panel IDs render for a TRA athlete and a DMT athlete.

## Blocked by

- #1 (requires `routine_classifier.is_crash` and `lookback_window` from slice 1).
