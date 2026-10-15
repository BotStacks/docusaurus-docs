"""Small GitHub REST client.

Write methods refuse every repository except the documentation repository.
Tokens are sent only on the Authorization header and stripped from errors.
"""

from __future__ import annotations

import json
from typing import Any
from urllib import error, parse, request

from docs_agent.checkpoint import CHECKPOINT_TITLE, Checkpoint, dumps, loads
from docs_agent.models import AgentPull, BranchRules, ChangedFile, PullRequest
from docs_agent.redact import redact


class GitHubError(RuntimeError):
    pass


def _next_link(header: str | None) -> str | None:
    if not header:
        return None
    for part in header.split(","):
        if 'rel="next"' in part:
            return part.split(";")[0].strip().strip("<>")
    return None


class GitHubClient:
    def __init__(self, token: str, docs_repo: str, *, base_url: str = "https://api.github.com", timeout: float = 30.0, http=None):
        self._token = token
        self.docs_repo = docs_repo
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._http = http or self._urllib
        self._checkpoint_issue: int | None = None

    def _urllib(self, method: str, url: str, body: bytes | None, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
        req = request.Request(url, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self._timeout) as response:
                return response.status, dict(response.headers), response.read()
        except error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()

    def _request(self, method: str, url: str, payload: dict | None = None) -> tuple[int, dict[str, str], Any]:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "botstacks-docs-agent",
        }
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self._token and self._token in url:
            raise GitHubError("refusing to place the token in a URL")
        try:
            status, response_headers, raw = self._http(method, url, body, headers)
        except Exception as exc:
            raise GitHubError(redact(str(exc), [self._token])) from None
        text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
        if status >= 400:
            raise GitHubError(redact(f"GitHub {method} {parse.urlparse(url).path} returned {status}: {text[:240]}", [self._token]))
        if not text:
            return status, response_headers, None
        try:
            return status, response_headers, json.loads(text)
        except json.JSONDecodeError as exc:
            raise GitHubError("GitHub returned non-JSON") from exc

    def _paged(self, url: str, pages: int = 3) -> list[Any]:
        items: list[Any] = []
        for _ in range(pages):
            _status, headers, payload = self._request("GET", url)
            if isinstance(payload, dict):
                return [payload]
            items.extend(payload or [])
            nxt = _next_link(headers.get("Link") or headers.get("link"))
            if not nxt:
                break
            url = nxt
        return items

    def _guard_write(self, repo: str) -> None:
        if repo.lower() != self.docs_repo.lower():
            raise GitHubError(f"refusing to write to {repo}")

    def list_merged_prs(self, repo: str, since: str, limit: int) -> list[PullRequest]:
        url = f"{self._base}/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=30"
        found: list[PullRequest] = []
        for item in self._paged(url):
            merged_at = item.get("merged_at")
            if not merged_at:
                continue
            if merged_at < since:
                continue
            found.append(
                PullRequest(
                    repo=repo,
                    number=int(item["number"]),
                    title=item.get("title") or "",
                    body=item.get("body") or "",
                    merged_at=merged_at,
                    base=(item.get("base") or {}).get("ref") or "",
                    head=(item.get("head") or {}).get("ref") or "",
                    author=(item.get("user") or {}).get("login") or "",
                    merge_commit_sha=item.get("merge_commit_sha") or "",
                    labels=tuple(label.get("name", "") for label in item.get("labels") or []),
                )
            )
            if len(found) >= limit:
                break
        return found

    def list_pr_files(self, repo: str, number: int) -> tuple[ChangedFile, ...]:
        url = f"{self._base}/repos/{repo}/pulls/{number}/files?per_page=50"
        files = []
        for item in self._paged(url, pages=2):
            files.append(
                ChangedFile(
                    filename=item.get("filename") or "",
                    status=item.get("status") or "modified",
                    patch=item.get("patch") or "",
                )
            )
        return tuple(files)

    def workflow_runs(self, repo: str, sha: str) -> list[dict[str, Any]]:
        if not sha:
            return []
        url = f"{self._base}/repos/{repo}/actions/runs?head_sha={parse.quote(sha)}&per_page=20"
        _status, _headers, payload = self._request("GET", url)
        return list((payload or {}).get("workflow_runs") or [])

    def branch_rules(self, repo: str, branch: str) -> BranchRules:
        url = f"{self._base}/repos/{repo}/rules/branches/{parse.quote(branch)}"
        try:
            _status, _headers, payload = self._request("GET", url)
        except GitHubError as exc:
            return BranchRules(readable=False, blocks_auto_merge=True, detail=str(exc)[:200])
        if not isinstance(payload, list):
            return BranchRules(readable=False, blocks_auto_merge=True, detail="unexpected rules payload")
        reviews = 0
        checks: list[str] = []
        blocking = False
        for rule in payload:
            kind = rule.get("type")
            params = rule.get("parameters") or {}
            if kind == "pull_request":
                reviews = max(reviews, int(params.get("required_approving_review_count") or 0))
                if params.get("require_code_owner_review") or params.get("require_last_push_approval"):
                    reviews = max(reviews, 1)
            elif kind == "required_status_checks":
                for check in params.get("required_status_checks") or []:
                    context = check.get("context")
                    if context:
                        checks.append(context)
            elif kind in {"required_signatures", "required_linear_history", "copilot_code_review"}:
                blocking = True
            elif kind not in {"deletion", "non_fast_forward", "creation"}:
                blocking = True
        return BranchRules(
            readable=True,
            required_reviews=reviews,
            required_checks=tuple(checks),
            blocks_auto_merge=blocking,
        )

    def list_agent_prs(self, label: str) -> list[AgentPull]:
        url = f"{self._base}/repos/{self.docs_repo}/pulls?state=open&per_page=20"
        pulls = []
        items = self._paged(url, pages=1)
        for item in items:
            labels = [label_item.get("name") for label_item in item.get("labels") or []]
            if label not in labels and not str(item.get("head", {}).get("ref", "")).startswith("docs-agent/"):
                continue
            number = int(item["number"])
            files = tuple(changed.filename for changed in self.list_pr_files(self.docs_repo, number))
            pulls.append(
                AgentPull(
                    number=number,
                    url=item.get("html_url") or "",
                    draft=bool(item.get("draft")),
                    body=item.get("body") or "",
                    files=files,
                    node_id=item.get("node_id") or "",
                    head_sha=(item.get("head") or {}).get("sha") or "",
                    mergeable=item.get("mergeable"),
                )
            )
        return pulls

    def read_checkpoint(self) -> Checkpoint | None:
        url = (
            f"{self._base}/repos/{self.docs_repo}/issues"
            f"?state=open&labels=docs-agent-checkpoint&per_page=10"
        )
        try:
            items = self._paged(url, pages=1)
        except GitHubError as exc:
            if "returned 404" in str(exc):
                return None
            raise
        for item in items:
            if "pull_request" in item:
                continue
            if item.get("title") != CHECKPOINT_TITLE:
                continue
            self._checkpoint_issue = int(item["number"])
            return loads(item.get("body") or "")
        return None

    def write_checkpoint(self, checkpoint: Checkpoint) -> None:
        self._guard_write(self.docs_repo)
        body = dumps(checkpoint)
        if self._checkpoint_issue is None:
            self.read_checkpoint()
        if self._checkpoint_issue is None:
            self._ensure_label("docs-agent-checkpoint", "Automation state for the docs agent")
            _status, _headers, created = self._request(
                "POST",
                f"{self._base}/repos/{self.docs_repo}/issues",
                {"title": CHECKPOINT_TITLE, "body": body, "labels": ["docs-agent-checkpoint"]},
            )
            self._checkpoint_issue = int(created["number"])
            return
        self._request(
            "PATCH",
            f"{self._base}/repos/{self.docs_repo}/issues/{self._checkpoint_issue}",
            {"body": body},
        )

    def _ensure_label(self, name: str, description: str) -> None:
        self._guard_write(self.docs_repo)
        try:
            self._request(
                "POST",
                f"{self._base}/repos/{self.docs_repo}/labels",
                {"name": name, "color": "1D76DB", "description": description},
            )
        except GitHubError as exc:
            if "422" not in str(exc) and "already_exists" not in str(exc):
                return

    def create_branch_commit(self, branch: str, files: dict[str, str], message: str) -> str:
        self._guard_write(self.docs_repo)
        ref_url = f"{self._base}/repos/{self.docs_repo}/git/ref/heads/main"
        _status, _headers, ref = self._request("GET", ref_url)
        base_sha = ref["object"]["sha"]
        self._request(
            "POST",
            f"{self._base}/repos/{self.docs_repo}/git/refs",
            {"ref": f"refs/heads/{branch}", "sha": base_sha},
        )
        tree_entries = []
        for path, content in sorted(files.items()):
            _status, _headers, blob = self._request(
                "POST",
                f"{self._base}/repos/{self.docs_repo}/git/blobs",
                {"content": content, "encoding": "utf-8"},
            )
            tree_entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        _status, _headers, tree = self._request(
            "POST",
            f"{self._base}/repos/{self.docs_repo}/git/trees",
            {"base_tree": base_sha, "tree": tree_entries},
        )
        _status, _headers, commit = self._request(
            "POST",
            f"{self._base}/repos/{self.docs_repo}/git/commits",
            {
                "message": message,
                "tree": tree["sha"],
                "parents": [base_sha],
                "author": {"name": "BotStacks Docs Agent", "email": "docs-agent@users.noreply.github.com"},
            },
        )
        self._request(
            "PATCH",
            f"{self._base}/repos/{self.docs_repo}/git/refs/heads/{parse.quote(branch, safe='/')}",
            {"sha": commit["sha"], "force": False},
        )
        return commit["sha"]

    def open_pull(self, branch: str, title: str, body: str, draft: bool, labels: list[str]) -> AgentPull:
        self._guard_write(self.docs_repo)
        for label in labels:
            self._ensure_label(label, "Public docs agent")
        _status, _headers, created = self._request(
            "POST",
            f"{self._base}/repos/{self.docs_repo}/pulls",
            {
                "title": title,
                "head": branch,
                "base": "main",
                "body": body,
                "draft": draft,
            },
        )
        number = int(created["number"])
        if labels:
            try:
                self._request(
                    "POST",
                    f"{self._base}/repos/{self.docs_repo}/issues/{number}/labels",
                    {"labels": labels},
                )
            except GitHubError:
                pass
        return AgentPull(
            number=number,
            url=created.get("html_url") or "",
            draft=draft,
            body=body,
            files=(),
            node_id=created.get("node_id") or "",
            head_sha=(created.get("head") or {}).get("sha") or "",
            mergeable=created.get("mergeable"),
        )

    def get_pull(self, number: int) -> AgentPull:
        _status, _headers, item = self._request("GET", f"{self._base}/repos/{self.docs_repo}/pulls/{number}")
        return AgentPull(
            number=number,
            url=item.get("html_url") or "",
            draft=bool(item.get("draft")),
            body=item.get("body") or "",
            files=(),
            node_id=item.get("node_id") or "",
            head_sha=(item.get("head") or {}).get("sha") or "",
            mergeable=item.get("mergeable"),
        )

    def check_conclusions(self, sha: str) -> dict[str, str]:
        conclusions: dict[str, str] = {}
        if not sha:
            return conclusions
        url = f"{self._base}/repos/{self.docs_repo}/commits/{sha}/check-runs?per_page=50"
        _status, _headers, payload = self._request("GET", url)
        for run in (payload or {}).get("check_runs") or []:
            conclusions[run.get("name") or "check"] = run.get("conclusion") or run.get("status") or "pending"
        status_url = f"{self._base}/repos/{self.docs_repo}/commits/{sha}/status"
        _status, _headers, statuses = self._request("GET", status_url)
        for item in (statuses or {}).get("statuses") or []:
            context = item.get("context") or "status"
            state = item.get("state") or "pending"
            conclusions[context] = "success" if state == "success" else state
        return conclusions

    def enable_auto_merge(self, node_id: str) -> None:
        self._guard_write(self.docs_repo)
        query = """
        mutation($id: ID!) {
          enablePullRequestAutoMerge(input: {pullRequestId: $id, mergeMethod: MERGE}) {
            pullRequest { number }
          }
        }
        """
        self._request("POST", f"{self._base}/graphql", {"query": query, "variables": {"id": node_id}})

    def merge_pull(self, number: int, title: str) -> None:
        self._guard_write(self.docs_repo)
        self._request(
            "PUT",
            f"{self._base}/repos/{self.docs_repo}/pulls/{number}/merge",
            {"merge_method": "merge", "commit_title": title},
        )


def fetch_public_page(url: str, timeout: float = 20.0, http=None) -> tuple[int, str]:
    """GET a docs page. Redirects off the original host are rejected."""
    parsed = parse.urlparse(url)
    if parsed.scheme != "https":
        raise GitHubError("public docs URL must be https")
    getter = http or _get
    status, headers, body = getter(url, timeout)
    location = headers.get("Location") or headers.get("location")
    if status in {301, 302, 303, 307, 308} and location:
        target = parse.urlparse(location)
        if target.netloc and target.netloc != parsed.netloc:
            raise GitHubError("public docs redirect left the docs host")
    return status, body[:200_000]


def _get(url: str, timeout: float) -> tuple[int, dict[str, str], str]:
    req = request.Request(url, headers={"User-Agent": "botstacks-docs-agent"}, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read().decode("utf-8", errors="replace")
