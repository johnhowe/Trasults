"""Pure-functional rolling-peak math.

Operates on parallel chronological arrays. The caller orders the routines
and supplies the crash flag for each.
"""


def best_n_of_last_k(totals, crashes, n=3, k=10):
    """At each index i, mean of the top `n` among the last `k` non-crashed
    totals at or before i — the **Rolling peak** value (CONTEXT.md).

    The window slides over *completed* routines: crashes are dropped, then
    the trailing k completed totals are kept. Returns None where fewer than
    `n` completed routines are available so far.
    """
    out = []
    completed = []
    for i in range(len(totals)):
        if not crashes[i]:
            completed.append(totals[i])
        window = completed[-k:]
        if len(window) < n:
            out.append(None)
        else:
            out.append(sum(sorted(window, reverse=True)[:n]) / n)
    return out


def crash_rate_last_k(crashes, k=10):
    """At each index i, the share of crashes among the last `k` routines
    (positions, not completions) ending at i."""
    out = []
    for i in range(len(crashes)):
        lo = max(0, i - k + 1)
        window = crashes[lo:i + 1]
        out.append(sum(1 for c in window if c) / len(window))
    return out
