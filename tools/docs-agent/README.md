# Docs agent

A single Python program that proposes small, sourced updates to the public
Docusaurus site. It runs from GitHub Actions. It does not use a vector
database, a multi-agent framework, or a long-running server.

The scheduled workflow is **report-only** until a maintainer edits it.
`AUTO_PUBLISH` defaults to false. The first runs after this lands do not
open pull requests and do not publish.

## What it does

1. Read the checkpoint (an issue titled `docs-agent checkpoint`).
2. List pull requests merged to `main` since that watermark in:
   - `BotStacks/botstacks-sandbox-build`
   - `BotStacks/botstacks-landing-page`
3. Drop dependency bumps, test-only changes, Sentry work, refactors, and
   the agent's own pull requests. Pull requests merged only into `Staging`
   are ignored. A `github-actions` promotion of `Staging` into `main` is
   considered, because that is the commit that reaches `main`.
4. Match the remaining changes to a few existing docs pages by path and
   keywords. No model call happens when nothing matches.
5. Ask one chat-completions model for exact snippet replacements. Repository
   text is wrapped as untrusted data.
6. Classify every proposal with deterministic rules. The model's own risk
   label is ignored.
7. Validate snippet placement, frontmatter, new links, secrets, path
   limits, and `yarn build`.
8. Open at most one docs pull request, or reuse an open agent pull request
   for the same source keys.
9. Merge only when `AUTO_PUBLISH=true`, the batch is `AUTO_ELIGIBLE`, branch
   rules are readable, and those rules do not require a review or another
   control the agent would have to bypass.
10. After a merge, request the affected `https://docs.botstacks.ai` URL.
    There is no deployment workflow in this repository. Publishing stays
    with whatever already hosts the site. A failed URL check is reported.
    The agent does not roll the site back and does not edit deploy config.

A merged product pull request is not treated as proof that customers have
the change. Public-availability wording is allowed only when `release-prod`
succeeded for that commit in the build repository, or `deploy` succeeded
for that commit in the landing-page repository. Sandbox `deploy` success
is not enough. Anything less stays `REVIEW_REQUIRED`.

## Layout

```
tools/docs-agent/docs_agent/   program (stdlib only)
tools/docs-agent/tests/        unittest suite
.github/workflows/docs-agent.yml
```

The agent does not modify product application code. It will only commit
files under `docs/**/*.md` and `docs/**/*.mdx`. It will not edit
`sidebars.ts`, `_category_.json`, `docusaurus.config.ts`, package scripts,
workflows, or deployment files. It will not add or delete a page.

## GitHub App

Create one GitHub App, install it on these three repositories only, and
store the credentials as Actions secrets on `docusaurus-docs`:

| Secret | Purpose |
| --- | --- |
| `DOCS_AGENT_APP_ID` | App id |
| `DOCS_AGENT_APP_PRIVATE_KEY` | App private key (PEM) |
| `DOCS_AGENT_LLM_API_KEY` | Key for the approved chat-completions API |

App permissions:

| Permission | Level | Why |
| --- | --- | --- |
| Metadata | Read | Required by GitHub |
| Contents | Read and write | Read source diffs. Commit a branch in the docs repo |
| Pull requests | Read and write | Read merged product PRs. Open and merge a docs PR |
| Issues | Read and write | Checkpoint issue and labels |
| Checks | Read | See required status checks before merging |
| Actions | Read | Read `deploy` and `release-prod` conclusions |

Do not grant Administration. The agent reads branch rules with the
repository rules API. If that call is not allowed, it leaves the pull
request open instead of assuming the branch is unprotected.

GitHub applies one permission set to every repository on the installation.
The program refuses every write whose repository is not
`BotStacks/docusaurus-docs`. Source repositories are read-only in code
even though the token is allowed to write.

Optional repository variables:

| Variable | Default |
| --- | --- |
| `DOCS_AGENT_LLM_API_BASE` | `https://api.openai.com/v1` |
| `DOCS_AGENT_LLM_MODEL` | `gpt-4.1-mini` |
| `DOCS_AGENT_DISABLED` | unset. Set to `true` to stop the agent |

The model endpoint must accept `POST /chat/completions` with a bearer key.
Point `DOCS_AGENT_LLM_API_BASE` at the approved provider. The key is sent
only on the `Authorization` header.

## Schedule

`.github/workflows/docs-agent.yml` runs at **07:00 UTC** every day
(`cron: "0 7 * * *"`). It also runs on `workflow_dispatch`.

Scheduled values are hard-coded in the workflow:

- `DRY_RUN=true`
- `AUTO_PUBLISH=false`

A manual run starts with the same safe inputs. Change them on the dispatch
form for one run.

Concurrency group `docs-agent` does not cancel an in-progress run.
The job timeout is 30 minutes. API timeouts, diff size, page count, and
model tokens are capped in `docs_agent/config.py`.

## Manual dry run

From a checkout, with a token that can read the two source repositories:

```bash
cd /path/to/docusaurus-docs
PYTHONPATH=tools/docs-agent \
DRY_RUN=true \
AUTO_PUBLISH=false \
GITHUB_TOKEN="$GITHUB_TOKEN" \
LLM_API_KEY="$LLM_API_KEY" \
python3 -m docs_agent
```

Dry run still calls GitHub and, when there is something to draft, the model.
It does **not** open a pull request, merge, publish, or update the checkpoint.

In Actions: Actions → docs-agent → Run workflow. Leave **Dry run** checked
and **Auto publish** unchecked.

Without `GITHUB_TOKEN` the process exits 1 and writes a summary. It does
not touch the repository.

## Turning on publishing later

Do this only after the App, secrets, and a dry run look right.

1. Dispatch one live run with **Dry run** unchecked and **Auto publish**
   unchecked. The agent may open a pull request. It will not merge.
2. Confirm the pull request, the checks, and the checkpoint issue.
3. To let later runs merge `AUTO_ELIGIBLE` changes, edit the schedule
   expressions in `.github/workflows/docs-agent.yml` so the scheduled
   `DRY_RUN` literal is `false` and the scheduled `AUTO_PUBLISH` literal is
   `true`. Review that edit like any other change.
4. If branch protection requires a review, the agent leaves the pull request
   open and says so. It will not approve its own work, will not use an admin
   bypass, and will not force-push `main`.

Pull requests that were already opened are reconsidered on a later
`AUTO_PUBLISH=true` run when they are still open, not drafts, and the body
is classified `AUTO_ELIGIBLE`.

## Checks before a pull request

- The snippet occurs exactly once.
- Frontmatter `id`, `slug`, `sidebar_position`, and `sidebar_label` stay put.
- No new broken internal link, compared with the links already in the tree.
- Secret, customer-email, internal-operations, and unsafe-URL scans.
- At most 5 files and 80 changed lines (both configurable).
- `yarn build` passes. `onBrokenLinks` is already `throw`.
- Every edit cites a source pull request and a file that pull request changed.
- No second agent pull request for the same pages.

`BLOCKED` output (secrets, customer data, internal operations, injection
text, unsafe URLs) is not committed. `REVIEW_REQUIRED` output is a draft
pull request. `AUTO_ELIGIBLE` output is a normal pull request and is merged
only under the rules above.

## Tests and build

```bash
cd tools/docs-agent
python3 -m unittest discover -s tests -v
cd ../..
yarn build
```

The suite covers a new docs change, nothing relevant, a missed day, a
duplicate pull request, an unverified feature, a bad source claim, a
secret, prompt injection, a failed docs build, a new broken link, a GitHub
failure, a model failure, an allowed merge, a review-required branch rule,
a failed public URL check, and checkpoint ordering. Dry run is asserted not
to write.

## Model use

There is at most one completion per run, and only when a merged pull request
survives the filters and matches an existing page. Input is capped (about
8 KB of diff plus 6 KB per matched page, at most 5 pull requests). Output is
capped at 2,000 tokens. Temperature is 0.

Most days should send nothing, because dependency, test, and observability
merges are ignored before the model is called. A day with a real product
change is one small request. Confirm the price of `DOCS_AGENT_LLM_MODEL`
with the provider; at typical mini-model rates this stays well under a
dollar per run. Set `LLM_MAX_TOKENS` if the approved model needs a lower cap.

## Security and rollback

- Workflow token permissions are `contents: read`. The App token does the
  writes, and only in the docs repository.
- Secrets are not printed and are stripped from errors and from model input.
- The checkpoint stores pull-request ids, outcomes, and timestamps. It does
  not store diffs or document text.
- Failed validation does not move the watermark past the failed item.
  After 3 attempts the item is held and the queue can continue.
- The agent does not process docs pull requests whose branch starts with
  `docs-agent/` as if they were product changes.
- To roll back a published docs change, revert the docs commit with a normal
  pull request. Do not force-push `main`.
- To roll back this agent, disable the workflow or revert this change.
  Existing docs commits stay until they are reverted on their own.

## Emergency stop

Either of these stops publishing immediately:

1. GitHub → Actions → docs-agent → **Disable workflow**.
2. Repository variable `DOCS_AGENT_DISABLED` = `true`.

Setting `AUTO_PUBLISH=false` stops merges. A dry run also stops pull
requests and checkpoint updates. Disabling the workflow is the full stop.
