"""Both manifests and both MCP configs are valid, and they agree."""
import json
import re

from tests.config import (
    CLAUDE_MANIFEST,
    CLAUDE_MARKETPLACE,
    CLAUDE_MCP_CONFIG,
    CURSOR_MANIFEST,
    CURSOR_MCP_CONFIG,
    PLUGIN_ROOT,
    WAYDOCK_MCP_URL,
    plugin_name,
)

KEBAB = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")


def _load(path):
    return json.loads(path.read_text())


class TestPluginManifests:
    def test_both_manifests_exist_and_parse(self):
        assert _load(CURSOR_MANIFEST)
        assert _load(CLAUDE_MANIFEST)

    def test_names_are_kebab_case_and_identical(self):
        cursor = _load(CURSOR_MANIFEST)["name"]
        claude = _load(CLAUDE_MANIFEST)["name"]
        assert KEBAB.match(cursor), f"cursor plugin name '{cursor}' not kebab-case"
        # One plugin, two harnesses. A mismatch means it installs under two
        # different names and the skill namespace differs per harness.
        assert cursor == claude == plugin_name()

    def test_versions_match(self):
        assert _load(CURSOR_MANIFEST)["version"] == _load(CLAUDE_MANIFEST)["version"]

    def test_descriptions_match(self):
        # The same 118-character sentence is stored in three files. That is the
        # exact shape of the bug PR A exists to fix (one number restated in nine
        # places, wrong in all of them). It cannot be derived across three JSON
        # documents that two different vendors read, so assert it instead.
        cursor = _load(CURSOR_MANIFEST)["description"]
        claude = _load(CLAUDE_MANIFEST)["description"]
        market = _load(CLAUDE_MARKETPLACE)["plugins"][0]["description"]
        assert cursor == claude == market, (
            "the plugin description has drifted between the two manifests and "
            "the marketplace entry; storefronts would show different copy"
        )

    def test_skills_dir_is_discoverable(self):
        assert (PLUGIN_ROOT / "skills").is_dir(), "skills/ must exist for auto-discovery"

    def test_logo_path_exists_and_is_relative(self):
        logo = _load(CURSOR_MANIFEST).get("logo")
        assert logo, "cursor plugin.json must declare a logo"
        assert not logo.startswith(("/", "..")), f"logo path '{logo}' must be relative"
        assert (PLUGIN_ROOT / logo).exists(), f"logo path '{logo}' does not exist"


class TestMcpConfigs:
    def test_cursor_config_is_a_bare_url(self):
        server = _load(CURSOR_MCP_CONFIG)["mcpServers"]["waydock"]
        assert server["url"] == WAYDOCK_MCP_URL

    def test_claude_config_declares_the_http_transport(self):
        # Claude Code reads a url with no type as a stdio server, skips it, and
        # reports: MCP server "waydock" has a "url" but no "type".
        server = _load(CLAUDE_MCP_CONFIG)["mcpServers"]["waydock"]
        assert server["type"] == "http"
        assert server["url"] == WAYDOCK_MCP_URL

    def test_both_configs_name_the_same_server(self):
        assert set(_load(CURSOR_MCP_CONFIG)["mcpServers"]) == set(
            _load(CLAUDE_MCP_CONFIG)["mcpServers"]
        )


class TestClaudeMarketplace:
    def test_declares_one_plugin_sourced_at_the_marketplace_root(self):
        entries = _load(CLAUDE_MARKETPLACE)["plugins"]
        assert len(entries) == 1
        assert entries[0]["name"] == plugin_name()
        # Root-as-plugin: the entry points at the marketplace root itself.
        assert entries[0]["source"] == "./"
