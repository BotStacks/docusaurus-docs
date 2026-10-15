"""In-memory GitHub and model doubles for the run tests."""

from __future__ import annotations

from docs_agent.github_api import GitHubError
from docs_agent.llm import LLMError
from docs_agent.models import AgentPull, BranchRules


class FakeGitHub:
    def __init__(self):
        self.prs: dict = {}
        self.files: dict = {}
        self.runs: dict = {}
        self.rules = BranchRules(readable=True, required_reviews=0)
        self.agent_prs: list[AgentPull] = []
        self.checkpoint = None
        self.writes = 0
        self.opened: list[AgentPull] = []
        self.merges: list[int] = []
        self.auto_merges: list[str] = []
        self.commits: list[dict] = []
        self.fail: str | None = None
        self.conclusions = {"docs-build": "success"}
        self.mergeable = True

    def list_merged_prs(self, repo, since, limit):
        if self.fail == "list":
            raise GitHubError("GitHub GET /pulls returned 500")
        found = [pr for pr in self.prs.get(repo, []) if pr.merged_at >= since]
        return found[:limit]

    def list_pr_files(self, repo, number):
        return tuple(self.files.get((repo, number), ()))

    def workflow_runs(self, repo, sha):
        return list(self.runs.get((repo, sha), []))

    def branch_rules(self, repo, branch):
        return self.rules

    def list_agent_prs(self, label):
        return list(self.agent_prs)

    def read_checkpoint(self):
        if self.fail == "checkpoint":
            raise GitHubError("checkpoint read failed token=should-not-leak")
        return self.checkpoint

    def write_checkpoint(self, checkpoint):
        self.writes += 1
        self.checkpoint = checkpoint

    def create_branch_commit(self, branch, files, message):
        self.commits.append({"branch": branch, "files": files, "message": message})
        return "commitsha"

    def open_pull(self, branch, title, body, draft, labels):
        pull = AgentPull(
            number=42,
            url="https://github.com/BotStacks/docusaurus-docs/pull/42",
            draft=draft,
            body=body,
            files=tuple(self.commits[-1]["files"]) if self.commits else (),
            node_id="PR_node",
            head_sha="commitsha",
            mergeable=True,
        )
        self.opened.append(pull)
        return pull

    def get_pull(self, number):
        return AgentPull(
            number=number,
            url=f"https://github.com/BotStacks/docusaurus-docs/pull/{number}",
            draft=False,
            body="",
            files=(),
            node_id="PR_node",
            head_sha="commitsha",
            mergeable=self.mergeable,
        )

    def check_conclusions(self, sha):
        return dict(self.conclusions)

    def enable_auto_merge(self, node_id):
        self.auto_merges.append(node_id)

    def merge_pull(self, number, title):
        if "force" in title.lower():
            raise GitHubError("refusing force")
        self.merges.append(number)


class FakeLLM:
    def __init__(self, proposals=None, error: str | None = None):
        self.proposals = list(proposals or [])
        self.error = error
        self.calls = 0

    def propose(self, prs, pages, evidence, truncated):
        self.calls += 1
        if self.error:
            raise LLMError(self.error)
        return list(self.proposals)


class FakeWeb:
    def __init__(self, status: int = 200, body: str = ""):
        self.status = status
        self.body = body
        self.urls: list[str] = []

    def __call__(self, url: str):
        self.urls.append(url)
        return self.status, self.body
