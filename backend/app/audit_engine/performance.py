"""Core Web Vitals with real reproducibility via snapshots (diagram 3.4).

Owns its own <48h snapshot: the goal is reproducibility of the *report*, not of
the physical measurement. CrUX field data is preferred when available; otherwise
a Lighthouse lab estimate is stored, always tagged with its source and timestamp.
"""

from .models import FetchResult, PerformanceResult


async def measure_performance(domain: str, fetch: FetchResult) -> PerformanceResult:
    """Return Core Web Vitals for ``domain``.

    If a snapshot younger than 48h exists it is returned as-is
    (``from_snapshot=True``). Otherwise runs Lighthouse locally 3 times and takes
    the median, pulls CrUX field data when the domain has enough traffic, and
    persists a fresh timestamped snapshot.
    """
    raise NotImplementedError
