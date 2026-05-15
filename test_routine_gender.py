"""Table-driven tests for routine_gender.

Coverage spans English, Portuguese, Spanish, French, German, Russian,
Japanese, Finnish, Danish, Swedish, Estonian, Chinese — the languages the
strict-F lexicon claims to cover (ADR-0003).
"""

import pytest

import routine_gender


INFER_CASES = [
    # English
    ("Women's Senior", "F"),
    ("Female Junior", "F"),
    ("Girls 11-12", "F"),
    ("Ladies Open", "F"),
    ("Men's Senior", "M"),
    ("Senior Open", "M"),
    # Portuguese
    ("Feminino Senior", "F"),
    ("Feminil 13-14", "F"),
    ("Masculino Senior", "M"),
    # Spanish
    ("Femenil Junior", "F"),
    ("Femenino Senior", "F"),
    # French — `fem` matches the ASCII-prefixed forms (Femmes/Feminin without
    # accent). `Féminin` slips through to the M fallback because SQLite LIKE
    # is byte-oriented for non-ASCII, and `infer` mirrors that contract.
    ("Femmes Élite", "F"),
    ("Feminin Élite", "F"),
    ("Hommes Élite", "M"),
    # German
    ("Damen Senior", "F"),
    ("Herren Senior", "M"),
    # Russian
    ("Девочки 11-12", "F"),
    ("Женщины", "F"),
    ("Юниорки", "F"),
    ("Мужчины", "M"),
    # Japanese
    ("女子 シニア", "F"),
    ("男子 シニア", "M"),
    # Finnish
    ("tytöt 9-10", "F"),
    ("naiset", "F"),
    ("miehet", "M"),
    # Danish
    ("Damer Senior", "F"),
    # Swedish
    ("Flickor 9-10", "F"),
    # Estonian
    ("Tüdrukud", "F"),
    # Chinese
    ("女子组", "F"),
    # Male-override disambiguation — the ` men` / `&m` tokens disambiguate
    # mixed-wording titles (whitespace-anchored so plain "Women" isn't broken).
    ("Open Men & Women", "M"),
    ("Senior Men &Women", "M"),
    ("Senior Open M&W", "M"),
    # Total — empty / None must not raise.
    ("", "M"),
    (None, "M"),
]


@pytest.mark.parametrize("title,expected", INFER_CASES)
def test_infer(title, expected):
    assert routine_gender.infer(title) == expected


def test_infer_returns_only_two_states():
    # Random nonsense titles must still resolve.
    for title in ("???", "12345", "Open", "Élite", "Senior", "Júnior"):
        assert routine_gender.infer(title) in ('M', 'F')


def test_gender_case_sql_shape():
    sql = routine_gender.gender_case_sql()
    assert sql.startswith('(CASE WHEN')
    assert sql.endswith("END)")
    assert "THEN 'F'" in sql
    assert "ELSE 'M'" in sql
    # Default column.
    assert "competition_title" in sql


def test_gender_case_sql_custom_column():
    sql = routine_gender.gender_case_sql('ct')
    assert "ct LIKE" in sql
    assert "competition_title" not in sql


def test_gender_filter_sql_female_params_match_lexicon():
    sql, params = routine_gender.gender_filter_sql('F')
    assert "LIKE" in sql and "NOT LIKE" in sql
    assert all(p.startswith('%') and p.endswith('%') for p in params)
    expected_n = len(routine_gender.FEMALE_TERMS) + len(
        routine_gender.MALE_OVERRIDE_TERMS)
    assert len(params) == expected_n


def test_gender_filter_sql_male_params_match_lexicon():
    sql, params = routine_gender.gender_filter_sql('M')
    assert "NOT LIKE" in sql and "LIKE" in sql
    expected_n = len(routine_gender.FEMALE_TERMS) + len(
        routine_gender.MALE_OVERRIDE_TERMS)
    assert len(params) == expected_n


def test_dead_regex_entry_removed():
    # The old `\bf\)` regex entry was a no-op (LIKE doesn't honour \b) and is
    # gone in the rewrite — pin the lexicon against accidental re-introduction.
    for term in routine_gender.FEMALE_TERMS:
        assert "\\b" not in term
        assert "\\B" not in term
