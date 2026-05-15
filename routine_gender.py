"""Multilingual gender inference for routine competition titles.

Single source of truth for the strict-female lexicon (CONTEXT.md → *Gender*,
ADR-0003). Three surfaces, one lexicon constant:

- ``gender_case_sql(column='competition_title')`` — literal-string ``CASE``
  expression for embedding in SELECT / PARTITION BY (frontier queries).
- ``gender_filter_sql(gender)`` — parameterised predicate + bind params for
  ``WHERE`` clauses (the CLI/web --female/--male filter in ``build_query``).
- ``infer(title)`` — Python-side inference for unit tests and one-off use.

Total and deterministic: every input resolves to ``'M'`` or ``'F'``. The
asymmetric default (``'M'`` when no female token matches) is load-bearing for
the elite-frontier queries; see ADR-0003 for the empirical justification and
ADR-0004 for how the partitioning consumes it.
"""

FEMALE_TERMS = [
    "fem", "wom", "gir", "ladies",
    "flickor",
    "女",
    "Дев", "Женщины", "Юниорки",
    "tytöt", "töt", "naiset",
    "dam",
    "tüdrukud",
]

MALE_OVERRIDE_TERMS = [" men", " male", "мужчины", "мужчины и женщины", "&m"]


def gender_case_sql(column: str = 'competition_title') -> str:
    """Return a literal-string SQLite ``CASE`` expression labelling every row
    ``'F'`` or ``'M'``.

    Suitable for ``SELECT`` / ``GROUP BY`` / ``PARTITION BY``. No bind params —
    lexicon entries are embedded as literals, which is safe because the lexicon
    is a code constant under our control.
    """
    fem_clause = " OR ".join(f"{column} LIKE '%{t}%'" for t in FEMALE_TERMS)
    male_override_clause = " AND ".join(
        f"{column} NOT LIKE '%{t}%'" for t in MALE_OVERRIDE_TERMS)
    return (f"(CASE WHEN ({fem_clause}) AND ({male_override_clause}) "
            f"THEN 'F' ELSE 'M' END)")


def gender_filter_sql(gender: str) -> tuple:
    """Return ``(sql_fragment, params)`` for filtering one gender.

    The fragment is a parenthesised predicate without a leading ``AND`` —
    callers join it with their own connector. Mirrors :func:`gender_case_sql`:
    ``'F'`` is "matches female lexicon AND no male-override token"; ``'M'`` is
    the logical complement.
    """
    g = (gender or '').upper()
    fem_or = " OR ".join("competition_title LIKE ?" for _ in FEMALE_TERMS)
    fem_params = [f"%{t}%" for t in FEMALE_TERMS]
    override_not_and = " AND ".join(
        "competition_title NOT LIKE ?" for _ in MALE_OVERRIDE_TERMS)
    override_params = [f"%{t}%" for t in MALE_OVERRIDE_TERMS]
    if g == 'F':
        return (f"(({fem_or}) AND ({override_not_and}))",
                fem_params + override_params)
    # 'M' — complement of the F predicate.
    fem_not_and = " AND ".join(
        "competition_title NOT LIKE ?" for _ in FEMALE_TERMS)
    override_or = " OR ".join(
        "competition_title LIKE ?" for _ in MALE_OVERRIDE_TERMS)
    return (f"(({fem_not_and}) OR ({override_or}))",
            fem_params + override_params)


def infer(competition_title) -> str:
    """Return ``'F'`` or ``'M'`` for a competition title. Total (handles
    ``None`` / empty by returning ``'M'``).

    Python ``.lower()`` folds case for non-ASCII too, which is a strict
    superset of SQLite ``LIKE`` (ASCII-only case folding). That asymmetry only
    makes ``infer`` slightly more permissive than the SQL surfaces — safe for
    the strict-F lexicon.
    """
    t = (competition_title or '').lower()
    matches_female = any(term.lower() in t for term in FEMALE_TERMS)
    has_male_override = any(term.lower() in t for term in MALE_OVERRIDE_TERMS)
    return 'F' if matches_female and not has_male_override else 'M'
