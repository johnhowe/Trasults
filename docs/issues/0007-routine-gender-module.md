# `routine_gender` module + CLI search rewire

## What to build

A new pure-functional `routine_gender` module that owns the multilingual female lexicon currently inlined in `build_query` (CONTEXT.md → *Gender*; ADR-0003). The module is the single source of truth — both the CLI/web `--female` / `--male` filters and the upcoming [[Frontier]] queries (#0008) consume it.

The module exposes three surfaces over one lexicon constant:

- `gender_case_sql(column: str = 'competition_title') -> str` — returns a SQL `CASE WHEN … THEN 'F' ELSE 'M' END` expression usable in `SELECT` / `GROUP BY` / `PARTITION BY`. Used by the frontier queries (#0008) to label every routine with a deterministic gender.
- `gender_filter_sql(gender: str) -> (sql_fragment: str, params: list)` — returns a `WHERE`-suitable SQL fragment + bind parameters for filtering one gender. Used by `build_query` to back the `female=True` / `male=True` params.
- `infer(competition_title: str) -> 'M' | 'F'` — Python-side inference for unit tests and any per-routine inference need. Deterministic and total — no `None` (ADR-0003).

The lexicon is the existing set already in `build_query` (with the dead `\bf\)` regex entry dropped — LIKE doesn't honour `\b`, so the entry was a no-op): strict-female prefixes that span Romance languages (`fem` → Female/Feminino/Feminil/Femenil/Féminin/Femmes, `wom`, `gir`, `ladies`), plus non-prefix tokens for Russian, Japanese, Finnish, Danish, Swedish, Estonian, Chinese; and a short male-override list (` men`, ` male`, `мужчины`, `мужчины и женщины`, `&m`) disambiguating mixed-wording titles.

`build_query` (in `db.py`) is rewired: the inline regex + the manual `qparams.extend(…)` calls are replaced with a single call to `gender_filter_sql(...)`. Behaviour is identical for `--female`; behaviour for `--male` becomes "not matching the female lexicon" via the same shared expression (matches today's de facto behaviour now made explicit).

## Acceptance criteria

- [ ] `routine_gender` module exists with `gender_case_sql`, `gender_filter_sql`, `infer`, plus the lexicon as a module-level constant.
- [ ] `infer` is total — returns `'M'` or `'F'` for every input including empty string and `None`. Unit-tested with table-driven cases covering English, Portuguese, Spanish, French, German, Russian, Japanese, Finnish, Danish, Swedish, Estonian, Chinese titles.
- [ ] `gender_case_sql` returns a syntactically valid SQLite `CASE` expression. Smoke-tested by embedding it in a `SELECT … FROM routines LIMIT 10` against the live DB and asserting every row gets `'M'` or `'F'`.
- [ ] `gender_filter_sql('F')` returns a fragment + params that, when concatenated into a query, produces the same row count as today's `build_query` with `female=True` (regression smoke test against the live DB).
- [ ] `build_query` no longer inlines the gender regex — it calls `routine_gender.gender_filter_sql(...)`.
- [ ] The dead `\bf\)` lexicon entry is removed.
- [ ] CLI search `--female` / `--male` flags work end-to-end against the live DB (smoke test asserts non-empty result set for a known multilingual women's competition title like "Femenil").

## Blocked by

None — can start immediately.
