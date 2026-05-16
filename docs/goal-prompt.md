# `/goal` prompt — complete pending issues

Paste the block below after `/goal ` in Claude Code. It targets the two unshipped issues (`0007`, `0008`) in dependency order. Issues `0001`–`0006` are already merged (see `git log`).

---

```text
/goal Implement the two unshipped issues in docs/issues/ in dependency order — 0007 first, then 0008 — until both are merged on main with their acceptance criteria satisfied. Stop after 20 turns if not complete.

Definition of done (the condition the evaluator checks):

1. Issue 0007 (routine_gender module + CLI rewire) — DONE when ALL hold:
   - File `routine_gender.py` exists at repo root and exports `gender_case_sql`, `gender_filter_sql`, `infer`, plus the lexicon constant.
   - `db.py` build_query no longer inlines the gender regex; the dead `\bf\)` entry is gone (`git grep '\\\\bf\\\\)' db.py` returns nothing).
   - `pytest test_routine_gender.py -q` exits 0 with table-driven cases covering English, Portuguese, Spanish, French, German, Russian, Japanese, Finnish, Danish, Swedish, Estonian, Chinese.
   - `python inspect_trasults.py --tra --female --since 2024-01-01 --limit 1` returns a non-empty row.
   - `git log -1 --pretty=%s` for the 0007 commit references issue 0007 and `git status` is clean before moving on.

2. Issue 0008 (Elite frontiers 2×2 overview section) — DONE when ALL hold:
   - `db.py` exposes `difficulty_frontier(db_path, top_n=50)` and `tof_frontier(db_path, top_n=50)` with the gender-first payload shape from the issue; the old `difficulty_inflation` is gone (`git grep difficulty_inflation` returns nothing in code, only ADRs/issue history).
   - Both helpers partition via `routine_gender.gender_case_sql()` — `git grep -n "PARTITION BY" db.py` shows gender in the partition clause; the lexicon is NOT re-inlined in `db.py`.
   - Smoke check via `python -c "from db import difficulty_frontier; d=difficulty_frontier('<db_path>'); print(d['series']['F']['TRA'][d['years'].index(2013)], d['series']['M']['TRA'][d['years'].index(2018)])"` prints values approximately 12.4 and 18.0 (±0.5).
   - The overview template renders the four canvas IDs `#c-frontier-d-m`, `#c-frontier-d-f`, `#c-frontier-tof-m`, `#c-frontier-tof-f` under an "Elite frontiers" section heading; `#c-inflation` is no longer in the template.
   - `Judge-panel variance` panel still present below the new section.
   - `progress.md` has new entries naming `difficulty_inflation → difficulty_frontier` rename and the new `tof_frontier`.
   - `pytest -q` exits 0 (Flask import failures predating this work are tolerated only if they were red on `main` before starting — run `git stash && pytest -q && git stash pop` once at the start to record the baseline and surface that delta in the transcript).

Working constraints:
- Read CONTEXT.md, docs/adr/0003-*.md, docs/adr/0004-*.md, docs/issues/0007-*.md, docs/issues/0008-*.md before writing code; honour the domain glossary and ADRs as load-bearing.
- One issue per commit. Commit message subject must include the issue number (e.g. "feat: routine_gender module (0007)"). Do not amend.
- Do NOT modify the issue files themselves, the ADRs, or CONTEXT.md unless an acceptance criterion explicitly requires it (0008 requires a progress.md update; CONTEXT.md and ADRs are frozen for this run).
- Do NOT add the test-event sanitisation, D-ceiling tightening, or any "foundation" work the user already rejected — only `_BASE_FILTER` + `< 25` bounds for D and ToF.
- Trust the existing `_BASE_FILTER` for test-event exclusion. Do not add new filters.
- Treat the Female lexicon as the single source of truth — `gender_case_sql` and `gender_filter_sql` must share one constant.
- If a smoke check fails because the live DB path is unknown, locate the `.sqlite` via `find . -maxdepth 3 -name '*.sqlite'` and use the first hit; do NOT fabricate a fixture.
- Surface every check's command and output in the transcript so the evaluator can read the proof. After each issue: run the acceptance commands one-by-one and quote the exit codes / output in your final message of that turn.
- If you hit a real blocker (missing DB, ambiguous schema, contradictory ADR), state the blocker plainly and stop — do not invent a workaround.
```

---

## Why this shape

- **One measurable end state per issue** — file existence, grep emptiness, pytest exit code, smoke-check numeric values. The evaluator can read each from the transcript.
- **Turn cap** — `stop after 20 turns` bounds runaway loops; 0007 is small, 0008 is the larger slice, 20 leaves headroom for debugging.
- **Constraints** capture the prior rejections from grilling (no over-engineering, no extra sanitisation, no ADR edits) so the autonomous run doesn't re-litigate them.
- **Dependency order is encoded in the goal** — 0007's clean-tree commit is gated before 0008 starts, mirroring the issue's "Blocked by" field.
- **Numeric smoke checks** (`≈ 12.4`, `≈ 18.0`) calibrate that the partition is actually retaining women's routines, not silently emptying — the load-bearing failure mode from ADR-0004.
```

Use this with `/goal` on a fresh session; recommended effort `xhigh` per the prompting guide for agentic coding.
