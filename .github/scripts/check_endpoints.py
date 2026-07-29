#!/usr/bin/env python3
"""Liveness check for manifest.json + plugins/*.json.

These endpoints get installed into users' ~/.config/opal/plugins/sources/, so
the governing rule is: pointing a user at the WRONG domain is materially worse
than pointing them at a stale one. A hijacked or parked domain that answers 200
looks exactly like a healthy move to an automated checker.

So this script auto-commits only moves that cannot change who is on the other
end -- an http->https upgrade or a www. normalisation on the *same host*.
Anything that changes the registrable domain (including a "same brand, new TLD"
move) is reported in the tracking issue for a human to confirm, never applied.

Usage: check_endpoints.py [--apply] [--issue] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, "manifest.json")
PLUGINS = os.path.join(ROOT, "plugins")
CONFIG = os.path.join(ROOT, ".github", "linkcheck.json")

ISSUE_TITLE = "Endpoint health: dead or moved source endpoints"
MARKER = "<!-- opal-plugins:endpoint-health -->"

# Verdicts that mean "a human needs to look at this".
ACTIONABLE = {probe.NOT_FOUND, probe.SERVER_ERROR, probe.REDIRECT_LOOP}
# Verdicts that say more about our vantage point than about the site.
VANTAGE = {probe.BLOCKED, probe.UNREACHABLE}


def load_config() -> dict:
    if not os.path.exists(CONFIG):
        return {}
    with open(CONFIG, encoding="utf-8") as fh:
        return json.load(fh).get("overrides", {})


def collect() -> tuple[list[dict], list[str]]:
    """Gather every endpoint from the manifest and the per-plugin files.

    Also reports drift: the manifest carries endpoints inline AND points at
    plugins/<id>.json, and the app can read either, so the two disagreeing is
    a real bug regardless of whether the URLs are alive.
    """
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)

    targets, drift = [], []
    for entry in manifest.get("plugins", []):
        pid = entry.get("id")
        inline = entry.get("endpoints", {}) or {}
        for key, val in inline.items():
            targets.append({"plugin": pid, "key": key, "url": val,
                            "where": "manifest.json", "name": entry.get("name", pid)})

        rel = entry.get("file")
        if not rel:
            continue
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            drift.append(f"`{pid}`: manifest references `{rel}`, which does not exist")
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                side = json.load(fh)
        except (OSError, ValueError) as exc:
            drift.append(f"`{pid}`: `{rel}` is unreadable ({exc})")
            continue

        for key, val in inline.items():
            if key not in side:
                drift.append(f"`{pid}`: `{key}` is in manifest.json but missing from `{rel}`")
            elif side[key] != val:
                drift.append(
                    f"`{pid}`: `{key}` differs -- manifest.json has `{val}`, "
                    f"`{rel}` has `{side[key]}`")
        for key in side:
            if key not in inline:
                drift.append(f"`{pid}`: `{key}` is in `{rel}` but missing from manifest.json")

    # Per-plugin files with no manifest entry at all.
    listed = {e.get("file") for e in manifest.get("plugins", [])}
    if os.path.isdir(PLUGINS):
        for fn in sorted(os.listdir(PLUGINS)):
            if fn.endswith(".json") and f"plugins/{fn}" not in listed:
                drift.append(f"`plugins/{fn}` exists but no manifest.json entry references it")

    return targets, drift


def mechanical_move(url: str, res: probe.ProbeResult):
    """Return (new_url, reason) only for moves that cannot change the operator.

    Deliberately narrow. See the module docstring for why a TLD change does
    not qualify, however obviously "the same site" it looks.
    """
    if res.first_status not in (301, 308):
        return None                      # temporary redirects are not a move
    if not res.healthy:
        return None                      # the destination must actually work
    if not res.final_url:
        return None

    old, new = urlsplit(url), urlsplit(res.final_url)
    if new.scheme != "https":
        return None                      # never "fix" a URL into plaintext http
    if (old.path.rstrip("/") or "/") != (new.path.rstrip("/") or "/"):
        return None                      # path changed -> not a plain move
    if old.query != new.query or new.username or new.password:
        return None

    oh, nh = old.hostname or "", new.hostname or ""
    if not oh or not nh:
        return None
    if (old.port or "") != (new.port or ""):
        return None

    same_host = oh == nh
    www_norm = oh.lstrip(".") == nh[4:] if nh.startswith("www.") else \
        (nh == oh[4:] if oh.startswith("www.") else False)

    if same_host and old.scheme == "http":
        return res.final_url, "http -> https upgrade on the same host"
    if www_norm:
        upgrade = " and http -> https" if old.scheme == "http" else ""
        return res.final_url, f"www. normalisation on the same registrable domain{upgrade}"

    # Everything else -- including <name>.to -> <name>.st -- is a registrable
    # domain change. Same brand or not, a different domain can be a different
    # operator, and this file gets installed into users' configs.
    return None


def normalise(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, p.path.rstrip("/") or "", p.query, ""))


def run_checks(concurrency: int) -> dict:
    overrides = load_config()
    targets, drift = collect()

    for t in targets:
        ov = overrides.get(f"{t['plugin']}.{t['key']}", {})
        t["probe_url"] = ov.get("probe", t["url"])
        t["expect"] = set(ov.get("expect", [])) or None
        t["why"] = ov.get("why", "")

    probeable = [t for t in targets if probe.is_probeable(t["probe_url"])]
    skipped = [t for t in targets if not probe.is_probeable(t["probe_url"])]

    print(f"probing {len(probeable)} endpoints "
          f"({len(skipped)} skipped: templates/loopback/non-URL)\n")

    results = probe.probe_many([t["probe_url"] for t in probeable],
                               concurrency=concurrency)

    # Retry unreachable hosts serially with longer timeouts before believing
    # them. Under load, most first-pass failures are our own resolver.
    retry = [u for u, r in results.items() if r.verdict == probe.UNREACHABLE]
    if retry:
        print(f"retrying {len(retry)} unreachable urls serially...")
        for url in retry:
            again = probe.probe(url, timeout=40, connect_timeout=20)
            if again.verdict != probe.UNREACHABLE:
                print(f"  recovered on retry: {url} -> {again.verdict}")
            results[url] = again
        print()

    rows = []
    for t in probeable:
        r = results[t["probe_url"]]
        verdict = r.verdict
        # An override can declare a verdict normal for this endpoint.
        expected_ok = bool(t["expect"] and verdict in t["expect"])
        rows.append({**t, "result": r, "verdict": verdict, "expected_ok": expected_ok})
        flag = "  " if (r.healthy or expected_ok) else "!!"
        print(f"{flag} {verdict:<19} {r.status:>3}  {t['plugin']}.{t['key']}  "
              f"{t['probe_url'][:60]}"
              f"{'  -> ' + r.final_url if r.moved else ''}")

    unreachable = sum(1 for r in rows if r["result"].verdict == probe.UNREACHABLE)
    pct = (100 * unreachable / len(rows)) if rows else 0
    print(f"\n{unreachable}/{len(rows)} unreachable after retry ({pct:.0f}%)")

    return {"rows": rows, "skipped": skipped, "drift": drift,
            "unreachable_pct": pct}


def probed_note(row: dict) -> str:
    """Say so when an override made us probe something other than the stored URL."""
    if row["probe_url"] == row["url"]:
        return ""
    return f"<br><sub>probed as `{row['probe_url']}` -- {row['why']}</sub>"


def build_report(data: dict, applied: list) -> tuple[str, bool]:
    rows = data["rows"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    needs_human, moved, vantage = [], [], []
    for row in rows:
        r = row["result"]
        if row["expected_ok"] or r.verdict == probe.OK:
            continue
        if r.verdict == probe.REDIRECT:
            if normalise(r.final_url) != normalise(row["probe_url"]):
                moved.append(row)
        elif r.verdict in ACTIONABLE:
            needs_human.append(row)
        elif r.verdict in VANTAGE:
            vantage.append(row)

    actionable = bool(needs_human or moved or data["drift"])

    out = [MARKER, "",
           f"Automated endpoint health check. Last run **{now}**.",
           "",
           "This issue is rewritten in place by "
           "`.github/workflows/endpoint-liveness.yml`. "
           "Close it and it will be recreated on the next run if problems remain.",
           ""]

    out += [
        "> **Read this before changing any endpoint.** The probe runs from a "
        "GitHub datacenter IP. Many of these sites refuse datacenter traffic "
        "wholesale, so `blocked` and `unreachable-from-ci` mean *we could not "
        "see it*, **not** *it is down*. Verify from a normal client before "
        "touching a URL. These files are installed into users' configs; a wrong "
        "domain is worse than a stale one.",
        "",
    ]

    if applied:
        out += ["## Auto-applied this run", "",
                "Mechanical, same-host rewrites only (see the commit):", ""]
        for a in applied:
            out.append(f"- `{a['plugin']}.{a['key']}`: `{a['old']}` -> "
                       f"`{a['new']}` ({a['reason']})")
        out.append("")

    if needs_human:
        out += ["## Broken -- needs a decision", "",
                "| plugin | endpoint | configured URL | verdict | detail |",
                "|---|---|---|---|---|"]
        for row in needs_human:
            r = row["result"]
            out.append(f"| `{row['plugin']}` | `{row['key']}` | `{row['url']}`"
                       f"{probed_note(row)} | **{r.verdict}** | {r.detail or '-'} |")
        out.append("")

    if moved:
        out += ["## Redirecting elsewhere -- confirm before rewriting", "",
                "Each of these resolves, but not to where the manifest points. "
                "A redirect to a *different registrable domain* is never applied "
                "automatically: it can indicate a rebrand, a mirror, an expired "
                "domain that someone else re-registered, or a takeover. Confirm "
                "the operator is the same before editing.",
                "",
                "| plugin | endpoint | configured | resolves to | first hop |",
                "|---|---|---|---|---|"]
        for row in moved:
            r = row["result"]
            perm = "301/308 permanent" if r.first_status in (301, 308) else \
                   f"{r.first_status} temporary"
            out.append(f"| `{row['plugin']}` | `{row['key']}` | `{row['url']}`"
                       f"{probed_note(row)} | `{r.final_url}` | {perm} |")
        out.append("")

    if data["drift"]:
        out += ["## Manifest / per-plugin file drift", "",
                "`manifest.json` carries endpoints inline *and* points at "
                "`plugins/<id>.json`. The app may read either, so these must agree.",
                ""]
        out += [f"- {d}" for d in data["drift"]]
        out.append("")

    if vantage:
        out += ["<details><summary>Not reachable from CI "
                f"({len(vantage)}) -- informational, probably not broken</summary>",
                "",
                "| plugin | endpoint | configured URL | verdict | detail |",
                "|---|---|---|---|---|"]
        for row in vantage:
            r = row["result"]
            out.append(f"| `{row['plugin']}` | `{row['key']}` | `{row['url']}`"
                       f"{probed_note(row)} | {r.verdict} | {r.detail or '-'} |")
        out += ["", "</details>", ""]

    healthy = sum(1 for r in rows if r["result"].healthy or r["expected_ok"])
    out += ["---",
            f"{healthy}/{len(rows)} endpoints healthy from CI - "
            f"{len(needs_human)} broken - {len(moved)} moved - "
            f"{len(vantage)} unverifiable from CI - {len(data['drift'])} drift."]

    return "\n".join(out), actionable


def gh(*args: str, check: bool = True) -> str:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def upsert_issue(body: str, actionable: bool) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    raw = gh("issue", "list", "--state", "open", "--limit", "100",
             "--json", "number,title", "--repo", repo)
    existing = next((i["number"] for i in json.loads(raw or "[]")
                     if i["title"] == ISSUE_TITLE), None)

    if not actionable:
        if existing:
            gh("issue", "comment", str(existing), "--repo", repo,
               "--body", "All tracked endpoints are healthy or explained as of "
                         "the latest run. Closing; this will reopen automatically "
                         "if problems return.")
            gh("issue", "close", str(existing), "--repo", repo)
            print(f"closed issue #{existing} (nothing actionable)")
        else:
            print("nothing actionable, no issue to update")
        return

    if existing:
        gh("issue", "edit", str(existing), "--repo", repo, "--body", body)
        print(f"updated issue #{existing}")
    else:
        url = gh("issue", "create", "--repo", repo,
                 "--title", ISSUE_TITLE, "--body", body)
        print(f"created issue {url}")


def apply_fixes(data: dict) -> list:
    """Apply and re-verify the narrow set of same-host rewrites."""
    applied = []
    for row in data["rows"]:
        # Only rewrite the value we actually store, never an override probe URL.
        if row["probe_url"] != row["url"]:
            continue
        move = mechanical_move(row["url"], row["result"])
        if not move:
            continue
        new_url, reason = move

        # Re-probe the destination on its own before trusting it. A one-shot
        # 200 during a redirect chain is weaker evidence than a direct hit.
        confirm = probe.probe(new_url)
        if not confirm.healthy:
            print(f"   skip {row['plugin']}.{row['key']}: re-probe of {new_url} "
                  f"returned {confirm.verdict}")
            continue

        applied.append({"plugin": row["plugin"], "key": row["key"],
                        "old": row["url"], "new": new_url, "reason": reason})

    if not applied:
        return []

    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)

    for a in applied:
        for entry in manifest.get("plugins", []):
            if entry.get("id") != a["plugin"]:
                continue
            if entry.get("endpoints", {}).get(a["key"]) == a["old"]:
                entry["endpoints"][a["key"]] = a["new"]
            rel = entry.get("file")
            if not rel:
                continue
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as fh:
                side = json.load(fh)
            if side.get(a["key"]) == a["old"]:
                side[a["key"]] = a["new"]
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(side, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    return applied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="apply same-host mechanical rewrites")
    ap.add_argument("--issue", action="store_true",
                    help="create/update the tracking issue via gh")
    ap.add_argument("--concurrency", type=int, default=probe.DEFAULT_CONCURRENCY)
    ap.add_argument("--max-unreachable-pct", type=int, default=40,
                    help="abort without touching the issue if more than this %% "
                         "of probes are unreachable (broken runner network)")
    ap.add_argument("--json", dest="json_out", default="")
    args = ap.parse_args()

    data = run_checks(args.concurrency)

    # Same reasoning as the catalog scan: if half the internet looks dead from
    # here, the runner is the problem. Rewriting the tracking issue with dozens
    # of false entries would train people to ignore it, so fail loudly instead.
    if data["unreachable_pct"] > args.max_unreachable_pct:
        print(f"\nABORT: {data['unreachable_pct']:.0f}% of endpoints were "
              f"unreachable, over the {args.max_unreachable_pct}% threshold.\n"
              "This runner's network is unhealthy, not the sources. Leaving the "
              "tracking issue untouched and applying nothing.")
        return 1

    applied = apply_fixes(data) if args.apply else []
    body, actionable = build_report(data, applied)

    print("\n" + "=" * 70)
    print(body)
    print("=" * 70)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump({"applied": applied,
                       "rows": [{k: v for k, v in r.items() if k != "result"}
                                | {"result": r["result"].as_dict()}
                                for r in data["rows"]],
                       "drift": data["drift"]}, fh, indent=2)

    step_out = os.environ.get("GITHUB_OUTPUT")
    if step_out:
        with open(step_out, "a", encoding="utf-8") as fh:
            fh.write(f"applied={'true' if applied else 'false'}\n")
            fh.write(f"applied_count={len(applied)}\n")
            desc = "; ".join(f"{a['plugin']}.{a['key']} {a['old']} -> {a['new']}"
                             for a in applied)
            fh.write(f"applied_desc={desc}\n")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(body + "\n")

    if args.issue:
        upsert_issue(body, actionable)

    # A checker that fails the build on an unreachable third-party site would
    # be red every week and get muted. Problems go to the issue; the job only
    # fails if the check itself could not run.
    return 0


if __name__ == "__main__":
    sys.exit(main())
