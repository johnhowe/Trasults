# Radar uses sport-empirical absolute scale, not cohort-relative

The rest of the dashboard compares an athlete to the cohort (mean / stdev / percentile within the field). The radar deliberately doesn't. Each axis runs from **0 at the centre to the sport-empirical ceiling at the outer edge** — calibrated once from the dataset's 99th percentile per discipline per component — and a static **field-median reference ring** is drawn in grey for context.

The intent is cross-athlete comparability and visual honesty for athletes at any level. With cohort-relative scaling, two athletes' radars share the same dial only if they share a cohort; the world champion and a developing junior get visually similar shapes (both fill their relative space). With absolute scaling, a junior's shape correctly reads as small and inside the median ring, the elite's correctly reads as filling the dial. The reference ring stops the junior's shape from becoming invisible.

This is a deliberate deviation from the cohort-comparison pattern used everywhere else, and a future maintainer "fixing the inconsistency" would silently break the comparability the radar exists to provide.

## Considered options

- **Cohort percentile rank on each axis (0–100)** — readable as "you're at the 80th percentile for D", matches the rest of the dashboard. Rejected because two athletes' radars are only comparable if both are scored against the same cohort, and the visual tautology (the cohort's median always sits at 50% on every axis) hides the absolute level of performance.
- **Data-driven min/max from the athlete's own routines** — always fills the dial, no calibration needed. Rejected as tautological: the outer ring (athlete PB) always touches every axis edge, so the radar only conveys distribution shape and is meaningless across athletes.
- **Hybrid (sport-knowable max, athlete-derived min)** — fills the dial while preserving an absolute ceiling. Rejected for added complexity without enough payoff: the field-median reference ring already solves the "tiny shape" problem the hybrid was meant to address.
