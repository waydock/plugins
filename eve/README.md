# Waydock for eve

Files for the [eve](https://eve.dev) agent framework: an MCP connection with a
write-gating approval policy, plus the same two skills the Cursor and Claude
Code plugins ship, byte for byte.

## Install

From an eve project:

```bash
eve registry add @waydock=https://waydock.ai/r/{name}.json
eve add @waydock/waydock
```

This writes three files into your project:

| File | Purpose |
|---|---|
| `agent/connections/waydock.ts` | The MCP connection: url, auth, approval policy |
| `agent/skills/waydock-mcp/SKILL.md` | Orientation: how to use Waydock without getting it wrong |
| `agent/skills/waydock-morning-triage/SKILL.md` | Workflow: rank what needs the user, offer replies, never send |

Then set the key:

```bash
WAYDOCK_MCP_KEY=wdmcp_...
```

Create one at https://waydock.ai and see
https://waydock.ai/docs/authentication. The key's granted scopes are enforced
server side on every call; a key without send scopes cannot send no matter what
the agent asks for.

## Why a key and not OAuth

Cursor and Claude Code run MCP's OAuth discovery flow, so those harnesses have
no key to paste. eve connections authenticate differently: a connection either
supplies a bearer token or hand-authors its own interactive OAuth flow, and it
does not run the MCP discovery dance. The `wdmcp_` key is Waydock's supported
path for exactly this kind of client. The consent step you would have seen in a
browser happens at key creation instead, where you choose the scopes.

## The approval policy

The connection gates every tool the live manifest does not flag `readOnly`
behind eve's human-in-the-loop approval. Reads run without a prompt; anything
that writes, sends, or changes state pauses the turn and asks.

Two properties worth knowing:

- **It enumerates nothing.** The policy fetches
  `https://waydock.ai/api/mcp/manifest` once per process and reads each tool's
  `readOnly` flag. The tool catalog changes with Waydock releases; a name list
  in this repo would be wrong on the next one.
- **It fails closed.** A tool the manifest does not list, or a manifest that
  cannot be fetched, gets an approval prompt rather than a pass.

The file is yours after `eve add`. If your agent should save drafts or move
cards without a prompt, relax the policy in your copy; the server still
enforces the key's scopes underneath whatever you decide.

## Choose the model deliberately

eve's default configuration routes model calls through the Vercel AI Gateway to
its default model. You are about to point an agent at your own mailbox: pick a
model and provider whose data handling you accept, in `agent/agent.ts`, before
the first real turn. eve's [agent configuration
docs](https://eve.dev/docs/agent-config) cover both gateway model ids and
direct provider SDKs.

## Development

The registry under `r/` is built output, committed because it is served as
static files: `waydock.ai/r/{name}.json` is a thin proxy in front of this
directory on raw.githubusercontent.com, so the repo remains the source of
truth and the raw URL keeps working as a fallback. After editing
`registry.json`, `registry/waydock.ts`, or either skill:

```bash
make build-eve
```

`make test` fails if the built output is stale, so forgetting is loud.
