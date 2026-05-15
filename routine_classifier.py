"""Routine classification predicates.

Single source of truth for the per-discipline expected-element table
and the compulsory routine threshold (TRA-only, 30% of athlete career-best D).
"""

EXPECTED_ELEMENTS = {'TRA': 10, 'DMT': 2, 'TUM': 8}
COMPULSORY_RATIO = 0.3


def is_crash(nelements, discipline):
    """nelements < expected_for_discipline. Unknown discipline -> False."""
    expected = EXPECTED_ELEMENTS.get((discipline or '').upper())
    if expected is None:
        return False
    return int(nelements) < expected


def is_compulsory(d_score, athlete_best_d, nelements, discipline):
    """TRA-only: nelements == 10 AND D < 30% of athlete career-best D."""
    if (discipline or '').upper() != 'TRA':
        return False
    if int(nelements) != EXPECTED_ELEMENTS['TRA']:
        return False
    if float(athlete_best_d) <= 0:
        return False
    return float(d_score) < COMPULSORY_RATIO * float(athlete_best_d)


def classify(nelements, d_score, athlete_best_d, discipline):
    if is_crash(nelements, discipline):
        return 'crash'
    if is_compulsory(d_score, athlete_best_d, nelements, discipline):
        return 'compulsory'
    return 'voluntary'
