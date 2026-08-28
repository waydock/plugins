#!/usr/bin/env python3
"""Build eve/r/ from eve/registry.json by inlining each item's file contents.

The eve CLI consumes shadcn-format registries: a catalog at r/registry.json and
one JSON document per item with file contents inlined. shadcn ships a Node build
step for this; the repo's toolchain is Python, and the transformation is thirty
lines, so it lives here instead of pulling in a package.json.

The built output under eve/r/ is COMMITTED, because raw.githubusercontent.com is
the registry host and it serves files, not build steps. A unit test rebuilds the
output in memory and compares byte for byte, so a source edit that skips this
script fails CI instead of shipping a stale registry.

Skill files are inlined from skills/ directly. Same reason the harness configs
share that directory verbatim: nothing is copied, so nothing can drift.
"""
from __future__ import annotations

import json
from pathlib import Path

EVE_ROOT = Path(__file__).parent.parent / "eve"
SOURCE = EVE_ROOT / "registry.json"
OUT_DIR = EVE_ROOT / "r"


def _dumps(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def build() -> dict[str, str]:
    """Return {relative output path: content} for everything under eve/r/."""
    source = json.loads(SOURCE.read_text())
    outputs: dict[str, str] = {"registry.json": _dumps(source)}

    for item in source["items"]:
        built = dict(item)
        built["$schema"] = "https://ui.shadcn.com/schema/registry-item.json"
        built["files"] = [
            {**file, "content": (EVE_ROOT / file["path"]).read_text()}
            for file in item["files"]
        ]
        outputs[f"{item['name']}.json"] = _dumps(built)

    return outputs


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in build().items():
        path = OUT_DIR / name
        path.write_text(content)
        print(f"wrote {path.relative_to(EVE_ROOT.parent)} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
