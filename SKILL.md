---
name: cumulus
description: Project-aware capability runtime for coding agents. Use in software repositories to maintain project memory, track task outcomes, detect repeated capability debt or new domains, scout existing skills/tools/workflows, and run evidence-based improvement trials with configurable autonomy.
---

# Cumulus

Treat the coding agent's capability set as a living project dependency.

Cumulus is repository-local and should stay quiet while development is going well. It becomes active when the project changes, a new domain appears, repeated failures accumulate, or the user asks for an optimization review.

## Start of a repository

If `.cumulus/config.json` does not exist:

```bash
./cumulus init --auto-level 1 --goal "<project goal>"
```

Initialization profiles the repo, creates project/capability state, generates a scout baseline, and adds a managed Cumulus block to `AGENTS.md`.

Do not ask the user for information already inferable from the repository.

## Substantial task lifecycle

Start:

```bash
./cumulus task-start --task-id <id> --domain <domain> --goal "<goal>"
```

Finish:

```bash
./cumulus task-end --result success --effort medium
```

When work fails or needs rework, record meaningful retries, manual intervention, or user correction. Do not store full transcripts or every tiny edit.

## New domains and prior art

When a specialized new domain appears:

```bash
./cumulus scout-plan --domain <domain>
```

Then search in this order:

1. official/vendor skills and documentation;
2. maintained public skill registries/repositories;
3. MCP/tool/CLI workflows;
4. custom skill only when existing options are inadequate.

Inspect actual instructions, dependencies, freshness, permissions, security, and project fit. Classify candidates as `install`, `adapt`, `learn`, or `skip`.

## Capability debt

Run:

```bash
./cumulus analyze
```

Default signals include repeated same-domain failures, manual intervention, repeated user correction, high-severity failure, and repeated high-effort tasks.

One ordinary failure is not enough to rewrite a skill.

## Skill provenance

Record selected skills:

```bash
./cumulus skill-add --name <name> --source <source> --ref <commit-or-tag> --domain <domain>
```

Use `.cumulus/skills.lock.json` as the project capability lock.

## Improvement lifecycle

```text
queued -> scout/evaluate -> trial -> keep | rollback
```

Use:

```bash
./cumulus improvements
./cumulus trial-start <id> --candidate <candidate> --before '{"success":0.5}'
./cumulus trial-finish <id> --outcome keep --after '{"success":0.9}' --reason "better outcomes"
```

Prefer measurable evidence such as retries, failures, manual intervention, user corrections, or task effort.

## Autonomy

Read `.cumulus/config.json` before capability changes.

- Level 0: observe and maintain project memory only.
- Level 1: also queue justified suggestions.
- Level 2: may auto-apply low-risk reversible project-local improvements.
- Level 3: may scout/trial/validate reversible improvements within granted permissions.

Credentials, paid services, destructive actions, security-sensitive changes, and system-level changes still require explicit approval.

## Review with the user

Review is a feature, not an autonomy mode:

```bash
./cumulus review
```

Use it when the user asks what the agent should improve after working on the project for a while.

## Durable decisions

```bash
./cumulus decide   --type architecture   --domain architecture   --decision "Use a modular monolith"   --reason "Current scale does not justify microservices"
```

Do not promote project-specific preferences into global rules without evidence across projects.

## Memory and health

```bash
./cumulus compact
./cumulus status
./cumulus doctor
./cumulus profile
```

Keep bookkeeping lightweight. Cumulus exists to reduce rediscovery and repeated mistakes, not to create process overhead.
