import re

from tests.skill import discover_skills

from tests.config import PLUGIN_ROOT

# Written as an escape, never as the literal character, so this file does not
# itself trip an em-dash grep. Code comments are exempt in the monorepo guard,
# but a SKILL.md and a README are all prose.
EM_DASH = "\u2014"


class TestMarkdownStructure:
    def setup_method(self):
        self.skills = discover_skills()

    def test_has_content(self):
        for skill in self.skills:
            assert len(skill.body) > 100, f"{skill.path}: body is suspiciously short"

    def test_has_top_level_heading(self):
        for skill in self.skills:
            assert re.search(r"(?m)^#\s+", skill.body), f"{skill.path}: missing a top-level (#) heading"

    def test_has_section_structure(self):
        for skill in self.skills:
            headings = re.findall(r"^##\s+", skill.body, re.MULTILINE)
            assert len(headings) >= 2, f"{skill.path}: needs at least two (##) sections"

    def test_no_em_dashes_anywhere_in_the_repo(self):
        # Not just SKILL.md. The README is the most-read file here and is the
        # one Cursor's reviewer opens first, and it was the only file with a
        # stated no-em-dash rule and no test enforcing it.
        offenders = [
            path
            for path in sorted(PLUGIN_ROOT.rglob("*.md"))
            if ".venv" not in path.parts and EM_DASH in path.read_text()
        ]
        assert not offenders, (
            "em-dashes found in: "
            + ", ".join(str(p.relative_to(PLUGIN_ROOT)) for p in offenders)
            + ". The house copy policy forbids them in prose."
        )

    def test_no_bare_skill_file_paths(self):
        for skill in self.skills:
            assert "SKILL.md" not in skill.body, (
                f"{skill.path} references a SKILL.md path; reference skills by name instead"
            )
