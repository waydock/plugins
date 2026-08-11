"""The only network test: are the tools, scopes AND SAFETY CLAIMS still true?

This repo is the source of truth for skill content, but the surface it describes
lives in a private monorepo we cannot see. A tool rename there would silently
make our skills wrong. Runs on a schedule as well as on push, so we hear about
drift we caused elsewhere without waiting for a commit here.

Two things this file gets right that the first draft did not.

1. It sends a real User-Agent and FAILS on an HTTP error instead of skipping.
   `urlopen`'s default UA is `Python-urllib/<ver>`, which Cloudflare answers with
   a 403 and error code 1010 (measured against production, 2026-08-09: browser UA
   returns 200 with 14 KB, python-urllib returns 403). `urllib.error.HTTPError`
   subclasses `URLError`, so a blanket `except URLError: pytest.skip(...)` turned
   that 403 into a skip and the job went green forever without ever fetching the
   manifest. A check that cannot fail is worse than no check.

2. It asserts CONTRACTS, not just nouns. Proving `waydock_send_email` still
   exists says nothing about whether it is still destructive, or whether
   `waydock_mail_search` still needs `read:mail.search`. Those properties are
   what the skills actually tell an agent, so those are what drift silently.
"""
import json
import urllib.error
import urllib.request

import pytest

from tests.config import MANIFEST_URL, SAFETY_CONTRACT, USER_AGENT
from tests.skill import discover_skills, named_scopes, named_tools


@pytest.fixture(scope="module")
def manifest():
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        # A status code is an ANSWER, not an outage. 403 here means a bot rule
        # is blocking us and the check is not running; that must be red.
        pytest.fail(f"{MANIFEST_URL} returned HTTP {exc.code}: {exc.read()[:200]!r}")
    except (urllib.error.URLError, TimeoutError) as exc:
        # Genuine transport failure (DNS, connection refused, timeout). The one
        # case where skipping is honest.
        pytest.skip(f"could not reach {MANIFEST_URL}: {exc}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        # An HTML challenge or error page served with a 200. Not a skip.
        pytest.fail(f"{MANIFEST_URL} did not return JSON: {exc}; body={raw[:200]!r}")


def test_manifest_shape(manifest):
    assert isinstance(manifest.get("tools"), list) and manifest["tools"]
    assert isinstance(manifest.get("scopes"), list) and manifest["scopes"]


def test_every_named_tool_still_exists(manifest):
    live = {t["name"] for t in manifest["tools"]}
    for skill in discover_skills():
        missing = sorted(named_tools(skill) - live)
        assert not missing, (
            f"{skill.path} names tools that no longer exist: {missing}. "
            f"They were renamed or removed in the Waydock monorepo."
        )


def test_every_named_scope_still_exists(manifest):
    live = set(manifest["scopes"])
    for skill in discover_skills():
        missing = sorted(named_scopes(skill) - live)
        assert not missing, (
            f"{skill.path} names scopes that no longer exist: {missing}."
        )


def test_the_safety_claims_our_skills_make_are_still_true(manifest):
    # The skills tell an agent which tools are safe and which need care. If
    # send_email stops being flagged destructive, or a draft tool starts
    # requiring a send scope, our published copy becomes a safety hazard and
    # nothing else in this suite would notice.
    by_name = {t["name"]: t for t in manifest["tools"]}
    for name, expected in SAFETY_CONTRACT.items():
        tool = by_name.get(name)
        assert tool, f"{name} is named in a skill but is gone from the manifest"
        for prop, want in expected.items():
            got = tool.get(prop)
            if isinstance(want, (list, tuple, set)):
                assert set(want) <= set(got or []), (
                    f"{name}.{prop} lost {sorted(set(want) - set(got or []))}; "
                    f"a skill documents the old contract"
                )
            else:
                assert got == want, (
                    f"{name}.{prop} is {got!r}, skills document {want!r}"
                )


def test_the_endpoint_we_ship_is_the_one_advertised(manifest):
    # If the transport path ever moves, both mcp.json files are wrong and every
    # install breaks. Catch it here rather than from a user report.
    assert manifest["transports"]["streamableHttp"]["url"] == "/api/mcp/stream"
