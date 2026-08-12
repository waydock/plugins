"""Every skill that can write carries its own safety rules.

`waydock-morning-triage` reads the user's mail and offers replies, and step 4
saves a real draft into their mailbox once approved. A skill that writes should
state the rules governing that write, rather than depend on a second skill
having been loaded first. Skill selection is a model decision, so "the other one
will be loaded too" is an assumption, not a guarantee, whatever its hit rate.

That is the reason. It is worth recording that it is NOT the reason this file was
originally added, because the first version of this docstring asserted something
measurably false and someone re-reading #4 will otherwise reach the same wrong
conclusion:

  PR #4 reported that "did anyone ever reply about the invoice" and "what
  meetings do I have tomorrow" loaded no skill at all, concluded that
  `waydock-mcp` does not fire on ordinary questions, and recommended moving the
  safety content out of it. PR #5 did the move and repeated the claim here.

  Both prompts load `waydock-mcp` 12 times out of 12, measured three times each
  against current main and three times each against #4's own tree. The
  description rewrite in #4 worked; #4's follow-up measurement, one run per
  prompt, did not survive a second sample.

So the rules are duplicated on purpose, not because `waydock-mcp` fails to load.
Re-measure with `make probe` (tools/probe_skill_loading.py) rather than reasoning
from either PR's table.

This test stops the rules drifting back out of the skill that performs the write.
"""
from tests.skill import discover_skills

WRITES_TO_THE_MAILBOX = "waydock-morning-triage"

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


class TestSafetyRulesLiveWithTheWrite:
    def test_the_skill_that_writes_carries_every_safety_rule(self):
        skill = next(
            s for s in discover_skills() if s.path.parent.name == WRITES_TO_THE_MAILBOX
        )
        for rule, (marker, consequence) in REQUIRED_RULES.items():
            assert marker in skill.content, (
                f"{WRITES_TO_THE_MAILBOX} no longer states '{rule}' (looked for "
                f"'{marker}'). This skill saves drafts, so without it "
                f"{consequence}. Keeping the rule only in waydock-mcp is not "
                f"enough: whether that skill is also loaded is a model decision, "
                f"not something this one can rely on."
            )
