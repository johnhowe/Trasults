# CONTEXT

Glossary of domain terms for TRASULTS. Keep this a glossary, not a spec.

## Core units

- **Routine** — one performed exercise; the canonical unit of analysis. One DB row
  (a `frame`) = one routine. All dashboard metrics are computed per routine unless
  stated otherwise. In TRA qualification an athlete performs two routines (a
  compulsory and a voluntary); these are two separate routines/rows.
- **Performance** — an athlete's entry in one stage of one competition, i.e. the
  1–2 routines grouped together. The DB's `performance_*` columns hold this rollup
  (e.g. `performance_mark_ttt_g` is shared across an athlete's routines in a stage).
  Secondary/derived for the dashboard.
- **Frame** — the DB's internal name for a routine row. Synonym of routine; prefer
  "routine" in UI and docs.

## Disciplines

- **TRA** — Trampoline (individual). **DMT** — Double Mini-Trampoline.
  **TUM** — Tumbling. **SYN** — Synchronised trampoline (110k rows but historically
  unimplemented in the CLI).

## Score components

Canonical UI labels are the abbreviations; full names live in tooltips.

- **D-score** (D) — difficulty. Column `frame_difficultyt_g`.
- **E-score** (E) — execution. Column `esigma_sigma`; needs rescale (some rows
  stored ×10 or ×100, see `get_execution` in `db.py`).
- **ToF** — time of flight, seconds. Column `t_sigma`. TRA only.
- **HD** — horizontal displacement. Column `h_sigma`. TRA only.
- **Landing** — landing deduction. Column `esigma_l`.
- **Pen** — penalty. Column `frame_penaltyt`.
- **Routine score** — the routine total. Column `frame_mark_ttt_g`. The canonical
  "score"; never call a bare number a "score" without saying which component.
- **Per-skill deduction** — execution deduction for skill *n*. Columns
  `esigma_s1`..`esigma_s10` (TRA), `esigma_s1`..`esigma_s2` (DMT),
  `esigma_s1`..`esigma_s8` (TUM).

## Dashboard terms (/dashboard route)

- **Cohort** — the comparison population a selected athlete is measured against:
  all routines of a discipline, optionally narrowed by a year range and/or stage
  (`cohort_filter` in `db.py`). Every athlete-vs-field panel uses a cohort.
- **Frontier** — the mean of a metric's *top N* values in a season, ranked
  **within each (discipline, gender) partition**. Two metrics carry frontiers:
  D-score (difficulty inflation) and ToF (TRA only — air-time inflation).
  Used instead of a plain seasonal mean because the dataset's population
  changes year to year (see Data caveats), so a mean tracks population
  change, not capability; the top-N frontier is robust to that dilution.
  The partition is load-bearing: men's elite D is consistently above
  women's, so a global top-N would produce a near-empty women's frontier —
  ranking within each gender yields equally-sized buckets and lets both
  stories emerge. Implementation owns this in the SQL window function
  (`PARTITION BY yr, discipline, gender`); see [[Gender]] for the inference
  rule. `top_n = 50` is fixed for v1. Surfaced on the overview page (no
  athlete selected) as the **Elite frontiers** 2×2 grid: rows = metric
  (D / ToF), columns = gender (M / F).
- **Radar** — the athlete-overview chart with one axis per score component:
  TRA = D, E, ToF, HD, Landing; DMT/TUM = D, E, Landing, Penalty. Penalty is its
  own axis on DMT/TUM where penalties are routine, but folded into Landing on
  TRA where they're rare. "Lower is better" axes (Landing, Penalty) are inverted
  so larger area always means stronger performance. Computed on **completed
  routines only**, scoped to the **lookback window** (not the cohort filter).
  Axes share one absolute scale: **centre = 0, outer edge = sport-empirical
  ceiling** (calibrated once from the dataset's 99th-percentile per discipline).
  A static **field-median ring** is drawn as a grey reference so an athlete who
  is far below the elite ceiling is still positioned legibly.
  Four athlete rings overlay the dial: **PB** (axis-wise personal max),
  **Top-5 mean** (axes averaged over the athlete's 5 best routines by total
  score — the filled headline ring), **p75**, **p50**. Percentile rings need a
  minimum window sample (n ≥ 10) and are suppressed below that.
- **Cohort filter** vs **lookback window** — two different time concepts. The
  cohort filter (year_from/year_to) bounds the comparison population for
  cross-athlete panels (deduction profile, decomposition, qual-vs-final). The
  lookback window (past N months, athlete-scoped) bounds the radar and the
  rolling best-of-N indicators — "how is the athlete looking right now." They
  are independent controls and should not be conflated in code or UI copy.
  Avoid the word "form" for the time window: in trampoline judging "form"
  means execution body-shape, which is a separate concept (E-score, [[E-score (E)]]).
- **Rolling peak** — mean of an athlete's **best 3 routine totals from their
  last 10 completed routines** (`frame_mark_ttt_g`). 3-of-10 is fixed for v1.
  Surfaced two ways: a KPI tile showing the current value within the lookback
  window, and a trend line plotting the rolling series across the athlete's
  full career so peaks/slumps/plateaus are visible. Computed on completed
  routines only — crashes are excluded from the "best 3" pool, so a string of
  crashes shows up as a stalled trend line, not a collapsed one. Deliberately
  *not* called "form": that word collides with the execution-form meaning of
  E-score, and this metric is a routine-total summary, not an execution one.
- **Crash rate** — share of crashes (per [[Crash]]) in the **lookback window**
  for the KPI tile, and **crashes per last 10 routines** as a rolling line over
  the athlete's career. The rolling line shares its window with the rolling
  peak so the two trends pair visually: peak going up = good, crashes going up
  = bad. No coloured thresholds — the line is the signal.
- **Trade-off scatters** — small-multiples view of pairwise component
  relationships, one dot per completed routine, coloured by stage (qual/final).
  TRA shows three: **D×E**, **D×ToF**, **E×ToF**. DMT/TUM show **D×E** only.
  No regression or quadrant overlays — the cloud carries the story. Crashes are
  excluded from the cloud and surfaced as a "crashes this window: N" caption.
  E×ToF is **not** redundant with D×ToF: ToF is the *potential* for high E
  (more air = more time to display form), but doesn't guarantee it; the
  E×ToF scatter separates "athletic ceiling" from "in-flight cleanness".
- **Compulsory** vs **voluntary routine** — *TRA only*. The compulsory is an
  optional prescribed routine some athletes still perform (low/zero D, judges
  score form). DMT and TUM have no compulsory — all routines are voluntary.
  There is no DB column for this; inferred by the predicate
  `nelements == 10 AND D < 0.3 × athlete_career_best_D`. The threshold is
  per-athlete so a junior with PB D=4 (threshold ≈ 1.2) and an elite with PB
  D=18 (threshold ≈ 5.4) are both classified correctly. Crashes never classify
  as compulsory because nelements < 10.
- **Skill heatmaps** — two views of per-skill execution deductions:
  *Heatmap A* (timeline) — rows = skill positions, columns = every completed
  routine chronologically, cell = deduction at that skill. TRA gets a
  two-tone strip above the columns marking compulsory vs voluntary; DMT/TUM
  omit the strip. Horizontal scroll when n > 200.
  *Heatmap B* (class summary) — rows = skill positions, columns = routine
  class. TRA: Compulsory / Voluntary Qual / Voluntary Semi / Voluntary Final.
  DMT/TUM: Qual / Semi / Final (no compulsory split). Cell = mean deduction
  in that class.
- **Panel spread** — disagreement across the six judge execution scores on one
  routine: `max(e1..e6_sigma) - min(e1..e6_sigma)`. Judges are anonymous and
  positional, so this is the only judging metric available.
- **Crash** — a routine cut short, defined as `CAST(frame_nelements AS INT) <
  expected_elements_for_discipline` (TRA = 10, DMT = 2 per pass, TUM = 8). A
  crash is a structural failure, not a low score; a clean low-D routine is not
  a crash. Crashes are common in TRA — performance metrics (means, frontiers,
  rolling-best) are computed on **completed routines only**; reliability
  metrics (crash rate, longest clean streak) use **all routines**. This split
  prevents a few crashes from distorting performance averages while still
  surfacing crash frequency as its own signal.

## Inference rules

- **Gender** — `routine_gender.infer(competition_title) -> 'M' | 'F'`.
  Inferred via a multilingual **strict-female lexicon** plus a small
  **male-override** list to disambiguate mixed wording. Strict-F prefixes
  (`fem`, `wom`, `gir`, `ladies`) cover Romance languages too because they
  match `Feminino` (PT), `Femenil/Femenino` (ES), `Féminin/Femmes` (FR),
  etc. Non-prefix entries cover Russian (`Дев`, `Женщины`, `Юниорки`),
  Japanese (`女`), Finnish (`tytöt`, `naiset`), Danish (`dam`), Swedish
  (`flickor`), Estonian (`tüdrukud`), plus a partial `töt`. Anything not
  matching F falls through to `'M'`. Two-state (no `None`) because at the
  top of the D-score distribution untagged routines are overwhelmingly
  male, so the fallback is empirically safe **as long as the female lexicon
  stays comprehensive**. Adding a language to the lexicon is the only
  maintenance touchpoint; silent under-coverage of F mis-tags women's
  routines as male. The module exposes both a SQL `CASE` expression
  (`gender_case_sql`) for `PARTITION BY` use and a Python `infer` for
  per-routine inference / tests. The CLI/web `--female` / `--male`
  filters and the [[Frontier]] queries share this single lexicon.

## Data caveats

- Table `routines` has **no column type affinities** — values may be TEXT or REAL
  inconsistently. Queries must `CAST` numeric columns.
- `athlete_date_of_birth` is mostly unusable: sentinels `01/01/0001`, `01/01/1900`,
  and year-only `01/01/YYYY` dominate. Do not build age cohorts from it.
- `person_representing` has mixed grain — nation codes at international events,
  club/region names at domestic ones. There is no clean national-federation column.
- **Athlete identity is name-based** — `(person_given_name, person_surname)` with
  no athlete ID. A surname-only lookup merges distinct people; the dashboard
  exact-matches whatever names are supplied (consistent with the existing
  `/athlete` route) and shows routine count + representing so a merge is visible.
- The dataset's **population shifts heavily across seasons** — 2013 has ~2k
  routines (elite-international only), 2025 has ~163k (dominated by domestic
  junior routines). Any cross-year *mean* is confounded by this; prefer frontier
  or fixed-cohort comparisons.
