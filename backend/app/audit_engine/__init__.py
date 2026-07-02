"""Deterministic audit engine — no LLM anywhere in the scoring path.

Public API: :func:`run_audit` and :class:`AuditResult`.
"""

from .models import AuditResult
from .orchestrator import run_audit

__all__ = ["AuditResult", "run_audit"]
