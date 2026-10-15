"""Deterministic redaction and secret detection.

Used both before anything is sent to a model and again on model output.
"""

from __future__ import annotations

import re

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]{12,}={0,2}\b"),
)

_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)ignore (all |any |previous |prior )?instructions"),
    re.compile(r"(?i)disregard (the |your )?(system|previous)"),
    re.compile(r"(?i)you are now"),
    re.compile(r"(?i)<\s*/?\s*system\s*>"),
)

_INTERNAL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bkubectl\b"),
    re.compile(r"(?i)\bdoctl\b"),
    re.compile(r"(?i)\bdigitalocean\b"),
    re.compile(r"(?i)\binfisical\b"),
    re.compile(r"(?i)registry\.digitalocean\.com"),
    re.compile(r"(?i)\bKUBERNETES_TOKEN\b"),
    re.compile(r"(?i)\bcluster[_ -]?id\b"),
    re.compile(r"(?i)\bprod-(frontend|api|core)\b"),
)

_UNSAFE_URL = re.compile(
    r"(?i)(javascript:|data:|file:|https?://(localhost|127\.0\.0\.1|169\.254\.169\.254|10\.\d+|192\.168\.\d+|172\.(1[6-9]|2\d|3[01])\.)|http://)"
)

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PUBLIC_EMAILS = {"support@botstacks.ai"}


def redact(text: str, secrets: list[str] | None = None) -> str:
    cleaned = text
    for secret in secrets or []:
        if secret:
            cleaned = cleaned.replace(secret, "[REDACTED]")
    for pattern in _SECRET_PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    return cleaned


def secret_findings(text: str) -> list[str]:
    return [pattern.pattern for pattern in _SECRET_PATTERNS if pattern.search(text)]


def injection_findings(text: str) -> list[str]:
    return [pattern.pattern for pattern in _INJECTION_PATTERNS if pattern.search(text)]


def internal_ops_findings(text: str) -> list[str]:
    return [pattern.pattern for pattern in _INTERNAL_PATTERNS if pattern.search(text)]


def unsafe_url_findings(text: str) -> list[str]:
    return ["unsafe url"] if _UNSAFE_URL.search(text) else []


def customer_data_findings(text: str) -> list[str]:
    emails = {item.lower() for item in _EMAIL.findall(text)} - _PUBLIC_EMAILS
    if emails:
        return ["email address that is not a published support address"]
    return []
