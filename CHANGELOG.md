# Changelog

## 0.2.1

Installation/setup focused release.

- Repo-local installation is now the default UX; no global PATH setup required.
- Added `scripts/install-repo.sh` for installation from inside the target repository.
- Installer creates `./cumulus` and `.cumulus-runtime/` locally and ignores them in Git.
- Installation automatically launches interactive `init`.
- `init` scans the repository before prompting, asks for project goal/autonomy only when needed, integrates `AGENTS.md` by default, and writes onboarding/scout artifacts.
- Integration instructions prefer the repo-local `./cumulus` launcher.
- Git-root discovery allows install/use from a repository subdirectory while keeping state at the root.

## 0.2.0

- Rich repository profiling and project/capability models.
- Task lifecycle and new-domain detection.
- Capability debt and improvement trial lifecycle.
- Skill lock, memory compaction, review, doctor, and AGENTS.md integration.
