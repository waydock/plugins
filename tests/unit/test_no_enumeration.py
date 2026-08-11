"""Skills describe workflows. They do not enumerate the catalog.

Enumeration is why the product docs claimed 58 tools against a real count of 60
for months. A skill that lists every tool is wrong on the next release, and this
repo has no visibility into monorepo changes. Naming a bounded set of workflow
tools keeps the skill useful and lets the live drift check stay meaningful.
"""
from tests.config import MAX_TOOLS_NAMED_PER_SKILL
from tests.skill import discover_skills, named_tools


class TestNoEnumeration:
    def setup_method(self):
        self.skills = discover_skills()

    def test_no_skill_enumerates_the_catalog(self):
        for skill in self.skills:
            named = named_tools(skill)
            assert len(named) <= MAX_TOOLS_NAMED_PER_SKILL, (
                f"{skill.path} names {len(named)} tools, over the "
                f"{MAX_TOOLS_NAMED_PER_SKILL} limit. Describe the workflow and "
                f"link the manifest instead of listing the catalog."
            )

    def test_skills_point_at_the_live_catalog(self):
        # If we are not listing every tool, at least one skill has to say where
        # the full list lives, or an agent has no way to find the rest.
        bodies = "\n".join(s.content for s in self.skills)
        assert "api/mcp/manifest" in bodies, (
            "no skill points at https://waydock.ai/api/mcp/manifest"
        )
