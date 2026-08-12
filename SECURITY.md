# Security policy

## Reporting a vulnerability

Report privately through GitHub, not in a public issue:

**https://github.com/waydock/plugins/security/advisories/new**

That opens a draft advisory visible only to you and the maintainers. Expect an
acknowledgement within three working days.

If GitHub is not an option, email **daniel@montoya.com.au** with `SECURITY` in
the subject line.

## What is in scope

This repository ships skill files and plugin manifests. It contains no server
code and holds no credentials. The things that can go wrong here are:

- **Skill content that misleads an agent about safety.** A skill telling an
  agent that a destructive tool is safe, or that a write operation is a read,
  is a real vulnerability even though it is only Markdown. `tests/live` checks
  the safety claims in `skills/` against the live tool manifest for exactly
  this reason.
- **Prompt injection reachable through a skill.** Instructions that redirect an
  agent to exfiltrate mail, send on the user's behalf, or skip the approval
  steps the skills require.
- **A change to the MCP endpoint** in `mcp.json` or `.mcp.json` that points an
  install at a host other than `waydock.ai`.
- **Supply chain.** Anything that lets a change reach `main` without review, or
  that alters what a marketplace install receives.

Vulnerabilities in the Waydock service itself (the MCP server, OAuth, or the
tools behind them) do not live in this repository. Report those to
**daniel@montoya.com.au**.

## Supported versions

Only the latest published plugin version is supported. Claude Code and Cursor
resolve the plugin from `main`, so a fix ships by bumping the version in both
`.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`. An unbumped fix
never reaches an existing install, which is why CI enforces the bump.
