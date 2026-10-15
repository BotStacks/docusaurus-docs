"""Checkpoint format and ordering rules.

The checkpoint records handled source pull requests. It never stores
document text, diffs, or credentials. A watermark moves only through a
prefix of fully handled items, so a failure cannot skip later work and
cannot hide an earlier one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from docs_agent.models import PullRequest

CHECKPOINT_TITLE = "docs-agent checkpoint"
_FENCE = "```json"


@dataclass
class RepoState:
    watermark: str | None = None
    processed: dict[str, str] = field(default_factory=dict)
    attempts: dict[str, int] = field(default_factory=dict)
    held: dict[str, str] = field(default_factory=dict)


@dataclass
class Checkpoint:
    version: int = 1
    repos: dict[str, RepoState] = field(default_factory=dict)

    def state_for(self, repo: str) -> RepoState:
        return self.repos.setdefault(repo, RepoState())


def select_pending(prs: list[PullRequest], state: RepoState) -> list[PullRequest]:
    """Return unhandled pull requests at or after the watermark, oldest first."""
    pending: list[PullRequest] = []
    for pr in sorted(prs, key=lambda item: (item.merged_at, item.number)):
        if pr.key in state.processed or pr.key in state.held:
            continue
        if state.watermark and pr.merged_at < state.watermark:
            continue
        pending.append(pr)
    return pending


def note_handled(state: RepoState, seen: list[PullRequest], key: str, outcome: str) -> None:
    state.processed[key] = outcome
    state.attempts.pop(key, None)
    _move_watermark(state, seen)


def note_held(state: RepoState, seen: list[PullRequest], key: str, reason: str) -> None:
    state.held[key] = reason[:240]
    state.processed.pop(key, None)
    _move_watermark(state, seen)


def note_attempt(state: RepoState, key: str) -> int:
    state.attempts[key] = state.attempts.get(key, 0) + 1
    return state.attempts[key]


def _move_watermark(state: RepoState, seen: list[PullRequest]) -> None:
    watermark = state.watermark
    for pr in sorted(seen, key=lambda item: (item.merged_at, item.number)):
        if state.watermark and pr.merged_at < state.watermark:
            continue
        if pr.key in state.processed or pr.key in state.held:
            watermark = pr.merged_at
            continue
        break
    state.watermark = watermark


def dumps(checkpoint: Checkpoint) -> str:
    payload = {
        "version": checkpoint.version,
        "repos": {
            repo: {
                "watermark": state.watermark,
                "processed": state.processed,
                "attempts": state.attempts,
                "held": state.held,
            }
            for repo, state in sorted(checkpoint.repos.items())
        },
    }
    body = json.dumps(payload, indent=2, sort_keys=True)
    return (
        "Automation state for the public docs agent. "
        "It stores pull-request identifiers and timestamps only.\n\n"
        f"{_FENCE}\n{body}\n```\n"
    )


def loads(body: str) -> Checkpoint:
    start = body.find(_FENCE)
    if start < 0:
        raise ValueError("checkpoint body has no JSON block")
    raw = body[start + len(_FENCE) :]
    end = raw.find("```")
    if end < 0:
        raise ValueError("checkpoint JSON block is not closed")
    payload = json.loads(raw[:end].strip())
    checkpoint = Checkpoint(version=int(payload.get("version", 1)))
    for repo, item in (payload.get("repos") or {}).items():
        checkpoint.repos[repo] = RepoState(
            watermark=item.get("watermark"),
            processed=dict(item.get("processed") or {}),
            attempts={key: int(value) for key, value in (item.get("attempts") or {}).items()},
            held=dict(item.get("held") or {}),
        )
    return checkpoint
