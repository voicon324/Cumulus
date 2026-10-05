# Security Policy

Cumulus can influence coding-agent behavior and may participate in discovery of external skills, tools, or workflows. Treat this as a supply-chain-sensitive surface.

## Reporting a vulnerability

Please do not publish exploit details in a public issue before a fix is available.

Until a private reporting channel is configured, open a minimal issue stating that you have a security report and request a private contact path. Do not include secrets, tokens, personal data, or working exploit payloads in the public issue.

## Security expectations

- The normal installer is repository-local and should not require `sudo`.
- Cumulus does not require storing full chat transcripts.
- External skill/tool discovery is not equivalent to trust or installation.
- Credentials and paid/security-sensitive/system-level changes require explicit approval.
- Project data under `.cumulus/` may contain architecture decisions and development history; teams should decide what is appropriate to commit.
