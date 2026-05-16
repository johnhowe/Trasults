# Gender inference: strict-female lexicon, fallback male

Routine gender is inferred from `competition_title` via a multilingual strict-female lexicon — anything not matching falls through to `'M'`. The output is two-state (`'M' | 'F'`), with no `'Unknown'` / `None` / `'Mixed'` bucket.

The two-state model is empirically defensible *because* of the shape of the data. At the top of every D-score, ToF, and total-score distribution, men's elite is consistently above women's; routines whose `competition_title` lacks any gender token are overwhelmingly from men's events (open international categories, untagged senior men's competitions, etc.). Defaulting to `'M'` is therefore a safe heuristic for the elite-frontier queries that drive the overview-page visuals — *as long as the female lexicon stays comprehensive*. The asymmetric default is the load-bearing trade-off: we accept silent mis-classification of any women's routine whose title lacks a recognised F token, in exchange for a deterministic two-state model that's trivially partitionable in SQL.

The lexicon prefixes (`fem`, `wom`, `gir`, `ladies`) intentionally span families — `fem` matches `Female`, `Feminine`, `Feminino` (PT), `Femenil/Femenino` (ES), `Féminin/Femmes` (FR) — so language coverage scales without per-language entries. Non-prefix tokens cover languages without Romance roots: Russian (`Дев`, `Женщины`, `Юниорки`), Japanese (`女`), Finnish (`tytöt`, `naiset`), Danish (`dam`), Swedish (`flickor`), Estonian (`tüdrukud`). A short male-override list (` men`, ` male`, `мужчины`, `мужчины и женщины`, `&m`) disambiguates titles like "Men & Women" that contain both gender markers.

The single load-bearing maintenance contract: **adding a language to the lexicon is the only ongoing touchpoint**. Silent under-coverage of F mis-tags women's routines as male, which biases the men's frontier upward and starves the women's frontier of data. A future maintainer reviewing the [[Frontier]] charts should suspect the lexicon first if the women's bucket looks thin in a region the dataset newly covers.

The module exposes the lexicon two ways:
- `gender_case_sql(column='competition_title') -> str` — a SQL `CASE` expression for `SELECT` / `GROUP BY` / `PARTITION BY` (used by the frontier queries).
- `gender_filter_sql(gender: str) -> (sql_fragment, params)` — used by `build_query` for the CLI/web `--female` / `--male` filters.
- `infer(competition_title: str) -> 'M' | 'F'` — Python-side, for unit tests and any per-routine inference.

All three share one lexicon constant. The previous `build_query` implementation inlined the regex; it had a dead `\bf\)` entry (LIKE doesn't honour `\b`) that this rewrite drops.

## Considered options

- **Three-state `'M' | 'F' | None`** — explicit unknown bucket. Rejected because the elite-frontier charts have to drop `None` anyway, and tracking the unknown bucket in payloads adds plumbing without informing any downstream decision. The empirical skew also means `None` for the elite tail behaves indistinguishably from `'M'`.
- **Four-state with explicit `'Mixed'`** — for demo events titled "Men & Women". Rejected because such events are vanishingly rare in the dataset and have zero effect on the top-N frontier.
- **External name-to-gender library against `person_given_name`** — would cover untagged events. Rejected because (a) it introduces a per-routine dependency (slow at the SQL boundary), (b) it requires culture-aware first-name lookup tables that don't exist for many federations represented in the data, and (c) the elite-skew default already handles the top-of-distribution case the visuals actually depend on.
