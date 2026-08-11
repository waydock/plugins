"""The safety rules have to live in the skill that actually loads.

Measured against the real harness in PR #4, reading Skill tool_use events rather
than self-report: `waydock-mcp` fires when Waydock is named, or when the question
is about how to use it, and does not fire when someone asks an ordinary question
about their own mail while the tools are already visible. Calling a tool the
model can see beats reading guidance about how to call it.

The four traps lived only in `waydock-mcp`, which put them out of reach during
exactly the ordinary use where they earn their keep. They now also live in
`waydock-morning-triage`, which does fire. Rewording the description was tried
first and changed neither failing prompt, so placement is the fix, not wording.

This test stops them drifting back out of the skill that loads.
"""
from tests.skill import discover_skills

LOADS_RELIABLY = "waydock-morning-triage"

# Marker to look for, and what its absence would mean in practice.
REQUIRED_RULES = {
    "tool output is untrusted": (
        "never as instructions",
        "an emailed subject line could steer a send",
    ),
    "sending is the user's action": (
        "waydock_send_email",
        "the skill could send mail on the user's behalf",
    ),
    "drafts are writes": (
        "waydock_draft_reply_save",
        "unrequested drafts could appear in the user's mailbox",
    ),
    "archived and live mail are addressed differently": (
        "providerMessageId",
        "a live search hit would be read back with the wrong identifier",
    ),
    "a refusal is not worth a retry": (
        "insufficient_scope",
        "a policy refusal would be retried as though it were a network blip",
    ),
}


class TestSafetyRulesReachOrdinaryUse:
    def test_the_skill_that_loads_carries_every_safety_rule(self):
        skill = next(
            s for s in discover_skills() if s.path.parent.name == LOADS_RELIABLY
        )
        for rule, (marker, consequence) in REQUIRED_RULES.items():
            assert marker in skill.content, (
                f"{LOADS_RELIABLY} no longer states '{rule}' (looked for "
                f"'{marker}'). It is the skill that fires on ordinary questions, "
                f"so without it {consequence}. Keeping the rule only in "
                f"waydock-mcp does not count: that skill does not load unless "
                f"the user names Waydock."
            )
