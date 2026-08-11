"""Paths and expected values shared across the test suite."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PLUGIN_ROOT = REPO_ROOT  # root-as-plugin: one directory serves both harnesses

SKILLS_ROOT = PLUGIN_ROOT / "skills"
CURSOR_MANIFEST = PLUGIN_ROOT / ".cursor-plugin" / "plugin.json"
CLAUDE_MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
CLAUDE_MARKETPLACE = PLUGIN_ROOT / ".claude-plugin" / "marketplace.json"
CURSOR_MCP_CONFIG = PLUGIN_ROOT / "mcp.json"
CLAUDE_MCP_CONFIG = PLUGIN_ROOT / ".mcp.json"


# Read from the manifest so a rename only needs to change one file. Deliberately
# a function, not a module-level constant: file I/O at import time turns a
# missing or malformed manifest into a pytest COLLECTION error ("the whole suite
# exploded") instead of a single readable test failure ("the manifest is
# broken"), which is exactly backwards for the defect this suite exists to catch.
def plugin_name() -> str:
    return json.loads(CURSOR_MANIFEST.read_text())["name"]


EXPECTED_SKILLS = ("waydock-mcp", "waydock-morning-triage")
WAYDOCK_MCP_URL = "https://waydock.ai/api/mcp/stream"
MANIFEST_URL = "https://waydock.ai/api/mcp/manifest"

# Skills describe workflows, they do not enumerate the catalog. The live tool
# count went 58 -> 59 -> 60 in six weeks; a skill that lists them all rots immediately.
MAX_TOOLS_NAMED_PER_SKILL = 20

# urlopen's default UA is `Python-urllib/<ver>`, which Cloudflare answers with a
# 403 (error code 1010). Measured against production 2026-08-09. Identify
# ourselves properly or the drift check never runs.
USER_AGENT = "waydock-plugins-drift-check (+https://github.com/waydock/plugins)"

# The safety properties our skills assert to an agent, checked against the live
# manifest. Values verified against lib/mcp-server-meta.ts on 2026-08-09 and
# re-verified against it on 2026-08-11, after the manifest changes in that
# repo's #941. All six still hold.
#
# Existence checks are not enough. "waydock_send_email still exists" says nothing
# about whether it is still flagged destructive, and the destructive flag is the
# entire basis on which the orientation skill tells an agent to be careful with
# it. A list value asserts containment (the live scope set must still include
# these), a scalar asserts equality.
SAFETY_CONTRACT = {
    # Destructive. The skills tell agents not to retry a refusal and not to send
    # unless asked. If this flag ever flips, that advice loses its footing.
    #
    # Note its requiredScopes is empty and the send scopes live in anyOfScopes
    # (either write:mail.send or write:mail.send.self admits it), so do not add a
    # requiredScopes key here expecting to catch a scope change; the flags are
    # what the skill's advice rests on.
    "waydock_send_email": {"destructive": True, "readOnly": False},
    # Writes, but reversible. Documented as "safe to offer, save on approval".
    "waydock_draft_reply_save": {
        "destructive": False,
        "readOnly": False,
        "requiredScopes": ["write:mail.drafts"],
    },
    "waydock_follow_up_nudge": {
        "destructive": False,
        "readOnly": False,
        "requiredScopes": ["write:mail.drafts"],
    },
    # The archive-versus-live-mail trap depends on these two differing exactly
    # this way. If mail_search stops needing its own scope, the skill's whole
    # explanation of why a search can be denied while a list succeeds is wrong.
    "waydock_mail_list": {"readOnly": True, "requiredScopes": ["read:mail"]},
    "waydock_mail_search": {"readOnly": True, "requiredScopes": ["read:mail.search"]},
    # Orientation tells agents to call this before concluding anything is
    # unavailable, on the basis that it costs no scope.
    "waydock_capabilities": {"readOnly": True, "destructive": False},
}
