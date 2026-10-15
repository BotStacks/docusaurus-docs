"""Shared data types. Kept free of I/O so the policy logic stays testable."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Risk(str, Enum):
    AUTO_ELIGIBLE = "AUTO_ELIGIBLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ChangedFile:
    filename: str
    status: str
    patch: str = ""


@dataclass(frozen=True)
class PullRequest:
    repo: str
    number: int
    title: str
    body: str
    merged_at: str
    base: str
    head: str
    author: str
    merge_commit_sha: str
    labels: tuple[str, ...] = ()
    files: tuple[ChangedFile, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.repo}#{self.number}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.repo}/pull/{self.number}"


@dataclass(frozen=True)
class ReleaseEvidence:
    """What we can prove from the source repository's own workflow runs.

    A merged pull request is not evidence that customers have the change.
    `deploy` success on the build repository is the sandbox rollout signal.
    `release-prod` success is the production promotion signal visible from
    that repository. Landing-page `deploy` success publishes the public site.
    """

    sandbox_deploy_success: bool = False
    production_release_success: bool = False
    landing_deploy_success: bool = False
    run_urls: tuple[str, ...] = ()

    @property
    def public_availability_verified(self) -> bool:
        return self.production_release_success or self.landing_deploy_success


@dataclass(frozen=True)
class DocPage:
    path: str
    title: str
    description: str
    headings: tuple[str, ...]
    text: str
    slug: str


@dataclass
class Proposal:
    path: str
    summary: str
    old_snippet: str
    new_snippet: str
    source_prs: list[str]
    source_files: list[str]
    claims_public_availability: bool = False
    kind: str = "unspecified"
    risk: Risk = Risk.REVIEW_REQUIRED
    reasons: list[str] = field(default_factory=list)
    truncated_input: bool = False


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    changed_lines: int = 0


@dataclass(frozen=True)
class BranchRules:
    readable: bool
    required_reviews: int = 0
    required_checks: tuple[str, ...] = ()
    blocks_auto_merge: bool = False
    detail: str = ""


@dataclass
class AgentPull:
    number: int
    url: str
    draft: bool
    body: str
    files: tuple[str, ...]
    node_id: str = ""
    head_sha: str = ""
    mergeable: bool | None = None


@dataclass
class MergeResult:
    merged: bool = False
    auto_merge_enabled: bool = False
    blocked: bool = False
    reason: str = ""


@dataclass
class RunReport:
    dry_run: bool
    auto_publish: bool
    status: str = "completed"
    considered: list[str] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)
    proposals: list[Proposal] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    pull_url: str = ""
    pull_action: str = ""
    merge: MergeResult | None = None
    deployment: str = ""
    error: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        if self.status in {"error", "misconfigured"}:
            return 1
        return 0
