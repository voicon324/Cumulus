---
name: cumulus
description: >
  Continuous project memory and capability optimization for AI coding agents.
  Use when starting or maintaining a software repository where the coding agent
  should remember project conventions and architecture decisions over time,
  detect repeated failures or high-effort work, discover relevant Agent Skills,
  MCP servers, developer tools and workflows, and improve its capabilities as
  the project evolves. Useful for Codex, Claude Code, Cursor, Gemini CLI and
  other Agent Skills-compatible coding agents.
license: MIT
compatibility: Requires a repository and Python 3 for the optional local Cumulus runtime. The skill instructions themselves are portable across Agent Skills-compatible coding agents.
---

# Cumulus

Use Cumulus as a project-aware capability layer for coding agents.

The core idea is simple:

```text
understand project
→ work
→ observe meaningful outcomes
→ detect repeated gaps or new domains
→ discover prior art / skills / tools
→ trial improvements
→ validate
→ keep or rollback
```

Do not optimize from a single ordinary failure. Accumulate evidence first.

## Trigger this skill when

The user wants any of the following:

- persistent project memory for a coding agent;
- a coding agent that learns repository conventions over time;
- a self-improving coding-agent workflow;
- automatic or assisted discovery of Agent Skills, MCP servers or developer tools;
- repeated-failure or capability-gap detection;
- project-aware agent retrospectives;
- an agent to improve as a repository evolves;
- reusable technical decisions and lessons without storing full chat transcripts.

Also trigger when entering a repository that already contains `.cumulus/`.

## Do not trigger for

- one tiny edit in an unrelated repo with no need for persistent agent context;
- generic coding questions where project history does not matter;
- silently installing arbitrary third-party code without inspection.

## Start of a repository

If the full Cumulus runtime is not installed and the user wants persistent project behavior, recommend the repository-local installer:

```bash
curl -fsSL https://raw.githubusercontent.com/voicon324/Cumulus/main/install.sh | bash
```

If `.cumulus/config.json` exists, read it before substantial work.

If `./cumulus` exists, use the local runtime instead of recreating state manually.

## Understand before asking

Inspect the repository before asking questions.

Prefer existing evidence from:

- README and AGENTS.md;
- package manifests and lock files;
- source tree;
- CI configuration;
- Docker/infrastructure files;
- tests;
- environment examples;
- existing architecture docs.

Only ask the user questions whose answers materially affect the next decision.

## Substantial task lifecycle

When the local runtime is available, start substantial work with:

```bash
./cumulus task-start \
  --task-id <id> \
  --domain <domain> \
  --goal "<goal>"
```

Finish with:

```bash
./cumulus task-end \
  --result success \
  --effort medium
```

Record meaningful retries, manual intervention, user correction, high effort, or failure.

Do not log full transcripts or every small edit.

## New domains: discover prior art first

When a specialized new domain appears:

```bash
./cumulus scout-plan --domain <domain>
```

Then search broadly enough to capture how experienced developers and agents already solve the problem.

Search order:

1. official/vendor Agent Skills and documentation;
2. maintained Agent Skill registries and public repositories;
3. MCP servers, plugins, CLIs and developer tools;
4. established workflows and best-practice references;
5. custom skill only when existing options are inadequate.

Expand the domain semantically.

Example:

```text
"payments"
→ Stripe
→ webhooks
→ idempotency
→ refunds
→ payment security
→ payment testing
```

Do not merely search the literal user phrase.

## Evaluate discovered capabilities

Read the actual skill/tool instructions before recommending them.

Evaluate:

- relevance to this repository;
- maintenance and freshness;
- source reputation;
- permissions and security;
- compatibility;
- documentation quality;
- reversibility;
- evidence of real-world use.

Classify each candidate:

- **INSTALL** — directly useful and trustworthy enough to use;
- **ADAPT** — useful pattern but needs project-specific changes;
- **LEARN** — valuable prior art without installation;
- **SKIP** — stale, duplicate, unsafe or low-value.

Custom skill creation is a fallback, not the default.

## Capability debt

Use repeated evidence rather than intuition.

Signals include:

- repeated same-domain failures;
- repeated manual intervention;
- repeated user correction;
- several high-effort tasks in the same domain;
- a new recurring domain with no supporting capability;
- stale tooling after a major dependency change.

With the runtime:

```bash
./cumulus analyze
./cumulus improvements
```

One ordinary failure must not rewrite a project or global skill.

## Improvement lifecycle

Use:

```text
queued
→ scout / evaluate
→ trial
→ validate
→ keep | rollback
```

When available:

```bash
./cumulus trial-start <id> \
  --candidate <candidate> \
  --before '{"success":0.5}'

./cumulus trial-finish <id> \
  --outcome keep \
  --after '{"success":0.9}' \
  --reason "fewer retries and no manual intervention"
```

Prefer measurable evidence such as:

- success/failure count;
- retry count;
- manual intervention;
- user correction;
- task effort;
- regressions.

## Autonomy

Read `.cumulus/config.json` before capability changes.

- **0 — Observe:** maintain project memory only.
- **1 — Suggest:** also queue justified improvements.
- **2 — Safe auto:** may apply low-risk, reversible, project-local changes.
- **3 — Full auto within permission:** may scout, trial and validate reversible improvements.

Regardless of level, require explicit approval for:

- credentials or secrets;
- paid services;
- destructive actions;
- security-sensitive changes;
- system-level changes;
- irreversible external actions.

## Project memory scopes

Separate:

- **task facts** — what happened once;
- **project memory** — repository-specific conventions and decisions;
- **domain lessons** — reusable patterns for a technical domain;
- **global agent lessons** — only patterns supported across multiple projects.

Do not turn one project preference into a global rule.

## Durable decisions

With the runtime:

```bash
./cumulus decide \
  --type architecture \
  --domain architecture \
  --decision "Use a modular monolith" \
  --reason "Current scale does not justify microservices"
```

User corrections are high-value evidence and should update project behavior.

## Review with the user

Review is independent of the autonomy level.

When the user asks what should improve:

```bash
./cumulus review
```

Present:

- what is working well;
- recurring capability debt;
- emerging domains;
- candidate skills/tools/workflows;
- evidence for each recommendation;
- risk and expected benefit.

Let the user choose what to apply unless the configured autonomy already permits the change.

## Health and memory

Useful runtime commands:

```bash
./cumulus status
./cumulus profile
./cumulus compact
./cumulus doctor
```

Keep bookkeeping lightweight. Cumulus exists to reduce rediscovery and repeated mistakes, not to create process overhead.
