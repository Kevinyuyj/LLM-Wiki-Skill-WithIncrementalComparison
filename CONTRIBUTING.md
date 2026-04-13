# Contributing to LLM-WIKI Ingest Skill

Thank you for your interest in contributing!

## How to Contribute

### Reporting Issues

- Use GitHub Issues for bug reports or feature requests
- Include your `SKILL.md` version (check the `version` field in frontmatter)
- Describe expected vs actual behavior

### Submitting Changes

1. **Fork the repository** on GitHub
2. **Create a branch** for your change:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** — update `SKILL.md` and/or documentation
4. **Test locally** by running an ingest and verifying log output
5. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add X for Y"
   ```
6. **Push and open a Pull Request**

### Versioning

This skill follows [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` in `SKILL.md` frontmatter
- Update `CHANGELOG.md` on every version change

### Coding Conventions

- Skill content is in **Markdown** (SKILL.md format)
- Use YAML frontmatter with: `title`, `created`, `updated`, `type`, `tags`
- Wiki pages must have at least 2 `[[wikilinks]]`
- Tags must come from the SCHEMA taxonomy in the parent wiki

## Questions?

Open a GitHub Issue for questions about the skill or workflow.
