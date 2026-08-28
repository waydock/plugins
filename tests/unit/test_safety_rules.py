"""Every skill that can write carries its own safety rules.

A skill that writes should state the rules governing that write, rather than
depend on a second skill having been loaded first. Skill selection is a model
decision, so "the other one will be loaded too" is an assumption, not a
guarantee, whatever its hit rate.

Which skills count as writers is DERIVED, not listed. When this file pinned one
skill by name, adding a second writing skill would have shipped with no
enforcement at all and nothing would have gone red: the exact failure mode this
suite exists to catch, a guard that silently stops guarding. Any skill that
names a mailbox-writing tool anywhere in its content is in the set. A guard
test asserts the derivation still catches the two known writers, so a rename
in tests/skill.py cannot quietly empty it.

That is the reason. It is worth recording what is NOT the reason this file was
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

This test stops the rules drifting back out of the skills that perform writes.
"""
from tests.skill import discover_skills, named_tools

# Naming any of these puts a real draft in, or sends real mail from, the user's
# mailbox. A skill that mentions one is instructing an agent about a write and
# must carry the rules that govern it.
MAILBOX_WRITING_TOOLS = {
    "waydock_draft_reply_save",
    "waydock_draft_reply_regenerate",
    "waydock_follow_up_nudge",
    "waydock_send_email",
    "waydock_morning_brief_send",
}

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


def writing_skills():
    return [
        skill
        for skill in discover_skills()
        if named_tools(skill) & MAILBOX_WRITING_TOOLS
    ]


class TestSafetyRulesLiveWithTheWrite:
    def test_the_derivation_still_catches_the_known_writers(self):
        # If a tool rename (or a TOOL_PATTERN change in tests/skill.py) stopped
        # the derivation matching anything, the rules test below would pass
        # vacuously over an empty set. These two skills write by design; the
        # derivation finding neither means the derivation is broken, not that
        # the repo has no writers.
        names = {skill.path.parent.name for skill in writing_skills()}
        assert "waydock-morning-triage" in names, names
        assert "waydock-mcp" in names, names

    def test_every_skill_that_writes_carries_every_safety_rule(self):
        for skill in writing_skills():
            name = skill.path.parent.name
            for rule, (marker, consequence) in REQUIRED_RULES.items():
                assert marker in skill.content, (
                    f"{name} names a mailbox-writing tool but no longer states "
                    f"'{rule}' (looked for '{marker}'). Without it "
                    f"{consequence}. Keeping the rule only in waydock-mcp is "
                    f"not enough: whether that skill is also loaded is a model "
                    f"decision, not something this one can rely on."
                )
