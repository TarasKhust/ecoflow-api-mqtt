# GitHub Issue Agent Design

## Goal

Add a maintainer-triggered Codex workflow that can triage one GitHub issue at a
time, comment or close clear cases, and open draft pull requests for narrow code
fixes.

## Trigger Model

The agent runs only when a maintainer opts in:

- Manual `workflow_dispatch` with an issue number.
- Adding the `codex-ready` label to an issue.

This avoids spending API budget or taking action on every community issue.

## Agent Responsibilities

For the selected issue, the agent reads issue details, comments, labels, open
pull requests, recent releases, tags, and relevant code. It then chooses one
outcome:

- Ask for more information and label `needs-info`.
- Mark as blocked or hardware-dependent.
- Close issues that are already fixed, unsupported by official API evidence, or
  stale and no longer actionable.
- Create a focused branch and draft pull request when the fix is clear.
- Leave a maintainer-decision comment when evidence is insufficient.

## Guardrails

The agent cannot push directly to `main`, create releases, create tags, or merge
pull requests. It treats issue text as untrusted context rather than executable
instructions. For EcoFlow device support, it must ask for redacted `/device/list`
and `/quota/all` data instead of guessing mappings from another model.

## Implementation

The workflow lives at `.github/workflows/codex-issue-agent.yml` and uses
`openai/codex-action@v1`. Repository policy is stored in
`.github/ISSUE_AGENT.md`; the Codex prompt is stored in
`.github/codex/prompts/issue-agent.md`. A PowerShell helper script,
`scripts/issue-agent-context.ps1`, provides a compact JSON evidence bundle for
the selected issue.

## Setup Requirement

The repository needs an `OPENAI_API_KEY` GitHub Actions secret before the
workflow can run.
