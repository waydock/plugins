<img src="logo.svg" alt="Waydock" width="72" height="72">

# Waydock plugins

Waydock unifies a person's mail, calendar, meetings, tasks, and follow-ups into
one context and exposes it to coding agents over MCP. Access is per-scope, every
call is audited, and the same tool registry backs Waydock's own in-app assistant,
so an agent and the product see exactly the same surface under exactly the same
rules. This repo is the plugin: two skills that teach an agent how to use that
surface well, plus the MCP server configuration for Cursor and Claude Code.

Connection is OAuth. There is no API key to paste.

## What is included

| File | Read by | Purpose |
|---|---|---|
| `mcp.json` | Cursor | MCP server config, bare url |
| `.mcp.json` | Claude Code | MCP server config, declares `"type": "http"` |
| `.cursor-plugin/plugin.json` | Cursor | Plugin manifest |
| `.claude-plugin/plugin.json` | Claude Code | Plugin manifest |
| `.claude-plugin/marketplace.json` | Claude Code | Marketplace entry |
| `skills/waydock-mcp` | both | Orientation: how to use Waydock without getting it wrong |
| `skills/waydock-morning-triage` | both | Workflow: rank what needs the user, offer replies, never send |

## One directory, two harnesses

```
                      waydock/plugins  (one directory, no symlinks, no sync)
                                 |
        +------------------------+------------------------+
        |                                                 |
     CURSOR reads                                    CLAUDE CODE reads
        |                                                 |
  .cursor-plugin/plugin.json                    .claude-plugin/plugin.json
  mcp.json          (bare url)                  .claude-plugin/marketplace.json
        |                                       .mcp.json   (needs "type": "http")
        |                                                 |
        +------------------------+------------------------+
                                 |
                            skills/          <-- shared verbatim, byte for byte
                              waydock-mcp/SKILL.md
                              waydock-morning-triage/SKILL.md

  Each harness ignores the other's files. Nothing is copied, so nothing can drift.
  Adding a third harness means adding files, never reconciling them.
```

## Install into Claude Code

```
/plugin marketplace add waydock/plugins
/plugin install waydock@waydock
```

Then **quit Claude Code and relaunch it**. Registering a plugin does not start its
MCP server; only a restart does. After relaunching:

```
/mcp
```

Pick `waydock` and authorize. The browser opens Waydock's consent screen, you
approve, and the server comes back `connected`.

## Install into Cursor

Once the listing is live, install Waydock from the Cursor plugin marketplace. Until
then, and any time you want to run an unreleased revision, use the local path under
[Development](#development).

If you want the MCP server without the skills, add it to `~/.cursor/mcp.json`
directly:

```json
{
  "mcpServers": {
    "waydock": {
      "url": "https://waydock.ai/api/mcp/stream"
    }
  }
}
```

## Authentication

Waydock's MCP server is an OAuth 2.1 authorization server and resource server.
The client discovers it from the transport's `WWW-Authenticate` challenge, registers
itself, and runs the authorization code flow with PKCE. You approve a consent screen
in the browser. Nothing is pasted anywhere.

**What you are granting is what the harness asks for, not what a skill uses.** Both
Cursor and Claude Code request the entire scope catalog at install, so the consent
screen lists all of it. Scopes that let the agent reach other people, such as
sending mail, stay named line items rather than being folded into a summary, and
they arrive unticked. Read the screen and grant what you actually want. The two
skills here are conservative by design (triage never sends), but a skill's restraint
is not the same thing as a limited grant.

A `wdmcp_` API key is still supported as a fallback for scripts and non-interactive
use. See https://waydock.ai/docs/authentication.

## Try it

```
what needs my attention today
did anyone ever reply about the invoice
what came out of my meeting with the design team
```

The first loads the triage workflow. The others use the orientation skill to reach
mail and meetings.

## Development

Run the test suite:

```bash
make test        # offline: manifests, MCP configs, skill structure
make test-live   # checks the skills against the live tool manifest
make probe       # measures which skill each prompt actually loads
```

`make probe` answers "does this description change work" by running the real
harness N times per prompt and reading the `Skill` events, instead of reasoning
from a single transcript. It is slow, costs tokens, needs the `claude` CLI, and
is probabilistic, so it is deliberately not part of `make test` and not a CI
gate. Run it after any edit to a skill's `description`, and read `FLAKY` as the
honest answer it is rather than as a failure.

Load this checkout into Cursor without publishing:

```bash
ln -sfn "$PWD" ~/.cursor/plugins/local/waydock
```

Then run `Developer: Reload Window`. Remove it with
`rm ~/.cursor/plugins/local/waydock`.

For Claude Code, point the marketplace at the checkout instead of the repo:

```
/plugin marketplace add /path/to/this/checkout
/plugin install waydock@waydock
```

### Releasing

**Any change under `skills/` or to either plugin manifest needs a version bump in
both `.cursor-plugin/plugin.json` and `.claude-plugin/plugin.json`.** Installed
copies update on version, not on commit. Ship a skill correction without bumping and
the repo is right while every existing install stays on the old copy, and nothing
anywhere reports a problem. CI enforces this on pull requests so it cannot be
forgotten.

**A skill's `description` decides whether it loads at all, so changing one is a
behaviour change and needs `make probe`, not a reading.** Whether a skill fires
is a model decision. A single run cannot tell "never" from "four times in five",
and a description fix has already been shipped here, measured once, and wrongly
written off as ineffective on that single sample.

Skills describe workflows and point at
https://waydock.ai/api/mcp/manifest for the full catalog. They deliberately do not
list every tool: the count and the catalog change, and a skill that enumerates them
is wrong on the next release. A test caps how many tool names a single skill may
mention.

## License

MIT. See [LICENSE](LICENSE).
