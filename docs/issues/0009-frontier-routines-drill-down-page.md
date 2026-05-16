# Frontier-routines drill-down page

## What to build

A new `/frontier` route that lists the top-N routines behind a single
[[Frontier]] point — the underlying data of one cell in the **Elite frontiers**
2×2 grid (#0008; CONTEXT.md → *Frontier*).

The route is a sport-wide deep link, keyed by the partition tuple
`(metric, year, discipline, gender)`:

```
/frontier?metric=d&year=2018&discipline=TRA&gender=M
```

It mirrors the convention of every other dashboard route (`/competition`,
`/leaderboard`, `/athlete`, `/compare`) — query-string params, no session
state, bookmarkable, no JS required to land on the page.

The page renders one table — no summary chips, no mini-chart, no
cross-metric panel. Each row is one of the top-N routines that fed the
frontier mean, ranked desc by the metric:

- **Rank** — 1..N (where N ≤ `top_n`).
- **Athlete** — `person_given_name` + `person_surname`, linked to
  `/athlete?given_name=…&surname=…` for purpose-(c) drill-into. The
  athlete-identity caveat from CONTEXT.md → *Data caveats* still applies
  (no athlete ID; name collisions surface on the athlete page).
- **Representing** — `person_representing` (the federation/club/region
  string; mixed-grain per CONTEXT.md).
- **Event** — `event_title`, linked to `/competition?event=…` using the
  same `LIKE` semantics the existing route uses.
- **Date** — `frame_last_start_time_g[:10]`, `YYYY-MM-DD`.
- **Value** — the routine's D-score (or ToF, depending on `metric`).

A new db helper backs the route:

```python
def frontier_routines(db_path, metric, year, discipline, gender, top_n=50):
    """Top-N routines that defined a single frontier point.
       metric ∈ {'d','tof'};  discipline ∈ {'TRA','DMT','TUM'};
       gender  ∈ {'M','F'}.   Returns
         {'metric','year','discipline','gender','top_n','n','rows':[…]}
       with each row {rank, given_name, surname, representing,
                      event_title, date, value}."""
```

It reuses `routine_gender.gender_case_sql()` (same lexicon as the
existing frontier helpers and the CLI `--female`/`--male` filter — #0007)
and the existing `_BASE_FILTER` plus the `< 25` metric validity bound.
**No new filters** — same test-event exclusion as the rest of the
overview page.

Behaviour at the partition boundaries (the only non-obvious contract):

- Partition with `N < top_n` routines → return all N rows (rank 1..N).
  The existing chart already accepts thin years (see `counts` in the
  current `difficulty_frontier` payload); the drill-down inherits the
  same low-n behaviour and renders fewer rows.
- Partition with `N = 0` → empty `rows`, page renders an empty-state
  message. **Does not 404** — the partition is structurally valid; a
  user reached the page by typing the URL or following a stale link.
- Invalid `metric` / `discipline` / `gender` enum value → **404**.
- `metric='tof'` with `discipline ≠ 'TRA'` → **404** (ToF is meaningless
  for DMT/TUM; `tof_frontier` only populates `series['*']['TRA']`).

No ADR is needed — this is a UI affordance over an existing concept, not
a new architectural call. CONTEXT.md → *Frontier* already documents the
drill-down's existence in one sentence; the implementation just realises it.

## Acceptance criteria

- [ ] `db.frontier_routines(db_path, metric, year, discipline, gender, top_n=50)`
      exists and returns the documented payload shape.
- [ ] Helper uses `routine_gender.gender_case_sql()` and `_BASE_FILTER`;
      no new lexicon inlining, no new test-event filters.
- [ ] Helper enforces the metric's validity bound (`> 0 AND < 25`) for
      both `d` and `tof`, matching `difficulty_frontier` / `tof_frontier`.
- [ ] Smoke check against the live DB: the `rows` returned for
      `(metric='d', year=2018, discipline='TRA', gender='M', top_n=50)`
      have mean ≈ 17.85 (matches `difficulty_frontier`'s point for the
      same partition, ±0.05); `len(rows) == 50`.
- [ ] Low-n smoke: `(metric='tof', year=2013, discipline='TRA', gender='F')`
      returns ≥1 row; `len(rows)` matches the `counts` value in
      `tof_frontier`.
- [ ] `/frontier?metric=d&year=2018&discipline=TRA&gender=M` returns
      HTTP 200 and renders a six-column table (Rank, Athlete,
      Representing, Event, Date, Value) with 50 rows.
- [ ] Athlete cell anchors `/athlete?given_name=…&surname=…`; event
      cell anchors `/competition?event=…`. URL-encoding handles Cyrillic /
      multi-byte names without breaking.
- [ ] `/frontier?metric=tof&year=2018&discipline=DMT&gender=M` returns
      HTTP 404.
- [ ] Any invalid enum value (`metric=foo`, `gender=X`, `discipline=SYN`)
      returns HTTP 404.
- [ ] An empty-but-valid partition returns HTTP 200 with an empty-state
      message, not 404.
- [ ] `pytest -q` exits 0 with new tests covering the helper payload
      and the route response codes (404 cases included).

## Blocked by

None — can start immediately. (#0007 and #0008 already shipped; the
helpers and lexicon they introduced are the substrate this builds on.)
