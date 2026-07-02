"""Security audit: headers + known CVEs (diagram 3.3).

Authoritative security result. When the stack version is not visible it reports
``version_known=False`` instead of inventing risk. It reports CVE id, severity
and the official source link only — never exploitation steps.
"""

from .models import FetchResult, SecurityResult, TechStackResult


async def scan_security(fetch: FetchResult, stack: TechStackResult) -> SecurityResult:
    """Assess security headers and known vulnerabilities.

    WordPress stacks are checked against WPScan; everything else against
    NVD/OSV. Security headers are graded via the MDN HTTP Observatory. Async
    because every path performs external API calls.
    """
    raise NotImplementedError
