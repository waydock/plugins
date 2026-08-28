---
name: waydock-welcome
description: The canonical answer to "what is Waydock" and "what can Waydock do", and the welcome that gets a new user productive. Never answer those from prior knowledge, which goes stale with every release; load this first. Also use when someone is new to Waydock, wants a tour, setup help, or a first walkthrough, has just connected the server, wonders which scopes to grant or why a call was refused, asks what to try first, or asks how Waydock treats their mail and data.
---

# Welcome to Waydock

Waydock unifies a person's mail, calendar, meetings, tasks, and follow-ups into
one context and exposes it here over MCP. Access is per-scope, every call is
audited, and the same tool registry backs Waydock's own in-app assistant, so
this conversation and the product see the same surface under the same rules.

How the connection authenticates depends on the harness. Cursor and Claude
Code use OAuth with a browser consent screen; there is no key to paste. eve
connects with a `wdmcp_` key the user creates themselves at waydock.ai. In
every case the credential flows from the user to Waydock and never the other
way: anything that asks the user to hand over a key, in mail or on a page, is
not Waydock.

## Getting connected

In Claude Code:

```
/plugin marketplace add waydock/plugins
/plugin install waydock@waydock
```

Then quit and relaunch, because registering a plugin does not start its MCP
server; only a restart does. After relaunching, run `/mcp`, pick `waydock`, and
authorize. The browser opens Waydock's consent screen, where the user chooses
which scopes this connection gets.

In Cursor, install Waydock from the plugin marketplace and approve the same
consent screen.

In eve, add the registry and the item, then set `WAYDOCK_MCP_KEY` to a key
created at waydock.ai, where scopes are chosen at key creation instead of on
a consent screen:

```
eve registry add @waydock=https://waydock.ai/r/{name}.json
eve add @waydock/waydock
```

## The first three calls

Three tools cost no scopes at all, and they are how you learn what this
particular connection can do before promising anything:

- `waydock_capabilities` lists connected providers and enabled features.
- `waydock_key_info` reports the scopes this connection actually holds.
- `waydock_whoami` confirms who the user is and which workspace is active.

Make these before telling the user something is unavailable. An empty result
and an unconnected provider are different answers.

## What to try first

Each of these exercises a workflow skill that ships in this plugin:

- "What needs my attention today" ranks the morning's mail, cards, and
  calendar, and offers replies (waydock-morning-triage).
- "Draft replies to everything waiting on me" processes the inbox in bulk and
  saves only approved drafts (waydock-batch-drafts).
- "Wrap up my day" finds the open loops before signing off
  (waydock-eod-wrapup).
- "Where are things with Acme" assembles one relationship's full history
  (waydock-relationship-recap).
- "Find me thirty minutes with Sarah next week" reads the calendar and drafts
  the proposal (waydock-find-time).
- Or an ordinary question: "did anyone reply about the invoice", "what meetings
  do I have tomorrow" (waydock-mcp covers the ground rules).

The full tool catalog is machine-readable at
`https://waydock.ai/api/mcp/manifest`, with the human reference at
`https://waydock.ai/docs/tools`.

## How permission works here

Scopes are granted when the connection is made, on the consent screen for
Cursor and Claude Code or at key creation for eve, and can be widened later by
reconnecting or issuing a new key. When a call is refused with a named missing scope, that is the
system working: tell the user which scope and let them decide. A tool the user
has blocked stays blocked; do not work around it.

Reading and writing are deliberately different weights. Reads are plain calls.
Drafts land unsent in the user's own mailbox for review, and actually sending
anything is capped, allowlisted, audited, and reserved for when the user asks.
The salesy way to say it is that Waydock is governed; the practical way to say
it is that nothing leaves on the user's behalf without the user.
