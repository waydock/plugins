"""The eve registry: built output in sync, no secrets, no tool enumeration.

The files under eve/r/ are committed build output served by
raw.githubusercontent.com, so "the source changed but the build did not run" is
a silent way to ship a stale registry. These tests rebuild the output in memory
with the same builder `make build-eve` uses and compare byte for byte.

The connection's approval policy deliberately names no tools; it reads the live
manifest's readOnly flag at runtime instead. That property is what makes the
eve directory immune to catalog drift, so a test pins it: the day someone adds
a hardcoded tool list to the connection or this directory's README, this fails
and points them at the manifest-driven design.
"""
import json
import sys
from pathlib import Path

from tests.config import MANIFEST_URL, REPO_ROOT, WAYDOCK_MCP_URL
from tests.skill import TOOL_PATTERN

sys.path.insert(0, str(REPO_ROOT / "tools"))
import build_eve_registry  # noqa: E402

EVE_ROOT = REPO_ROOT / "eve"
CONNECTION = EVE_ROOT / "registry" / "waydock.ts"


def test_built_output_matches_sources():
    expected = build_eve_registry.build()
    built_dir = EVE_ROOT / "r"
    committed = {p.name: p.read_text() for p in sorted(built_dir.glob("*.json"))}
    assert committed == expected, "eve/r/ is stale; run `make build-eve`"


def test_every_catalog_item_has_a_built_document():
    catalog = json.loads((EVE_ROOT / "r" / "registry.json").read_text())
    for item in catalog["items"]:
        assert (EVE_ROOT / "r" / f"{item['name']}.json").exists()


def test_connection_points_at_the_real_endpoints():
    content = CONNECTION.read_text()
    assert f'"{WAYDOCK_MCP_URL}"' in content
    assert f'"{MANIFEST_URL}"' in content


def test_connection_and_readme_enumerate_no_tools():
    # The built JSON inlines the skills, which legitimately name tools; the
    # eve-authored files must not.
    for path in (CONNECTION, EVE_ROOT / "README.md"):
        named = set(TOOL_PATTERN.findall(path.read_text()))
        assert not named, f"{path.name} names tools; the manifest is the catalog: {named}"


def test_env_var_is_declared_and_empty():
    item = json.loads((EVE_ROOT / "r" / "waydock.json").read_text())
    assert item["envVars"] == {"WAYDOCK_MCP_KEY": ""}


def test_every_file_installs_under_agent():
    item = json.loads((EVE_ROOT / "r" / "waydock.json").read_text())
    targets = [f["target"] for f in item["files"]]
    assert targets, "item installs nothing"
    for target in targets:
        assert target.startswith("agent/"), target


def test_skills_are_shared_verbatim():
    """The registry inlines skills/ content, same bytes as the other harnesses."""
    item = json.loads((EVE_ROOT / "r" / "waydock.json").read_text())
    by_target = {f["target"]: f["content"] for f in item["files"]}
    for name in ("waydock-mcp", "waydock-morning-triage"):
        source = (REPO_ROOT / "skills" / name / "SKILL.md").read_text()
        assert by_target[f"agent/skills/{name}/SKILL.md"] == source


def test_no_key_material_anywhere():
    for path in EVE_ROOT.rglob("*"):
        if path.is_file():
            assert "wdmcp_" + "live" not in path.read_text(errors="ignore")
            # A real key is wdmcp_ followed by a long token; the literal prefix
            # alone appears in prose and is fine.
            for word in TOOL_PATTERN.sub("", path.read_text(errors="ignore")).split():
                assert not (word.startswith("wdmcp_") and len(word) > 20), (
                    f"{path} appears to contain a real key"
                )
