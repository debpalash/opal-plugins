#!/usr/bin/env python3
"""Re-probe `reachable` across catalog/*.json and log the scan.

The `reachable` field is a probe result from a datacenter IP, and
catalog/README.md already fixes its meaning:

    confirmed        - answered us
    blocked-from-ci  - refused by geo/UA/Cloudflare; NOT dead
    unknown          - we could not tell

This script keeps that vocabulary closed. It never writes a value meaning
"dead", because a scan from a GitHub runner cannot establish that: DNS
failures, TLS resets and timeouts are exactly what hostile-to-datacenter
sites do to us. Those all become `unknown`, not a death certificate.

Two values are provenance, not probe results, and are never overwritten:
`community` and `confirmed-community` record that a human/community source
vouched for the entry.

Usage: refresh_catalog.py [--dry-run] [--concurrency N]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG = os.path.join(ROOT, "catalog")
SCAN_LOG = os.path.join(CATALOG, "SCAN_LOG.md")

BEGIN = "<!-- BEGIN AUTOMATED-SCANS (managed by .github/workflows/catalog-reachability.yml) -->"
END = "<!-- END AUTOMATED-SCANS -->"
KEEP_RUNS = 8

# Human/community provenance -- a CI probe has no authority to overwrite these.
STICKY = {"community", "confirmed-community"}

VERDICT_TO_REACHABLE = {
    probe.OK: "confirmed",
    probe.REDIRECT: "confirmed",
    probe.BLOCKED: "blocked-from-ci",
    probe.SERVER_ERROR: "error-500",
    probe.NOT_FOUND: "unknown",
    probe.REDIRECT_LOOP: "unknown",
    probe.UNREACHABLE: "unknown",
}

# A TCP/TLS reset is an *active* refusal -- something on the path chose to
# kill the connection, which is the signature of a datacenter-IP block. A DNS
# or connect timeout is far more likely to be our own resolver having a bad
# minute, so that stays the honest "unknown".
CURL_EXIT_TO_REACHABLE = {
    35: "blocked-from-ci",   # TLS handshake reset
    56: "blocked-from-ci",   # connection reset by peer
}

# If more than this share of the run comes back unreachable, the runner's
# network is the problem, not 60 independent websites. Bail rather than
# mass-downgrade good data -- the same instinct as the lists shrink gate.
DEFAULT_MAX_UNREACHABLE_PCT = 40


def iter_entries(doc):
    """Yield every dict in every top-level array that carries a `reachable`."""
    for section, items in doc.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and "reachable" in item:
                yield section, item


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--concurrency", type=int, default=probe.DEFAULT_CONCURRENCY)
    ap.add_argument("--max-unreachable-pct", type=int,
                    default=DEFAULT_MAX_UNREACHABLE_PCT,
                    help="abort without writing if more than this %% of probes "
                         "are unreachable (indicates a broken runner network)")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(CATALOG, "*.json")))
    docs, work = {}, []

    for path in files:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        docs[path] = doc
        for section, item in iter_entries(doc):
            url = probe.extract_url(item.get("url"))
            if url and probe.is_probeable(url):
                work.append((path, section, item, url))

    print(f"{len(work)} catalog entries with a probeable url "
          f"across {len(files)} files\n")

    results = probe.probe_many([w[3] for w in work], concurrency=args.concurrency)

    # Second pass: anything unreachable gets one more try, run slowly and
    # serially with longer timeouts. Most first-pass failures under load are
    # our own resolver, not the site.
    retry = [u for u, r in results.items() if r.verdict == probe.UNREACHABLE]
    if retry:
        print(f"retrying {len(retry)} unreachable urls serially "
              "with longer timeouts...")
        for url in retry:
            again = probe.probe(url, timeout=40, connect_timeout=20)
            if again.verdict != probe.UNREACHABLE:
                print(f"  recovered on retry: {url} -> {again.verdict}")
            results[url] = again
        print()

    unreachable = sum(1 for r in results.values() if r.verdict == probe.UNREACHABLE)
    pct = (100 * unreachable / len(results)) if results else 0
    print(f"{unreachable}/{len(results)} unreachable after retry ({pct:.0f}%)\n")
    if results and pct > args.max_unreachable_pct:
        print(f"ABORT: {pct:.0f}% of probes were unreachable, over the "
              f"{args.max_unreachable_pct}% threshold.\n"
              "That pattern means this runner's network is broken, not that "
              "dozens of independent sites died at once. Refusing to "
              "mass-downgrade the catalog; nothing written.")
        return 1

    changes, notable, counts = [], [], {}
    for path, section, item, url in work:
        res = results[url]
        old = item.get("reachable")
        new = VERDICT_TO_REACHABLE.get(res.verdict, "unknown")
        if res.verdict == probe.UNREACHABLE:
            new = CURL_EXIT_TO_REACHABLE.get(res.meta.get("curl_exit"), new)
        counts[new] = counts.get(new, 0) + 1

        if old in STICKY:
            # Provenance beats our vantage point; record only what we saw.
            if res.verdict not in probe.HEALTHY:
                notable.append(f"`{item.get('id', '?')}` ({os.path.basename(path)}): "
                               f"kept `{old}` (community-vouched); CI saw "
                               f"`{res.verdict}`")
            continue

        if res.verdict in (probe.NOT_FOUND, probe.REDIRECT_LOOP):
            notable.append(f"`{item.get('id', '?')}` ({os.path.basename(path)}): "
                           f"{url} -> {res.detail}; recorded `unknown`, "
                           "not a death certificate -- verify by hand")
        if res.verdict == probe.REDIRECT and res.moved:
            notable.append(f"`{item.get('id', '?')}` ({os.path.basename(path)}): "
                           f"{url} redirects to {res.final_url} "
                           "(catalog url left as-is; confirm before editing)")

        if old != new:
            changes.append({"file": os.path.basename(path), "section": section,
                            "id": item.get("id", "?"), "old": old, "new": new,
                            "detail": res.detail})
            item["reachable"] = new

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")

    for path, doc in docs.items():
        if any(c["file"] == os.path.basename(path) for c in changes):
            doc["last_scan"] = now.strftime("%Y-%m-%d")

    for c in changes:
        print(f"  {c['file']}/{c['id']}: {c['old']} -> {c['new']}"
              f"{'  (' + c['detail'] + ')' if c['detail'] else ''}")
    if not changes:
        print("  no reachable-value changes")

    print(f"\ntally: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    if args.dry_run:
        print("\n(dry run -- nothing written)")
        return 0

    for path, doc in docs.items():
        if any(c["file"] == os.path.basename(path) for c in changes):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    write_scan_log(stamp, len(work), counts, changes, notable)

    step_out = os.environ.get("GITHUB_OUTPUT")
    if step_out:
        with open(step_out, "a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if changes else 'false'}\n")
            fh.write(f"change_count={len(changes)}\n")
            fh.write(f"probed={len(work)}\n")
    return 0


def write_scan_log(stamp, probed, counts, changes, notable) -> None:
    """Rewrite only the delimited auto-managed block; never touch prose above."""
    body = [f"### {stamp}", "",
            f"Probed **{probed}** catalog urls from a GitHub runner. "
            + ", ".join(f"`{k}`: {v}" for k, v in sorted(counts.items())) + ".",
            ""]
    if changes:
        body += ["| id | file | was | now |", "|---|---|---|---|"]
        body += [f"| `{c['id']}` | `{c['section']}` in `{c['file']}` "
                 f"| `{c['old']}` | `{c['new']}` |" for c in changes]
        body.append("")
    else:
        body += ["No `reachable` values changed.", ""]
    if notable:
        body += ["Notes:", ""] + [f"- {n}" for n in notable] + [""]
    entry = "\n".join(body)

    existing = ""
    if os.path.exists(SCAN_LOG):
        with open(SCAN_LOG, encoding="utf-8") as fh:
            existing = fh.read()

    if BEGIN in existing and END in existing:
        head, rest = existing.split(BEGIN, 1)
        block, tail = rest.split(END, 1)
    else:
        head = existing.rstrip() + (
            "\n\n## Automated reachability scans\n\n"
            "Written by `.github/workflows/catalog-reachability.yml`. A probe "
            "runs from a datacenter IP, so `blocked-from-ci` and `unknown` mean "
            "*we could not see the site*, not that it is gone. Everything above "
            "this line is hand-written and is never modified by the workflow.\n\n")
        block, tail = "", "\n"

    runs = [r for r in block.split("\n### ") if r.strip()]
    runs = [entry] + [("### " + r).rstrip() + "\n" for r in runs]
    kept = runs[:KEEP_RUNS]

    with open(SCAN_LOG, "w", encoding="utf-8") as fh:
        fh.write(head + BEGIN + "\n\n" + "\n".join(kept).rstrip()
                 + "\n\n" + END + tail.rstrip() + "\n")


if __name__ == "__main__":
    sys.exit(main())
