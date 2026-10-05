# Contributing to Cumulus

Thanks for helping improve Cumulus.

## Good contributions

- reproducible bugs in repo-local installation or project profiling;
- new coding-agent integrations;
- better capability-debt signals with clear evidence;
- safer skill/tool discovery workflows;
- small, testable runtime improvements;
- documentation and real-world usage examples.

## Development workflow

1. Fork the repository and create a focused branch.
2. Keep changes small enough to review.
3. Run:

```bash
bash scripts/smoke-test.sh
```

4. Explain the problem, the change, and how it was validated in the pull request.

## Design constraints

Please preserve these principles:

- project-local by default;
- no `sudo` requirement for normal installation;
- structured evidence instead of full transcript logging;
- one ordinary failure is not enough to rewrite a capability;
- reversible changes and explicit rollback where practical;
- external code/skills are not trusted merely because they were discovered;
- user approval remains required for credentials, paid services, destructive actions, security-sensitive changes, and system-level changes.
