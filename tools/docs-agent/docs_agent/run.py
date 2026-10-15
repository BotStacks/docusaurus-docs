"""Daily run.

The checkpoint is a copy of the stored state. Dry runs mutate only the
copy and never write it back. A failure stops the queue at that source
pull request instead of moving the watermark past it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from docs_agent.checkpoint import Checkpoint, loads, dumps, note_attempt, note_handled, note_held
from docs_agent.classify import classify
from docs_agent.config import Settings, load_settings
from docs_agent.docs_index import load_pages, match_pages, slug_for
from docs_agent.evidence import from_runs
from docs_agent.github_api import GitHubClient, GitHubError, fetch_public_page
from docs_agent.llm import LLMClient, LLMError
from docs_agent.models import Proposal, PullRequest, ReleaseEvidence, Risk, RunReport
from docs_agent.publish import attempt_merge, find_conflict, find_reusable, render_body
from docs_agent.relevance import assess
from docs_agent.summary import emit
from docs_agent.validate import validate, yarn_build


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "docusaurus.config.ts").is_file():
            return parent
    raise RuntimeError("could not find the docusaurus repository root")


def _copy(checkpoint: Checkpoint) -> Checkpoint:
    return loads(dumps(checkpoint))


def _batch_risk(proposals: list[Proposal]) -> Risk:
    if any(item.risk == Risk.BLOCKED for item in proposals):
        return Risk.BLOCKED
    if any(item.risk == Risk.REVIEW_REQUIRED for item in proposals):
        return Risk.REVIEW_REQUIRED
    if proposals and all(item.risk == Risk.AUTO_ELIGIBLE for item in proposals):
        return Risk.AUTO_ELIGIBLE
    return Risk.REVIEW_REQUIRED


def _retry_open_eligible(settings: Settings, github, report: RunReport) -> None:
    """Merge eligible pull requests left open before auto-publish was enabled."""
    try:
        existing = github.list_agent_prs(settings.agent_label)
    except GitHubError as exc:
        report.notes.append(f"could not inspect open docs pull requests: {exc}")
        return
    for pull in existing:
        if pull.draft or Risk.AUTO_ELIGIBLE.value not in pull.body:
            continue
        try:
            result = attempt_merge(github, settings, pull, Risk.AUTO_ELIGIBLE)
        except GitHubError as exc:
            report.notes.append(f"existing #{pull.number} was left open: {exc}")
            continue
        report.notes.append(f"existing #{pull.number}: {result.reason}")


def _verify_pages(settings: Settings, proposals: list[Proposal], files: dict[str, str], fetch) -> str:
    """Confirm the public site is serving the new sentences.

    Docusaurus renders Markdown to HTML, so this looks for the visible
    text of each replacement. A miss is reported and not treated as a
    successful publish. Nothing is rolled back from here.
    """
    from docs_agent.validate import _frontmatter

    failures: list[str] = []
    seen: set[str] = set()
    for proposal in proposals:
        if proposal.path in seen or proposal.path not in files:
            continue
        seen.add(proposal.path)
        slug = slug_for(proposal.path, _frontmatter(files[proposal.path]))
        url = settings.public_docs_base + slug
        try:
            status, body = fetch(url)
        except Exception as exc:
            failures.append(f"{url} ({exc})")
            continue
        if status != 200:
            failures.append(f"{url} returned HTTP {status}")
            continue
        needle = " ".join(proposal.new_snippet.split())
        for token in ("*", "`", "[", "]", "#", ">", "_"):
            needle = needle.replace(token, "")
        needle = " ".join(needle.split())[:160]
        if len(needle) < 12:
            failures.append(f"{url} returned HTTP 200 but the edit is too small to confirm")
            continue
        if needle not in body:
            failures.append(f"{url} does not contain the updated documentation yet")
    if failures:
        return "failed: " + "; ".join(failures[:5])
    return "verified"


def execute(settings, github, llm, repo_root: Path, build_runner, fetch_page, now: datetime) -> RunReport:
    report = RunReport(dry_run=settings.dry_run, auto_publish=settings.auto_publish)
    if settings.disabled:
        report.status = "disabled"
        report.notes.append("DOCS_AGENT_DISABLED is set. Nothing was read or written.")
        return report

    try:
        stored = github.read_checkpoint()
    except GitHubError as exc:
        report.status = "error"
        report.error = f"could not read the checkpoint: {exc}"
        return report
    scratch = _copy(stored or Checkpoint())
    progress = False
    if settings.auto_publish and not settings.dry_run:
        _retry_open_eligible(settings, github, report)

    def persist() -> None:
        nonlocal progress
        if settings.dry_run or not progress:
            return
        github.write_checkpoint(scratch)

    pending_by_repo: dict[str, list[PullRequest]] = {}
    ordered: list[PullRequest] = []
    try:
        for repo in settings.source_repos:
            state = scratch.state_for(repo)
            since = state.watermark or _iso(now - timedelta(days=settings.lookback_days))
            merged = github.list_merged_prs(repo, since, settings.max_prs)
            from docs_agent.checkpoint import select_pending

            pending = select_pending(merged, state)
            pending_by_repo[repo] = pending
            ordered.extend(pending)
    except GitHubError as exc:
        report.status = "error"
        report.error = f"could not list merged pull requests: {exc}"
        return report

    ordered.sort(key=lambda item: (item.merged_at, item.repo, item.number))
    relevant: list[tuple[PullRequest, ReleaseEvidence]] = []
    hard_skip = {"not merged to main", "generated by the docs agent", "automation author", "maintenance change"}

    for pr in ordered:
        if len(relevant) >= settings.max_relevant:
            report.notes.append("relevant-change cap reached; later pull requests stay queued")
            break
        current = pr
        early = assess(current)
        if not early.relevant and early.reason in hard_skip:
            report.considered.append(current.key)
            report.skipped.append((current.key, early.reason))
            if not settings.dry_run:
                note_handled(scratch.state_for(current.repo), pending_by_repo[current.repo], current.key, early.reason)
                progress = True
            continue
        try:
            files = github.list_pr_files(current.repo, current.number)
            runs = github.workflow_runs(current.repo, current.merge_commit_sha)
        except GitHubError as exc:
            report.status = "error"
            report.error = f"could not read {current.key}: {exc}"
            persist()
            return report
        current = PullRequest(
            repo=current.repo,
            number=current.number,
            title=current.title,
            body=current.body,
            merged_at=current.merged_at,
            base=current.base,
            head=current.head,
            author=current.author,
            merge_commit_sha=current.merge_commit_sha,
            labels=current.labels,
            files=tuple(files),
        )
        decision = assess(current)
        report.considered.append(current.key)
        if not decision.relevant:
            report.skipped.append((current.key, decision.reason))
            if not settings.dry_run:
                note_handled(scratch.state_for(current.repo), pending_by_repo[current.repo], current.key, decision.reason)
                progress = True
            continue
        relevant.append((current, from_runs(current, runs)))

    if not relevant:
        persist()
        report.notes.append("no customer-facing documentation changes")
        return report

    pages = load_pages(repo_root / "docs")
    matched = []
    seen_paths: set[str] = set()
    for pr, _evidence in relevant:
        for page in match_pages(pr, pages):
            if page.path not in seen_paths:
                matched.append(page)
                seen_paths.add(page.path)
    if not matched:
        for pr, _evidence in relevant:
            report.notes.append(f"{pr.key} matched no public page; held for placement")
            if not settings.dry_run:
                note_held(scratch.state_for(pr.repo), pending_by_repo[pr.repo], pr.key, "no matching public page")
                progress = True
        persist()
        return report

    truncated = False
    for pr, _evidence in relevant:
        size = sum(len(item.patch) for item in pr.files)
        if size > settings.max_diff_chars:
            truncated = True
            report.notes.append(f"{pr.key} diff truncated to {settings.max_diff_chars} characters")

    evidence = {pr.key: item for pr, item in relevant}
    try:
        proposals = llm.propose([pr for pr, _item in relevant], matched, evidence, truncated)
    except LLMError as exc:
        report.status = "error"
        report.error = f"model request failed: {exc}"
        if not settings.dry_run:
            for pr, _item in relevant:
                attempts = note_attempt(scratch.state_for(pr.repo), pr.key)
                if attempts >= settings.max_attempts:
                    note_held(scratch.state_for(pr.repo), pending_by_repo[pr.repo], pr.key, "model request failed")
            progress = True
            persist()
        return report

    cited: set[str] = set()
    tainted: set[str] = set()
    classified: list[Proposal] = []
    batch = [pr for pr, _item in relevant]
    for proposal in proposals:
        if truncated:
            proposal.truncated_input = True
        risk, reasons = classify(proposal, batch, evidence, seen_paths, settings)
        proposal.risk = risk
        proposal.reasons = reasons
        classified.append(proposal)
        cited.update(proposal.source_prs)
        if risk == Risk.BLOCKED:
            tainted.update(proposal.source_prs)
    report.proposals = classified

    if not settings.dry_run:
        for pr, _item in relevant:
            if pr.key not in cited:
                note_handled(scratch.state_for(pr.repo), pending_by_repo[pr.repo], pr.key, "no documentation change")
                progress = True
            elif pr.key in tainted:
                reason = next(item.reasons[0] for item in classified if pr.key in item.source_prs and item.risk == Risk.BLOCKED)
                note_held(scratch.state_for(pr.repo), pending_by_repo[pr.repo], pr.key, reason)
                progress = True

    publishable = [item for item in classified if item.risk != Risk.BLOCKED and not any(key in tainted for key in item.source_prs)]
    if not publishable:
        report.notes.append("no publishable documentation change")
        persist()
        return report

    risk = _batch_risk(publishable)
    result = validate(repo_root, publishable, settings, build_runner)
    report.validation_errors = result.errors
    if not result.ok:
        report.notes.append("validation failed; nothing was published")
        if not settings.dry_run:
            keys = {key for item in publishable for key in item.source_prs}
            for pr, _item in relevant:
                if pr.key not in keys:
                    continue
                attempts = note_attempt(scratch.state_for(pr.repo), pr.key)
                if attempts >= settings.max_attempts:
                    note_held(
                        scratch.state_for(pr.repo),
                        pending_by_repo[pr.repo],
                        pr.key,
                        "validation failed",
                    )
            progress = True
            persist()
        return report

    keys = {key for item in publishable for key in item.source_prs}
    paths = set(result.files)
    try:
        open_prs = github.list_agent_prs(settings.agent_label)
    except GitHubError as exc:
        report.status = "error"
        report.error = f"could not list existing docs pull requests: {exc}"
        persist()
        return report

    reusable = find_reusable(open_prs, keys)
    conflict = None if reusable else find_conflict(open_prs, paths, keys)
    if conflict is not None:
        report.pull_action = f"held; #{conflict.number} already edits the same page"
        report.pull_url = conflict.url
        report.notes.append("conflicting active docs update; checkpoint left in place")
        persist()
        return report

    evidence_lines = []
    for pr, item in relevant:
        if pr.key not in keys:
            continue
        evidence_lines.append(
            f"{pr.key}: production={item.production_release_success} "
            f"sandbox={item.sandbox_deploy_success} landing={item.landing_deploy_success} "
            f"runs={', '.join(item.run_urls) or 'none'}"
        )
    body = render_body(publishable, True, [], evidence_lines, risk)
    title = "docs: update public guides from merged product changes"

    if settings.dry_run:
        report.pull_action = "would reuse an open pull request" if reusable else "would open a pull request"
        report.notes.append("dry run: no pull request, merge, deploy, or checkpoint write")
        return report

    if reusable:
        pull = reusable
        report.pull_action = "reused the open docs-agent pull request"
    else:
        stamp = _iso(now).replace(":", "").replace("-", "")
        first = sorted(keys)[0].split("#")[-1]
        branch = f"docs-agent/update-{stamp}-{first}"
        try:
            github.create_branch_commit(branch, result.files, title)
            pull = github.open_pull(
                branch,
                title,
                body,
                draft=risk != Risk.AUTO_ELIGIBLE,
                labels=[settings.agent_label, f"{settings.agent_label}:{risk.value.lower().replace('_', '-')}"],
            )
        except GitHubError as exc:
            report.status = "error"
            report.error = f"could not open the docs pull request: {exc}"
            for pr, _item in relevant:
                if pr.key in keys:
                    note_attempt(scratch.state_for(pr.repo), pr.key)
            progress = True
            persist()
            return report
        report.pull_action = "opened a draft pull request" if pull.draft else "opened a pull request"
    report.pull_url = pull.url

    report.merge = attempt_merge(github, settings, pull, risk)
    if report.merge.merged:
        report.deployment = _verify_pages(settings, publishable, result.files, fetch_page)
        if report.deployment.startswith("failed"):
            report.notes.append("merge succeeded but the public page did not verify; no rollback was attempted")
    elif report.merge.auto_merge_enabled:
        report.deployment = "pending until GitHub auto-merge completes"
    else:
        report.deployment = "not published"

    for pr, _item in relevant:
        if pr.key in keys:
            outcome = f"pr:{pull.number}"
            if report.merge and report.merge.merged:
                outcome = f"merged:{pull.number}"
            note_handled(scratch.state_for(pr.repo), pending_by_repo[pr.repo], pr.key, outcome)
            progress = True
    persist()
    return report


def main() -> int:
    try:
        settings = load_settings()
    except (ValueError, TypeError) as exc:
        report = RunReport(dry_run=True, auto_publish=False, status="misconfigured", error=str(exc))
        emit(report)
        return report.exit_code
    if settings.disabled:
        report = RunReport(dry_run=settings.dry_run, auto_publish=settings.auto_publish, status="disabled")
        report.notes.append("Emergency stop is active (DOCS_AGENT_DISABLED).")
        emit(report)
        return 0
    if not settings.github_token:
        report = RunReport(
            dry_run=settings.dry_run,
            auto_publish=settings.auto_publish,
            status="misconfigured",
            error="GITHUB_TOKEN is not set. No pull request, merge, or checkpoint write was attempted.",
        )
        emit(report)
        return 1
    root = _repo_root()
    github = GitHubClient(settings.github_token, settings.docs_repo, timeout=settings.request_timeout)
    llm = LLMClient(settings)

    def build():
        return yarn_build(root, settings.build_timeout)

    report = execute(
        settings,
        github,
        llm,
        root,
        build,
        lambda url: fetch_public_page(url, timeout=settings.request_timeout),
        datetime.now(timezone.utc),
    )
    emit(report)
    return report.exit_code
