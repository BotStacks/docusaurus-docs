"""GitHub client guards: no token leakage and no writes outside the docs repo."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docs_agent.github_api import GitHubClient, GitHubError


class GitHubApiTests(unittest.TestCase):
    def test_errors_do_not_contain_the_token(self):
        token = "super-secret-token-value"

        def http(method, url, body, headers):
            raise RuntimeError(f"connection failed for {token}")

        client = GitHubClient(token, "BotStacks/docusaurus-docs", http=http)
        with self.assertRaises(GitHubError) as caught:
            client.list_merged_prs("BotStacks/botstacks-sandbox-build", "2026-10-01T00:00:00Z", 5)
        self.assertNotIn(token, str(caught.exception))
        self.assertNotIn(token, " ".join(caught.exception.args))

    def test_token_is_not_placed_in_the_url(self):
        seen = {}

        def http(method, url, body, headers):
            seen["url"] = url
            seen["body"] = body
            seen["authorization"] = headers.get("Authorization")
            return 200, {}, b"[]"

        client = GitHubClient("super-secret-token-value", "BotStacks/docusaurus-docs", http=http)
        client.list_merged_prs("BotStacks/botstacks-sandbox-build", "2026-10-01T00:00:00Z", 5)
        self.assertNotIn("super-secret-token-value", seen["url"])
        self.assertIsNone(seen["body"])
        self.assertEqual(seen["authorization"], "Bearer super-secret-token-value")

    def test_write_guard_refuses_source_repositories(self):
        client = GitHubClient("token", "BotStacks/docusaurus-docs", http=lambda *args: (500, {}, b""))
        with self.assertRaises(GitHubError) as caught:
            client._guard_write("BotStacks/botstacks-sandbox-build")
        self.assertIn("refusing to write", str(caught.exception))

    def test_branch_rules_require_review_and_unknown_rules_block_merge(self):
        payload = json.dumps(
            [
                {"type": "pull_request", "parameters": {"required_approving_review_count": 1}},
                {
                    "type": "required_status_checks",
                    "parameters": {"required_status_checks": [{"context": "ci"}]},
                },
            ]
        ).encode()

        def http(method, url, body, headers):
            return 200, {}, payload

        rules = GitHubClient("token", "BotStacks/docusaurus-docs", http=http).branch_rules(
            "BotStacks/docusaurus-docs", "main"
        )
        self.assertTrue(rules.readable)
        self.assertEqual(rules.required_reviews, 1)
        self.assertEqual(rules.required_checks, ("ci",))
        self.assertFalse(rules.blocks_auto_merge)

        unknown = json.dumps([{"type": "required_signatures", "parameters": {}}]).encode()
        rules = GitHubClient("token", "BotStacks/docusaurus-docs", http=lambda *a: (200, {}, unknown)).branch_rules(
            "BotStacks/docusaurus-docs", "main"
        )
        self.assertTrue(rules.blocks_auto_merge)

    def test_unreadable_branch_rules_are_not_treated_as_open(self):
        def http(method, url, body, headers):
            return 403, {}, b'{"message":"Resource not accessible"}'

        rules = GitHubClient("token", "BotStacks/docusaurus-docs", http=http).branch_rules(
            "BotStacks/docusaurus-docs", "main"
        )
        self.assertFalse(rules.readable)
        self.assertTrue(rules.blocks_auto_merge)


if __name__ == "__main__":
    unittest.main()
