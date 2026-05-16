# Elite frontier ranked within each (discipline, gender) partition

The [[Frontier]] queries — `difficulty_frontier`, `tof_frontier` — rank top-N routines using `ROW_NUMBER() OVER (PARTITION BY year, discipline, gender ORDER BY metric DESC)` and then average the top-N within each partition. The naive alternative is to rank globally per (year, discipline) and split the resulting top-N by gender afterwards.

Global ranking would produce a near-empty women's frontier every year. Men's elite D-scores are consistently 2–4 points above women's at the top of every discipline; in a global top-50 by D, women contribute 0–8 routines per year per discipline in this dataset. The women's frontier line would be either invisible or computed off 1–8 samples — meaningless as a trend. Within-gender ranking gives 50 men's *and* 50 women's routines per partition, both robust, both legibly trending.

The decision propagates beyond the SQL: the [[Gender]] inference is constrained to be **deterministic and total** (every routine gets a gender) so the partition is non-empty for every routine. The asymmetric default in ADR-0003 falls out of this requirement.

The cost is that "top-50 women" and "top-50 men" measure different competitive populations, and comparing the absolute values across the two charts is not a like-for-like comparison — the gap between the men's and women's frontiers is real (the sport's elite is gendered) but it's not the message the chart is trying to convey. The message is *each frontier's trajectory over time*. Side-by-side panels (rather than overlaid lines on one panel) reinforce this: each panel reads as its own series.

## Considered options

- **Global top-N then split by gender** — simpler SQL, single ranking. Rejected because the women's frontier would be empty in this dataset; the chart would lie by omission.
- **Side-by-side per-gender lines on one chart per discipline** — overlay men and women per discipline. Rejected because it invites direct comparison of *levels* between genders, which is not the chart's intent; the trajectory is the story. The 2×2 grid (rows = metric, columns = gender) keeps each frontier as its own panel.
- **Variable `top_n` per gender** — give women's partition a smaller `top_n` because the women's pool is shallower in some years/disciplines. Rejected for v1 simplicity; if a year/(discipline, gender) bucket genuinely lacks 50 routines the existing query will simply average fewer. The chart's caption surfaces the `n` per partition (parallel to today's `counts` payload), so a thin year is visible.
