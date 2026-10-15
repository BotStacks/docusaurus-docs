"""Deterministic risk classification.

The model's own label is not trusted. Public-availability wording is
detected from the proposed text, and anything uncertain stays in review.
"""

from __future__ import annotations

import re

from docs_agent.config import Settings
from docs_agent.models import Proposal, PullRequest, ReleaseEvidence, Risk
from docs_agent.redact import (
    customer_data_findings,
    injection_findings,
    internal_ops_findings,
    secret_findings,
    unsafe_url_findings,
)

_REVIEW_TOPICS = re.compile(
    r"(?i)\b(billing|payment|stripe|invoice|privacy|gdpr|ccpa|retention|legal|"
    r"compliance|authentication|oauth|password|breaking change|deprecated|"
    r"security policy|data deletion|delete your data)\b"
)
_AVAILABILITY = re.compile(
    r"(?i)\b(now available|generally available|publicly available|you can now|"
    r"available to (all|every) customers|live for (all|everyone))\b"
)
_NAV_KEYS = ("id:", "slug:", "sidebar_position:", "sidebar_label:")


def _allowed_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if not normalized.startswith("docs/"):
        return False
    if normalized.endswith("/_category_.json"):
        return False
    return normalized.endswith(".md") or normalized.endswith(".mdx")


def classify(
    proposal: Proposal,
    prs: list[PullRequest],
    evidence_by_pr: dict[str, ReleaseEvidence],
    candidate_paths: set[str],
    settings: Settings,
) -> tuple[Risk, list[str]]:
    text = f"{proposal.summary}\n{proposal.new_snippet}"
    reasons: list[str] = []

    if secret_findings(text) or secret_findings(proposal.old_snippet):
        return Risk.BLOCKED, ["credential or secret material"]
    if customer_data_findings(text):
        return Risk.BLOCKED, ["private customer data"]
    if internal_ops_findings(text):
        return Risk.BLOCKED, ["internal operational information"]
    if unsafe_url_findings(text):
        return Risk.BLOCKED, ["unsafe URL"]
    if injection_findings(text):
        return Risk.BLOCKED, ["instruction injection in the proposed text"]
    if not _allowed_path(proposal.path):
        return Risk.BLOCKED, ["path is outside approved public docs content"]

    if proposal.path not in candidate_paths:
        reasons.append("page was not retrieved for this change")
    known_prs = {pr.key for pr in prs}
    if not proposal.source_prs or any(item not in known_prs for item in proposal.source_prs):
        reasons.append("source pull request is missing or not part of this run")
    known_files: set[str] = set()
    for key in proposal.source_prs:
        match = next((pr for pr in prs if pr.key == key), None)
        if match:
            known_files.update(item.filename for item in match.files)
    if proposal.source_files and any(item not in known_files for item in proposal.source_files):
        reasons.append("incorrect source claim")
    if not proposal.source_files:
        reasons.append("no source file reference")

    if proposal.kind != "correction":
        reasons.append("not a small correction of an existing guide")
    if proposal.truncated_input:
        reasons.append("source diff was truncated")
    if _REVIEW_TOPICS.search(text):
        reasons.append("sensitive product topic")
    if any(key in proposal.new_snippet for key in _NAV_KEYS):
        reasons.append("navigation frontmatter")

    claims = proposal.claims_public_availability or bool(_AVAILABILITY.search(proposal.new_snippet))
    if claims:
        cited = [evidence_by_pr.get(key, ReleaseEvidence()) for key in proposal.source_prs]
        verified = any(item.public_availability_verified for item in cited)
        if not verified:
            reasons.append("availability is not verified by a production or site release")

    new_lines = proposal.new_snippet.count("\n") + 1
    old_lines = proposal.old_snippet.count("\n") + 1
    if max(new_lines, old_lines) > settings.max_changed_lines:
        reasons.append("change is larger than the auto-merge limit")
    if not proposal.old_snippet.strip() or not proposal.new_snippet.strip():
        reasons.append("refuses to create or delete a page")

    if reasons:
        return Risk.REVIEW_REQUIRED, reasons
    return Risk.AUTO_ELIGIBLE, ["small factual correction with source references"]
