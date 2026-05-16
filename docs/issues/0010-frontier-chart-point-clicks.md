# Frontier chart-point click navigation

## What to build

Wire every data point on the four **Elite frontiers** canvases to
navigate to the drill-down page (#0009) for the corresponding
`(metric, year, discipline, gender)` partition. After this slice, the
2×2 grid stops being a read-only chart and becomes the discoverability
entry point for the drill-down.

Scope — all four canvases at once, no staged rollout:

| Canvas ID            | Lines       | Click sends user to                              |
|----------------------|-------------|--------------------------------------------------|
| `c-frontier-d-m`     | TRA/DMT/TUM | `/frontier?metric=d&year=…&discipline=…&gender=M` |
| `c-frontier-d-f`     | TRA/DMT/TUM | `/frontier?metric=d&year=…&discipline=…&gender=F` |
| `c-frontier-tof-m`   | TRA only    | `/frontier?metric=tof&year=…&discipline=TRA&gender=M` |
| `c-frontier-tof-f`   | TRA only    | `/frontier?metric=tof&year=…&discipline=TRA&gender=F` |

For D-frontier canvases, the clicked dataset's label (`'TRA'` / `'DMT'`
/ `'TUM'`) selects `discipline`. For ToF-frontier canvases, `discipline`
is always `'TRA'`. `year` comes from the clicked point's label;
`gender` and `metric` are derived from the canvas ID at chart-init
time and closed over by the handler.

Implementation note (kept terse — the template already constructs
charts via `drawD` / `drawToF` helpers from #0008): each chart config
gains an `onClick` handler that uses Chart.js's
`chart.getElementsAtEventForMode(event, 'nearest', { intersect: true }, true)`
to resolve the clicked point's `datasetIndex` + `index`, builds the URL,
and assigns `window.location.href`. Empty-bucket points (`null` in the
series) are not clickable — `getElementsAtEventForMode` returns no hit
for null data, so they fall through naturally.

**No on-page hint** (no caption, no cursor change, no tooltip text).
This is a deliberate choice from the design discussion — keep the panel
visually unchanged; let interaction surface itself. Future polish can
add discoverability if usage data suggests users miss the affordance.

## Acceptance criteria

- [ ] Each of the four `c-frontier-*` canvases has an `onClick` handler
      that navigates to `/frontier?metric=…&year=…&discipline=…&gender=…`
      for the clicked point.
- [ ] D-frontier canvases pick `discipline` from the clicked dataset's
      label; ToF-frontier canvases hard-code `discipline=TRA`.
- [ ] `gender` and `metric` are derived from the canvas ID, not from
      user state, so the wiring stays correct if Chart.js dataset
      ordering changes.
- [ ] Clicking a null/empty data point is a no-op (no navigation, no
      error).
- [ ] The URL constructed for a point that's already known to land on a
      valid drill-down (e.g. `metric=d, year=2018, discipline=TRA,
      gender=M`) loads HTTP 200; the URL constructed for any chart
      point on `c-frontier-tof-*` always uses `discipline=TRA` (so the
      tof-on-DMT 404 from #0009 cannot be reached via a chart click).
- [ ] No visual change to the panel chrome (no caption added, no
      cursor-pointer hover, no tooltip-text augmentation).
- [ ] `pytest -q` exits 0; the existing dashboard panel-render tests
      still pass (no template structure change beyond JS handlers).

## Blocked by

- #0009 (the drill-down route must exist for chart clicks to land on a
  real page; otherwise clicking produces a 404 on a route that doesn't
  yet exist).
