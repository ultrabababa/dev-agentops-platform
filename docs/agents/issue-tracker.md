# Issue tracker: GitHub

Issues and PRDs for this repo live in GitHub Issues for `ultrabababa/dev-agentops-platform`. Use the `gh` CLI for issue operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..." --label "ready-for-agent"`.
- **Read an issue**: `gh issue view <number> --comments`.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments`.
- **Comment on an issue**: `gh issue comment <number> --body "..."`.
- **Apply a label**: `gh issue edit <number> --add-label "..."`.
- **Remove a label**: `gh issue edit <number> --remove-label "..."`.
- **Close an issue**: `gh issue close <number> --comment "..."`.

Run `gh` commands from inside this repository so the repository can be inferred from `git remote -v`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue and apply the appropriate triage label. For PRDs that are ready for implementation, apply `ready-for-agent`.

## Environment note

If an agent cannot find `gh` in its shell, treat that as an environment/PATH problem rather than a tracker policy change.
