"""Human-readable run summary for the Actions log and step summary."""

from __future__ import annotations

import os

from docs_agent.models import RunReport


def render(report: RunReport) -> str:
    skipped = "\n".join(f"- `{key}`: {reason}" for key, reason in report.skipped) or "- none"
    proposals = []
    for item in report.proposals:
        proposals.append(f"- `{item.risk.value}` `{item.path}` ({', '.join(item.source_prs) or 'no source'}): {item.summary}")
    proposal_block = "\n".join(proposals) or "- none"
    validation = "\n".join(f"- {item}" for item in report.validation_errors) or "- none"
    notes = "\n".join(f"- {item}" for item in report.notes) or "- none"
    merge = "not attempted"
    if report.merge is not None:
        if report.merge.merged:
            merge = "merged"
        elif report.merge.auto_merge_enabled:
            merge = "auto-merge enabled"
        elif report.merge.blocked:
            merge = "blocked: " + report.merge.reason
        else:
            merge = report.merge.reason or "not merged"
    considered = "\n".join(f"- `{item}`" for item in report.considered) or "- none"
    return f"""# Docs agent summary

- Mode: {"dry run" if report.dry_run else "live"}
- Auto-publish: {"on" if report.auto_publish else "off"}
- Status: {report.status}
- Error: {report.error or "none"}

## Source pull requests considered
{considered}

## Skipped
{skipped}

## Proposals
{proposal_block}

## Validation
{validation}

## Pull request
{report.pull_action or "none"}
{report.pull_url}

## Merge
{merge}

## Deployment
{report.deployment or "not checked"}

## Notes
{notes}
"""


def emit(report: RunReport) -> None:
    text = render(report)
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(text)
            handle.write("\n")
    if report.status in {"error", "misconfigured"} and report.error:
        print(f"::error::{report.error}")
    elif report.validation_errors:
        print("::warning::" + report.validation_errors[0])
    elif report.merge and report.merge.blocked:
        print("::warning::" + report.merge.reason)
