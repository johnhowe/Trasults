# Form window separated from cohort filter

The dashboard's existing year-range filter (`year_from`/`year_to`) bounds the **comparison population** for cross-athlete panels — deduction profile, decomposition, qual-vs-final. The new "Depth" view introduces a second, athlete-scoped time concept — the **form window** (past N months) — which bounds the radar, the form indicator, and the rolling crash rate.

We're keeping these as two independent controls in the UI and as two distinct parameters in the query API, even though it would be simpler to expose one. They answer different questions: cohort filter says "who is this athlete being measured against", form window says "how is this athlete looking right now". Folding them into a single control silently corrupts both — narrowing the cohort to the last 6 months collapses the comparison field; widening the form window dilutes the "right now" signal with old data.

## Considered options

- **Single time filter** — simpler UI, one query parameter. Rejected because the two questions are genuinely different and collapsing them produces misleading numbers without any visual cue that the meaning has shifted.
- **Form window derived from cohort filter** (e.g. always the last 12 months of the cohort range) — rejected for the same reason: the radar would lie when a user picks a historical cohort range to compare an athlete against their younger self.
