#!/usr/bin/env python3
"""Measure which skill a prompt actually loads, over N trials.

## Why this is a committed tool and not a shell one-liner

PR #4 reported that two of the plan's three acceptance prompts loaded no skill at
all, and recommended moving the safety content out of `waydock-mcp` on that
basis. PR #5 did the move. Re-running the same prompts three times each, against
current main and against PR #4's own tree, loaded `waydock-mcp` 12 times out of
12. The description change in #4 had worked. Its own follow-up measurement did
not survive a second sample, and two PRs were reasoned off it as fact.

Skill selection is a model decision. One observation cannot tell "never fires"
apart from "fired four times in five", and no amount of care in reading a single
transcript recovers that difference. This exists so the question is answered by a
command anyone can re-run, rather than by a table someone remembers.

## Why it is not a test and must never be a required check

It spawns a model per trial: slow, costs tokens, needs auth, and is
probabilistic by construction. A required check that fails one run in ten trains
people to re-run CI until it passes, which is worse than having no check. Same
reasoning that keeps `drift` advisory in `.github/workflows/ci.yml`.

## Why timeouts are reported separately

A trial that timed out and a trial where the model chose no skill look identical
if you only count Skill events: both yield an empty list. They mean opposite
things. The first is a measurement that failed, the second is a measurement that
succeeded and found nothing. Collapsing them is a plausible way to have produced
#4's result, and the first draft of this probe hit exactly that case, so the
distinction is load-bearing here rather than decorative.

Usage:
    make probe                  # every case, 3 trials each
    make probe TRIALS=5
    python3 tools/probe_skill_loading.py --trials 5 --json
"""
import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Outcome of a single trial. `loaded is None` means the trial did not produce an
# answer (timeout or a CLI failure) and is excluded from the denominator.
TIMEOUT = None


@dataclass(frozen=True)
class Case:
    prompt: str
    expect: str
    why: str


# The plan's acceptance prompts, plus the two diagnostics from #4 that isolate
# "the skill is undiscoverable" from "the model preferred a visible tool".
CASES = (
    Case(
        "what needs my attention today",
        "waydock-morning-triage",
        "the triage workflow's headline prompt",
    ),
    Case(
        "did anyone ever reply about the invoice",
        "waydock-mcp",
        "an ordinary mail question, named nothing",
    ),
    Case(
        "what meetings do I have tomorrow",
        "waydock-mcp",
        "an ordinary calendar question, named nothing",
    ),
    Case(
        "how should I use Waydock to find an old email safely",
        "waydock-mcp",
        "diagnostic: asks how to use it, so it should always fire",
    ),
    Case(
        "use waydock to check my mail",
        "waydock-mcp",
        "diagnostic: names the product, so it should always fire",
    ),
)


def run_trial(prompt: str, plugin_dir: Path, timeout: int):
    """Return the skills a single run loaded, or TIMEOUT if it produced no answer.

    `--strict-mcp-config` matters: without it a pre-existing `waydock` connector
    in the user's own settings supplies tools, which is a different condition
    from the one being measured and the confound #4 called out.
    """
    cmd = [
        "claude",
        "--plugin-dir", str(plugin_dir),
        "--strict-mcp-config",
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return TIMEOUT
    if proc.returncode != 0:
        return TIMEOUT

    loaded = []
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in (event.get("message") or {}).get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "Skill":
                params = block.get("input") or {}
                name = params.get("command") or params.get("skill") or ""
                # Namespaced as `waydock:waydock-mcp` when loaded from a plugin.
                loaded.append(str(name).split(":")[-1])
    return loaded


def verdict(hits: int, answered: int) -> str:
    if answered == 0:
        return "INCONCLUSIVE"
    if hits == answered:
        return "PASS"
    if hits == 0:
        return "FAIL"
    return "FLAKY"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trials", type=int, default=3,
                        help="runs per prompt (default 3, minimum 2)")
    parser.add_argument("--timeout", type=int, default=90,
                        help="seconds per trial (default 90)")
    parser.add_argument("--plugin-dir", type=Path, default=REPO_ROOT,
                        help="tree to measure (default this checkout)")
    parser.add_argument("--filter", default="",
                        help="only run cases whose prompt contains this text")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    if shutil.which("claude") is None:
        print("claude CLI not on PATH; this probe drives the real harness.",
              file=sys.stderr)
        return 2
    if args.trials < 2:
        # The entire point is that one sample cannot distinguish never from
        # sometimes. Refuse to reproduce the mistake this tool documents.
        print("--trials must be at least 2; one sample is what caused #4.",
              file=sys.stderr)
        return 2

    cases = [c for c in CASES if args.filter in c.prompt]
    results = []
    for case in cases:
        trials = [run_trial(case.prompt, args.plugin_dir, args.timeout)
                  for _ in range(args.trials)]
        answered = [t for t in trials if t is not TIMEOUT]
        hits = sum(1 for t in answered if case.expect in t)
        other = sorted({s for t in answered for s in t if s != case.expect})
        results.append({
            "prompt": case.prompt,
            "expect": case.expect,
            "why": case.why,
            "hits": hits,
            "answered": len(answered),
            "trials": args.trials,
            "timeouts": args.trials - len(answered),
            "also_loaded": other,
            "verdict": verdict(hits, len(answered)),
        })

    if args.json:
        print(json.dumps({"plugin_dir": str(args.plugin_dir), "results": results},
                         indent=2))
    else:
        print(f"\nplugin-dir: {args.plugin_dir}")
        print(f"{args.trials} trials per prompt, strict MCP config, no authenticated server\n")
        for r in results:
            line = f"  {r['verdict']:<13} {r['hits']}/{r['answered']}  {r['prompt']}"
            if r["timeouts"]:
                line += f"   [{r['timeouts']} timed out, excluded]"
            print(line)
            if r["verdict"] != "PASS":
                print(f"{'':<17}expected {r['expect']} ({r['why']})")
                if r["also_loaded"]:
                    print(f"{'':<17}loaded instead: {', '.join(r['also_loaded'])}")
        print()

    # Exit codes are for humans reading a terminal, not for a CI gate.
    # FLAKY is deliberately not a failure: it is the honest result for a
    # probabilistic choice, and treating it as red is how a useful signal
    # becomes something people learn to ignore.
    if any(r["verdict"] == "FAIL" for r in results):
        return 1
    if any(r["verdict"] == "INCONCLUSIVE" for r in results):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
