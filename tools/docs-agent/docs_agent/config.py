"""Environment configuration.

Defaults are deliberately safe: a missing flag means dry-run, and
auto-publish stays off until someone sets it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    docs_repo: str = "BotStacks/docusaurus-docs"
    source_repos: tuple[str, ...] = (
        "BotStacks/botstacks-sandbox-build",
        "BotStacks/botstacks-landing-page",
    )
    docs_root_name: str = "docs"
    public_docs_base: str = "https://docs.botstacks.ai"
    dry_run: bool = True
    auto_publish: bool = False
    disabled: bool = False
    lookback_days: int = 7
    max_prs: int = 10
    max_relevant: int = 5
    max_diff_chars: int = 8_000
    max_doc_chars: int = 6_000
    max_files: int = 5
    max_changed_lines: int = 80
    max_attempts: int = 3
    llm_api_base: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4.1-mini"
    llm_max_tokens: int = 2_000
    request_timeout: float = 30.0
    llm_timeout: float = 60.0
    build_timeout: int = 900
    agent_label: str = "docs-agent"
    checkpoint_label: str = "docs-agent-checkpoint"
    base_branch: str = "main"
    github_token: str = ""
    llm_api_key: str = ""

    @property
    def allowed_write_repo(self) -> str:
        return self.docs_repo


def load_settings() -> Settings:
    repos = os.environ.get(
        "SOURCE_REPOS",
        "BotStacks/botstacks-sandbox-build,BotStacks/botstacks-landing-page",
    )
    source = tuple(part.strip() for part in repos.split(",") if part.strip())
    docs_repo = os.environ.get("DOCS_REPO", "BotStacks/docusaurus-docs")
    if docs_repo in source:
        raise ValueError("DOCS_REPO must not be listed in SOURCE_REPOS")
    return Settings(
        docs_repo=docs_repo,
        source_repos=source,
        public_docs_base=os.environ.get("PUBLIC_DOCS_BASE", "https://docs.botstacks.ai").rstrip("/"),
        dry_run=_bool("DRY_RUN", True),
        auto_publish=_bool("AUTO_PUBLISH", False),
        disabled=_bool("DOCS_AGENT_DISABLED", False),
        lookback_days=_int("LOOKBACK_DAYS", 7),
        max_prs=_int("MAX_PRS", 10),
        max_relevant=_int("MAX_RELEVANT", 5),
        max_diff_chars=_int("MAX_DIFF_CHARS", 8_000),
        max_doc_chars=_int("MAX_DOC_CHARS", 6_000),
        max_files=_int("MAX_FILES", 5),
        max_changed_lines=_int("MAX_CHANGED_LINES", 80),
        max_attempts=_int("MAX_ATTEMPTS", 3),
        llm_api_base=os.environ.get("LLM_API_BASE", "https://api.openai.com/v1").rstrip("/"),
        llm_model=os.environ.get("LLM_MODEL", "gpt-4.1-mini"),
        llm_max_tokens=_int("LLM_MAX_TOKENS", 2_000),
        request_timeout=float(os.environ.get("REQUEST_TIMEOUT", "30")),
        llm_timeout=float(os.environ.get("LLM_TIMEOUT", "60")),
        build_timeout=_int("BUILD_TIMEOUT", 900),
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        llm_api_key=os.environ.get("LLM_API_KEY", ""),
    )
