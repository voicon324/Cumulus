# Cumulus use cases

Cumulus is intended for repositories where a coding agent benefits from persistent project understanding and capability improvement over time.

## Coding agent keeps forgetting project context

Symptoms:

- the agent repeatedly asks questions already answered in the repository;
- architecture decisions are rediscovered every session;
- conventions drift between tasks;
- the same setup work is repeated.

Cumulus preserves structured project memory and durable decisions rather than requiring full chat transcript replay.

Search intents: `coding agent project memory`, `persistent memory for coding agents`, `repository memory for AI agents`, `project-aware coding agent`.

## Repeated failures in one technical domain

Example: database migrations repeatedly require retries or manual fixes.

Cumulus treats repeated evidence as capability debt, then encourages the agent to scout existing migration skills, workflows and tooling before creating a new custom process.

Search intents: `self improving coding agent`, `coding agent repeated failures`, `agent capability debt`, `continuous agent optimization`.

## A new domain enters the project

Example: a backend project adds Stripe payments.

Instead of immediately coding, the agent can decompose the domain into payments, webhooks, idempotency, refunds, security and testing, then search existing Agent Skills, MCP servers, official docs and developer tools.

Search intents: `Agent Skills discovery`, `MCP discovery for coding agents`, `coding agent skill discovery`, `agent capability management`.

## RAG / AI application grows in complexity

A project that starts with basic retrieval may later add chunking, hybrid search, reranking, evaluation, observability and prompt-injection defenses.

Cumulus can treat each emerging area as a capability domain and acquire prior art just in time instead of installing a huge skill set up front.

## Deployment becomes part of the workflow

When Docker, Kubernetes, CI/CD or cloud deployment becomes recurring work, Cumulus can identify the new domain and help the agent discover deployment-specific skills and tools before repeated mistakes accumulate.

## Team wants agent retrospectives

After a sprint or milestone, run an optimization review to summarize:

- what the agent handles reliably;
- recurring high-effort areas;
- user corrections;
- missing capabilities;
- skills or tools worth trialing;
- changes that should be kept or rolled back.

This review is separate from Cumulus autonomy settings: users can request it at any time.

## What Cumulus is not

Cumulus is not:

- a replacement for Git, tests or CI;
- a reason to install every available Agent Skill;
- full transcript logging;
- permission to execute arbitrary third-party code;
- a guarantee that a discovered skill is trustworthy.

Discovery is followed by evaluation, and meaningful capability changes should be reversible and evidence-based.