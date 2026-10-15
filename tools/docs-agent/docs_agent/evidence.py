"""Interpret workflow runs from a source repository.

The deploy repository is intentionally not required. Evidence is limited
to workflows in the repository that owns the pull request.
"""

from __future__ import annotations

from typing import Any

from docs_agent.models import PullRequest, ReleaseEvidence


def from_runs(pr: PullRequest, runs: list[dict[str, Any]]) -> ReleaseEvidence:
    sandbox = False
    production = False
    landing = False
    urls: list[str] = []
    is_landing = pr.repo.endswith("/botstacks-landing-page") or pr.repo == "botstacks-landing-page"
    for run in runs:
        if run.get("head_sha") and run.get("head_sha") != pr.merge_commit_sha:
            continue
        if run.get("conclusion") != "success":
            continue
        name = str(run.get("name") or "")
        url = str(run.get("html_url") or "")
        if name == "release-prod":
            production = True
            if url:
                urls.append(url)
        elif name == "deploy":
            if is_landing:
                landing = True
            else:
                sandbox = True
            if url:
                urls.append(url)
    return ReleaseEvidence(
        sandbox_deploy_success=sandbox,
        production_release_success=production,
        landing_deploy_success=landing,
        run_urls=tuple(urls),
    )
