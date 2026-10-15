"""Checks that run before a documentation pull request is opened."""

from __future__ import annotations

import difflib
import re
import subprocess
from pathlib import Path
from urllib.parse import urljoin

from docs_agent.config import Settings
from docs_agent.docs_index import load_pages, slug_for
from docs_agent.models import Proposal, ValidationResult
from docs_agent.redact import (
    customer_data_findings,
    injection_findings,
    internal_ops_findings,
    secret_findings,
    unsafe_url_findings,
)

_LINK = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)")
_FM_KEYS = ("id", "slug", "sidebar_position", "sidebar_label")
_FORBIDDEN_PREFIXES = (
    ".github/",
    "package.json",
    "yarn.lock",
    "package-lock.json",
    "docusaurus.config.ts",
    "sidebars.ts",
    "src/",
    "static/",
    "tools/",
)


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    data: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data


def _fences_balanced(text: str) -> bool:
    return text.count("```") % 2 == 0 and text.count("---") >= (2 if text.startswith("---") else 0)


def changed_line_count(before: str, after: str) -> int:
    diff = difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="")
    return sum(
        1
        for line in diff
        if (line.startswith("+") or line.startswith("-")) and not line.startswith(("+++", "---"))
    )


def _resolve(base_slug: str, target: str) -> str | None:
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return None
    if target.startswith("/"):
        return target.rstrip("/") or "/"
    base = base_slug if base_slug.endswith("/") else base_slug.rsplit("/", 1)[0] + "/"
    return urljoin(base, target).rstrip("/") or "/"


def broken_links(files: dict[str, str], slugs: set[str]) -> set[tuple[str, str]]:
    broken: set[tuple[str, str]] = set()
    for path, text in files.items():
        meta = _frontmatter(text)
        slug = slug_for(path, meta)
        for _label, target in _LINK.findall(text):
            resolved = _resolve(slug, target)
            if resolved is None:
                if target.startswith("http://"):
                    broken.add((path, target))
                continue
            if resolved not in slugs:
                broken.add((path, resolved))
    return broken


def apply_proposals(repo_root: Path, proposals: list[Proposal]) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    files: dict[str, str] = {}
    for proposal in proposals:
        path = proposal.path.replace("\\", "/")
        if any(path == prefix or path.startswith(prefix) for prefix in _FORBIDDEN_PREFIXES):
            errors.append(f"{path} is not an approved docs path")
            continue
        if not (path.startswith("docs/") and path.endswith((".md", ".mdx"))):
            errors.append(f"{path} is not a public docs page")
            continue
        if path.endswith("/_category_.json"):
            errors.append(f"{path} would change navigation")
            continue
        disk = repo_root / path
        if not disk.is_file():
            errors.append(f"{path} does not exist; refusing to add a page")
            continue
        original = files.get(path, disk.read_text(encoding="utf-8"))
        count = original.count(proposal.old_snippet)
        if count != 1:
            errors.append(f"{path} snippet matched {count} times")
            continue
        files[path] = original.replace(proposal.old_snippet, proposal.new_snippet, 1)
    return files, errors


def validate(
    repo_root: Path,
    proposals: list[Proposal],
    settings: Settings,
    build_runner,
) -> ValidationResult:
    if not proposals:
        return ValidationResult(ok=True)
    if len({item.path for item in proposals}) > settings.max_files:
        return ValidationResult(ok=False, errors=["too many files"])

    files, errors = apply_proposals(repo_root, proposals)
    if errors:
        return ValidationResult(ok=False, errors=errors)

    total_lines = 0
    originals = {path: (repo_root / path).read_text(encoding="utf-8") for path in files}
    for path, updated in files.items():
        before = originals[path]
        if not updated.strip():
            errors.append(f"{path} would be emptied")
        if before.startswith("---") and not updated.startswith("---"):
            errors.append(f"{path} lost its frontmatter")
        before_meta = _frontmatter(before)
        after_meta = _frontmatter(updated)
        for key in _FM_KEYS:
            if before_meta.get(key) != after_meta.get(key):
                errors.append(f"{path} changes navigation field {key}")
        if before_meta.get("title") and not after_meta.get("title"):
            errors.append(f"{path} dropped its title")
        if not _fences_balanced(updated):
            errors.append(f"{path} has unbalanced fences or frontmatter")
        combined = updated
        if secret_findings(combined) or customer_data_findings(combined):
            errors.append(f"{path} contains sensitive data")
        if injection_findings(updated) or internal_ops_findings(updated) or unsafe_url_findings(updated):
            errors.append(f"{path} failed the safety scan")
        total_lines += changed_line_count(before, updated)
    if total_lines > settings.max_changed_lines:
        errors.append(f"changed lines {total_lines} exceed {settings.max_changed_lines}")
    if errors:
        return ValidationResult(ok=False, errors=errors, files=files, changed_lines=total_lines)

    pages = load_pages(repo_root / "docs")
    slugs = {page.slug for page in pages}
    current = {page.path: page.text for page in pages}
    before_broken = broken_links(current, slugs)
    after_map = dict(current)
    after_map.update(files)
    # Slugs do not change because navigation frontmatter is rejected above.
    new_broken = broken_links(after_map, slugs) - before_broken
    if new_broken:
        sample = ", ".join(f"{path}->{target}" for path, target in sorted(new_broken)[:5])
        errors.append(f"new broken links: {sample}")
        return ValidationResult(ok=False, errors=errors, files=files, changed_lines=total_lines)

    if build_runner is not None:
        ok, detail = build_runner()
        if not ok:
            errors.append(f"docusaurus build failed: {detail[:300]}")
            return ValidationResult(ok=False, errors=errors, files=files, changed_lines=total_lines)

    return ValidationResult(ok=True, files=files, changed_lines=total_lines)


def yarn_build(repo_root: Path, timeout: int) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            ["yarn", "build"],
            cwd=repo_root,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)[:300]
    tail = (completed.stdout + "\n" + completed.stderr)[-1500:]
    return completed.returncode == 0, tail
