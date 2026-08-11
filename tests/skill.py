"""Discover and parse plugin skill files."""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import yaml

from tests.config import SKILLS_ROOT

# One definition, used by BOTH the offline no-enumeration guard and the live
# drift check. It was copy-pasted into each before review: two guards that
# disagree about what counts as a tool name is a guard that silently stops
# guarding, and the whole point of this suite is that a fact restated in two
# places drifts.
TOOL_PATTERN = re.compile(r"\bwaydock_[a-z0-9_]+\b")
SCOPE_PATTERN = re.compile(r"\b(?:read|write):[a-z]+(?:\.[a-z]+)*\b")


def named_tools(skill: "Skill") -> set[str]:
    """Distinct waydock_* tool names a skill mentions anywhere, frontmatter included."""
    return set(TOOL_PATTERN.findall(skill.content))


def named_scopes(skill: "Skill") -> set[str]:
    """Distinct read:/write: scopes a skill mentions anywhere."""
    return set(SCOPE_PATTERN.findall(skill.content))


@dataclasses.dataclass
class Metadata:
    name: str
    description: str


@dataclasses.dataclass
class Skill:
    metadata: Metadata
    body: str
    path: Path
    content: str

    @classmethod
    def from_path(cls, path: Path) -> "Skill":
        content = path.read_text()
        frontmatter: dict = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
        return cls(
            metadata=Metadata(
                name=frontmatter.get("name", ""),
                description=frontmatter.get("description", ""),
            ),
            body=body,
            path=path,
            content=content,
        )


def discover_skills() -> tuple[Skill, ...]:
    skills = []
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            skills.append(Skill.from_path(skill_file))
    return tuple(skills)


def load_skill(skill_name: str) -> Skill:
    skill_path = SKILLS_ROOT / skill_name / "SKILL.md"
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill not found: {skill_path}")
    return Skill.from_path(skill_path)
