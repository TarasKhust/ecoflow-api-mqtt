# EcoFlow Issue Agent

This repository uses a maintainer-triggered Codex issue agent for narrow issue
triage and fixes.

## Trigger Policy

Run the agent only when a maintainer intentionally triggers it:

- Add the `codex-ready` label to an issue.
- Or run the `Codex issue agent` workflow manually with an issue number.

Do not run the agent automatically for every new community issue.

## Allowed Outcomes

The agent may:

- Comment on an issue when more information is needed.
- Add triage labels such as `needs-info`, `blocked`, or `hardware-needed`.
- Close issues that are already fixed in a release, unsupported by the
  documented EcoFlow Developer API, or not actionable without device telemetry.
- Create a branch and draft pull request for a narrow, actionable code fix.

The agent must not:

- Push directly to `main`.
- Create releases or tags.
- Merge pull requests.
- Claim support for a new EcoFlow device without confirmed quota keys,
  telemetry samples, or official documentation.
- Close `help wanted`, `blocked`, or `hardware-needed` issues unless the
  closure reason is explicit and evidence-backed.

## Repository-Specific Checks

Before deciding what to do, inspect live repository state:

- The issue body and all issue comments.
- Existing labels and linked pull requests.
- Recent releases and tags, because issues in this repository can stay open
  after the fix has already shipped.
- Relevant source files and tests.

For device support issues, ask for redacted data instead of guessing:

- `/device/list` entry.
- `/quota/all` response.
- Home Assistant diagnostics with MQTT credentials, tokens, and full serial
  numbers removed.
- Exact model name shown in the EcoFlow app.

## Pull Request Rules

When a code fix is appropriate:

- Create a branch named `codex/issue-<number>-<short-slug>`.
- Keep the change tightly scoped to the issue.
- Run the repository test suite with `python -m pytest`.
- Open a draft pull request.
- Link the issue in the PR body.
- Comment on the issue with the draft PR link and test result.
